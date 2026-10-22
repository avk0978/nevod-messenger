import Foundation
import AVFoundation
import CoreAudioTypes
import WebRTC

// RTCAudioDevice.h documents that all lifecycle methods (initializeWithDelegate,
// terminateDevice, initialize/start/stopPlayout, initialize/start/stopRecording) are called by
// native ADM from the SAME thread between initializeWithDelegate and terminateDevice — so those
// don't need locking against each other. isInterrupted is the one piece of state written from an
// arbitrary thread (AVAudioSession interruption notification), hence the lock.
private final class AtomicBool: @unchecked Sendable {
    private let lock = NSLock()
    private var value: Bool
    init(_ initial: Bool) { value = initial }
    var current: Bool {
        get { lock.lock(); defer { lock.unlock() }; return value }
        set { lock.lock(); defer { lock.unlock() }; value = newValue }
    }
}

// Converts AVAudioSinkNode's captured PCM (32-bit float, hardware sample rate/channel count)
// into the 16-bit interleaved integer format WebRTC's ADM requires. Same rate in/out only —
// AudioConverterNew doesn't do sample-rate conversion here, which is fine since our sink/source
// nodes are always built at the hardware's own rate.
private final class SimpleAudioConverter {
    let from: AVAudioFormat
    let to: AVAudioFormat
    private var audioConverter: AudioConverterRef?

    init?(from: AVAudioFormat, to: AVAudioFormat) {
        guard from.sampleRate == to.sampleRate else { return nil }
        guard noErr == AudioConverterNew(from.streamDescription, to.streamDescription, &audioConverter) else {
            return nil
        }
        self.from = from
        self.to = to
    }

    deinit {
        if let audioConverter { AudioConverterDispose(audioConverter) }
    }

    func convert(framesCount: AVAudioFrameCount, from: UnsafePointer<AudioBufferList>,
                 to: UnsafeMutablePointer<AudioBufferList>) -> OSStatus {
        guard let audioConverter else { preconditionFailure("SimpleAudioConverter not initialized") }
        return AudioConverterConvertComplexBuffer(audioConverter, framesCount, from, to)
    }
}

private extension AVAudioFormat {
    var isSampleRateAndChannelCountValid: Bool {
        !sampleRate.isZero && !sampleRate.isNaN && sampleRate.isFinite && channelCount > 0
    }
}

private extension AVAudioEngine {
    func isInputOutputSampleRatesNative(for audioSession: AVAudioSession) -> Bool {
        let hw = audioSession.sampleRate
        return inputNode.inputFormat(forBus: 1).sampleRate == hw
            && outputNode.outputFormat(forBus: 0).sampleRate == hw
    }
}

/// Custom WebRTC AudioDeviceModule, replacing the framework's built-in iOS ADM entirely — see
/// CallKit_Speaker_Investigation.md / dapper-swimming-bonbon.md for the full root-cause writeup.
///
/// Root cause this exists to fix: WebRTC's own built-in `RTCAudioSession` (inside the prebuilt
/// WebRTC.xcframework, not something we can patch) subscribes to
/// AVAudioSessionRouteChangeNotification itself and reacts to ANY route change by re-running
/// setCategory() internally — invisible to and unreachable from our own code. Re-running
/// setCategory silently resets whatever overrideOutputAudioPort is currently in effect, which is
/// what caused the native CallKit Speaker button to self-flip every few seconds with zero user
/// interaction (confirmed via device logs — ruled out WebRTC version M149→M150, Bluetooth, and
/// iOS proximity behavior as the cause; Telegram doesn't have this problem under identical
/// conditions). There's no public flag to disable RTCAudioSession's internal behavior.
///
/// The only way to remove that behavior from the chain without forking/patching WebRTC's own
/// source (a much bigger, ongoing-maintenance-heavy undertaking) is to stop using its built-in
/// ADM at all, via the public RTCPeerConnectionFactory(audioDevice:) extension point. Modeled on
/// https://github.com/mstyura/RTCAudioDevice's AVAudioEngineRTCAudioDevice.swift — a reference
/// implementation directly linked from WebRTC's own RTCAudioDevice.h — scoped down to
/// voice-call-only needs (no background-music mixing, no stereo-input preference).
///
/// This class owns the AVAudioSession's category configuration (per RTCAudioDevice.h:
/// "Implementation is fully responsible for configuring application's AVAudioSession") —
/// but NOT its activation: CallKit activates/deactivates the session and tells us via
/// didActivate/didDeactivate (see configureSession/handleSessionActivated). It reacts to
/// route changes narrowly — only rebuilding the audio graph if the actual hardware format (sample rate) changed, via AVAudioEngine's own
/// AVAudioEngineConfigurationChangeNotification, never by blindly re-applying setCategory or
/// overrideOutputAudioPort.
final class NevodAudioDevice: NSObject {
    private let audioSession = AVAudioSession.sharedInstance()
    private let queue = DispatchQueue(label: "NevodAudioDevice")

    private var audioEngine: AVAudioEngine?
    private var engineConfigObserver: NSObjectProtocol?
    private var sessionObservers: [NSObjectProtocol] = []

    private var passThroughNode = AVAudioMixerNode()
    private var audioSinkNode: AVAudioSinkNode?
    private var audioSourceNode: AVAudioSourceNode?

    private var shouldPlay = false
    private var shouldRecord = false
    private let isInterrupted = AtomicBool(false)

    private var delegate: RTCAudioDeviceDelegate?

    private var audioInputFormat: AVAudioFormat? {
        didSet {
            guard oldValue != audioInputFormat else { return }
            delegate?.notifyAudioInputParametersChange()
        }
    }
    private var audioOutputFormat: AVAudioFormat? {
        didSet {
            guard oldValue != audioOutputFormat else { return }
            delegate?.notifyAudioOutputParametersChange()
        }
    }

    private(set) var inputLatency: TimeInterval = 0 {
        didSet {
            guard oldValue != inputLatency else { return }
            delegate?.notifyAudioInputParametersChange()
        }
    }
    private(set) var outputLatency: TimeInterval = 0 {
        didSet {
            guard oldValue != outputLatency else { return }
            delegate?.notifyAudioOutputParametersChange()
        }
    }

    private let sessionActiveFlag = AtomicBool(false)

    override init() {
        super.init()
    }

    // MARK: - AVAudioSession (configured by us, activated only by CallKit)

    /// Apple's CallKit contract (DTS, developer.apple.com/forums/thread/810385): a call's
    /// session must be fully configured BEFORE the call is reported/started, the app must NOT
    /// activate it itself, and it must not be changed while the call is active. Breaking all
    /// three (lazy setCategory at answer time, our own setActive retry loop, reportCall
    /// "nudges") is what produced the CategoryChange (reason=3) that silently flipped the
    /// CallKit speaker back to the earpiece on a cold-start answer (nevod (36).log, 23:11:19).
    ///
    /// CallManager calls this right before every reportNewIncomingCall / CXStartCallAction and
    /// again in the CXStart/CXAnswer perform handlers (same place Apple's Speakerbox sample
    /// configures). No-op when the session already has exactly this configuration — so a call
    /// that's already active never sees a category change from here. Re-applied per call, not
    /// once at launch, because voice-message record/playback (ChatView, AVAudioPlayerWrapper)
    /// switches the category between calls.
    func configureSession() {
        let options: AVAudioSession.CategoryOptions = [.allowBluetoothHFP, .allowBluetoothA2DP]
        if audioSession.category == .playAndRecord && audioSession.mode == .voiceChat
            && audioSession.categoryOptions == options {
            return
        }
        do {
            try audioSession.setCategory(.playAndRecord, mode: .voiceChat, options: options)
            nlog("audioDevice session configured (playAndRecord/voiceChat)")
        } catch {
            nlog("audioDevice setCategory FAILED err=\(error)")
        }
    }

    /// Called ONLY from CXProviderDelegate's didActivate — CallKit has activated the session
    /// (we never call setActive ourselves any more, see configureSession).
    func handleSessionActivated() {
        sessionActiveFlag.current = true
        // CallKit taking over the session can itself post an "interruption began" with no
        // matching "ended" (CallKit IS us) — confirmed 2026-08-21, answerer sent no audio for
        // a whole call because isInterrupted stayed latched. Activation proves we hold the
        // session, so any interruption latch is stale here.
        isInterrupted.current = false
        nlog("audioDevice session activated by CallKit sampleRate=\(audioSession.sampleRate)")
        queue.async { [weak self] in self?.updateEngine() }
    }

    /// Called from CXProviderDelegate's didDeactivate — CallKit itself deactivates the session
    /// at the OS level, this just updates our own bookkeeping and tears the engine down.
    func handleSessionDeactivated() {
        sessionActiveFlag.current = false
        queue.async { [weak self] in self?.updateEngine() }
    }

    // MARK: - Engine reconciliation

    private func shutdownEngine() {
        guard let audioEngine else { return }
        if audioEngine.isRunning { audioEngine.stop() }
        if let engineConfigObserver {
            NotificationCenter.default.removeObserver(engineConfigObserver)
            self.engineConfigObserver = nil
        }
        if let audioSinkNode {
            audioEngine.detach(audioSinkNode)
            self.audioSinkNode = nil
            delegate?.notifyAudioInputInterrupted()
        }
        if let audioSourceNode {
            audioEngine.detach(audioSourceNode)
            self.audioSourceNode = nil
            delegate?.notifyAudioOutputInterrupted()
        }
        // passThroughNode is a single instance reused across every engine rebuild (unlike
        // sink/source, which are recreated fresh each time) — attach(_:) unconditionally
        // attaches it to whichever engine updateEngine() just built. Detaching it here too is
        // what makes that safe: AVAudioEngine enforces a node can only ever belong to one
        // engine at a time (asserts "nil == owningEngine || GetEngine() == owningEngine" and
        // throws NSException otherwise) — without this, a second rebuild in the same call
        // (e.g. from a burst of route-change notifications, each triggering shutdown+rebuild)
        // crashed trying to attach a node still owned by the just-torn-down engine. Confirmed
        // via device crash log 2026-08-08: exactly this exception, on exactly this line.
        audioEngine.detach(passThroughNode)
        self.audioEngine = nil
    }

    /// Single reconciliation point — builds/tears down the engine to match current
    /// shouldPlay/shouldRecord/isInterrupted state. Called from startPlayout/stopPlayout/
    /// startRecording/stopRecording, from handleSessionActivated() once CallKit activates the
    /// session, and from the AVAudioEngineConfigurationChange observer (format actually changed underneath
    /// us — e.g. a real device swap, not just a route notification firing).
    private func updateEngine() {
        guard let delegate, shouldPlay || shouldRecord, sessionActiveFlag.current, !isInterrupted.current else {
            shutdownEngine()
            return
        }

        if let audioEngine, !audioEngine.isInputOutputSampleRatesNative(for: audioSession) {
            nlog("audioDevice format changed, rebuilding engine")
            shutdownEngine()
        }

        let useVoiceProcessing = audioSession.category == .playAndRecord
            && (audioSession.mode == .voiceChat || audioSession.mode == .videoChat)
        if let audioEngine, audioEngine.inputNode.isVoiceProcessingEnabled != useVoiceProcessing {
            shutdownEngine()
        }

        let engine: AVAudioEngine
        if let existing = audioEngine {
            engine = existing
        } else {
            let newEngine = AVAudioEngine()
            newEngine.isAutoShutdownEnabled = true
            // Toggle voice processing over outputNode, not inputNode, to avoid eagerly creating
            // inputNode before it's actually needed (matches the reference implementation —
            // observed to avoid spurious crashes when toggled later).
            if newEngine.outputNode.isVoiceProcessingEnabled != useVoiceProcessing {
                do {
                    try newEngine.outputNode.setVoiceProcessingEnabled(useVoiceProcessing)
                } catch {
                    nlog("audioDevice setVoiceProcessingEnabled FAILED err=\(error)")
                    return
                }
            }
            newEngine.attach(passThroughNode)

            engineConfigObserver = NotificationCenter.default.addObserver(
                forName: .AVAudioEngineConfigurationChange, object: newEngine, queue: nil
            ) { [weak self] _ in
                self?.queue.async { self?.updateEngine() }
            }
            audioEngine = newEngine
            engine = newEngine
        }

        let ioUnit = engine.outputNode.auAudioUnit
        if ioUnit.isInputEnabled != shouldRecord || ioUnit.isOutputEnabled != shouldPlay {
            if engine.isRunning { engine.stop() }
            ioUnit.isInputEnabled = shouldRecord
            ioUnit.isOutputEnabled = shouldPlay
        }

        if shouldRecord {
            attachRecordingIfNeeded(to: engine, delegate: delegate)
        } else if let audioSinkNode {
            engine.detach(audioSinkNode)
            self.audioSinkNode = nil
        }

        if shouldPlay {
            attachPlayoutIfNeeded(to: engine, delegate: delegate)
        } else if let audioSourceNode {
            engine.detach(audioSourceNode)
            self.audioSourceNode = nil
        }

        if !engine.isRunning {
            engine.prepare()
            do {
                try engine.start()
            } catch {
                nlog("audioDevice engine start FAILED err=\(error)")
            }
        }
    }

    private func attachRecordingIfNeeded(to engine: AVAudioEngine, delegate: RTCAudioDeviceDelegate) {
        guard audioSinkNode == nil else { return }
        let inputFormat = engine.inputNode.outputFormat(forBus: 1)
        guard inputFormat.isSampleRateAndChannelCountValid else {
            nlog("audioDevice invalid input format \(inputFormat)")
            return
        }
        engine.connect(engine.inputNode, to: passThroughNode, format: inputFormat)

        guard let rtcRecordFormat = AVAudioFormat(commonFormat: .pcmFormatInt16,
                                                   sampleRate: inputFormat.sampleRate,
                                                   channels: inputFormat.channelCount,
                                                   interleaved: true),
              let converter = SimpleAudioConverter(from: inputFormat, to: rtcRecordFormat) else {
            nlog("audioDevice failed to build record converter")
            return
        }
        audioInputFormat = rtcRecordFormat
        inputLatency = audioSession.inputLatency

        let deliverRecordedData = delegate.deliverRecordedData
        let renderBlock: RTCAudioDeviceRenderRecordedDataBlock = { actionFlags, timestamp, _, frameCount, abl, renderContext in
            let (converterRef, inputData) = renderContext!
                .assumingMemoryBound(to: (Unmanaged<SimpleAudioConverter>, UnsafeMutablePointer<AudioBufferList>).self)
                .pointee
            return converterRef.takeUnretainedValue().convert(framesCount: frameCount, from: inputData, to: abl)
        }

        let sink = AVAudioSinkNode { timestamp, framesCount, inputData -> OSStatus in
            var flags: AudioUnitRenderActionFlags = []
            var renderContext = (Unmanaged.passUnretained(converter), inputData)
            return deliverRecordedData(&flags, timestamp, 1, framesCount, nil, &renderContext, renderBlock)
        }
        engine.attach(sink)
        engine.connect(passThroughNode, to: sink, format: inputFormat)
        audioSinkNode = sink
    }

    private func attachPlayoutIfNeeded(to engine: AVAudioEngine, delegate: RTCAudioDeviceDelegate) {
        guard audioSourceNode == nil else { return }
        let outputFormat = engine.outputNode.outputFormat(forBus: 0)
        guard outputFormat.isSampleRateAndChannelCountValid else {
            nlog("audioDevice invalid output format \(outputFormat)")
            return
        }
        engine.connect(engine.mainMixerNode, to: engine.outputNode, format: outputFormat)

        guard let rtcPlayFormat = AVAudioFormat(commonFormat: .pcmFormatInt16,
                                                 sampleRate: outputFormat.sampleRate,
                                                 channels: outputFormat.channelCount,
                                                 interleaved: true) else {
            nlog("audioDevice failed to build playout format")
            return
        }
        audioOutputFormat = rtcPlayFormat
        outputLatency = audioSession.outputLatency

        let getPlayoutData = delegate.getPlayoutData
        let source = AVAudioSourceNode(format: rtcPlayFormat) { isSilence, timestamp, frameCount, outputData -> OSStatus in
            var flags: AudioUnitRenderActionFlags = []
            let status = getPlayoutData(&flags, timestamp, 0, frameCount, outputData)
            guard status == noErr else { return status }
            isSilence.initialize(to: ObjCBool(flags.contains(.unitRenderAction_OutputIsSilence)))
            return noErr
        }
        engine.attach(source)
        engine.connect(source, to: engine.mainMixerNode, format: outputFormat)
        audioSourceNode = source
    }

    // MARK: - AVAudioSession interruption handling

    private func subscribeSessionNotifications() {
        guard sessionObservers.isEmpty else { return }
        let center = NotificationCenter.default
        let interruption = center.addObserver(forName: AVAudioSession.interruptionNotification,
                                                object: audioSession, queue: nil) { [weak self] note in
            guard let self, let raw = note.userInfo?[AVAudioSessionInterruptionTypeKey] as? NSNumber,
                  let type = AVAudioSession.InterruptionType(rawValue: raw.uintValue) else { return }
            switch type {
            case .began:
                self.isInterrupted.current = true
                nlog("audioDevice interruption began")
                self.queue.async { self.updateEngine() }
            case .ended:
                self.isInterrupted.current = false
                nlog("audioDevice interruption ended")
                self.queue.async { self.updateEngine() }
            @unknown default:
                break
            }
        }
        // Bluetooth headset/speaker never got picked up for calls (confirmed 2026-08-05,
        // undiagnosed until now): the category already allows it (.allowBluetoothHFP,
        // .allowBluetoothA2DP below), but nothing in this class ever reacted to
        // AVAudioSessionRouteChangeNotification — updateEngine() only ran again on
        // AVAudioEngineConfigurationChangeNotification, which is the ENGINE's own notification
        // about its I/O format and isn't guaranteed to fire promptly for every route change
        // (e.g. a Bluetooth HFP accessory connecting/disconnecting mid-call — narrowband
        // Bluetooth audio uses a different sample rate than the built-in mic/speaker, which is
        // exactly the case updateEngine()'s own isInputOutputSampleRatesNative check already
        // handles, it just was never being asked to check again). This is the officially
        // documented Apple pattern for reacting to route changes (vs. the earlier lesson in
        // CallManager about NOT blindly reapplying setCategory/overrideOutputAudioPort on every
        // route change — updateEngine() here is idempotent/cheap when the format hasn't
        // actually changed, so reacting to every reason is safe).
        let routeChange = center.addObserver(forName: AVAudioSession.routeChangeNotification,
                                              object: audioSession, queue: nil) { [weak self] note in
            guard let self else { return }
            let reason = (note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt) ?? 999
            nlog("audioDevice routeChange reason=\(reason)")
            self.queue.async { self.updateEngine() }
        }
        sessionObservers = [interruption, routeChange]
    }

    private func unsubscribeSessionNotifications() {
        let center = NotificationCenter.default
        sessionObservers.forEach { center.removeObserver($0) }
        sessionObservers = []
    }
}

// MARK: - RTCAudioDevice

extension NevodAudioDevice: RTCAudioDevice {

    var deviceInputSampleRate: Double { audioInputFormat?.sampleRate ?? audioSession.sampleRate }
    var deviceOutputSampleRate: Double { audioOutputFormat?.sampleRate ?? audioSession.sampleRate }
    var inputIOBufferDuration: TimeInterval { audioSession.ioBufferDuration }
    var outputIOBufferDuration: TimeInterval { audioSession.ioBufferDuration }
    var inputNumberOfChannels: Int { Int(audioInputFormat?.channelCount ?? AVAudioChannelCount(min(2, audioSession.inputNumberOfChannels))) }
    var outputNumberOfChannels: Int { Int(audioOutputFormat?.channelCount ?? AVAudioChannelCount(min(2, audioSession.outputNumberOfChannels))) }
    var isInitialized: Bool { delegate != nil }

    func initialize(with delegate: RTCAudioDeviceDelegate) -> Bool {
        guard self.delegate == nil else {
            nlog("audioDevice initialize called while already initialized")
            return false
        }
        subscribeSessionNotifications()
        self.delegate = delegate
        nlog("audioDevice initialized")
        return true
    }

    func terminateDevice() -> Bool {
        unsubscribeSessionNotifications()
        delegate = nil
        // sessionActiveFlag deliberately NOT cleared here — session activation is owned by
        // CallKit's didActivate/didDeactivate alone now; WebRTC tearing down/re-creating the
        // device mid-call must not make us forget a session CallKit still has active (nothing
        // would ever set it back — there is no more retry loop).
        // Also called from WebRTC's own thread (see startPlayout/etc's doc comment above) —
        // same queue for the same reason. shouldPlay/shouldRecord=false alone already routes
        // the queued updateEngine() into shutdownEngine() regardless of delegate/session state
        // above, so reordering those three resets ahead of the dispatch changes nothing.
        queue.async { [weak self] in
            self?.shouldPlay = false
            self?.shouldRecord = false
            self?.updateEngine()
        }
        nlog("audioDevice terminated")
        return true
    }

    var isPlayoutInitialized: Bool { isInitialized }
    func initializePlayout() -> Bool { isPlayoutInitialized }
    var isPlaying: Bool { shouldPlay }

    // WebRTC calls startPlayout/stopPlayout/startRecording/stopRecording from its own internal
    // thread, never from `queue` — calling updateEngine() directly here (as this used to)
    // raced against every other caller (handleSessionActivated, the interruption/routeChange/
    // engineConfigChange notification handlers), all of which already go through
    // `queue.async`. Two concurrent updateEngine() runs could both try to build/tear down
    // AVAudioEngine at once, e.g. one attaching passThroughNode to a freshly-built engine
    // while the other's shutdownEngine() (from a still-in-flight rebuild) detaches it from
    // underneath — confirmed via device crash log 2026-08-08 (AVAudioEngine assertion "nil ==
    // owningEngine || GetEngine() == owningEngine" on attach). Routing these through the same
    // queue as every other caller — with shouldPlay/shouldRecord written on that queue too,
    // not on WebRTC's calling thread — closes the race at its source rather than only at one
    // of its symptoms. Return value doesn't depend on updateEngine() actually finishing
    // (matches handleSessionActivated's fire-and-forget dispatch), so this can stay async.
    func startPlayout() -> Bool {
        nlog("audioDevice startPlayout")
        queue.async { [weak self] in
            self?.shouldPlay = true
            self?.updateEngine()
        }
        return true
    }

    func stopPlayout() -> Bool {
        nlog("audioDevice stopPlayout")
        queue.async { [weak self] in
            self?.shouldPlay = false
            self?.updateEngine()
        }
        return true
    }

    var isRecordingInitialized: Bool { isInitialized }
    func initializeRecording() -> Bool { isRecordingInitialized }
    var isRecording: Bool { shouldRecord }

    func startRecording() -> Bool {
        nlog("audioDevice startRecording")
        queue.async { [weak self] in
            self?.shouldRecord = true
            self?.updateEngine()
        }
        return true
    }

    func stopRecording() -> Bool {
        nlog("audioDevice stopRecording")
        queue.async { [weak self] in
            self?.shouldRecord = false
            self?.updateEngine()
        }
        return true
    }
}
