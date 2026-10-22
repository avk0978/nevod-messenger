import CryptoKit
import Foundation
import Network
import Security

/// NWConnection's stateUpdateHandler fires on `queue`, a non-isolated context — a plain
/// captured `var` there trips Swift's strict concurrency checker ("mutation of captured
/// var in concurrently-executing code"). `nonisolated(unsafe)` would be the natural fix
/// but needs Swift 5.10 (Xcode 15.3+); this lock-backed box is the Xcode-15.2-compatible
/// equivalent, same pattern as CallManager.swift's AtomicBool.
private final class AtomicBool: @unchecked Sendable {
    private let lock = NSLock()
    private var value: Bool
    init(_ initial: Bool) { value = initial }
    var current: Bool {
        get { lock.lock(); defer { lock.unlock() }; return value }
        set { lock.lock(); defer { lock.unlock() }; value = newValue }
    }
}

/// Minimal WebSocket client built directly on Network.framework, used instead of
/// URLSessionWebSocketTask. Why: URLSessionWebSocketTask's URLSessionDelegate-based
/// server-trust override (the standard, documented pinning mechanism for HTTPS) has
/// been confirmed via device logs to be silently ignored for this task type — the
/// delegate is called, answers `.useCredential` with a matching fingerprint, and the
/// connection still fails with NSURLErrorDomain -1200. This is a known platform
/// limitation, not a logic bug on our side. NWConnection's TLS verify block IS
/// actually honored for arbitrary TCP+TLS traffic (it's not HTTPS-specific), so the
/// fix is to stop routing through URLSessionWebSocketTask entirely and speak the
/// WebSocket handshake + framing (RFC 6455) ourselves over a raw NWConnection.
final class NWWebSocketTask: @unchecked Sendable {
    enum WSError: LocalizedError {
        case connectionFailed(String)
        case handshakeFailed(String)
        case closed
        var errorDescription: String? {
            switch self {
            case .connectionFailed(let m): return "Connection failed: \(m)"
            case .handshakeFailed(let m):  return "WebSocket handshake failed: \(m)"
            case .closed:                  return "Connection closed"
            }
        }
    }

    private let connection: NWConnection
    // All mutable frame-parsing state is only ever touched from callbacks NWConnection
    // guarantees run on `queue` (state updates, receive completions) — no extra locking
    // needed as long as nothing outside this file touches it directly.
    private let queue = DispatchQueue(label: "nevod.ws.transport")
    private var frameBuffer: [UInt8] = []
    private var fragmentBuffer = Data()
    private var fragmentOpcode: UInt8? = nil
    private let messagesContinuation: AsyncStream<Data>.Continuation
    private var messageIterator: AsyncStream<Data>.AsyncIterator
    private var closedError: Error? = nil
    // For the drop diagnostics below (device logs 2026-10-21: the connection kept dropping
    // with the app on screen and nothing in the log said why). Touched only on `queue`.
    private var lastBytesAt = Date()
    private var wasReady = false
    private var secsSinceLastBytes: String { String(format: "%.1f", Date().timeIntervalSince(lastBytesAt)) }

    init(host: String, port: UInt16, pinnedFingerprint: String?) {
        let tlsOptions = NWProtocolTLS.Options()
        // No pin (nil/empty) => leave the verify block unset => Network.framework does
        // its normal default system CA trust evaluation, unchanged from before (the
        // prod path: nginx fronts the node with a real Let's Encrypt cert).
        if let pinned = pinnedFingerprint, !pinned.isEmpty {
            let verifyQueue = DispatchQueue(label: "nevod.ws.tls.verify")
            sec_protocol_options_set_verify_block(tlsOptions.securityProtocolOptions, { _, trustRef, complete in
                let trust = sec_trust_copy_ref(trustRef).takeRetainedValue()
                guard let chain = SecTrustCopyCertificateChain(trust) as? [SecCertificate],
                      let cert = chain.first else {
                    complete(false)
                    return
                }
                let certData = SecCertificateCopyData(cert) as Data
                let hex = SHA256.hash(data: certData).map { String(format: "%02x", $0) }.joined()
                let match = hex.caseInsensitiveCompare(pinned) == .orderedSame
                nlog("NWWebSocketTask TLS verify pinned=\(pinned) serverCert=\(hex) match=\(match)")
                complete(match)
            }, verifyQueue)
        }
        // TCP keepalive — Apple's own documented Network.framework mechanism for detecting a
        // connection that's gone silently dead (network hiccup, NAT/carrier timeout, no
        // clean FIN/RST) rather than a real, explicit failure. Without this, NWConnection has
        // no way to notice the far end is gone until *something* is actually sent and fails
        // (or the OS's own default TCP retransmission timeout expires, which can be minutes)
        // — confirmed via device logs 2026-08-02/03: isConnected stayed true and
        // sendSignal/sendCallOffer reported success on a connection that was already dead,
        // silently dropping a second call placed shortly after the first one ended, and
        // separately dropping a mid-call hangup signal. Idle/interval/count below detect a
        // dead peer within ~19s of the connection actually going silent, which then flows
        // through the existing .failed handling in stateUpdateHandler below exactly like any
        // other connection failure — no separate app-level ping protocol needed.
        let tcpOptions = NWProtocolTCP.Options()
        tcpOptions.enableKeepalive = true
        tcpOptions.keepaliveIdle = 10
        tcpOptions.keepaliveInterval = 3
        tcpOptions.keepaliveCount = 3
        let params = NWParameters(tls: tlsOptions, tcp: tcpOptions)
        let endpoint = NWEndpoint.hostPort(host: NWEndpoint.Host(host),
                                            port: NWEndpoint.Port(rawValue: port) ?? 443)
        connection = NWConnection(to: endpoint, using: params)

        var streamContinuation: AsyncStream<Data>.Continuation!
        let stream = AsyncStream<Data> { c in streamContinuation = c }
        messagesContinuation = streamContinuation
        messageIterator = stream.makeAsyncIterator()
    }

    /// Establishes the TCP+TLS connection, then performs the WebSocket HTTP Upgrade
    /// handshake. Throws if either step fails. `host` is used for the Host header and
    /// TLS SNI is already handled by NWConnection based on the endpoint given at init.
    func connect(host: String, port: UInt16, path: String) async throws {
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Void, Error>) in
            let resumed = AtomicBool(false)
            connection.stateUpdateHandler = { [weak self] state in
                guard let self else { return }
                switch state {
                case .ready:
                    self.wasReady = true
                    if !resumed.current { resumed.current = true; cont.resume() }
                case .waiting(let err):
                    nlog("ws state waiting err=\(err) lastBytes=\(self.secsSinceLastBytes)s ago")
                case .failed(let err):
                    if self.wasReady { nlog("ws state FAILED err=\(err) lastBytes=\(self.secsSinceLastBytes)s ago") }
                    if !resumed.current { resumed.current = true; cont.resume(throwing: WSError.connectionFailed(String(describing: err))) }
                    self.closedError = WSError.connectionFailed(String(describing: err))
                    self.messagesContinuation.finish()
                case .cancelled:
                    if !resumed.current { resumed.current = true; cont.resume(throwing: WSError.closed) }
                    self.closedError = WSError.closed
                    self.messagesContinuation.finish()
                default: break
                }
            }
            connection.viabilityUpdateHandler = { [weak self] viable in
                guard let self, self.wasReady else { return }
                nlog("ws viable=\(viable) lastBytes=\(self.secsSinceLastBytes)s ago path=\(self.connection.currentPath?.availableInterfaces.map { "\($0.type)" } ?? [])")
            }
            connection.betterPathUpdateHandler = { better in
                if better { nlog("ws better path available") }
            }
            connection.start(queue: queue)
        }
        let hostHeader = (port == 443) ? host : "\(host):\(port)"
        try await performHTTPUpgrade(hostHeader: hostHeader, path: path)
        startFrameReceiveLoop()
    }

    func cancel() {
        connection.cancel()
    }

    func send(_ data: Data) async throws {
        let frame = encodeFrame(opcode: 0x2, payload: data)  // binary
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Void, Error>) in
            connection.send(content: frame, completion: .contentProcessed { error in
                if let error { cont.resume(throwing: WSError.connectionFailed(String(describing: error))) }
                else { cont.resume() }
            })
        }
    }

    func receive() async throws -> Data {
        if let err = closedError { throw err }
        guard let data = await messageIterator.next() else {
            throw closedError ?? WSError.closed
        }
        return data
    }

    // MARK: - HTTP Upgrade handshake

    private func performHTTPUpgrade(hostHeader: String, path: String) async throws {
        var keyBytes = [UInt8](repeating: 0, count: 16)
        for i in 0..<16 { keyBytes[i] = UInt8.random(in: 0...255) }
        let wsKey = Data(keyBytes).base64EncodedString()

        let request = "GET \(path) HTTP/1.1\r\n" +
                      "Host: \(hostHeader)\r\n" +
                      "Upgrade: websocket\r\n" +
                      "Connection: Upgrade\r\n" +
                      "Sec-WebSocket-Key: \(wsKey)\r\n" +
                      "Sec-WebSocket-Version: 13\r\n" +
                      "\r\n"
        guard let requestData = request.data(using: .utf8) else {
            throw WSError.handshakeFailed("could not encode HTTP request")
        }
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Void, Error>) in
            connection.send(content: requestData, completion: .contentProcessed { error in
                if let error { cont.resume(throwing: WSError.connectionFailed(String(describing: error))) }
                else { cont.resume() }
            })
        }

        var headerBytes: [UInt8] = []
        while true {
            let chunk = try await receiveRaw(minLength: 1, maxLength: 4096)
            headerBytes.append(contentsOf: chunk)
            if let end = findSubsequence(headerBytes, [0x0D, 0x0A, 0x0D, 0x0A]) {
                let headerData = Data(headerBytes[0..<end])
                try validateUpgradeResponse(headerData, expectedKey: wsKey)
                // Any bytes after the header terminator already belong to the WS frame
                // stream (arrived in the same TCP segment as the HTTP response) — seed
                // the frame buffer with them instead of discarding.
                frameBuffer = Array(headerBytes[(end + 4)...])
                return
            }
            if headerBytes.count > 16384 {
                throw WSError.handshakeFailed("response headers too large")
            }
        }
    }

    private func receiveRaw(minLength: Int, maxLength: Int) async throws -> [UInt8] {
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<[UInt8], Error>) in
            connection.receive(minimumIncompleteLength: minLength, maximumLength: maxLength) { data, _, isComplete, error in
                if let error {
                    cont.resume(throwing: WSError.connectionFailed(String(describing: error)))
                } else if let data, !data.isEmpty {
                    cont.resume(returning: [UInt8](data))
                } else if isComplete {
                    cont.resume(throwing: WSError.closed)
                } else {
                    cont.resume(returning: [])
                }
            }
        }
    }

    private func findSubsequence(_ haystack: [UInt8], _ needle: [UInt8]) -> Int? {
        guard haystack.count >= needle.count else { return nil }
        for i in 0...(haystack.count - needle.count) {
            if Array(haystack[i..<i + needle.count]) == needle { return i }
        }
        return nil
    }

    private func validateUpgradeResponse(_ headerData: Data, expectedKey: String) throws {
        guard let text = String(data: headerData, encoding: .utf8) else {
            throw WSError.handshakeFailed("non-UTF8 response headers")
        }
        let lines = text.components(separatedBy: "\r\n")
        guard let statusLine = lines.first, statusLine.contains(" 101 ") else {
            throw WSError.handshakeFailed("unexpected status line: \(lines.first ?? "")")
        }
        var acceptHeader: String? = nil
        for line in lines.dropFirst() {
            let parts = line.split(separator: ":", maxSplits: 1)
            guard parts.count == 2 else { continue }
            if parts[0].trimmingCharacters(in: .whitespaces).caseInsensitiveCompare("Sec-WebSocket-Accept") == .orderedSame {
                acceptHeader = parts[1].trimmingCharacters(in: .whitespaces)
            }
        }
        guard let accept = acceptHeader else {
            throw WSError.handshakeFailed("missing Sec-WebSocket-Accept header")
        }
        let magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        let expected = Data(Insecure.SHA1.hash(data: Data((expectedKey + magic).utf8))).base64EncodedString()
        guard accept == expected else {
            throw WSError.handshakeFailed("Sec-WebSocket-Accept mismatch")
        }
    }

    // MARK: - Frame receive loop (post-handshake)

    private func startFrameReceiveLoop() {
        connection.receive(minimumIncompleteLength: 1, maximumLength: 65536) { [weak self] data, _, isComplete, error in
            guard let self else { return }
            if let data, !data.isEmpty {
                self.lastBytesAt = Date()
                self.handleIncomingBytes(data)
            }
            if let error {
                nlog("ws receive ERROR err=\(error) lastBytes=\(self.secsSinceLastBytes)s ago")
                self.closedError = WSError.connectionFailed(String(describing: error))
                self.messagesContinuation.finish()
                return
            }
            if isComplete {
                nlog("ws receive EOF — the other end closed TCP without a close frame")
                self.closedError = WSError.closed
                self.messagesContinuation.finish()
                return
            }
            self.startFrameReceiveLoop()
        }
    }

    private func handleIncomingBytes(_ data: Data) {
        frameBuffer.append(contentsOf: data)
        while let (frame, consumed) = tryParseFrame(frameBuffer) {
            frameBuffer.removeFirst(consumed)
            processFrame(frame)
        }
    }

    private struct RawFrame { let fin: Bool; let opcode: UInt8; let payload: Data }

    /// RFC 6455 §5.2 frame parsing. Returns nil if `buf` doesn't yet contain a
    /// complete frame — caller re-invokes once more bytes have arrived.
    private func tryParseFrame(_ buf: [UInt8]) -> (RawFrame, Int)? {
        guard buf.count >= 2 else { return nil }
        let byte0 = buf[0], byte1 = buf[1]
        let fin = (byte0 & 0x80) != 0
        let opcode = byte0 & 0x0F
        let masked = (byte1 & 0x80) != 0
        var len = UInt64(byte1 & 0x7F)
        var offset = 2
        if len == 126 {
            guard buf.count >= offset + 2 else { return nil }
            len = UInt64(buf[offset]) << 8 | UInt64(buf[offset + 1])
            offset += 2
        } else if len == 127 {
            guard buf.count >= offset + 8 else { return nil }
            var v: UInt64 = 0
            for i in 0..<8 { v = (v << 8) | UInt64(buf[offset + i]) }
            len = v
            offset += 8
        }
        var maskKey: [UInt8] = [0, 0, 0, 0]
        if masked {
            guard buf.count >= offset + 4 else { return nil }
            maskKey = [buf[offset], buf[offset + 1], buf[offset + 2], buf[offset + 3]]
            offset += 4
        }
        guard len <= UInt64(Int.max), buf.count - offset >= Int(len) else { return nil }
        var payloadBytes = Array(buf[offset..<offset + Int(len)])
        if masked {
            for i in 0..<payloadBytes.count { payloadBytes[i] ^= maskKey[i % 4] }
        }
        let consumed = offset + Int(len)
        return (RawFrame(fin: fin, opcode: opcode, payload: Data(payloadBytes)), consumed)
    }

    private func processFrame(_ frame: RawFrame) {
        switch frame.opcode {
        case 0x0: // continuation
            fragmentBuffer.append(frame.payload)
            if frame.fin {
                messagesContinuation.yield(fragmentBuffer)
                fragmentBuffer.removeAll()
                fragmentOpcode = nil
            }
        case 0x1, 0x2: // text, binary
            if frame.fin {
                messagesContinuation.yield(frame.payload)
            } else {
                fragmentOpcode = frame.opcode
                fragmentBuffer = frame.payload
            }
        case 0x8: // close
            let p = [UInt8](frame.payload)
            let code = p.count >= 2 ? Int(p[0]) << 8 | Int(p[1]) : 0
            let reason = p.count > 2 ? String(decoding: p[2...], as: UTF8.self) : ""
            nlog("ws close frame from server code=\(code) reason=\(reason)")
            closedError = WSError.closed
            messagesContinuation.finish()
        case 0x9: // ping — must reply pong with the same payload to avoid the server
                  // (Python `websockets`, ping_interval=20s by default) closing us as dead
            let pong = encodeFrame(opcode: 0xA, payload: frame.payload)
            connection.send(content: pong, completion: .contentProcessed { _ in })
        case 0xA: // pong — nothing to do
            break
        default:
            break
        }
    }

    /// RFC 6455 §5.2 frame encoding — client-to-server frames MUST be masked.
    private func encodeFrame(opcode: UInt8, payload: Data) -> Data {
        var frame = Data()
        frame.append(0x80 | opcode) // FIN=1
        let len = payload.count
        let maskKey = (0..<4).map { _ in UInt8.random(in: 0...255) }
        if len <= 125 {
            frame.append(0x80 | UInt8(len))
        } else if len <= 65535 {
            frame.append(0x80 | 126)
            frame.append(UInt8((len >> 8) & 0xFF))
            frame.append(UInt8(len & 0xFF))
        } else {
            frame.append(0x80 | 127)
            for shift in stride(from: 56, through: 0, by: -8) {
                frame.append(UInt8((UInt64(len) >> shift) & 0xFF))
            }
        }
        frame.append(contentsOf: maskKey)
        var maskedPayload = [UInt8](payload)
        for i in 0..<maskedPayload.count { maskedPayload[i] ^= maskKey[i % 4] }
        frame.append(contentsOf: maskedPayload)
        return frame
    }
}
