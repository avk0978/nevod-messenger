import Foundation

/// One published cell/moon entry on a node's "planet detail" screen — see
/// node/storage.py's PublishedCellEntry and node.py's _handle_node_cells_request.
struct PublishedCell: Identifiable {
    var id: String { cellId }
    let cellId: String
    let name: String
    let description: String
    let kind: String  // "bot" | "page"
    let encPubkey: Data?    // present for kind == "bot"
    let landingMd: String?  // present for kind == "page"
    /// BYOK AI bot: providers it accepts the user's own key for ("anthropic", "openai",
    /// "gemini" — node/ai_providers.py). Empty for an ordinary bot.
    var aiProviders: [String] = []
}

/// One-off, unregistered peek at another node's published cell list — used when
/// tapping a planet on "Explore Network" that ISN'T your own home node (your home
/// node already has a live NevdClient connection — reuse that instead, see
/// NevdClient.getNodeCells()). Connects, authenticates (same Schnorr handshake as
/// any node/cell connection), asks node_cells_request, disconnects — deliberately
/// never sends cell_register, so browsing an open node's cell list doesn't leave a
/// registration behind on a node you don't otherwise use.
enum NodeCellsBrowser {
    static func fetch(nodeAddr: String, expectedFingerprint: String?,
                      identity: NevdIdentity) async throws -> [PublishedCell] {
        nlog("NodeCellsBrowser fetch addr=\(nodeAddr) pinned=\(expectedFingerprint?.prefix(16).description ?? "nil")")
        guard let url = URL(string: "wss://\(nodeAddr)"), let host = url.host else {
            nlog("NodeCellsBrowser FAILED invalid address \(nodeAddr)")
            throw NevdError.invalidAddress
        }
        let port = UInt16(url.port ?? 443)
        let path = url.path.isEmpty ? "/" : url.path
        let ws = NWWebSocketTask(host: host, port: port, pinnedFingerprint: expectedFingerprint)
        let watchdog = Task {
            try? await Task.sleep(nanoseconds: 8_000_000_000)
            nlog("NodeCellsBrowser addr=\(nodeAddr) TIMEOUT after 8s, cancelling")
            ws.cancel()
        }
        defer { watchdog.cancel(); ws.cancel() }

        do {
            try await ws.connect(host: host, port: port, path: path)
            nlog("NodeCellsBrowser addr=\(nodeAddr) transport connected")

            let cid = identity.cellId
            let commit = try schnorrCommit()
            let commitPkt = makePacket(type: "auth_commit", payload: encodePayload([
                "R": commit.R, "signing_pub": identity.signingPub, "enc_pub": identity.encPub,
            ]), from: cid, to: "")
            try await ws.send(packPacket(commitPkt))
            nlog("NodeCellsBrowser addr=\(nodeAddr) sent auth_commit")

            let theirCommit = try unpackPacket(try await ws.receive())
            nlog("NodeCellsBrowser addr=\(nodeAddr) received type=\(theirCommit.type)")
            guard theirCommit.type == "auth_commit" else {
                throw NevdError.authFailed("expected auth_commit, got \(theirCommit.type)")
            }
            let d = try decodePayload(theirCommit.payload)
            let R_peer = d["R"].data ?? Data()
            let X_peer = d["signing_pub"].data ?? Data()

            let c_self = schnorrChallenge(R_prover: commit.R, X_prover: identity.signingPub,
                                           R_verifier: R_peer, X_verifier: X_peer)
            let s_self = schnorrProve(signingPriv: identity.signingPriv, rBytes: commit.rBytes, c: c_self)
            var respPkt = makePacket(type: "auth_response", payload: encodePayload(["s": s_self]),
                                      from: cid, to: Hex.encode(X_peer))
            try signPacket(&respPkt, seed: identity.signingPriv)
            try await ws.send(packPacket(respPkt))
            nlog("NodeCellsBrowser addr=\(nodeAddr) sent auth_response")

            let theirResp = try unpackPacket(try await ws.receive())
            nlog("NodeCellsBrowser addr=\(nodeAddr) received type=\(theirResp.type)")
            guard theirResp.type == "auth_response" else {
                throw NevdError.authFailed("expected auth_response, got \(theirResp.type)")
            }

            let nodeId = Hex.encode(X_peer)
            var req = makePacket(type: "node_cells_request", payload: Data(),
                                 from: "\(cid)@\(nodeId)", to: nodeId)
            try signPacket(&req, seed: identity.signingPriv)
            try await ws.send(packPacket(req))
            nlog("NodeCellsBrowser addr=\(nodeAddr) auth OK, sent node_cells_request")

            let resp = try unpackPacket(try await ws.receive())
            nlog("NodeCellsBrowser addr=\(nodeAddr) received type=\(resp.type)")
            guard resp.type == "node_cells_response" else { return [] }
            let cells = parseCellsPayload(resp.payload)
            nlog("NodeCellsBrowser addr=\(nodeAddr) parsed \(cells.count) cell(s)")
            return cells
        } catch {
            nlog("NodeCellsBrowser addr=\(nodeAddr) FAILED error=\(error) "
                 + "detail=\(fullErrorDetail(error))")
            throw error
        }
    }

    /// Walks NSUnderlyingError chains — mirrors NevdClient's own fullErrorDetail, since a
    /// TLS/Network.framework failure's real cause is usually nested one or two levels down.
    private static func fullErrorDetail(_ error: Error) -> String {
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

    static func parseCellsPayload(_ payload: Data) -> [PublishedCell] {
        guard let data = try? decodePayload(payload), let arr = data["cells"].array else { return [] }
        return arr.compactMap { c -> PublishedCell? in
            guard let cellId = c["cell_id"].string, let name = c["name"].string,
                  let kind = c["kind"].string else { return nil }
            return PublishedCell(
                cellId: cellId, name: name, description: c["description"].string ?? "",
                kind: kind, encPubkey: c["enc_pubkey"].data, landingMd: c["landing_md"].string,
                aiProviders: (c["ai_providers"].array ?? []).compactMap(\.string)
                    .filter { AIProvider(rawValue: $0) != nil }
            )
        }
    }
}
