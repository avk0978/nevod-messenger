import Foundation
import WebRTC
import CallKit
import AVFoundation
import CoreMedia
import UIKit
import UserNotifications

// MARK: - TURN credentials (received from the Nevod node)

struct TurnInfo {
    let url: String
    let username: String
    let credential: String
}

// MARK: - Call state

enum CallQuality { case poor, medium, good }

enum CallState: CustomStringConvertible {
    case idle
    case outgoing(contactName: String, cellId: String)   // establishing, no ring yet
    case ringing(contactName: String, cellId: String)    // remote is ringing
    case incoming(callerName: String, cellId: String)    // showing accept/reject
    case connecting(contactName: String, cellId: String) // ICE negotiating
    case active(contactName: String, cellId: String)     // audio flowing
    // Transient — shown for a couple seconds after the callee reports busy (either their app
    // was already on another Nevod call, or CallKit itself is occupied), then auto-returns to
    // .idle. Exists purely so the caller sees *why* their call screen just disappeared instead
    // of it silently vanishing, which testing showed reads as "the app broke", not "busy".
    case busy(contactName: String)

    var isIdle: Bool { if case .idle = self { return true }; return false }

    var description: String {
        switch self {
        case .idle: return "idle"
        case .outgoing(_, let id): return "outgoing(\(id.prefix(8)))"
        case .ringing(_, let id): return "ringing(\(id.prefix(8)))"
        case .incoming(_, let id): return "incoming(\(id.prefix(8)))"
        case .connecting(_, let id): return "connecting(\(id.prefix(8)))"
        case .active(_, let id): return "active(\(id.prefix(8)))"
        case .busy: return "busy"
        }
    }

    var contactName: String? {
        switch self {
        case .idle: return nil
        case .outgoing(let n, _), .ringing(let n, _),
             .connecting(let n, _), .active(let n, _): return n
        case .incoming(let n, _): return n
        case .busy(let n): return n
        }
    }
    var cellId: String? {
        switch self {
        case .idle, .busy: return nil
        case .outgoing(_, let id), .ringing(_, let id), .incoming(_, let id),
             .connecting(_, let id), .active(_, let id): return id
        }
    }
}

// MARK: - Thread-safe flag

/// CXProviderDelegate's didActivate/didDeactivate fire on CallKit's own (non-isolated) audio
/// thread and need a synchronous read of audioReadyForCall — `nonisolated(unsafe)` would be the
/// natural fit but needs Swift 5.10 (Xcode 15.3+); this lock-backed box is the equivalent that
/// also builds on Xcode 15.2.
private final class AtomicBool: @unchecked Sendable {
    private let lock = NSLock()
    private var value: Bool
    init(_ initial: Bool) { value = initial }
    var current: Bool {
        get { lock.lock(); defer { lock.unlock() }; return value }
        set { lock.lock(); defer { lock.unlock() }; value = newValue }
    }
}

// MARK: - Frame-counting capture delegate proxy

/// Wraps the real capture delegate (an RTCVideoSource) purely to count/log real camera frames
/// as they arrive from AVCaptureSession — added 2026-08-06 to pin down a confirmed asymmetry
/// where the call ANSWERER's own outgoing video sits at framesSent=0 for an entire call despite
/// AVCaptureSession reporting isRunning=true and startCapture's completionHandler reporting no
/// error, while the caller's (offerer's) outgoing video works every time, regardless of which
/// side turns their camera on first. If frameCount here never grows, the failure is at the
/// camera/OS level, before WebRTC ever sees a frame (rules out anything SDP/transceiver-related).
/// If it grows normally, the failure is further downstream (RTCVideoSource → encoder → RTP
/// sender), which would instead point at something specific to the answerer's negotiated
/// transceiver.
private final class FrameCountingCapturerDelegate: NSObject, RTCVideoCapturerDelegate {
    private let inner: RTCVideoCapturerDelegate
    private var frameCount = 0
    init(inner: RTCVideoCapturerDelegate) { self.inner = inner }
    func capturer(_ capturer: RTCVideoCapturer, didCapture frame: RTCVideoFrame) {
        frameCount += 1
        if frameCount == 1 || frameCount % 60 == 0 {
            nlog("call capturer didCapture frame #\(frameCount) \(frame.width)x\(frame.height)")
        }
        inner.capturer(capturer, didCapture: frame)
    }
}

// MARK: - CallManager

@MainActor
final class CallManager: NSObject, ObservableObject {

    @Published var state: CallState = .idle {
        // File chunks wait and the connection to the node stays put while a call rings or is
        // up — see NevdClient.callInProgress.
        didSet { NevdClient.callInProgress = !state.isIdle }
    }
    @Published var callDuration: Int = 0
    @Published var isMuted: Bool = false
    // Manually traced every write site in this file (toggleSpeaker(), reset()) and found
    // nothing that explains the user's direct, repeated visual observation 2026-08-03 of the
    // "Динамик" button going dark on its own a few seconds after turning it on, with the
    // call still ongoing (reset() would end the call entirely, which isn't what's reported).
    // didSet catches every single mutation regardless of call site — trust the runtime over
    // another manual code-reading pass that's already been wrong twice this investigation.
    @Published var isSpeaker: Bool = false {
        didSet {
            guard oldValue != isSpeaker else { return }
            nlog("call isSpeaker CHANGED \(oldValue) -> \(isSpeaker)")
        }
    }
    // Drives the Bluetooth button's highlight — synced the same passive way as isSpeaker
    // (see observeRouteChangesIfNeeded), never written to directly. iOS auto-routes to
    // Bluetooth the moment a paired device is reachable, so "route is currently Bluetooth"
    // doubles as "a Bluetooth device is connected" without a second, separately-maintained flag.
    @Published var isBluetooth: Bool = false
    @Published var quality: CallQuality? = nil
    // Video needs the screen actually on to be useful (unlike audio calls, which work fine
    // with the screen dark) — iOS's normal auto-lock timeout was confirmed to fire mid video
    // call otherwise. didSet here (rather than setting isIdleTimerDisabled at each of the two
    // call sites that flip isVideoCall — enableVideoMidCall()/receiveVideoOn() — plus reset())
    // covers all of them from one place and can't drift out of sync if a future call site adds
    // a third way to enter/leave video.
    @Published var isVideoCall: Bool = false {
        didSet {
            guard oldValue != isVideoCall else { return }
            UIApplication.shared.isIdleTimerDisabled = isVideoCall
        }
    }
    @Published var isCameraOff: Bool = false
    @Published var isFrontCamera: Bool = true
    @Published var localVideoTrack: RTCVideoTrack?
    @Published var remoteVideoTrack: RTCVideoTrack?

    weak var store: AppStore?
    var turnInfo: TurnInfo?

    // WebRTC — factory is expensive, initialise once. audioDevice replaces WebRTC's built-in
    // iOS ADM entirely — see NevodAudioDevice's own doc comment for why (its internal
    // RTCAudioSession silently resets overrideOutputAudioPort on every route change, which is
    // what caused the native CallKit Speaker button to self-flip).
    private static let audioDevice = NevodAudioDevice()
    private static let factory: RTCPeerConnectionFactory = {
        RTCInitializeSSL()
        return RTCPeerConnectionFactory(
            encoderFactory: RTCDefaultVideoEncoderFactory(),
            decoderFactory: RTCDefaultVideoDecoderFactory(),
            audioDevice: audioDevice
        )
    }()

    private var pc: RTCPeerConnection?
    private var localAudio: RTCAudioTrack?
    private var localVideoCapturer: RTCCameraVideoCapturer?
    // RTCVideoCapturer.delegate is held weak by the capturer (standard WebRTC pattern) — this
    // keeps FrameCountingCapturerDelegate alive for the capturer's lifetime. See its own doc
    // comment for why it exists (2026-08-06 diagnostic for the answerer-side outgoing-video bug).
    private var frameCountingDelegate: FrameCountingCapturerDelegate?
    private var ringbackPlayer: AVAudioPlayer?
    private var pendingCandidates: [RTCIceCandidate] = []
    private let audioReadyForCall = AtomicBool(false)
    // Re-asserting .speaker only for the first ~2.5s of a call (the burst below) leaves
    // nothing to catch iOS silently rerouting audio away from Speaker LATER in a call —
    // confirmed to happen well past that window (reported by user 2026-08-02: the speaker
    // toggle "turns itself off" some time into an otherwise-working call). Observing route
    // changes for the call's whole duration and re-applying .speaker whenever the user
    // hasn't explicitly chosen the earpiece (isSpeaker still true) covers that.
    private var routeChangeObserver: NSObjectProtocol?
    // Guards watchForStaleConnection()'s one-time reconnect+retry so a call that's
    // genuinely just unanswered (not a dead socket) doesn't get stuck retrying forever.
    private var staleConnectionRetried = false
    // This call's offer and the ICE candidates sent with it, as sent — the retry resends
    // exactly these rather than making a new offer (see watchForStaleConnection).
    private var sentOffer: String?
    private var sentIce: [String] = []
    private var hasRemoteDesc = false
    private var pendingSDP: RTCSessionDescription?
    private var hangupSent = false

    // CallKit
    private let provider: CXProvider
    private let callController = CXCallController()
    private var callUUID = UUID()

    // Set when a VoIP push already reported this call to CallKit (callUUID assigned there)
    // before the real offer (with SDP) arrived over the WebSocket — receiveOffer() checks
    // this to reuse callUUID instead of reporting a second, duplicate incoming call.
    private var pendingPushCallerId: String?

    // Set when the user answers via CallKit's UI before the real offer (buffered on the
    // node, only delivered once the socket reconnects) has actually arrived — performAccept
    // has no SDP to act on yet. CallKit already dismissed its UI as "answered" at that point,
    // so there's no second accept coming; receiveOffer() finishes the job once the SDP shows up.
    private var acceptPending = false

    // Tasks replace Timer to avoid @MainActor/Sendable conflicts
    private var durationTask: Task<Void, Never>?
    private var timeoutTask: Task<Void, Never>?
    private var statsTask: Task<Void, Never>?
    private var prevBytesReceived: Int64 = 0
    private var prevBytesSent: Int64 = 0
    private var prevStatsTime: Date = .distantPast

    // Call log bookkeeping — set at the start of a call (outgoing dial, or the moment we
    // first learn of an incoming one), read once in reset() (the one true endpoint every
    // termination path funnels through — timeout, hangup, reject, busy, or the system UI
    // ending the call via CXEndCallAction) to write a single CallLogEntry per call.
    private var callStartedAt: Date?
    private var callIsOutgoingFlag = false
    private var callWasAnswered = false

    override init() {
        let cfg = CXProviderConfiguration()
        cfg.supportsVideo = true
        cfg.maximumCallGroups = 1
        cfg.maximumCallsPerCallGroup = 1
        cfg.supportedHandleTypes = [.generic]
        provider = CXProvider(configuration: cfg)
        super.init()
        provider.setDelegate(self, queue: .main)
    }

    // MARK: - Outgoing call

    // There is no separate "video call" entry point (only a single Call button; video is
    // always a later, user-initiated action — see enableVideoMidCall). Historically (until
    // 2026-08-05) the video transceiver itself was also deferred to a mid-call renegotiation,
    // specifically to keep the very FIRST offer small — a video call's larger SDP (2 media
    // sections vs 1) was confirmed via device logs 2026-08-01 to reliably take long enough,
    // combined with however many seconds a real person takes to notice and answer their
    // phone, that by the time setActive(true) was attempted, CallKit had moved into a state
    // where it *permanently* refused it (a different, non-transient error than the
    // audio-only case, which always eventually clears on retry).
    //
    // setupPC() now adds the video transceiver upfront on every call too (matching how
    // Telegram-iOS's OngoingCallThreadLocalContext negotiates its media channels once at call
    // setup, then just attaches/detaches local capture — see enableVideoMidCall()'s own doc
    // comment for the full reasoning) — WITHOUT a track, so no camera/AVCaptureSession access
    // happens at call setup either way. This does make the first SDP bigger again for every
    // call than the audio-first design did; the audio-activation retry logic has gotten much
    // more robust since the original 2026-08-01 finding (see NevodAudioDevice/AUDIO_CALLS.md),
    // which is the bet this redesign is making — first thing to re-verify after this change is
    // that a cold VoIP-push launch still activates audio reliably.
    func startCall(to cellId: String, contactName: String) {
        guard state.isIdle else { return }
        // Defense-in-depth: every UI call button already disables itself for a
        // deleted-identity contact (see AppStore.isIdentityDeleted), this just guarantees no
        // future call site can slip through without that check.
        guard store?.isIdentityDeleted(cellId: cellId) != true else { return }
        AVAudioApplication.requestRecordPermission { granted in
            nlog("call mic permission=\(granted)")
        }
        callUUID = UUID()
        hangupSent = false
        staleConnectionRetried = false
        sentOffer = nil
        sentIce = []
        audioReadyForCall.current = false  // audio enabled only after answer arrives
        state = .outgoing(contactName: contactName, cellId: cellId)
        callStartedAt = Date()
        callIsOutgoingFlag = true
        callWasAnswered = false
        isVideoCall = false
        isCameraOff = false
        isFrontCamera = true
        nlog("call startCall to=\(cellId.prefix(8)) hasTurn=\(turnInfo != nil)")

        Self.audioDevice.configureSession()   // before the call exists — see configureSession
        let handle = CXHandle(type: .generic, value: contactName)
        let action = CXStartCallAction(call: callUUID, handle: handle)
        callController.request(CXTransaction(action: action)) { _ in }

        // TURN credentials are fetched asynchronously right after the socket (re)connects —
        // if we just reopened the app (e.g. it was backgrounded and just woke up), there's a
        // brief window where turnInfo is still nil. setupPC() falls back to zero ICE servers
        // in that case, which only works on the same LAN — over the internet ICE fails
        // outright. Confirmed via device logs 2026-08-02: two calls placed in exactly this
        // window both hit ICE state=failed. A short bounded wait covers the common case; if
        // it truly never arrives, dial anyway (LAN-only fallback, per setupPC's own comment).
        Task { @MainActor [weak self] in
            guard let self else { return }
            var waited = 0
            while self.turnInfo == nil && waited < 3000 {
                try? await Task.sleep(for: .milliseconds(200))
                waited += 200
                guard case .outgoing = self.state else { return }
            }
            self.dial(cellId: cellId)
        }
    }

    private func dial(cellId: String) {
        timeoutTask?.cancel()
        watchForStaleConnection(cellId: cellId)
        setupPC()

        // No OfferToReceiveAudio/Video mandatory constraints — legacy pre-Unified-Plan
        // mechanism, superseded by explicit transceiver direction (both audio and video
        // transceivers already exist with the right direction by the time setupPC() returns,
        // see its own comment on the upfront video transceiver).
        let constraints = RTCMediaConstraints(mandatoryConstraints: nil, optionalConstraints: nil)
        pc?.offer(for: constraints) { [weak self] sdp, err in
            guard let self, let sdp else {
                nlog("call offer FAILED err=\(String(describing: err))")
                return
            }
            Task { @MainActor in
                nlog("call offer created type=\(sdp.type.rawValue) sdpLen=\(sdp.sdp.count)")
                self.pc?.setLocalDescription(sdp) { error in
                    if let error { nlog("call offer setLocalDescription FAILED err=\(error)") }
                }
                // Include our identity so receiver can show our name and send signals back
                // even if they don't have us in their contacts/nodeMembers yet (fresh session)
                let callerName = IdentityStore.displayName
                let callerEncPub = self.store?.identity?.encPub
                    .map { String(format: "%02x", $0) }.joined() ?? ""
                let dict: [String: Any] = [
                    "type": "offer", "sdp": sdp.sdp,
                    "callerName": callerName, "callerEncPub": callerEncPub
                ]
                guard let data = try? JSONSerialization.data(withJSONObject: dict),
                      let json = String(data: data, encoding: .utf8) else { return }
                self.sentOffer = "vcall:offer:\(json)"
                try? await self.store?.sendCallOffer("vcall:offer:\(json)", to: cellId)
            }
        }

        timeoutTask = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(30))
            guard !Task.isCancelled else { return }
            self?.endCall(.unanswered)
        }
    }

    /// NevdClient.isConnected can be stale — true even though the underlying socket already
    /// died silently (see AppStore.forceReconnect's doc comment). If a call we just dialed is
    /// still sitting in .outgoing 12 seconds later with nothing at all back from the peer, the
    /// offer has probably not left this device. One-time recovery: a fresh connection, then
    /// the SAME offer and candidates again, rather than burning the full 30s dial timeout.
    ///
    /// Not sooner: a callee whose phone sleeps needs 5–7 s (VoIP push, app start, connect)
    /// before it can ring back. Not a new offer: at 5 s this used to dial again with a new
    /// peer connection, the callee answered the first offer, which no longer matched, and the
    /// answered call stayed silent (device logs 2026-10-21, twice). The callee ignores a
    /// repeated offer for a call it already has.
    private func watchForStaleConnection(cellId: String) {
        guard !staleConnectionRetried else { return }
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(12))
            guard let self, case .outgoing = self.state, !self.staleConnectionRetried else { return }
            self.staleConnectionRetried = true
            nlog("call watchForStaleConnection — no ring after 12s, reconnecting and resending the same offer")
            self.store?.forceReconnect()
            try? await Task.sleep(for: .milliseconds(300))   // let the old socket go first
            var waited = 0
            while self.store?.client?.isConnected != true && waited < 5000 {
                try? await Task.sleep(for: .milliseconds(200))
                waited += 200
            }
            guard case .outgoing = self.state, let offer = self.sentOffer else { return }
            try? await self.store?.sendCallOffer(offer, to: cellId)
            for ice in self.sentIce {
                try? await self.store?.sendSignal(ice, to: cellId)
            }
        }
    }

    // MARK: - Signal dispatcher (called by AppStore)

    func handleSignal(from cellId: String, signal: String) {
        let parts = signal.split(separator: ":", maxSplits: 2).map(String.init)
        guard parts.count >= 2, parts[0] == "vcall" else { return }
        let type = parts[1]
        let payload = parts.count > 2 ? parts[2] : ""
        nlog("call handleSignal type=\(type) from=\(cellId.prefix(8)) state=\(state)")

        switch type {
        case "offer":  receiveOffer(from: cellId, json: payload)
        case "answer": receiveAnswer(json: payload)
        case "ice":    receiveICE(json: payload)
        case "video_on": receiveVideoOn()
        case "ring":
            if case .outgoing(let name, let id) = state {
                state = .ringing(contactName: name, cellId: id)
                startRingback()
                // The 30s "unanswered" timer from startCall() was measuring from dial
                // time, not from when the callee's phone actually started ringing — if
                // signaling took a while to reach them (e.g. their app needed relaunching),
                // it could expire right as they picked up. Give a fresh window from the
                // moment we know they're actually ringing — 60s, matching receiveOffer's own
                // answer window on the callee side (confirmed via device logs 2026-07-30:
                // a 30s window here raced ahead of and closed the call while the callee,
                // correctly still within their 60s, was legitimately still ringing).
                timeoutTask?.cancel()
                timeoutTask = Task { @MainActor [weak self] in
                    try? await Task.sleep(for: .seconds(60))
                    guard !Task.isCancelled else { return }
                    self?.endCall(.unanswered)
                }
            }
        case "reject":
            switch state {
            case .outgoing, .ringing: endCall(.remoteEnded)
            default: break
            }
        case "hangup": endCall(.remoteEnded)
        case "busy":
            switch state {
            case .outgoing, .ringing: endCall(.busy)
            default: break
            }
        default: break
        }
    }

    // MARK: - Incoming

    /// Best-known display name for `cellId` — prefers what WE call them locally (a saved
    /// contact, or a fellow member of our own node) over whatever they claim about
    /// themselves (VoIP push payload / offer's callerName, which — being self-declared and
    /// possibly cross-node — only reflects the name they registered under, not necessarily
    /// what the receiving user actually recognizes them by). `callerId` alone is enough to
    /// look this up even from a VoIP push, before the real (E2E-encrypted) offer arrives.
    private func resolvedCallerName(cellId: String, fallback: String?) -> String {
        if let c = store?.contacts.first(where: { $0.cellId == cellId }), !c.displayName.isEmpty {
            nlog("call resolvedCallerName cellId=\(cellId.prefix(8)) source=contact alias=\(c.alias) -> \(c.displayName)")
            return c.displayName
        }
        if let m = store?.nodeMembers.first(where: { $0.cellId == cellId }), !m.displayName.isEmpty {
            nlog("call resolvedCallerName cellId=\(cellId.prefix(8)) source=nodeMember -> \(m.displayName)")
            return m.displayName
        }
        if let n = fallback, !n.isEmpty {
            nlog("call resolvedCallerName cellId=\(cellId.prefix(8)) source=fallback -> \(n)")
            return n
        }
        nlog("call resolvedCallerName cellId=\(cellId.prefix(8)) source=none -> raw id")
        return String(cellId.prefix(8)) + "…"
    }

    /// Called the instant a VoIP push arrives (app may have been fully killed) — must
    /// synchronously report to CallKit per Apple's contract. The real SDP offer is still
    /// E2E encrypted and hasn't arrived yet, but callerId is already enough to resolve a
    /// locally-known name (see resolvedCallerName). The eventual real offer (receiveOffer,
    /// once the socket reconnects and the node flushes its buffer) fills in the rest and
    /// reuses this same call UUID.
    func reportIncomingCallFromPush(callerId: String, callerName: String) {
        nlog("call reportIncomingCallFromPush callerId=\(String(callerId.prefix(8))) callerName=\(callerName) state=\(state)")
        let name = resolvedCallerName(cellId: callerId, fallback: callerName)
        let update = CXCallUpdate()
        update.remoteHandle = CXHandle(type: .generic, value: name)
        update.localizedCallerName = name
        update.hasVideo = false

        if !state.isIdle && state.cellId == callerId {
            // Redelivered/duplicate VoIP push for the call ALREADY ringing/connecting/active
            // with this exact caller (APNs redelivery, or the caller's own client retry) —
            // confirmed via two independent real-world device logs 2026-08-27 that reporting
            // this as a brand-new CXCall (fresh random UUID) and then immediately ending that
            // second call disrupts the FIRST (real) call's already-activating audio session:
            // silent call, speaker toggle does nothing, then a forced hangup a few seconds in
            // — exactly the "works on the next call once the app is warm" pattern both times.
            // Still must call reportNewIncomingCall — Apple's contract requires reporting
            // every VoIP push, no exceptions — but reusing the EXISTING call's own UUID
            // instead of a fresh one makes CallKit recognize this as the SAME call it already
            // knows about (errors out harmlessly) instead of creating a second overlapping
            // call that then has to be torn down.
            nlog("call reportIncomingCallFromPush duplicate for in-progress call, reusing uuid=\(callUUID)")
            provider.reportNewIncomingCall(with: callUUID, update: update) { err in
                nlog("call reportNewIncomingCall(duplicate) err=\(String(describing: err))")
            }
            return
        }

        let uuid = UUID()
        if store?.isBlocked(callerId) == true {
            // The home node normally never sends a VoIP push for a blocked caller
            // (chat_prefs "blocked", node/router.py) — this covers a block made while offline
            // and not yet synced. PushKit still requires every VoIP push be reported, so report
            // and end it at once; no signal goes back, the caller just gets no answer.
            nlog("call reportIncomingCallFromPush — caller \(callerId.prefix(8)) is blocked, ending")
            provider.reportNewIncomingCall(with: uuid, update: update) { [weak self] _ in
                self?.callController.request(CXTransaction(action: CXEndCallAction(call: uuid))) { _ in }
            }
            return
        }
        guard state.isIdle else {
            // Already on a DIFFERENT call — must still report every VoIP push (Apple's
            // contract), then immediately end it since there's no call-waiting support here.
            nlog("call reportIncomingCallFromPush busy — reporting then ending uuid=\(uuid)")
            provider.reportNewIncomingCall(with: uuid, update: update) { [weak self] err in
                nlog("call reportNewIncomingCall(busy) err=\(String(describing: err))")
                self?.callController.request(CXTransaction(action: CXEndCallAction(call: uuid))) { _ in }
            }
            Task { try? await store?.sendSignal("vcall:busy", to: callerId) }
            return
        }

        callUUID = uuid
        pendingPushCallerId = callerId
        hangupSent = false
        callStartedAt = Date()
        callIsOutgoingFlag = false
        callWasAnswered = false
        // Every call negotiates audio-only first regardless of call type (see startCall's
        // doc comment) — video is always a later, separate mid-call event, never known at
        // the moment a push arrives.
        isVideoCall = false
        isCameraOff = false
        isFrontCamera = true
        state = .incoming(callerName: name, cellId: callerId)
        Self.audioDevice.configureSession()   // before reporting — see configureSession
        provider.reportNewIncomingCall(with: uuid, update: update) { err in
            nlog("call reportNewIncomingCall err=\(String(describing: err)) uuid=\(uuid)")
        }

        // Safety net: if the real offer never shows up (buffered packet lost, decrypt
        // failure, etc.) don't leave CallKit's UI showing a call forever.
        timeoutTask = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(30))
            guard !Task.isCancelled, self?.pendingPushCallerId == callerId,
                  self?.callUUID == uuid else { return }
            self?.pendingPushCallerId = nil
            self?.endCall(.unanswered)
        }
    }

    private func receiveOffer(from cellId: String, json: String) {
        let reusingPendingCall = (pendingPushCallerId == cellId)
        if !state.isIdle && !reusingPendingCall {
            if state.cellId == cellId {
                // Retransmitted/duplicate offer for the call already in progress with this
                // exact peer (node resend, or the caller's own retry) — nothing new to do.
                // Confirmed via device logs 2026-08-21: without this check, this fell through
                // to the busy branch below and sent a spurious vcall:busy to a caller mid-
                // connect, right as their call was actually succeeding (the real vcall:answer
                // went out moments later).
                nlog("call receiveOffer ignoring duplicate offer from=\(cellId.prefix(8)) state=\(state)")
                return
            }
            Task { try? await store?.sendSignal("vcall:busy", to: cellId) }
            return
        }
        guard let sdp = parseSDP(json, type: .offer) else { return }

        // Extract callerName + callerEncPub embedded in the offer by the remote side. The
        // offer's SDP itself now always includes an (inactive, trackless) video transceiver
        // (see startCall's doc comment) — but nobody's actually sending video yet at this
        // point regardless, so isVideoCall correctly stays false here; it only flips once a
        // genuine vcall:video_on signal arrives or the local user taps the camera button.
        var offerCallerName: String? = nil
        if let data = json.data(using: .utf8),
           let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            offerCallerName = dict["callerName"] as? String
            if let hexPub = dict["callerEncPub"] as? String, !hexPub.isEmpty,
               let encPubData = Hex.decode(hexPub) {
                store?.tempEncPubs[cellId] = encPubData
            }
        }
        let name = resolvedCallerName(cellId: cellId, fallback: offerCallerName)
        if reusingPendingCall {
            // Already reported to CallKit via reportIncomingCallFromPush() — same callUUID,
            // don't report a second time. callStartedAt etc. were already set there too.
            pendingPushCallerId = nil
        } else {
            callUUID = UUID()
            callStartedAt = Date()
            callIsOutgoingFlag = false
            callWasAnswered = false
            let update = CXCallUpdate()
            update.remoteHandle = CXHandle(type: .generic, value: name)
            update.localizedCallerName = name
            update.hasVideo = false
            Self.audioDevice.configureSession()   // before reporting — see configureSession
            provider.reportNewIncomingCall(with: callUUID, update: update) { _ in }
        }
        hangupSent = false
        pendingSDP = sdp
        state = .incoming(callerName: name, cellId: cellId)

        if acceptPending {
            // User already answered via CallKit's UI before this (buffered) offer arrived —
            // finish the job now; there's no second accept coming.
            nlog("call receiveOffer — completing deferred accept")
            acceptPending = false
            completeAccept(name: name, cellId: cellId, offer: sdp)
            return
        }

        Task { try? await store?.sendSignal("vcall:ring", to: cellId) }

        timeoutTask = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(60))
            guard !Task.isCancelled else { return }
            self?.endCall(.unanswered)
        }
    }

    // Called from CXAnswerCallAction delegate AND from in-app accept button
    // In-app: triggers CXAnswerCallAction → delegate → performAccept
    func accept() {
        let action = CXAnswerCallAction(call: callUUID)
        callController.request(CXTransaction(action: action)) { _ in }
    }

    // Actual WebRTC setup (called from CXProviderDelegate)
    fileprivate func performAccept() {
        guard case .incoming(let name, let cellId) = state else { return }
        guard let offer = pendingSDP else {
            // Real offer hasn't arrived yet (still buffered on the node, waiting for the
            // socket to reconnect) — nothing to set up yet. CallKit's UI is already gone at
            // this point, so remember the request; receiveOffer() will finish it below.
            nlog("call performAccept — no pendingSDP yet, deferring")
            acceptPending = true
            return
        }
        completeAccept(name: name, cellId: cellId, offer: offer)
    }

    private func completeAccept(name: String, cellId: String, offer: RTCSessionDescription) {
        timeoutTask?.cancel()
        state = .connecting(contactName: name, cellId: cellId)
        // Audio itself starts only when CallKit calls didActivate (Apple's contract — see
        // NevodAudioDevice.configureSession); we no longer activate the session ourselves.
        audioReadyForCall.current = true
        observeRouteChangesIfNeeded()

        // includeVideoTransceiver: false — see setupPC()'s own doc comment. The incoming
        // offer's m=video line makes setRemoteDescription(offer) below auto-create the video
        // transceiver instead; pre-adding our own here was confirmed (build 81 device logs) to
        // leave a second, orphaned one that addLocalVideoTrack() was picking by mistake.
        setupPC(includeVideoTransceiver: false)
        pc?.setRemoteDescription(offer) { [weak self] error in
            guard let self else { return }
            if let error { nlog("call setRemoteDescription(offer) FAILED err=\(error)") }
            Task { @MainActor in
                self.hasRemoteDesc = true
                self.pendingCandidates.forEach { self.pc?.add($0) { _ in } }
                self.pendingCandidates.removeAll()

                // The transceiver setRemoteDescription(offer) just auto-created for the
                // incoming m=video line defaults to recvOnly (we never pre-declared an intent
                // to send). Promote it to sendRecv HERE, before creating the answer, so the
                // answer itself already grants us send capability in this same round trip — no
                // extra renegotiation needed later when the user taps "video" (which is the
                // whole point of this redesign). Confirmed via device logs (build 81) this is
                // the ONLY video transceiver at this point now that setupPC() no longer
                // pre-adds a second one.
                if let vt = self.videoTransceiver(), vt.direction != .sendRecv {
                    var err: NSError?
                    vt.setDirection(.sendRecv, error: &err)
                    if let err { nlog("call setDirection(.sendRecv) on answer-side video transceiver FAILED err=\(err)") }
                }
                for t in self.pc?.transceivers ?? [] {
                    nlog("call transceiver post-setRemoteDescription(offer) kind=\(t.mediaType.rawValue) mid=\(t.mid) dir=\(t.direction.rawValue) senderTrackId=\(t.sender.track?.trackId ?? "nil") receiverTrackId=\(t.receiver.track?.trackId ?? "nil")")
                }

                // No mandatory constraints — see dial()'s matching comment. The video
                // transceiver from setupPC() already negotiates recvRecv both ways; answering
                // just accepts whatever the offer (including its video m-line) proposed.
                let constraints = RTCMediaConstraints(mandatoryConstraints: nil, optionalConstraints: nil)
                self.pc?.answer(for: constraints) { sdp, err in
                    guard let sdp else {
                        nlog("call answer FAILED err=\(String(describing: err))")
                        return
                    }
                    Task { @MainActor in
                        self.pc?.setLocalDescription(sdp) { error in
                            if let error { nlog("call answer setLocalDescription FAILED err=\(error)") }
                        }
                        let json = self.sdpJSON(sdp)
                        try? await self.store?.sendSignal("vcall:answer:\(json)", to: cellId)
                    }
                }
            }
        }
    }

    /// Registered once per call (guarded by routeChangeObserver == nil — called from
    /// completeAccept/receiveAnswer and didActivate, whichever comes first).
    ///
    /// Passively SYNCS isSpeaker to whatever the real route now is, instead of fighting to
    /// force the route back to whatever isSpeaker last said. This replaced an
    /// enforce-in-both-directions version (2026-08-03) that turned out to actively break a
    /// real use case: on a call where our own CallOverlay isn't foregrounded (confirmed
    /// platform limitation, see bringAppToForeground's removal — the user is looking at
    /// iOS's own native CallKit call screen instead), the ONLY speaker control available is
    /// CallKit's own native button, which calls the exact same overrideOutputAudioPort API we
    /// do. Our old "enforce" logic couldn't tell that apart from unwanted drift and kept
    /// reverting the user's genuine, deliberate choice within milliseconds — confirmed via
    /// device logs 2026-08-03: pressing the native speaker toggle showed reason=4 (route
    /// really changed), immediately followed by our own "corrected route toward isSpeaker"
    /// undoing it, because our internal isSpeaker flag never knew the native button was
    /// pressed. Since isSpeaker's only real job is to drive our OWN button's color when our
    /// UI IS visible, just keeping it truthful to reality is correct in all cases: it
    /// reflects our own toggleSpeaker() calls (no-op, already matches), CallKit's native
    /// button (now respected instead of fought), and genuine WebRTC/OS drift (visible as a
    /// color change instead of invisibly fought — a real change either way, so honesty is the
    /// least-surprising behavior).
    private func observeRouteChangesIfNeeded() {
        guard routeChangeObserver == nil else { return }
        routeChangeObserver = NotificationCenter.default.addObserver(
            forName: AVAudioSession.routeChangeNotification, object: nil, queue: .main
        ) { [weak self] note in
            // Unwrap BEFORE creating the Task — capturing the still-weak/optional self
            // directly inside a concurrently-executing closure is what triggers "Reference
            // to captured var 'self'"; a plain immutable `let self` captured from here on is
            // safe to hand into the Task below.
            guard let self else { return }
            // AVAudioSessionRouteChangeReasonKey tells us WHY this fired — .override (5) is
            // our own overrideOutputAudioPort call causing this same notification, anything
            // else (categoryChange, newDeviceAvailable, routeConfigurationChange, ...) is iOS
            // acting on its own. Logging unconditionally (not just when we re-assert) so a
            // real device test shows the full sequence of what's actually happening around a
            // toggleSpeaker() call, instead of guessing — 2026-08-03: the previous two fixes
            // (default-to-quiet's isSpeaker-forcing removal, then routing overrides through
            // RTCAudioSession's lock) both looked right on paper but neither actually fixed
            // "toggle changes color, second+ press stops changing the real route."
            let reasonValue = (note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt) ?? 999
            // queue: .main above guarantees this runs on the main thread, but that's a
            // Dispatch/OperationQueue guarantee, not one the Swift actor system can see —
            // the closure itself is still nonisolated, so touching @MainActor state
            // (isSpeaker, routeDescription()) directly here is a Swift 6 error. Hop into a
            // real @MainActor Task, same pattern used by the CXProviderDelegate methods
            // below for the same reason.
            Task { @MainActor in
                let outs = AVAudioSession.sharedInstance().currentRoute.outputs
                let isOnSpeaker = outs.contains(where: { $0.portType == .builtInSpeaker })
                let isOnBluetooth = outs.contains(where: {
                    $0.portType == .bluetoothHFP || $0.portType == .bluetoothA2DP || $0.portType == .bluetoothLE
                })
                nlog("call routeChange fired reason=\(reasonValue) isSpeaker=\(self.isSpeaker) isOnSpeaker=\(isOnSpeaker) isOnBluetooth=\(isOnBluetooth) \(self.routeDescription())")
                if self.isBluetooth != isOnBluetooth { self.isBluetooth = isOnBluetooth }
                guard self.isSpeaker != isOnSpeaker else { return }
                self.isSpeaker = isOnSpeaker
                nlog("call routeChange synced isSpeaker -> \(self.isSpeaker) \(self.routeDescription())")
            }
        }
    }

    // Compact summary of what iOS thinks is actually connected right now — e.g.
    // "in=[MicrophoneBuiltIn] out=[Speaker]" vs out=[Receiver]/[BluetoothHFP]/empty. If audio
    // never reaches the ear despite isAudioEnabled=true and healthy RTP stats, this is what
    // tells us whether the OS routed to the wrong physical output (or none at all) rather
    // than a WebRTC-level problem.
    private func routeDescription() -> String {
        let route = AVAudioSession.sharedInstance().currentRoute
        let ins = route.inputs.map { $0.portType.rawValue }.joined(separator: ",")
        let outs = route.outputs.map { $0.portType.rawValue }.joined(separator: ",")
        return "route(in=[\(ins)] out=[\(outs)])"
    }

    func reject() {
        guard case .incoming(_, let cellId) = state else { return }
        Task { try? await store?.sendSignal("vcall:reject", to: cellId) }
        hangupSent = true
        callController.request(CXTransaction(action: CXEndCallAction(call: callUUID))) { _ in }
    }

    func hangup() {
        if let cellId = state.cellId {
            Task { try? await store?.sendSignal("vcall:hangup", to: cellId) }
        }
        hangupSent = true
        callController.request(CXTransaction(action: CXEndCallAction(call: callUUID))) { _ in }
        reset()
    }

    func toggleMute() {
        isMuted.toggle()
        localAudio?.isEnabled = !isMuted
    }

    // Bumped on every toggleSpeaker() call — lets the deferred check below tell "the user
    // tapped again before we got to look" apart from "our own override silently didn't
    // stick", so a stale check never fights a newer, genuine choice.
    private var speakerToggleGeneration = 0

    func toggleSpeaker() {
        speakerToggleGeneration += 1
        let myGeneration = speakerToggleGeneration
        nlog("call toggleSpeaker BEFORE isSpeaker=\(isSpeaker) \(routeDescription())")
        isSpeaker.toggle()
        let wantSpeaker = isSpeaker
        setSpeakerOverride(wantSpeaker)
        nlog("call toggleSpeaker AFTER isSpeaker=\(isSpeaker) \(routeDescription())")
        // The override call above can take a moment to actually land on the hardware —
        // check again shortly after to see whether it stuck or silently reverted, instead of
        // only ever seeing the (possibly stale) state read back synchronously above.
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .milliseconds(500))
            guard let self, self.speakerToggleGeneration == myGeneration else { return }
            nlog("call toggleSpeaker +500ms isSpeaker=\(self.isSpeaker) \(self.routeDescription())")
            let isOnSpeakerNow = AVAudioSession.sharedInstance().currentRoute.outputs
                .contains(where: { $0.portType == .builtInSpeaker })
            guard isOnSpeakerNow != wantSpeaker else { return } // stuck correctly, nothing to do
            // Confirmed on device 2026-09-24: right after a cold-start CallKit answer, the
            // first tap can land while the audio session's route hasn't finished settling yet
            // (logged route(in=[] ...) — no input port assigned at that instant); the override
            // silently doesn't take, and the passive route-change sync above (see its own doc
            // comment — deliberately honest about the real route, not fighting it) correctly
            // but unhelpfully flips isSpeaker back within ~500ms. A manual second tap, once
            // the session had settled, always worked — so retry once automatically instead of
            // leaving the user to notice and tap again themselves.
            nlog("call toggleSpeaker override didn't stick, retrying once")
            self.isSpeaker = wantSpeaker
            self.setSpeakerOverride(wantSpeaker)
            Task { @MainActor [weak self] in
                try? await Task.sleep(for: .milliseconds(500))
                guard let self else { return }
                nlog("call toggleSpeaker retry+500ms isSpeaker=\(self.isSpeaker) \(self.routeDescription())")
            }
        }
    }

    /// No longer wrapped in RTCAudioSession.lockForConfiguration() — that lock coordinated with
    /// WebRTC's built-in ADM, which NevodAudioDevice has fully replaced (see its own doc
    /// comment); the lock is meaningless now that WebRTC never touches the audio unit itself.
    /// (Confirmed 2026-08-03, before the ADM swap, that the lock alone did NOT fix "Динамик
    /// toggle changes isSpeaker but the real route stays on loudspeaker" — the real cause was
    /// WebRTC's own internal RTCAudioSession resetting the override on route changes, which
    /// the ADM swap removes from the chain entirely.)
    private func setSpeakerOverride(_ enabled: Bool) {
        try? AVAudioSession.sharedInstance().overrideOutputAudioPort(enabled ? .speaker : .none)
    }

    // MARK: - Ringback tone (440+480 Hz, 2s on / 4s off, generated in-memory)

    private func startRingback() {
        guard ringbackPlayer == nil else { return }
        // Route to speaker for this phase specifically: at this point nobody has the phone to
        // their ear yet (they're still waiting to see if the other side picks up), and the
        // default route otherwise is the earpiece (Receiver) — plenty audible held up, but
        // easy to mistake for "no ringback at all" when testing with the phone lying flat, and
        // matches how Telegram/WhatsApp dial out (loud on speaker while ringing; only switches
        // to earpiece once the user actually raises the phone or the call connects and they
        // haven't touched "Динамик"). Deliberately NOT resetting this once the call connects —
        // same reasoning: whatever route was active when the peer answers should just persist,
        // not silently flip back (that's the exact "isSpeaker fighting" bug class documented
        // in AUDIO_CALLS.md's "Динамик" episode — see setSpeakerOverride's own doc comment).
        setSpeakerOverride(true)
        let wav = makeRingbackWAV()
        do {
            let player = try AVAudioPlayer(data: wav)
            player.numberOfLoops = -1
            player.volume = 0.8
            player.prepareToPlay()
            let ok = player.play()
            nlog("call ringback started ok=\(ok) \(routeDescription())")
            if ok { ringbackPlayer = player }
        } catch {
            nlog("call ringback init error: \(error)")
        }
    }

    private func stopRingback() {
        ringbackPlayer?.stop()
        ringbackPlayer = nil
    }

    private func makeRingbackWAV() -> Data {
        let sampleRate = 22050
        let toneSamples = Int(2.0 * Double(sampleRate))   // 2 s tone
        let totalSamples = Int(6.0 * Double(sampleRate))  // 2 s tone + 4 s silence
        var samples = [Int16](repeating: 0, count: totalSamples)
        for i in 0..<toneSamples {
            let t = Double(i) / Double(sampleRate)
            let v = (sin(t * 440 * 2 * .pi) + sin(t * 480 * 2 * .pi)) * 0.35
            let clamped = max(-32767, min(32767, Int(v * 32767)))
            samples[i] = Int16(clamped)
        }
        var data = Data()
        func le<T: FixedWidthInteger>(_ v: T) {
            withUnsafeBytes(of: v.littleEndian) { data.append(contentsOf: $0) }
        }
        func str(_ s: String) { data.append(s.data(using: .ascii)!) }
        let byteCount = UInt32(totalSamples * 2)
        str("RIFF"); le(UInt32(36 + byteCount)); str("WAVE")
        str("fmt "); le(UInt32(16)); le(UInt16(1)); le(UInt16(1))
        le(UInt32(sampleRate)); le(UInt32(sampleRate * 2)); le(UInt16(2)); le(UInt16(16))
        str("data"); le(byteCount)
        samples.withUnsafeBytes { data.append(contentsOf: $0) }
        return data
    }

    // MARK: - Receive answer / ICE

    private func receiveAnswer(json: String) {
        let (name, cellId): (String, String)
        switch state {
        case .outgoing(let n, let id), .ringing(let n, let id): (name, cellId) = (n, id)
        default: return
        }
        guard let sdp = parseSDP(json, type: .answer) else { return }
        timeoutTask?.cancel()
        stopRingback()
        // CallKit already activated the session for the outgoing call (didActivate right
        // after CXStartCallAction) — nothing to activate here, see completeAccept().
        audioReadyForCall.current = true
        observeRouteChangesIfNeeded()
        state = .connecting(contactName: name, cellId: cellId)
        pc?.setRemoteDescription(sdp) { error in
            if let error { nlog("call setRemoteDescription(answer) FAILED err=\(error)") }
            Task { @MainActor [weak self] in
                self?.hasRemoteDesc = true
                self?.pendingCandidates.forEach { self?.pc?.add($0) { _ in } }
                self?.pendingCandidates.removeAll()
            }
        }
    }

    private func receiveICE(json: String) {
        guard let data = json.data(using: .utf8),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let cand = dict["candidate"] as? String,
              let mid  = dict["sdpMid"] as? String,
              let idx  = dict["sdpMLineIndex"] as? Int32 else { return }
        let ice = RTCIceCandidate(sdp: cand, sdpMLineIndex: idx, sdpMid: mid)
        if hasRemoteDesc {
            pc?.add(ice) { _ in }
        } else {
            pendingCandidates.append(ice)
        }
    }

    // MARK: - Internal helpers

    /// includeVideoTransceiver: false for the answerer path (completeAccept()) — confirmed via
    /// device logs 2026-08-06 (build 81) that pre-adding our own video transceiver via
    /// addTransceiver() here, BEFORE setRemoteDescription(offer) processes the incoming offer,
    /// does NOT get reused by WebRTC's offer-matching on the answerer side the way the audio
    /// track (added via the older pc.add(track:) API) does — it left the answerer with TWO
    /// video-kind transceivers: ours, orphaned (mid never assigned, never part of the
    /// negotiated session) and a second one WebRTC auto-created to actually represent the
    /// offer's m=video line (real mid, but defaulted to recvOnly). videoTransceiver()'s
    /// `.first(where:)` was grabbing the orphaned one, so addLocalVideoTrack() attached the
    /// camera track to a transceiver going nowhere — camera genuinely captured frames
    /// (confirmed via FrameCountingCapturerDelegate) but zero were ever sent, every single
    /// test, only on the answerer side. Not pre-adding a transceiver here lets
    /// setRemoteDescription(offer) create exactly one, already correctly associated —
    /// completeAccept() then promotes its direction to sendRecv itself (see its own comment)
    /// before answering, in the same round trip, no renegotiation needed.
    private func setupPC(includeVideoTransceiver: Bool = true) {
        // Guard against a leaked prior RTCPeerConnection still generating ICE candidates in
        // the background — normally setupPC() runs once per call, but
        // watchForStaleConnection()'s retry calls dial() (and so setupPC()) a second time for
        // the same call, and the RTCPeerConnectionDelegate callbacks don't check which pc
        // they came from (see didGenerate candidate:) — a stale connection left alive could
        // send ICE candidates for an SDP session the peer already discarded.
        pc?.close()
        let cfg = RTCConfiguration()
        if let t = turnInfo {
            // All traffic through the Nevod node — no third-party STUN/TURN
            cfg.iceServers = [RTCIceServer(
                urlStrings: [t.url],
                username: t.username,
                credential: t.credential
            )]
            cfg.iceTransportPolicy = .relay  // force relay-only, no direct P2P IP exposure
        }
        // If no TURN credentials yet: no ICE servers — call will still work on LAN
        cfg.sdpSemantics = .unifiedPlan
        cfg.continualGatheringPolicy = .gatherContinually

        let constraints = RTCMediaConstraints(mandatoryConstraints: nil, optionalConstraints: nil)
        pc = Self.factory.peerConnection(with: cfg, constraints: constraints, delegate: self)

        let src = Self.factory.audioSource(with: RTCMediaConstraints(
            mandatoryConstraints: nil, optionalConstraints: nil
        ))
        localAudio = Self.factory.audioTrack(with: src, trackId: "audio0")
        pc?.add(localAudio!, streamIds: ["stream0"])

        // Video transceiver added here, upfront, in the very first offer/answer — WITHOUT a
        // track (sender.track stays nil until addLocalVideoTrack() attaches one). This is the
        // architectural redesign that replaces mid-call SDP renegotiation for turning video
        // on (see enableVideoMidCall()'s doc comment for the full reasoning and the Telegram
        // comparison that motivated it, 2026-08-05): since both sides negotiate a sendRecv
        // video m-line once, right at call setup, either side can later attach a track to
        // their own sender and start sending immediately — no new offer/answer round trip,
        // so no glare (offer collision) is possible for this action at all, unlike the old
        // deferred-renegotiation design.
        //
        // Deliberate regression risk, not yet device-confirmed: this makes the very first SDP
        // bigger for EVERY call (previously video was kept out of it entirely specifically to
        // avoid a confirmed cold-launch bug — see startCall's doc comment on audio-first
        // negotiation). The mitigating factor is that no camera/AVCaptureSession is touched
        // here (sender.track is nil), so if the original bug's real cause was camera hardware
        // access time rather than raw SDP byte count, this shouldn't reproduce it — but that
        // wasn't conclusively distinguished at the time. First thing to verify on a real
        // device after this change: a cold VoIP-push launch still activates audio reliably.
        if includeVideoTransceiver {
            let videoTransceiverInit = RTCRtpTransceiverInit()
            videoTransceiverInit.direction = .sendRecv
            pc?.addTransceiver(of: .video, init: videoTransceiverInit)
        }
    }

    // MARK: - Video — channel negotiated upfront in setupPC() (2026-08-05 redesign, see its
    // own doc comment). Turning the camera on/off from here on is a purely local action, no
    // SDP renegotiation involved — modeled on how Telegram-iOS's OngoingCallThreadLocalContext
    // handles it: requestVideo:/disableVideo: call straight into the native call engine's
    // setVideoCapture(), no offer/answer round trip. This also means the glare/offer-collision
    // failure mode (both sides renegotiating at once — the likely cause of the "both sides see
    // only themselves" regression, since WebRTC renegotiation has no built-in collision
    // protection and this codebase had none either) can't happen for this action anymore,
    // since there's no renegotiation left to collide.

    /// Called by enableVideoMidCall() only — the user explicitly tapping their own camera
    /// button — creates the local capturer/track and attaches it to the video transceiver
    /// setupPC() already negotiated at call setup. Assigning sender.track on an
    /// already-negotiated sendRecv transceiver starts sending on the existing RTP session
    /// immediately; the peer's receiver picks up real frames without any new offer/answer.
    private func addLocalVideoTrack() {
        guard localVideoTrack == nil, let transceiver = videoTransceiver() else { return }
        nlog("call addLocalVideoTrack using transceiver mid=\(transceiver.mid) dir=\(transceiver.direction.rawValue) totalVideoTransceivers=\(pc?.transceivers.filter { $0.mediaType == .video }.count ?? -1)")
        let videoSrc = Self.factory.videoSource()
        // Wrapped in a counting proxy (2026-08-06) — see FrameCountingCapturerDelegate's own
        // doc comment. Confirmed via device logs (builds 78/79, 3 test rounds) that the
        // ANSWERER's own outgoing video sits at framesSent=0 for the whole call even though
        // AVCaptureSession reports isRunning=true and startCapture's completionHandler reports
        // no error — this settles whether the camera ever hands WebRTC a real frame at all.
        let frameCounter = FrameCountingCapturerDelegate(inner: videoSrc)
        frameCountingDelegate = frameCounter
        let capturer = RTCCameraVideoCapturer(delegate: frameCounter)
        // AVCaptureSession defaults to automatically reconfiguring the app's shared
        // AVAudioSession whenever it starts/stops. Harmless at this point (audio is already
        // active), but disabling it costs nothing and avoids any chance of it touching a
        // session we've already fought to establish.
        capturer.captureSession.automaticallyConfiguresApplicationAudioSession = false
        localVideoCapturer = capturer
        let videoTrack = Self.factory.videoTrack(with: videoSrc, trackId: "video0")
        localVideoTrack = videoTrack
        transceiver.sender.track = videoTrack
        AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
            nlog("call camera permission=\(granted)")
            guard granted else { return }
            Task { @MainActor in self?.startCameraCapture(front: self?.isFrontCamera ?? true) }
        }
    }

    /// The single video transceiver for this call — always exists from setupPC() onward
    /// (added upfront on both sides, direction sendRecv, no track attached until
    /// addLocalVideoTrack() assigns one).
    private func videoTransceiver() -> RTCRtpTransceiver? {
        pc?.transceivers.first(where: { $0.mediaType == .video })
    }

    /// User-initiated ONLY — turns on our own camera and starts sending it to the peer. Never
    /// triggered automatically by anything the peer does (see receiveVideoOn()'s doc comment
    /// for why: auto-joining was a privacy bug). No SDP involved — just attaches a track to
    /// the already-negotiated transceiver and tells the peer to look for it.
    func enableVideoMidCall() {
        guard case .active = state, localVideoTrack == nil, let cellId = state.cellId else { return }
        isVideoCall = true
        addLocalVideoTrack()
        let update = CXCallUpdate()
        update.hasVideo = true
        provider.reportCall(with: callUUID, updated: update)
        Task { @MainActor in
            try? await self.store?.sendSignal("vcall:video_on", to: cellId)
        }
    }

    /// Reads whatever video track is currently on the (single, always-present) video
    /// transceiver's receiver. Safe to call any time after receiveVideoOn() — unlike the old
    /// renegotiation design, the transceiver already exists from call setup, so there's no
    /// "did the offer/answer actually create it yet" question anymore.
    private func refreshRemoteVideoTrack() {
        guard let track = pc?.receivers.compactMap({ $0.track as? RTCVideoTrack }).first else { return }
        nlog("call refreshRemoteVideoTrack found track")
        remoteVideoTrack = track
    }

    /// Peer turned their camera on mid-call (vcall:video_on signal — see enableVideoMidCall).
    /// We switch our UI to the video screen so we can SEE their video, but our own camera
    /// stays off — sending our own video is a separate, user-initiated action
    /// (enableVideoMidCall(), triggered only by tapping our own camera button). Auto-starting
    /// our own camera here in response to the peer's signal was an earlier design's bug
    /// ("join symmetrically") — confirmed via same-node device testing 2026-08-02 to be a
    /// real privacy bug: it turned the receiving side's camera on without any action from
    /// that side's user, and the peer could then see them without consent. This handler never
    /// touches localVideoTrack/addLocalVideoTrack — only reacts to the peer's own track.
    private func receiveVideoOn() {
        guard case .active(let name, _) = state else { return }
        isVideoCall = true
        refreshRemoteVideoTrack()
        let update = CXCallUpdate()
        update.hasVideo = true
        provider.reportCall(with: callUUID, updated: update)
        notifyPeerVideoAvailable(name: name)
    }

    /// Cold-start-answered calls never bring CallOverlay to the foreground automatically
    /// (confirmed platform limitation — see completeAccept's neighboring notes), so if the
    /// peer turns their camera on while we're still sitting on CallKit's native screen, we'd
    /// otherwise never know. A local notification (generated on-device, no APNs round trip)
    /// gives a one-tap way in — RootView already shows CallOverlay reactively the instant the
    /// app is foregrounded (`!callManager.state.isIdle`), so no deep-link/navigation code is
    /// needed here, just getting the app opened at all. Skipped entirely if we're already
    /// foregrounded (nothing to alert the user to — they're already looking at it), which also
    /// means, combined with iOS's own default of not banner-presenting local notifications
    /// delivered while the app is active, this can't double up with what's already on screen.
    private func notifyPeerVideoAvailable(name: String) {
        guard UIApplication.shared.applicationState != .active else { return }
        let content = UNMutableNotificationContent()
        content.title = name
        content.body = String(localized: "Нажмите, чтобы посмотреть видео")
        content.sound = .default
        let request = UNNotificationRequest(
            identifier: "video_on_\(callUUID.uuidString)", content: content, trigger: nil
        )
        UNUserNotificationCenter.current().add(request) { error in
            if let error { nlog("call notifyPeerVideoAvailable FAILED err=\(error)") }
        }
    }

    // MARK: - Camera

    private func startCameraCapture(front: Bool) {
        guard let capturer = localVideoCapturer else { return }
        let position: AVCaptureDevice.Position = front ? .front : .back
        let devices = RTCCameraVideoCapturer.captureDevices()
        guard let device = devices.first(where: { $0.position == position }) ?? devices.first else {
            nlog("call camera no capture device found")
            return
        }
        // Pick the format closest to 640pt wide — plenty for a phone call, keeps CPU/bandwidth
        // reasonable (this call already competes with TURN relay bandwidth, see 2026-07-30
        // TURN-relay notes — video is much heavier than audio on that same relay path).
        let targetWidth: Int32 = 640
        let formats = RTCCameraVideoCapturer.supportedFormats(for: device)
        guard let format = formats.min(by: { a, b in
            let da = abs(CMVideoFormatDescriptionGetDimensions(a.formatDescription).width - targetWidth)
            let db = abs(CMVideoFormatDescriptionGetDimensions(b.formatDescription).width - targetWidth)
            return da < db
        }) else { return }
        let maxFps = format.videoSupportedFrameRateRanges.map(\.maxFrameRate).max() ?? 30
        // completionHandler (rather than the fire-and-forget overload) plus applicationState —
        // added to chase a 2026-08-05 finding: on the cold-start (VoIP-push-answered) side of a
        // call, "capture started" logged with no error, yet zero video bytes/frames were ever
        // sent for the whole call (confirmed via processStats' video counters) while the
        // hot-start side's outgoing video worked fine. AVCaptureSession is well known to not
        // deliver frames while the app isn't truly foregrounded — capturing applicationState
        // right here will confirm or rule that out directly instead of guessing.
        Task { @MainActor in
            nlog("call camera capture starting position=\(front ? "front" : "back") appState=\(UIApplication.shared.applicationState.rawValue)")
        }
        capturer.startCapture(with: device, format: format, fps: Int(min(30, maxFps))) { error in
            Task { @MainActor in
                if let error {
                    nlog("call camera capture start FAILED err=\(error)")
                } else {
                    nlog("call camera capture started position=\(front ? "front" : "back") sessionRunning=\(capturer.captureSession.isRunning) appState=\(UIApplication.shared.applicationState.rawValue)")
                }
            }
        }
    }

    /// Switches which physical camera feeds the call — stop, then restart on the other device.
    func toggleCamera() {
        guard isVideoCall, let capturer = localVideoCapturer else { return }
        let newFront = !isFrontCamera
        capturer.stopCapture { [weak self] in
            Task { @MainActor in
                self?.isFrontCamera = newFront
                self?.startCameraCapture(front: newFront)
            }
        }
    }

    /// Mutes video the same way toggleMute() mutes audio — disables the track (sends nothing)
    /// rather than stopping capture, so it can be flipped back on instantly.
    func toggleCameraEnabled() {
        isCameraOff.toggle()
        localVideoTrack?.isEnabled = !isCameraOff
    }

    private enum EndReason { case localEnded, remoteEnded, unanswered, busy }

    private func endCall(_ reason: EndReason) {
        let ckReason: CXCallEndedReason
        switch reason {
        case .localEnded:  ckReason = .failed
        case .remoteEnded: ckReason = .remoteEnded
        case .unanswered:  ckReason = .unanswered
        case .busy:        ckReason = .answeredElsewhere
        }
        // .unanswered fires from our own local timers (we gave up waiting for an answer,
        // or — on the callee side — for the offer/for the user to pick up) — the peer has
        // no way to know unless we tell them, otherwise their side just keeps ringing/
        // ringing-back until their own timeout eventually catches up (confirmed via device
        // logs 2026-07-30: caller's UI ended while the callee kept ringing for tens of
        // seconds more, having received nothing).
        if reason == .unanswered, let cellId = state.cellId {
            Task { try? await store?.sendSignal("vcall:hangup", to: cellId) }
        }
        provider.reportCall(with: callUUID, endedAt: Date(), reason: ckReason)

        if reason == .busy, let name = state.contactName {
            // Tear down right away (mic/audio session/timers) but hold the UI on a "busy"
            // screen briefly instead of jumping straight to .idle — see CallState.busy's doc
            // comment for why.
            if let cellId = state.cellId {
                NevdClient.callEndedAt[cellId] = Int64(Date().timeIntervalSince1970)
            }
            cleanupResources()
            state = .busy(contactName: name)
            Task { @MainActor [weak self] in
                try? await Task.sleep(for: .seconds(2.5))
                guard let self, case .busy = self.state else { return }
                self.state = .idle
            }
        } else {
            reset()
        }
    }

    /// Writes one CallLogEntry per call to the local, on-device call history (the "Calls"
    /// tab) — every device logs its own side of the conversation independently, no network
    /// notice needed (previously sent as an auto chat message, which the user reported as
    /// cluttering the conversation like spam — 2026-07-31). Called from reset(), the one
    /// endpoint every termination path funnels through (timeout, hangup, reject, busy, or
    /// the system UI ending the call via CXEndCallAction) — so unlike the old notice, this
    /// can't be skipped by whichever specific path happened to end the call.
    private func logCall() {
        guard let cellId = state.cellId, let startedAt = callStartedAt else { return }
        let outcome: CallLogEntry.Outcome = callWasAnswered ? .answered : .missed
        let duration = callWasAnswered ? callDuration : 0
        let isOutgoing = callIsOutgoingFlag
        store?.logCall(cellId: cellId, isOutgoing: isOutgoing, timestamp: startedAt,
                       durationSecs: duration, outcome: outcome, isVideo: isVideoCall)
        callStartedAt = nil
    }

    private func reset() {
        if let cellId = state.cellId {
            NevdClient.callEndedAt[cellId] = Int64(Date().timeIntervalSince1970)
        }
        cleanupResources()
        state = .idle
    }

    /// Everything reset() does except the actual `state = .idle` transition — split out so
    /// endCall(.busy) can tear resources down immediately while still parking the UI on
    /// CallState.busy for a couple seconds first (see its own doc comment).
    private func cleanupResources() {
        logCall()
        timeoutTask?.cancel()
        durationTask?.cancel()
        timeoutTask = nil
        durationTask = nil
        pc?.close()
        pc = nil
        localAudio = nil
        if let observer = routeChangeObserver {
            NotificationCenter.default.removeObserver(observer)
            routeChangeObserver = nil
        }
        localVideoCapturer?.stopCapture()
        localVideoCapturer = nil
        frameCountingDelegate = nil
        localVideoTrack = nil
        remoteVideoTrack = nil
        isVideoCall = false
        isCameraOff = false
        isFrontCamera = true
        pendingCandidates = []
        pendingSDP = nil
        hasRemoteDesc = false
        hangupSent = false
        acceptPending = false
        pendingPushCallerId = nil
        audioReadyForCall.current = false
        stopRingback()
        stopQualityMonitor()
        store?.tempEncPubs.removeAll()
        isMuted = false
        isSpeaker = false
        isBluetooth = false
        setSpeakerOverride(false)
        callDuration = 0

        // Memory-leak investigation (2026-09): pc.close() and the other releases above are
        // synchronous, but WebRTC's own native buffers (encoder/decoder, camera capture) are
        // known to free on a delay via its internal threads, not necessarily by the time this
        // function returns. These checkpoints exist purely to see, with the now-fixed
        // phys_footprint metric (see Logger.swift's memMB()), whether footprint actually settles
        // back down a few seconds after hangup, or stays inflated — nlog's own call-site logging
        // already captures "right now"; this fills in "a bit later."
        nlog("call cleanupResources +0s checkpoint")
        Task {
            try? await Task.sleep(for: .seconds(2))
            nlog("call cleanupResources +2s checkpoint")
            try? await Task.sleep(for: .seconds(8))
            nlog("call cleanupResources +10s checkpoint")
        }
    }

    private func startDurationTimer() {
        durationTask = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(1))
                guard !Task.isCancelled else { break }
                self?.callDuration += 1
            }
        }
    }

    private func startQualityMonitor() {
        prevBytesReceived = 0
        prevBytesSent = 0
        prevStatsTime = Date()
        statsTask = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(2))
                guard !Task.isCancelled else { break }
                self?.fetchStats()
            }
        }
    }

    private func stopQualityMonitor() {
        statsTask?.cancel()
        statsTask = nil
        quality = nil
    }

    private func fetchStats() {
        pc?.statistics { [weak self] report in
            Task { @MainActor in self?.processStats(report) }
        }
    }

    private func processStats(_ report: RTCStatisticsReport) {
        var bytes: Int64 = 0
        var lost: Int64 = 0
        var received: Int64 = 0
        var sentBytes: Int64 = 0
        var sentPackets: Int64 = 0
        var audioLevel: Double = -1
        var tracksReceivers = 0
        var trackDetail = ""
        // Video RTP counters — only meaningful once isVideoCall is true, but the video
        // transceiver (and so these stats entries) exist from call setup regardless (see
        // setupPC's upfront-transceiver doc comment). framesDecoded/framesSent are the
        // ground truth for "is real video actually flowing," independent of what the local
        // UI renders — if these stay 0 while the peer insists they turned their camera on,
        // the bug is in negotiation/transport, not in CallOverlay's rendering.
        var vBytesReceived: Int64 = 0
        var vFramesDecoded: Int64 = 0
        var vFramesReceived: Int64 = 0
        var vFrameW: Int64 = 0
        var vFrameH: Int64 = 0
        var vBytesSent: Int64 = 0
        var vFramesSent: Int64 = 0
        var vFrameWSent: Int64 = 0
        var vFrameHSent: Int64 = 0
        for (_, s) in report.statistics {
            if s.type == "inbound-rtp", (s.values["kind"] as? String) == "audio" {
                bytes    = (s.values["bytesReceived"]    as? NSNumber)?.int64Value ?? 0
                lost     = (s.values["packetsLost"]      as? NSNumber)?.int64Value ?? 0
                received = (s.values["packetsReceived"]  as? NSNumber)?.int64Value ?? 0
            } else if s.type == "outbound-rtp", (s.values["kind"] as? String) == "audio" {
                sentBytes   = (s.values["bytesSent"]   as? NSNumber)?.int64Value ?? 0
                sentPackets = (s.values["packetsSent"] as? NSNumber)?.int64Value ?? 0
            } else if s.type == "track", (s.values["kind"] as? String) == "audio" {
                tracksReceivers += 1
                if let lvl = (s.values["audioLevel"] as? NSNumber)?.doubleValue { audioLevel = lvl }
                let ended = (s.values["ended"] as? NSNumber)?.boolValue ?? false
                let detached = (s.values["detached"] as? NSNumber)?.boolValue ?? false
                trackDetail += " track(ended=\(ended) detached=\(detached))"
            } else if s.type == "inbound-rtp", (s.values["kind"] as? String) == "video" {
                vBytesReceived = (s.values["bytesReceived"] as? NSNumber)?.int64Value ?? 0
                vFramesDecoded = (s.values["framesDecoded"] as? NSNumber)?.int64Value ?? 0
                vFramesReceived = (s.values["framesReceived"] as? NSNumber)?.int64Value ?? 0
                vFrameW = (s.values["frameWidth"] as? NSNumber)?.int64Value ?? 0
                vFrameH = (s.values["frameHeight"] as? NSNumber)?.int64Value ?? 0
            } else if s.type == "outbound-rtp", (s.values["kind"] as? String) == "video" {
                vBytesSent = (s.values["bytesSent"] as? NSNumber)?.int64Value ?? 0
                vFramesSent = (s.values["framesSent"] as? NSNumber)?.int64Value ?? 0
                vFrameWSent = (s.values["frameWidth"] as? NSNumber)?.int64Value ?? 0
                vFrameHSent = (s.values["frameHeight"] as? NSNumber)?.int64Value ?? 0
            }
        }
        let now = Date()
        let dt = now.timeIntervalSince(prevStatsTime)
        let kbps = dt > 0 ? Double((bytes - prevBytesReceived) * 8) / dt / 1000 : 0
        let sentKbps = dt > 0 ? Double((sentBytes - prevBytesSent) * 8) / dt / 1000 : 0
        prevBytesReceived = bytes
        prevBytesSent = sentBytes
        prevStatsTime = now
        let total = received + lost
        let lossRate = total > 0 ? Double(lost) / Double(total) : 0
        var videoDetail = ""
        if isVideoCall {
            videoDetail = " video(recvBytes=\(vBytesReceived) framesDecoded=\(vFramesDecoded) framesReceived=\(vFramesReceived) recvRes=\(vFrameW)x\(vFrameH) sentBytes=\(vBytesSent) framesSent=\(vFramesSent) sentRes=\(vFrameWSent)x\(vFrameHSent) localTrackId=\(localVideoTrack?.trackId ?? "nil") remoteTrackId=\(remoteVideoTrack?.trackId ?? "nil"))"
        }
        nlog("call stats kbps=\(Int(kbps)) sentKbps=\(Int(sentKbps)) sentPackets=\(sentPackets) loss=\(String(format: "%.1f", lossRate*100))% audioLevel=\(audioLevel) tracks=\(tracksReceivers)\(trackDetail) playing=\(Self.audioDevice.isPlaying) recording=\(Self.audioDevice.isRecording) localAudioEnabled=\(localAudio?.isEnabled ?? false) \(routeDescription()) outputVolume=\(AVAudioSession.sharedInstance().outputVolume)\(videoDetail)")
        if kbps < 5 || lossRate > 0.15 {
            quality = .poor
        } else if kbps < 20 || lossRate > 0.05 {
            quality = .medium
        } else {
            quality = .good
        }
    }

    // MARK: - SDP helpers

    private func sdpJSON(_ sdp: RTCSessionDescription) -> String {
        let type = sdp.type == .offer ? "offer" : "answer"
        let dict: [String: Any] = ["type": type, "sdp": sdp.sdp]
        guard let data = try? JSONSerialization.data(withJSONObject: dict),
              let str = String(data: data, encoding: .utf8) else { return "" }
        return str
    }

    private func parseSDP(_ json: String, type: RTCSdpType) -> RTCSessionDescription? {
        guard let data = json.data(using: .utf8),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let sdp = dict["sdp"] as? String else { return nil }
        return RTCSessionDescription(type: type, sdp: sdp)
    }
}

// MARK: - CXProviderDelegate

extension CallManager: CXProviderDelegate {

    nonisolated func providerDidReset(_ provider: CXProvider) {
        Task { @MainActor in self.reset() }
    }

    nonisolated func provider(_ provider: CXProvider, perform action: CXStartCallAction) {
        // Same place Apple's Speakerbox configures; a no-op if startCall() already did.
        Self.audioDevice.configureSession()
        action.fulfill()
    }

    // Answering a CallKit call (even via the full-screen "slide to answer" gesture on a
    // fully cold-launched process) does NOT bring the app's own UI to the foreground — this
    // was confirmed to be a genuine iOS platform limitation, not a Nevod bug, after two
    // separate workarounds both failed: self-opening a custom URL scheme (predates the
    // modern SwiftUI App/Scene lifecycle, and self-opening apparently needs foreground UI
    // privileges the app doesn't have yet in this state) and
    // UIApplication.requestSceneSessionActivation (Apple's own scene-activation API, but it
    // rejected the call outright with "The current device does not support multiple
    // scenes" — that API is for iPad-style multi-scene apps, not single-scene iPhone ones).
    // User independently confirmed Telegram has the exact same limitation on the same
    // device/scenario — no third-party VoIP app can force itself to the foreground from a
    // cold, lock-screen-answered call; the user has to open it manually, same as any other.
    nonisolated func provider(_ provider: CXProvider, perform action: CXAnswerCallAction) {
        // Same place Apple's Speakerbox configures; a no-op if the report already did.
        Self.audioDevice.configureSession()
        action.fulfill()
        Task { @MainActor in self.performAccept() }
    }

    nonisolated func provider(_ provider: CXProvider, perform action: CXEndCallAction) {
        action.fulfill()
        Task { @MainActor in
            // This fires for EVERY CXCall this provider manages, including the
            // throwaway "busy" duplicate reportIncomingCallFromPush() reports and
            // immediately ends when a second VoIP push arrives while already on a
            // call (Apple requires every push be reported, but there's no call-
            // waiting support here). Without this guard, ending that phantom call
            // silently rejected/hung-up the REAL call instead, because state/
            // hangupSent/sendSignal below are keyed off self.callUUID, not
            // action.callUUID -- confirmed via device logs 2026-08-10: a second,
            // near-simultaneous VoIP push (itself triggered by the caller's own
            // socket needing a reconnect-and-resend retry mid-dial) caused the
            // callee's real, still-ringing call to receive a spurious vcall:reject.
            guard action.callUUID == self.callUUID else { return }
            if !self.hangupSent {
                let cellId = self.state.cellId
                if case .incoming(_, let id) = self.state {
                    try? await self.store?.sendSignal("vcall:reject", to: id)
                } else if let id = cellId {
                    try? await self.store?.sendSignal("vcall:hangup", to: id)
                }
            }
            self.reset()
        }
    }

    nonisolated func provider(_ provider: CXProvider, didActivate audioSession: AVAudioSession) {
        nlog("call didActivate audioSession ready=\(audioReadyForCall.current)")
        // The ONLY place call audio starts (Apple's CallKit contract — see
        // NevodAudioDevice.configureSession). No self-activation, no retry loop, no reportCall
        // nudges any more; if this never fires, the call has no audio and the log will show it.
        Self.audioDevice.handleSessionActivated()
        Task { @MainActor in self.observeRouteChangesIfNeeded() }
    }

    nonisolated func provider(_ provider: CXProvider, didDeactivate audioSession: AVAudioSession) {
        nlog("call didDeactivate audioSession")
        // CallKit deactivated the session at the OS level — just update NevodAudioDevice's own
        // bookkeeping and let it tear its engine down; it's safe to call from any thread.
        Self.audioDevice.handleSessionDeactivated()
    }
}

// MARK: - RTCPeerConnectionDelegate

extension CallManager: RTCPeerConnectionDelegate {

    nonisolated func peerConnection(_ pc: RTCPeerConnection, didChange state: RTCSignalingState) {}

    // No auto-assignment of remoteVideoTrack here (removed 2026-08-05) — this legacy
    // stream-based callback isn't reliable under Unified Plan (confirmed via device logs
    // 2026-08-01: didn't fire for a renegotiated track at all) and, now that the video
    // transceiver exists from call setup for every call, it can fire with a placeholder/
    // frameless receiver even when the peer isn't actually sending anything — exactly the
    // "black screen" failure mode receiveVideoOn()/refreshRemoteVideoTrack() are designed to
    // avoid. The vcall:video_on signal is now the sole trigger for reading remote video.
    nonisolated func peerConnection(_ pc: RTCPeerConnection, didAdd stream: RTCMediaStream) {}

    nonisolated func peerConnection(_ pc: RTCPeerConnection, didRemove stream: RTCMediaStream) {
        Task { @MainActor in
            if stream.videoTracks.contains(where: { $0.trackId == self.remoteVideoTrack?.trackId }) {
                self.remoteVideoTrack = nil
            }
        }
    }
    nonisolated func peerConnectionShouldNegotiate(_ pc: RTCPeerConnection) {}
    nonisolated func peerConnection(_ pc: RTCPeerConnection, didChange state: RTCIceGatheringState) {}
    nonisolated func peerConnection(_ pc: RTCPeerConnection, didRemove candidates: [RTCIceCandidate]) {}
    nonisolated func peerConnection(_ pc: RTCPeerConnection, didOpen ch: RTCDataChannel) {}

    nonisolated func peerConnection(_ pc: RTCPeerConnection, didChange iceState: RTCIceConnectionState) {
        Task { @MainActor in
            // watchForStaleConnection()'s retry calls dial() → setupPC() a second time for the
            // SAME call, which closes the old RTCPeerConnection and replaces self.pc with a new
            // one — but this delegate callback (same `self`, not re-scoped per connection) can
            // still be in flight for the OLD one. Confirmed via device logs 2026-08-21: the old
            // connection's delayed .closed fired AFTER the retry had already created a new pc
            // and sent a fresh offer, and this unconditionally called endCall() — killing the
            // very retry that was supposed to save the call, collapsing state to .idle out from
            // under it. Every other stale-pc callback here already gets discarded by acting on
            // stale/already-reset state; this one doesn't, because .closed's whole job IS to
            // change state. Only the current self.pc's events may drive call state now.
            guard pc === self.pc else {
                nlog("call ICE state=\(iceState.rawValue) IGNORED — from a stale/replaced RTCPeerConnection")
                return
            }
            nlog("call ICE state=\(iceState.rawValue)")
            switch iceState {
            case .connected, .completed:
                switch self.state {
                case .connecting(let name, let cellId):
                    self.state = .active(contactName: name, cellId: cellId)
                    self.callWasAnswered = true
                    self.startDurationTimer()
                    self.startQualityMonitor()
                    self.provider.reportOutgoingCall(with: self.callUUID, connectedAt: Date())
                    // ICE actually connecting proves this cellId's device is reachable right
                    // now — mitigates the "stuck offline forever" delivery-status bug, see
                    // AppStore.markReachableByCall's doc comment. Fires for both call
                    // directions: .connecting is reached whether WE called them or they
                    // answered ours, this switch doesn't distinguish (nor does it need to).
                    self.store?.markReachableByCall(chatId: cellId)
                default:
                    break
                }
            case .failed, .closed:
                // Failed: the peer may not know — tell them, or their side keeps ringing or
                // waiting (device logs 2026-10-21: the caller rang on after the callee's
                // call had already failed). A hangup after theirs is dropped there.
                if iceState == .failed, let cellId = self.state.cellId {
                    Task { try? await self.store?.sendSignal("vcall:hangup", to: cellId) }
                }
                self.endCall(.remoteEnded)
            default:
                break
            }
        }
    }

    nonisolated func peerConnection(_ pc: RTCPeerConnection, didGenerate candidate: RTCIceCandidate) {
        Task { @MainActor in
            // Same stale-connection race as didChange(iceState:) above — a leaked prior
            // RTCPeerConnection (setupPC()'s own doc comment already flagged this as a known
            // gap here) could otherwise send ICE candidates for an SDP session the peer already
            // discarded, right as a fresh retry is under way — confusing, not just wasted.
            guard pc === self.pc, let cellId = self.state.cellId else { return }
            let dict: [String: Any] = [
                "candidate": candidate.sdp,
                "sdpMid": candidate.sdpMid ?? "",
                "sdpMLineIndex": candidate.sdpMLineIndex
            ]
            guard let data = try? JSONSerialization.data(withJSONObject: dict),
                  let json = String(data: data, encoding: .utf8) else { return }
            if case .outgoing = self.state { self.sentIce.append("vcall:ice:\(json)") }
            try? await self.store?.sendSignal("vcall:ice:\(json)", to: cellId)
        }
    }
}

// MARK: - Contact display name helper

private extension Contact {
    var displayName: String {
        alias.isEmpty ? cellId : alias
    }
}
