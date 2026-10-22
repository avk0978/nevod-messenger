import Foundation

struct NevdPacket {
    var id:      String
    var type:    String
    var from:    String
    var to:      String
    var payload: Data
    var sig:     Data
    var ts:      Int64
    // Cleartext (not E2E-encrypted) caller display name — only ever set on
    // vcall_offer. See node/protocol.py's Packet.caller_name for why this can't
    // just be resolved node-side from the encrypted offer.
    var callerName: String = ""
}

func packPacket(_ pkt: NevdPacket) -> Data {
    msgpackEncode([
        "v": 1, "id": pkt.id, "type": pkt.type,
        "from": pkt.from, "to": pkt.to,
        "payload": pkt.payload, "sig": pkt.sig,
        "ts": Int(pkt.ts), "caller_name": pkt.callerName,
    ] as [String: Any?])
}

func unpackPacket(_ data: Data) throws -> NevdPacket {
    let v = try msgpackDecode(data)
    return NevdPacket(
        id:      v["id"].string    ?? "",
        type:    v["type"].string  ?? "",
        from:    v["from"].string  ?? "",
        to:      v["to"].string    ?? "",
        payload: v["payload"].data ?? Data(),
        sig:     v["sig"].data     ?? Data(),
        ts:      v["ts"].int64     ?? 0,
        callerName: v["caller_name"].string ?? ""
    )
}

func encodePayload(_ obj: [String: Any?]) -> Data { msgpackEncode(obj) }
func decodePayload(_ data: Data) throws -> MsgPackValue { try msgpackDecode(data) }

private func signBytes(_ pkt: NevdPacket) -> Data {
    var d = Data()
    d += pkt.id.data(using: .utf8)!
    d += pkt.type.data(using: .utf8)!
    d += pkt.from.data(using: .utf8)!
    d += pkt.to.data(using: .utf8)!
    d += pkt.payload
    d += String(pkt.ts).data(using: .utf8)!
    d += pkt.callerName.data(using: .utf8)!
    return d
}

func signPacket(_ pkt: inout NevdPacket, seed: Data) throws {
    pkt.sig = try ed25519Sign(data: signBytes(pkt), seed: seed)
}

func verifyPacket(_ pkt: NevdPacket, publicKey: Data) -> Bool {
    ed25519Verify(signature: pkt.sig, data: signBytes(pkt), publicKey: publicKey)
}

func makePacket(type: String, payload: Data, from: String, to: String, id: String? = nil,
                callerName: String = "") -> NevdPacket {
    NevdPacket(id: id ?? UUID().uuidString, type: type, from: from, to: to,
               payload: payload, sig: Data(), ts: Int64(Date().timeIntervalSince1970),
               callerName: callerName)
}
