import Foundation
import Network

@MainActor
final class NevdClient: NSObject, ObservableObject {

    @Published var status: String = "disconnected"
    @Published var isConnected = false

    var onMessage: ((String, String, String, String?, String?, Bool) -> Void)?  // (from, msgId, text, card, replyTo, churchFont)
    var onInviteRequired: ((String, String) -> Void)?  // (reason, inviteMode: "admin"/"delegated"/etc.)
    var onJoinRequestAck: ((Bool, String?) -> Void)?  // (ok, reason)
    var onJoinRequestResolved: ((Bool) -> Void)?  // (approved) — real-time nudge sent the
                                                   // instant an admin decides, best-effort
                                                   // (only reaches a still-connected client;
                                                   // see node.py's _notify_join_request_resolved)
    var onNameTaken: (() -> Void)?
    var onCellRemoved: (() -> Void)?
    var onTurnCredentials: ((TurnInfo) -> Void)?
    var onAck: ((String, String) -> Void)?  // (msgId, status: "offline"/"delivered"/"read"/"failed")
    var onReaction: ((String, String, String?) -> Void)?  // (fromAddr, msgId, emoji: nil clears it)
    // "delete:"/"edit:" are in-band text prefixes on a normal encrypted "msg" packet (like
    // reply:/slavonic:), NOT a separate wire packet type — see project plan for why (REACT's
    // out-of-band unencrypted-payload pattern is wrong for these: delete needs the offline-
    // buffering/push/ack machinery that's only wired to T.MSG, and edit carries real message
    // content that must stay E2E encrypted). Detected and stripped in handleMsg below, BEFORE
    // the normal onMessage path — a delete/edit signal must never become a new chat bubble.
    var onDeleteMsg: ((String, String) -> Void)?  // (fromAddr, targetMsgId)
    var onEditMsg: ((String, String, String) -> Void)?  // (fromAddr, targetMsgId, newText)
    var onIdentityDeleted: ((String) -> Void)?  // (fromAddr) — sender reset their identity
    var onMemberAdded: (() -> Void)?  // a new home cell just registered on this node — refetch nodeMembers
    /// cellId → when this phone last ended a call with them (unix seconds), set by CallManager.
    /// Static: a reconnect creates a new NevdClient, and the call outlives it.
    static var callEndedAt: [String: Int64] = [:]
    var onMissedCall: ((String, Int64) -> Void)?  // (fromAddr, packetTs) — a buffered offer arrived too stale to ring live; still worth a call-log entry

    private(set) var identity: NevdIdentity
    var displayName: String = ""
    private(set) var nodeId: String = ""

    // Ordered candidate addresses for "our" node (e.g. a home node's LAN + external
    // address) — index 0 is tried first. See IdentityStore.nodeRoutes's doc comment.
    private var routes: [String] = []
    // Whichever route is actually connected right now — nil/empty when not connected.
    // Used for the outgoing card line (send()) instead of routes[0], since the
    // preferred route and the one we're actually live on can differ mid-failover.
    @Published private(set) var activeAddr: String = ""
    private var nodeSigningPub: Data = Data()
    private var webSocket: NWWebSocketTask?
    private var reconnect = false
    private var inviteCode: String? = nil
    /// Bumped synchronously on every NACK. AppStore's "connected held for 1.5 s" check reads
    /// this, not the status mirror, which arrives via RunLoop.main and lags while the user is
    /// touching the screen — see AppStore.startClient.
    private(set) var nackCount = 0
    // SHA-256 fingerprint to pin the server's self-signed TLS cert against — nil
    // means fall back to normal system CA trust (the prod path, fronted by nginx
    // with a real cert). Passed into NWWebSocketTask's TLS verify block at connect
    // time; see NWWebSocketTask.swift for why a custom transport was needed at all.
    private var pinnedFingerprint: String? = nil

    // Per-candidate cap for tryConnect()'s whole pipeline (transport + auth + register)
    // — see tryConnect's doc comment for why this exists.
    private let connectTimeoutSecs: UInt64 = 8

    private var pendingMembers: CheckedContinuation<[GroupMember], Error>?
    private var pendingNodeList: CheckedContinuation<[PublicNode], Error>?
    private var pendingNodeCells: CheckedContinuation<[PublishedCell], Error>?
    private var pendingInvite:  CheckedContinuation<InviteResult, Error>?
    private var pendingCard:    CheckedContinuation<CardResult, Error>?
    private var reconnectTask:  Task<Void, Never>?
    // Reentrancy guard for connectWithFailover() — see its own doc comment. Without this,
    // two independent triggers (scheduleReconnect()'s 3s timer, pathDebounceTask's 1.5s
    // timer, the initial connect() call) can each start a pass concurrently; tryConnect()'s
    // `old?.cancel()` step then cancels whatever socket the OTHER still-in-flight pass just
    // set, dropping it mid-handshake or right after a buffered message was flushed onto it.
    // Confirmed on device 2026-09-24: exactly this race lost a join-request notification —
    // the server's own logs showed it flushed successfully, but two overlapping "connected"
    // transitions ~2s apart in the client log show the delivering socket got torn down by a
    // sibling reconnect attempt before the message was ever processed.
    private var isConnectingPass = false

    init(identity: NevdIdentity) {
        self.identity = identity
        super.init()
    }

    func connect(to addresses: [String], pinnedFingerprint: String? = nil, inviteCode: String? = nil) {
        routes = addresses
        self.pinnedFingerprint = pinnedFingerprint
        if let inviteCode {
            self.inviteCode = inviteCode.trimmingCharacters(in: .whitespaces).uppercased()
        }
        reconnect = true
        Task { await connectWithFailover() }
        startPathMonitorIfNeeded()
    }

    /// Updates the candidate list for the NEXT reconnect attempt without forcing one
    /// now — called when the user edits their route list mid-session so it's picked up
    /// without requiring an app relaunch.
    func updateRoutes(_ addresses: [String]) {
        routes = addresses
    }

    func disconnect() {
        reconnect = false
        reconnectTask?.cancel(); reconnectTask = nil
        stopPathMonitor()
        webSocket?.cancel()
        webSocket = nil; activeAddr = ""; setStatus("disconnected")
    }

    /// Tries each candidate in `routes`, in order, until one works. On success, promotes
    /// the winner to the front of the list and persists that — "last successful route
    /// becomes primary" survives an app relaunch. If every candidate fails, falls back
    /// to the same fixed-delay retry loop as before (scheduleReconnect), which will
    /// re-run this same failover pass rather than blindly retrying one dead address.
    /// Guarded against concurrent invocation (isConnectingPass) — see that property's doc
    /// comment. A second trigger arriving mid-pass just no-ops: whatever prompted it (a
    /// path change, a scheduled retry) is still reflected once the current pass concludes,
    /// either by succeeding or by itself calling scheduleReconnect for a fresh attempt.
    private func connectWithFailover() async {
        guard !isConnectingPass else {
            nlog("doConnect connectWithFailover SKIP — a pass is already in flight")
            return
        }
        isConnectingPass = true
        defer { isConnectingPass = false }
        guard !routes.isEmpty else { return }
        for (i, addr) in routes.enumerated() {
            guard reconnect else { return }  // disconnected while we were iterating
            nlog("doConnect trying route \(i + 1)/\(routes.count) addr=\(addr)")
            if await tryConnect(addr: addr) {
                activeAddr = addr
                promoteToPrimary(addr)
                return
            }
        }
        nlog("doConnect all \(routes.count) route(s) failed")
        setStatus("error: no reachable route")
        isConnected = false
        scheduleReconnect()
    }

    private func promoteToPrimary(_ addr: String) {
        guard routes.first != addr else { return }
        var reordered = routes
        reordered.removeAll { $0 == addr }
        reordered.insert(addr, at: 0)
        routes = reordered
        IdentityStore.nodeRoutes = reordered
    }

    /// One candidate address, full pipeline (transport connect + Schnorr auth + cell
    /// register). Time-boxed by a watchdog that force-cancels the attempt if it's still
    /// running after `connectTimeoutSecs` — NWWebSocketTask.connect() has no timeout of
    /// its own, and without this a single unreachable/silently-dropping candidate (e.g.
    /// a LAN address tried from off that LAN) could hang the whole failover pass
    /// instead of moving on to the next route. Returns true on success; on failure or
    /// timeout, cleans up and returns false — the caller decides what to try next.
    private func tryConnect(addr: String) async -> Bool {
        let old = webSocket
        webSocket = nil
        old?.cancel()
        // Not connected from here until registered again: senders must see the gap (and
        // queue, see AppStore.sendSignal) instead of writing into no socket at all.
        isConnected = false

        setStatus("connecting…")
        nlog("doConnect addr=\(addr) pinned=\(pinnedFingerprint?.prefix(16).description ?? "nil")")
        do {
            let commit = try schnorrCommit()
            guard let url = URL(string: "wss://\(addr)"), let host = url.host else {
                throw NevdError.invalidAddress
            }
            let port = UInt16(url.port ?? 443)
            let path = url.path.isEmpty ? "/" : url.path
            let ws = NWWebSocketTask(host: host, port: port, pinnedFingerprint: pinnedFingerprint)
            let watchdog = Task { [connectTimeoutSecs] in
                try? await Task.sleep(nanoseconds: connectTimeoutSecs * 1_000_000_000)
                guard !Task.isCancelled else { return }
                nlog("doConnect addr=\(addr) TIMEOUT after \(connectTimeoutSecs)s, cancelling attempt")
                ws.cancel()
            }
            defer { watchdog.cancel() }

            try await ws.connect(host: host, port: port, path: path)
            webSocket = ws

            setStatus("authenticating…")
            let auth = try await performAuth(ws: ws, commit: commit)
            nodeId = auth.nodeId; nodeSigningPub = auth.nodeSigningPub

            try await registerCell(ws: ws)
            setStatus("connected"); isConnected = true
            receiveLoop(ws: ws)
            return true
        } catch {
            nlog("doConnect FAILED addr=\(addr) error=\(error) detail=\(fullErrorDetail(error))")
            isConnected = false
            return false
        }
    }

    /// Walks NSUnderlyingError chains — the top-level NSURLErrorDomain -1200 message
    /// is generic ("A TLS error caused..."); the real reason (e.g. a SecureTransport/
    /// Network.framework OSStatus) is usually nested one or two levels down.
    private func fullErrorDetail(_ error: Error) -> String {
        var parts: [String] = []
        var current: NSError? = error as NSError
        var depth = 0
        while let e = current, depth < 5 {
            parts.append("[\(e.domain) \(e.code)] \(e.userInfo[NSLocalizedDescriptionKey] ?? "")")
            current = e.userInfo[NSUnderlyingErrorKey] as? NSError
            depth += 1
        }
        return parts.joined(separator: " <- ")
    }

    private func scheduleReconnect() {
        guard reconnect else { return }
        reconnectTask?.cancel()
        reconnectTask = Task {
            try? await Task.sleep(nanoseconds: 3_000_000_000)
            guard !Task.isCancelled, self.reconnect else { return }
            await self.connectWithFailover()
        }
    }

    // MARK: - Network path monitoring
    //
    // Deliberately NOT a periodic timer-based ping to probe whether a candidate route
    // (e.g. a home node's LAN address) has become reachable — a regular, scheduled
    // connection attempt is a distinctive traffic pattern a passive network observer
    // could use to fingerprint "this device talks to a Nevod node on a schedule".
    // NWPathMonitor instead reacts to the OS's own on-device knowledge that network
    // conditions changed (Wi-Fi joined/left, interface changed) — zero network traffic
    // of its own, invisible to anyone outside the device. When it fires, the reaction
    // is just a normal connectWithFailover() pass — the exact same real connect
    // pipeline (TLS + Schnorr auth) any other reconnect uses, so there's no new,
    // separately-identifiable "probe" traffic shape at all, only a possibly-earlier
    // ordinary reconnect. This is also the fix for a home node's hairpin-NAT case: a
    // device connected via the external address that walks onto the node's own LAN
    // typically loses that route immediately (most home routers can't loop back to
    // their own public IP from inside), and the existing TCP keepalive alone can take
    // up to ~19s (NWWebSocketTask.swift) to notice — this reacts within ~1.5s instead.
    private var pathMonitor: NWPathMonitor?
    private var pathDebounceTask: Task<Void, Never>?
    // NWPathMonitor invokes pathUpdateHandler once synchronously with the CURRENT path
    // as soon as start() is called — that first call isn't a change, just a status
    // dump, and would otherwise trigger a redundant failover pass moments after every
    // ordinary connect(). Only this one, very first callback is skipped; every
    // subsequent one is a genuine change and must still be acted on regardless of
    // current connection state (deliberately NOT gated on "already connected to
    // primary" — that would also suppress the hairpin-NAT case this exists for: the
    // external address can still look "connected" for a while after it's actually
    // gone dead).
    private var isFirstPathUpdate = true
    // Last-seen coarse fingerprint (satisfied? + which interface TYPES are available) — see
    // onPathChanged's doc comment for why this exists: confirmed on device 2026-08-27, the
    // home-node connection was churning every 10-30s (server logs: "no close frame received
    // or sent", the signature of tryConnect()'s abrupt old-socket .cancel(), not a graceful
    // close). Root cause traced to pathUpdateHandler firing on EVERY callback regardless of
    // whether anything about the actual usable network changed (NWPathMonitor is documented
    // to sometimes re-fire for non-substantive changes — DNS server list, interface metrics —
    // not just real transitions), each one triggering a full abrupt reconnect.
    private var lastPathFingerprint: String? = nil

    private func startPathMonitorIfNeeded() {
        guard pathMonitor == nil else { return }
        isFirstPathUpdate = true
        lastPathFingerprint = nil
        let monitor = NWPathMonitor()
        monitor.pathUpdateHandler = { [weak self] path in
            guard let self else { return }
            Task { @MainActor in self.onPathChanged(path) }
        }
        monitor.start(queue: DispatchQueue(label: "nevod.pathmonitor"))
        pathMonitor = monitor
    }

    private func stopPathMonitor() {
        pathMonitor?.cancel()
        pathMonitor = nil
        pathDebounceTask?.cancel(); pathDebounceTask = nil
    }

    /// Coarse summary of "what kind of network do we have" — satisfied/not, plus which
    /// interface TYPES (wifi/cellular/wired/...) are available, deliberately not the full
    /// interface list (names/order can shuffle harmlessly) or anything finer-grained (DNS,
    /// gateways) that NWPathMonitor can re-report without the usable route actually changing.
    private func pathFingerprint(_ path: NWPath) -> String {
        let types = Set(path.availableInterfaces.map { "\($0.type)" }).sorted().joined(separator: ",")
        return "\(path.status == .satisfied)|\(types)"
    }

    /// Debounced because a single real network transition can fire pathUpdateHandler
    /// several times in quick succession — collapse those into one fresh failover pass
    /// instead of racing multiple reconnect attempts against each other. Also gated on the
    /// fingerprint actually changing (see lastPathFingerprint's doc comment) — every callback
    /// used to trigger a reconnect unconditionally, which is what was causing the churn.
    private func onPathChanged(_ path: NWPath) {
        guard reconnect else { return }
        let fp = pathFingerprint(path)
        if isFirstPathUpdate { isFirstPathUpdate = false; lastPathFingerprint = fp; return }
        guard fp != lastPathFingerprint else {
            nlog("pathUpdateHandler fired, fingerprint unchanged (\(fp)) — ignored, no reconnect")
            return
        }
        nlog("pathUpdateHandler fingerprint changed: \(lastPathFingerprint ?? "nil") -> \(fp)")
        lastPathFingerprint = fp
        // Mid-call a working connection stays: Wi-Fi coming up as a woken phone answered
        // started a reconnect, and the answer went out in the gap and was lost (device logs
        // 2026-10-21). If the old network really went away, the receive loop fails and
        // reconnects anyway; the call's own audio follows the network through WebRTC.
        if Self.callInProgress && isConnected {
            nlog("pathUpdateHandler call in progress, connection kept")
            return
        }
        pathDebounceTask?.cancel()
        pathDebounceTask = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 1_500_000_000)
            guard !Task.isCancelled, let self, self.reconnect else { return }
            nlog("doConnect network path changed, re-checking routes")
            await self.connectWithFailover()
        }
    }

    // MARK: - Auth

    private struct AuthResult { let nodeId: String; let nodeSigningPub: Data; let nodeEncPub: Data }

    private func performAuth(ws: NWWebSocketTask, commit: SchnorrCommit) async throws -> AuthResult {
        let cid = identity.cellId
        let commitPkt = makePacket(type: "auth_commit", payload: encodePayload([
            "R": commit.R, "signing_pub": identity.signingPub, "enc_pub": identity.encPub,
        ]), from: cid, to: "")
        try await wsSend(ws: ws, pkt: commitPkt)

        let theirCommit = try unpackPacket(try await wsRecv(ws: ws))
        guard theirCommit.type == "auth_commit" else { throw NevdError.authFailed("expected auth_commit") }
        let d = try decodePayload(theirCommit.payload)
        let R_peer = d["R"].data ?? Data()
        let X_peer = d["signing_pub"].data ?? Data()
        let E_peer = d["enc_pub"].data ?? Data()

        let c_self = schnorrChallenge(R_prover: commit.R, X_prover: identity.signingPub,
                                       R_verifier: R_peer, X_verifier: X_peer)
        let s_self = schnorrProve(signingPriv: identity.signingPriv, rBytes: commit.rBytes, c: c_self)

        var respPkt = makePacket(type: "auth_response", payload: encodePayload(["s": s_self]),
                                  from: cid, to: Hex.encode(X_peer))
        try signPacket(&respPkt, seed: identity.signingPriv)
        try await wsSend(ws: ws, pkt: respPkt)

        let theirResp = try unpackPacket(try await wsRecv(ws: ws))
        guard theirResp.type == "auth_response" else { throw NevdError.authFailed("expected auth_response") }

        nlog("performAuth OK nodeId=\(Hex.encode(X_peer).prefix(16))")
        return AuthResult(nodeId: Hex.encode(X_peer), nodeSigningPub: X_peer, nodeEncPub: E_peer)
    }

    // MARK: - Register

    private func registerCell(ws: NWWebSocketTask) async throws {
        var payload: [String: Any?] = [
            "cell_id": identity.cellId, "signing_pubkey": identity.signingPub,
            "enc_pubkey": identity.encPub, "is_home": true, "display_name": displayName,
        ]
        if let code = inviteCode { payload["invite_code"] = code }
        var pkt = makePacket(type: "cell_register", payload: encodePayload(payload),
                              from: identity.cellId, to: nodeId)
        try signPacket(&pkt, seed: identity.signingPriv)
        nlog("registerCell sending cell=\(identity.cellId.prefix(8)) name=\(displayName) hasInviteCode=\(inviteCode != nil)")
        try await wsSend(ws: ws, pkt: pkt)
        nlog("registerCell sent (no synchronous ack — success is implicit unless a nack follows)")
    }

    /// Re-registers the same cell_id with a new display_name — node.py's register_cell is an
    /// upsert keyed on cell_id, so this updates the server's record in place rather than
    /// creating anything new. Same "no ack on success" trust as registerCell/registerWithCode;
    /// a name collision still surfaces via the existing onNameTaken/cell_register_nack path.
    func updateDisplayName(_ name: String) {
        displayName = name
        guard let ws = webSocket, isConnected else { return }
        Task {
            let payload: [String: Any?] = [
                "cell_id": identity.cellId, "signing_pubkey": identity.signingPub,
                "enc_pubkey": identity.encPub, "is_home": true, "display_name": name,
            ]
            var pkt = makePacket(type: "cell_register", payload: encodePayload(payload),
                                  from: identity.cellId, to: nodeId)
            try? signPacket(&pkt, seed: identity.signingPriv)
            try? await wsSend(ws: ws, pkt: pkt)
        }
    }

    func registerWithCode(_ code: String) {
        inviteCode = code.trimmingCharacters(in: .whitespaces).uppercased()
        guard let ws = webSocket else { return }
        let currentCode = inviteCode!
        setStatus("invite required")  // reset so optimistic check works on retry too
        Task {
            let payload: [String: Any?] = [
                "cell_id": identity.cellId, "signing_pubkey": identity.signingPub,
                "enc_pubkey": identity.encPub, "is_home": true,
                "display_name": displayName, "invite_code": currentCode,
            ]
            var pkt = makePacket(type: "cell_register", payload: encodePayload(payload),
                                  from: identity.cellId, to: nodeId)
            try? signPacket(&pkt, seed: identity.signingPriv)
            try? await wsSend(ws: ws, pkt: pkt)
            // No ack from node on success — optimistically connect after 2s if no nack
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            if self.status == "invite required" {
                self.setStatus("connected")
                self.isConnected = true
            }
        }
    }

    // MARK: - Receive Loop

    private func receiveLoop(ws: NWWebSocketTask) {
        Task { [weak self] in
            while let self = self, self.webSocket === ws {
                do {
                    let data = try await self.wsRecv(ws: ws)
                    await self.handleRaw(data)
                } catch {
                    await MainActor.run {
                        guard self.webSocket === ws else { return }
                        nlog("receive loop ended err=\(error)")
                        self.isConnected = false
                        self.setStatus("reconnecting…")
                        self.scheduleReconnect()
                    }
                    return
                }
            }
        }
    }

    private func handleRaw(_ data: Data) async {
        // Both guards used to fail completely silently — confirmed via server-side node logs
        // 2026-08-24 that a "delivered"+"read" ack pair was sent successfully (home_node
        // send=True) while this client was connected, yet neither ever reached handleAck.
        // Whichever guard is actually failing was untraceable without this: no way to tell
        // "packet never arrived" from "arrived but got dropped here" after the fact.
        guard let pkt = try? unpackPacket(data) else {
            nlog("handleRaw unpackPacket FAILED len=\(data.count)")
            return
        }
        guard verifyPacket(pkt, publicKey: nodeSigningPub) else {
            nlog("handleRaw verifyPacket FAILED type=\(pkt.type) id=\(pkt.id.prefix(8))")
            return
        }
        switch pkt.type {
        case "msg", "msg_chunk", "msg_silent", "vcall_offer", "vcall_signal": await handleMsg(pkt)
        case "turn_creds":             handleTurnCreds(pkt)
        case "group_members_response": handleMembers(pkt)
        case "node_list_response":     handleNodeList(pkt)
        case "node_cells_response":    handleNodeCells(pkt)
        case "cell_register_nack":     handleNack(pkt)
        case "join_request_ack":       handleJoinRequestAck(pkt)
        case "join_request_resolved":  handleJoinRequestResolved(pkt)
        case "invite_response":        handleInviteResponse(pkt)
        case "card_response":          handleCardResponse(pkt)
        case "cell_removed":           handleCellRemoved()
        case "ack":                    handleAck(pkt)
        case "react":                  handleReaction(pkt)
        default: break
        }
    }

    // MARK: - Message

    private func handleMsg(_ pkt: NevdPacket) async {
        guard let d = try? decodePayload(pkt.payload),
              let ephPub = d["ephemeral_pubkey"].data,
              let nonce  = d["nonce"].data,
              let ct     = d["ciphertext"].data,
              let pt     = try? decryptMsg(ciphertext: ct, nonce: nonce, ephPub: ephPub,
                                            myEncPriv: identity.encPriv) else { return }
        // Defense in depth against a stale buffered call signal being replayed as if
        // live (the node itself now drops these past CALL_SIGNAL_STALE_SECS=60s at
        // flush time — see router.py — but this catches it here too in case a signal
        // ever reaches the client some other way). Found 2026-09-02: a missed call
        // whose VoIP push failed silently got replayed hours later on next app open,
        // showing a full ringing/answering UI for a call that was long over. A stale
        // offer specifically still becomes a "missed call" log entry — silently
        // dropping it too would make the call vanish from history with no trace,
        // trading one bug (phantom live call) for another (call just disappears).
        // Stale non-offer signals (ring/ice/answer/etc.) carry no useful information
        // on their own once their offer is gone — dropped with no further action.
        if pkt.type == "vcall_offer" || pkt.type == "vcall_signal" {
            let age = Date().timeIntervalSince1970 - Double(pkt.ts)
            if age > 60 {
                nlog("handleMsg dropping stale \(pkt.type) from=\(pkt.from.prefix(8)) age=\(Int(age))s")
                if pkt.type == "vcall_offer" { onMissedCall?(pkt.from, pkt.ts) }
                return
            }
            // Created before this phone ended the call with that peer: a signal of a call that is
            // already over, delivered late (it sat on the node behind a video). An offer like
            // that rang again after the caller had hung up (device logs 2026-10-20). 2 s of
            // slack for the two phones' clocks.
            let fromCell = String(pkt.from.split(separator: "@").first ?? Substring(pkt.from))
            if let ended = Self.callEndedAt[fromCell], pkt.ts + 2 < ended {
                nlog("handleMsg dropping \(pkt.type) from=\(fromCell.prefix(8)) — made \(ended - pkt.ts)s before the call with them ended")
                return
            }
        }
        var text = String(data: pt, encoding: .utf8) ?? ""
        var senderCard: String? = nil
        if text.hasPrefix("card:"), let nl = text.firstIndex(of: "\n") {
            senderCard = String(text[text.index(text.startIndex, offsetBy: 5)..<nl])
            text = String(text[text.index(after: nl)...])
        }
        // delete:/edit: are control signals about an EXISTING message, not new chat content —
        // checked before reply:/slavonic: (which don't apply to them) and, when matched, skip
        // onMessage entirely so no spurious new bubble gets created. Still falls through to the
        // ack below like any other "msg" packet.
        if text.hasPrefix("delete:"), let nl = text.firstIndex(of: "\n") {
            let targetId = String(text[text.index(text.startIndex, offsetBy: 7)..<nl])
            onDeleteMsg?(pkt.from, targetId)
        } else if text.hasPrefix("edit:"), let nl = text.firstIndex(of: "\n") {
            let targetId = String(text[text.index(text.startIndex, offsetBy: 5)..<nl])
            let newText = String(text[text.index(after: nl)...])
            onEditMsg?(pkt.from, targetId, newText)
        } else if text.hasPrefix("identity_deleted:") {
            onIdentityDeleted?(pkt.from)
        } else if text.hasPrefix("member_added:") {
            onMemberAdded?()
        } else {
            var replyTo: String? = nil
            if text.hasPrefix("reply:"), let nl = text.firstIndex(of: "\n") {
                replyTo = String(text[text.index(text.startIndex, offsetBy: 6)..<nl])
                text = String(text[text.index(after: nl)...])
            }
            var churchFont = false
            if text.hasPrefix("slavonic:\n") {
                churchFont = true
                text = String(text.dropFirst("slavonic:\n".count))
            }
            onMessage?(pkt.from, pkt.id, text, senderCard, replyTo, churchFont)
        }
        // Call offers don't have a corresponding stored Message to correlate a delivery
        // status against — CallManager has its own timeout/ring signaling for reliability.
        // msg_chunk (a non-final file-transfer fragment) is acked too, but only for the node:
        // it keeps each chunk in flight until this ack and re-queues it if our connection
        // drops first (router.py _deliver_local/on_connection_lost) — otherwise one fragment
        // lost in a dying mobile socket leaves the file unassemblable. The node doesn't
        // forward a chunk ack to the sender, which stores no message for a fragment's id.
        if pkt.type == "msg" || pkt.type == "msg_chunk" || pkt.type == "msg_silent" {
            sendAck(msgId: pkt.id, status: "delivered", toAddr: pkt.from)
        }
    }

    /// id: pass the caller's own message id (e.g. AppStore's Message.msgId) so a later
    /// incoming ACK for this packet id can be matched back to that stored message.
    /// Omit for signaling sends (e.g. vcall:) that don't need delivery tracking.
    /// type: "msg" for chat, "vcall_offer" for a call offer specifically, "msg_silent" for
    /// a control signal (delete:/edit:/identity_deleted:/contact-added notice) that must
    /// never surface as a "New message" push since it produces no visible chat bubble — the
    /// router can't tell these apart from real content by payload (E2E encrypted either
    /// way), only by this wire-level type.
    /// Marks the id of a packet sent without a stored message behind it (id omitted above:
    /// file chunks, msg_silent edit/delete/notices). Their acks can still come back — every
    /// msg_silent ack does, and a chunk ack does when the recipient's node predates keeping
    /// those to itself — and AppStore.handleAck drops them quietly by this prefix instead of
    /// logging each as "NO MATCHING MESSAGE". The recipient only echoes the id back, so this
    /// works whatever version it runs.
    static let untrackedIdPrefix = "u-"

    /// fileData: a chunk of a file (header and last one included) — waits its turn, see
    /// callInProgress.
    func send(toCellId: String, toNodeId: String, recipientEncPub: Data, text: String,
              id: String? = nil, type: String = "msg", callerName: String = "",
              fileData: Bool = false) async throws {
        if fileData { await Self.takeFileTurn() }
        defer { if fileData { Self.fileWriteBusy = false; Self.wakeFileSenders() } }
        guard let ws = webSocket, isConnected else { throw NevdError.notConnected }
        let cardLine = "card:\(identity.cellId)@\(activeAddr)|\(nodeId)|\(Hex.encode(identity.encPub))\n"
        let full = cardLine.data(using: .utf8)! + (text.data(using: .utf8) ?? Data())
        let enc = try encryptMsg(plaintext: full, recipientEncPub: recipientEncPub)
        var pkt = makePacket(type: type, payload: encodePayload([
            "ephemeral_pubkey": enc.ephPub, "nonce": enc.nonce, "ciphertext": enc.ciphertext,
        ]), from: "\(identity.cellId)@\(nodeId)", to: "\(toCellId)@\(toNodeId)",
           id: id ?? Self.untrackedIdPrefix + UUID().uuidString, callerName: callerName)
        try signPacket(&pkt, seed: identity.signingPriv)
        if fileData {
            try await ws.send(packPacket(pkt))
        } else {
            try await wsSend(ws: ws, pkt: pkt)
        }
    }

    // MARK: - Send priority
    //
    // On one socket everything goes out in the order it was written, so what is written
    // first matters: service packets (acks, silent signals, registration) and call signals
    // and messages go out at once, as always; file data one chunk at a time, only while
    // nothing more urgent is being written, and not at all while a call is ringing or up.
    // Device logs 2026-10-21: a hangup waited 10–16 s behind the sender's own video chunks,
    // and the call's audio shared the uplink with them.

    /// Set by CallManager while its state isn't idle. File chunks wait until it's cleared,
    /// and a network change doesn't replace a working connection meanwhile (onPathChanged).
    static var callInProgress = false {
        didSet { if !callInProgress { wakeFileSenders() } }
    }
    private static var urgentWrites = 0
    private static var fileWriteBusy = false
    private static var fileWaiters: [CheckedContinuation<Void, Never>] = []

    private static func wakeFileSenders() {
        let waiting = fileWaiters
        fileWaiters.removeAll()
        waiting.forEach { $0.resume() }
    }

    /// Returns once no call is on, no urgent write is in progress and no other chunk is being
    /// written — then this chunk holds the turn until its write completes.
    private static func takeFileTurn() async {
        while callInProgress || urgentWrites > 0 || fileWriteBusy {
            await withCheckedContinuation { fileWaiters.append($0) }
        }
        fileWriteBusy = true
    }

    /// Proactively tells `toCellId` that we just added them as a contact — lets
    /// their app surface a "X added you" prompt right away instead of only
    /// discovering us whenever their first real chat message happens to arrive.
    func sendContactAddNotice(toCellId: String, toNodeId: String, recipientEncPub: Data) async throws {
        try await send(toCellId: toCellId, toNodeId: toNodeId, recipientEncPub: recipientEncPub,
                       text: "\(contactAddNoticePrefix)\(displayName)", type: "msg_silent")
    }

    // MARK: - Group Members

    struct GroupMember { let cellId: String; let encPubkey: Data; let displayName: String }

    func getGroupMembers() async throws -> [GroupMember] {
        guard let ws = webSocket, isConnected else { throw NevdError.notConnected }
        return try await withCheckedThrowingContinuation { [weak self] cont in
            guard let self else { cont.resume(throwing: NevdError.notConnected); return }
            self.pendingMembers = cont
            var req = makePacket(type: "group_members_request", payload: Data(),
                                  from: "\(self.identity.cellId)@\(self.nodeId)", to: self.nodeId)
            try? signPacket(&req, seed: self.identity.signingPriv)
            Task { try? await self.wsSend(ws: ws, pkt: req) }
            Task {
                try? await Task.sleep(nanoseconds: 5_000_000_000)
                self.pendingMembers?.resume(throwing: NevdError.timeout); self.pendingMembers = nil
            }
        }
    }

    private func handleMembers(_ pkt: NevdPacket) {
        guard let d = try? decodePayload(pkt.payload),
              let arr = d["members"].array else {
            pendingMembers?.resume(returning: [])
            pendingMembers = nil
            return
        }
        let members = arr.compactMap { m -> GroupMember? in
            guard let cid = m["cell_id"].string, let enc = m["enc_pubkey"].data else { return nil }
            return GroupMember(cellId: cid, encPubkey: enc, displayName: m["display_name"].string ?? "")
        }
        pendingMembers?.resume(returning: members)
        pendingMembers = nil
    }

    // MARK: - Public node directory

    struct PublicNode { let nodeId: String; let name: String; let address: String }

    func getPublicNodes() async throws -> [PublicNode] {
        guard let ws = webSocket, isConnected else { throw NevdError.notConnected }
        return try await withCheckedThrowingContinuation { [weak self] cont in
            guard let self else { cont.resume(throwing: NevdError.notConnected); return }
            self.pendingNodeList = cont
            var req = makePacket(type: "node_list_request", payload: Data(),
                                  from: "\(self.identity.cellId)@\(self.nodeId)", to: self.nodeId)
            try? signPacket(&req, seed: self.identity.signingPriv)
            Task { try? await self.wsSend(ws: ws, pkt: req) }
            Task {
                try? await Task.sleep(nanoseconds: 5_000_000_000)
                self.pendingNodeList?.resume(throwing: NevdError.timeout); self.pendingNodeList = nil
            }
        }
    }

    private func handleNodeList(_ pkt: NevdPacket) {
        guard let d = try? decodePayload(pkt.payload),
              let arr = d["nodes"].array else {
            pendingNodeList?.resume(returning: [])
            pendingNodeList = nil
            return
        }
        let nodes = arr.compactMap { n -> PublicNode? in
            guard let nid = n["node_id"].string else { return nil }
            return PublicNode(nodeId: nid, name: n["name"].string ?? "",
                              address: n["address"].string ?? "")
        }
        pendingNodeList?.resume(returning: nodes)
        pendingNodeList = nil
    }

    // MARK: - Published cells (Explore Network planet detail)

    /// Own home node only — reuses this live connection. For any OTHER node
    /// discovered on the planets screen, see NodeCellsBrowser (a separate,
    /// unregistered one-off connection).
    func getNodeCells() async throws -> [PublishedCell] {
        guard let ws = webSocket, isConnected else { throw NevdError.notConnected }
        // One request at a time: AppStore.fetchNodeMembers asks on every connect, the planet
        // screen on open — a second continuation would overwrite the first, which then never resumes.
        guard pendingNodeCells == nil else { throw NevdError.timeout }
        return try await withCheckedThrowingContinuation { [weak self] cont in
            guard let self else { cont.resume(throwing: NevdError.notConnected); return }
            self.pendingNodeCells = cont
            var req = makePacket(type: "node_cells_request", payload: Data(),
                                  from: "\(self.identity.cellId)@\(self.nodeId)", to: self.nodeId)
            try? signPacket(&req, seed: self.identity.signingPriv)
            Task { try? await self.wsSend(ws: ws, pkt: req) }
            Task {
                try? await Task.sleep(nanoseconds: 5_000_000_000)
                self.pendingNodeCells?.resume(returning: [])  // withheld (off/not-member) reads as empty
                self.pendingNodeCells = nil
            }
        }
    }

    private func handleNodeCells(_ pkt: NevdPacket) {
        pendingNodeCells?.resume(returning: NodeCellsBrowser.parseCellsPayload(pkt.payload))
        pendingNodeCells = nil
    }

    // MARK: - Invite

    struct InviteResult {
        let ok: Bool; let code: String?; let reason: String?
        let address: String?; let fingerprint: String?
    }

    func createInvite() async throws -> InviteResult {
        guard let ws = webSocket, isConnected else { throw NevdError.notConnected }
        return try await withCheckedThrowingContinuation { [weak self] cont in
            guard let self else { cont.resume(throwing: NevdError.notConnected); return }
            self.pendingInvite = cont
            var req = makePacket(type: "invite_create", payload: Data(),
                                  from: "\(self.identity.cellId)@\(self.nodeId)", to: self.nodeId)
            try? signPacket(&req, seed: self.identity.signingPriv)
            Task { try? await self.wsSend(ws: ws, pkt: req) }
            Task {
                try? await Task.sleep(nanoseconds: 5_000_000_000)
                self.pendingInvite?.resume(throwing: NevdError.timeout); self.pendingInvite = nil
            }
        }
    }

    private func handleInviteResponse(_ pkt: NevdPacket) {
        guard let d = try? decodePayload(pkt.payload) else { return }
        pendingInvite?.resume(returning: InviteResult(
            ok: d["ok"].bool ?? false, code: d["code"].string, reason: d["reason"].string,
            address: d["address"].string, fingerprint: d["tls_fingerprint"].string))
        pendingInvite = nil
    }

    // MARK: - Card

    struct CardResult { let code: String?; let card: String? }

    func createCard() async throws -> CardResult {
        guard let ws = webSocket, isConnected else { throw NevdError.notConnected }
        return try await withCheckedThrowingContinuation { [weak self] cont in
            guard let self else { cont.resume(throwing: NevdError.notConnected); return }
            self.pendingCard = cont
            var req = makePacket(type: "card_create", payload: Data(),
                                  from: "\(self.identity.cellId)@\(self.nodeId)", to: self.nodeId)
            try? signPacket(&req, seed: self.identity.signingPriv)
            Task { try? await self.wsSend(ws: ws, pkt: req) }
            Task {
                try? await Task.sleep(nanoseconds: 5_000_000_000)
                self.pendingCard?.resume(throwing: NevdError.timeout); self.pendingCard = nil
            }
        }
    }

    private func handleCardResponse(_ pkt: NevdPacket) {
        guard let d = try? decodePayload(pkt.payload) else { return }
        pendingCard?.resume(returning: CardResult(code: d["code"].string, card: d["card"].string))
        pendingCard = nil
    }

    // MARK: - Deregister

    func deregister() {
        // Not connected: nothing to tell the node, but this client must still stop — the
        // caller (resetIdentity) drops its reference right after, and a client left in its
        // reconnect loop keeps dialing for the deleted identity forever (device log
        // 2026-10-13: an iPad reset while its node was unreachable kept retrying every ~11 s
        // as the old cell, alongside the fresh identity).
        guard let ws = webSocket, isConnected else {
            disconnect()
            return
        }
        var pkt = makePacket(type: "cell_deregister", payload: Data(),
                              from: "\(identity.cellId)@\(nodeId)", to: nodeId)
        try? signPacket(&pkt, seed: identity.signingPriv)
        Task {
            try? await wsSend(ws: ws, pkt: pkt)
            disconnect()
        }
    }

    private func handleTurnCreds(_ pkt: NevdPacket) {
        guard let d = try? decodePayload(pkt.payload),
              let url  = d["url"].string,
              let user = d["username"].string,
              let cred = d["credential"].string else { return }
        onTurnCredentials?(TurnInfo(url: url, username: user, credential: cred))
    }

    private func handleCellRemoved() {
        reconnect = false
        isConnected = false
        stopPathMonitor()
        setStatus("removed")
        webSocket?.cancel()
        webSocket = nil; activeAddr = ""
        onCellRemoved?()
    }

    // MARK: - Push Token

    /// Deliberately does NOT gate on `isConnected` — same lesson as sendJoinRequest's own
    /// comment: `handleNack` sets it false unconditionally on ANY nack, including
    /// invite_required, but the socket that nack arrived on is still live (only
    /// disconnect() ever nils `webSocket`). node.py's PUSH_REGISTER handler needs no
    /// admission check either — auth completes before the invite check, so even a
    /// not-yet-approved cell can register a token on the same connection. Gating on
    /// isConnected here silently meant a pending join-request applicant's push token
    /// NEVER reached the server while waiting: found 2026-09-18 tracing why an admin's
    /// "approve" (see node.py's approve_join_request, which sends an alert push only if
    /// get_push_token finds one on file) never actually woke the applicant's phone — the
    /// new member only showed up once they happened to reopen the app themselves and
    /// retryPendingJoinRequestIfNeeded's own reconnect incidentally re-registered it.
    func registerPushToken(_ token: String) {
        guard let ws = webSocket else {
            nlog("registerPushToken SKIP no websocket")
            return
        }
        var pkt = makePacket(type: "push_register",
                              payload: encodePayload(["token": token, "platform": "apns",
                                                      "bundle_id": "com.avk.Nevod"]),
                              from: "\(identity.cellId)@\(nodeId)", to: nodeId)
        try? signPacket(&pkt, seed: identity.signingPriv)
        Task { try? await wsSend(ws: ws, pkt: pkt) }
    }

    /// Separate slot from registerPushToken — a cell needs both a regular alert token
    /// (for chat push) and a VoIP token (for incoming-call push) registered at once.
    /// Same isConnected caveat as registerPushToken above applies here too.
    func registerVoipPushToken(_ token: String) {
        guard let ws = webSocket else {
            nlog("registerVoipPushToken SKIP no websocket")
            return
        }
        var pkt = makePacket(type: "push_register",
                              payload: encodePayload(["token": token, "platform": "voip",
                                                      "bundle_id": "com.avk.Nevod"]),
                              from: "\(identity.cellId)@\(nodeId)", to: nodeId)
        try? signPacket(&pkt, seed: identity.signingPriv)
        Task { try? await wsSend(ws: ws, pkt: pkt) }
    }

    // MARK: - Chat prefs

    /// Node-directed preference update (currently just push sound on/off for a chat) — same
    /// shape as registerPushToken above. The node resolves whose preference this is from the
    /// authenticated connection, not from the payload (see node.py's _handle_chat_prefs).
    /// Each preference is sent only when non-nil — the node applies only the keys present
    /// (a block-only update must not reset the sound preference, and vice versa). Omitted,
    /// not sent as nil: a msgpack nil would arrive as a present-but-None key.
    @discardableResult
    func sendChatPrefs(peerCellId: String, soundEnabled: Bool? = nil, blocked: Bool? = nil) -> Bool {
        guard let ws = webSocket, isConnected else { return false }
        var payload: [String: Any?] = ["peer_cell_id": peerCellId]
        if let soundEnabled { payload["sound_enabled"] = soundEnabled }
        if let blocked { payload["blocked"] = blocked }
        var pkt = makePacket(type: "chat_prefs",
                              payload: encodePayload(payload),
                              from: "\(identity.cellId)@\(nodeId)", to: nodeId)
        try? signPacket(&pkt, seed: identity.signingPriv)
        Task { try? await wsSend(ws: ws, pkt: pkt) }
        return true
    }

    // MARK: - Nack / Ack

    private func handleNack(_ pkt: NevdPacket) {
        guard let d = try? decodePayload(pkt.payload) else {
            nlog("handleNack decode FAILED")
            return
        }
        let reason = d["reason"].string ?? "invite_required"
        nlog("handleNack reason=\(reason)")
        nackCount += 1
        isConnected = false
        switch reason {
        case "name_taken":    setStatus("name taken"); onNameTaken?()
        case "invite_invalid": setStatus("invite invalid")
        default:
            // "delegated" is the safe fallback for an older node that doesn't send this
            // field yet — same as today's behavior, no "Request access" option offered.
            let inviteMode = d["invite_mode"].string ?? "delegated"
            nlog("handleNack invite_mode=\(inviteMode)")
            setStatus("invite required"); onInviteRequired?(reason, inviteMode)
        }
    }

    /// invite_mode="admin" registration channel — sent right after this same connection's
    /// CELL_REGISTER got NACK'd with invite_required. Deliberately does NOT gate on
    /// `isConnected`: handleNack() above just set it false, but `webSocket` itself is only
    /// ever nilled in disconnect() — the socket that the NACK just arrived on is still live,
    /// `isConnected` merely reflects "not a registered member" here, not "no connection."
    func sendJoinRequest(note: String) async throws {
        guard let ws = webSocket else {
            nlog("sendJoinRequest SKIP no websocket")
            throw NevdError.notConnected
        }
        // display_name rides along because it never survives the earlier CELL_REGISTER
        // NACK — without it the admin's panel/notification only ever showed a bare
        // cell_id, no way to tell who's actually asking (see node/node.py's
        // _handle_join_request).
        var pkt = makePacket(type: "join_request",
                              payload: encodePayload(["note": note, "display_name": displayName]),
                              from: "\(identity.cellId)@\(nodeId)", to: nodeId)
        try? signPacket(&pkt, seed: identity.signingPriv)
        try await wsSend(ws: ws, pkt: pkt)
        nlog("sendJoinRequest sent id=\(pkt.id.prefix(8))")
    }

    private func handleJoinRequestAck(_ pkt: NevdPacket) {
        guard let d = try? decodePayload(pkt.payload) else {
            nlog("handleJoinRequestAck decode FAILED")
            return
        }
        let ok = d["ok"].bool ?? false
        nlog("handleJoinRequestAck ok=\(ok) reason=\(d["reason"].string ?? "nil")")
        onJoinRequestAck?(ok, d["reason"].string)
    }

    private func handleJoinRequestResolved(_ pkt: NevdPacket) {
        guard let d = try? decodePayload(pkt.payload) else {
            nlog("handleJoinRequestResolved decode FAILED")
            return
        }
        let approved = d["approved"].bool ?? false
        nlog("handleJoinRequestResolved approved=\(approved)")
        onJoinRequestResolved?(approved)
    }

    private func sendAck(msgId: String, status: String, toAddr: String) {
        guard let ws = webSocket else {
            nlog("sendAck SKIP no websocket msgId=\(msgId.prefix(8)) status=\(status)")
            return
        }
        nlog("sendAck msgId=\(msgId.prefix(8)) status=\(status) toAddr=\(toAddr)")
        var ack = makePacket(type: "ack", payload: encodePayload(["message_id": msgId, "status": status]),
                              from: "\(identity.cellId)@\(nodeId)", to: toAddr)
        try? signPacket(&ack, seed: identity.signingPriv)
        Task { try? await wsSend(ws: ws, pkt: ack) }
    }

    /// Sent when the user actually views a chat containing this incoming message.
    /// toNodeId: the SENDER's node — defaults to our own only as a same-node fallback,
    /// the caller should pass the sender's actual node when known (cross-node chat).
    func sendReadReceipt(msgId: String, toCellId: String, toNodeId: String? = nil) {
        sendAck(msgId: msgId, status: "read", toAddr: "\(toCellId)@\(toNodeId ?? nodeId)")
    }

    private func handleAck(_ pkt: NevdPacket) {
        guard let d = try? decodePayload(pkt.payload),
              let msgId = d["message_id"].string,
              let status = d["status"].string else {
            nlog("NevdClient handleAck decode FAILED")
            return
        }
        nlog("NevdClient handleAck msgId=\(msgId.prefix(8)) status=\(status)")
        onAck?(msgId, status)
    }

    // MARK: - Reactions

    /// emoji: nil/empty clears the reaction (a repeat tap on the same emoji, client-side).
    func sendReaction(msgId: String, emoji: String?, toCellId: String, toNodeId: String? = nil) {
        guard let ws = webSocket else {
            nlog("sendReaction SKIP no websocket msgId=\(msgId.prefix(8))")
            return
        }
        let toAddr = "\(toCellId)@\(toNodeId ?? nodeId)"
        nlog("sendReaction msgId=\(msgId.prefix(8)) emoji=\(emoji ?? "(clear)") toAddr=\(toAddr)")
        var pkt = makePacket(type: "react", payload: encodePayload(["message_id": msgId, "emoji": emoji ?? ""]),
                              from: "\(identity.cellId)@\(nodeId)", to: toAddr)
        try? signPacket(&pkt, seed: identity.signingPriv)
        Task { try? await wsSend(ws: ws, pkt: pkt) }
    }

    private func handleReaction(_ pkt: NevdPacket) {
        guard let d = try? decodePayload(pkt.payload),
              let msgId = d["message_id"].string else {
            nlog("NevdClient handleReaction decode FAILED")
            return
        }
        let emoji = d["emoji"].string ?? ""
        nlog("NevdClient handleReaction msgId=\(msgId.prefix(8)) emoji=\(emoji.isEmpty ? "(clear)" : emoji)")
        onReaction?(pkt.from, msgId, emoji.isEmpty ? nil : emoji)
    }

    // MARK: - WS helpers

    /// Everything but file data (see send's fileData) — written at once; a waiting chunk
    /// goes after it.
    private func wsSend(ws: NWWebSocketTask, pkt: NevdPacket) async throws {
        Self.urgentWrites += 1
        defer { Self.urgentWrites -= 1; Self.wakeFileSenders() }
        try await ws.send(packPacket(pkt))
    }

    private func wsRecv(ws: NWWebSocketTask) async throws -> Data {
        try await ws.receive()
    }

    private func setStatus(_ text: String) {
        nlog("status -> \(text) addr=\(activeAddr.isEmpty ? (routes.first ?? "?") : activeAddr) cell=\(identity.cellId.prefix(8))")
        Task { @MainActor in self.status = text }
    }
}

enum NevdError: LocalizedError {
    case notConnected, invalidAddress, authFailed(String), invalidData, timeout
    var errorDescription: String? {
        switch self {
        case .notConnected: return "Not connected"
        case .invalidAddress: return "Invalid server address"
        case .authFailed(let m): return "Auth failed: \(m)"
        case .invalidData: return "Invalid data"
        case .timeout: return "Request timed out"
        }
    }
}
