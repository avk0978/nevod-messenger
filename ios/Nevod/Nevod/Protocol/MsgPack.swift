import Foundation

enum MsgPackError: Error {
    case unexpectedEnd
    case unknownFormat(UInt8)
    case typeMismatch
}

func msgpackEncode(_ value: Any?) -> Data {
    var out = Data(); _encode(value, into: &out); return out
}

private func _encode(_ value: Any?, into out: inout Data) {
    switch value {
    case nil: out.append(0xc0)
    case let b as Bool: out.append(b ? 0xc3 : 0xc2)
    case let i as Int: _encodeInt(Int64(i), into: &out)
    case let i as Int64: _encodeInt(i, into: &out)
    case let u as UInt64:
        if u <= 0x7f { out.append(UInt8(u)) }
        else if u <= 0xff { out.append(contentsOf: [0xcc, UInt8(u)]) }
        else if u <= 0xffff { out.append(0xcd); _w16(UInt16(u), &out) }
        else if u <= 0xffff_ffff { out.append(0xce); _w32(UInt32(u), &out) }
        else { out.append(0xcf); _w64(u, &out) }
    case let f as Double: out.append(0xcb); _w64(f.bitPattern, &out)
    case let s as String:
        let b = s.utf8; let n = b.count
        if n <= 31 { out.append(0xa0 | UInt8(n)) }
        else if n <= 0xff { out.append(contentsOf: [0xd9, UInt8(n)]) }
        else if n <= 0xffff { out.append(0xda); _w16(UInt16(n), &out) }
        else { out.append(0xdb); _w32(UInt32(n), &out) }
        out.append(contentsOf: b)
    case let d as Data:
        let n = d.count
        if n <= 0xff { out.append(contentsOf: [0xc4, UInt8(n)]) }
        else if n <= 0xffff { out.append(0xc5); _w16(UInt16(n), &out) }
        else { out.append(0xc6); _w32(UInt32(n), &out) }
        out.append(d)
    case let arr as [Any?]:
        let n = arr.count
        if n <= 15 { out.append(0x90 | UInt8(n)) }
        else if n <= 0xffff { out.append(0xdc); _w16(UInt16(n), &out) }
        else { out.append(0xdd); _w32(UInt32(n), &out) }
        for v in arr { _encode(v, into: &out) }
    case let dict as [String: Any?]:
        let n = dict.count
        if n <= 15 { out.append(0x80 | UInt8(n)) }
        else if n <= 0xffff { out.append(0xde); _w16(UInt16(n), &out) }
        else { out.append(0xdf); _w32(UInt32(n), &out) }
        for (k, v) in dict { _encode(k, into: &out); _encode(v, into: &out) }
    default: out.append(0xc0)
    }
}

private func _encodeInt(_ i: Int64, into out: inout Data) {
    if i >= 0 { _encode(UInt64(i), into: &out) }
    else if i >= -32 { out.append(UInt8(bitPattern: Int8(i))) }
    else if i >= -128 { out.append(contentsOf: [0xd0, UInt8(bitPattern: Int8(i))]) }
    else if i >= -32768 { out.append(0xd1); _w16(UInt16(bitPattern: Int16(i)), &out) }
    else if i >= -2_147_483_648 { out.append(0xd2); _w32(UInt32(bitPattern: Int32(i)), &out) }
    else { out.append(0xd3); _w64(UInt64(bitPattern: i), &out) }
}

private func _w16(_ v: UInt16, _ o: inout Data) { o.append(UInt8(v>>8)); o.append(UInt8(v&0xff)) }
private func _w32(_ v: UInt32, _ o: inout Data) { _w16(UInt16(v>>16), &o); _w16(UInt16(v&0xffff), &o) }
private func _w64(_ v: UInt64, _ o: inout Data) { _w32(UInt32(v>>32), &o); _w32(UInt32(v&0xffff_ffff), &o) }

struct MsgPackValue {
    let raw: Any?
    var string: String? { raw as? String }
    var data: Data? { raw as? Data }
    var bool: Bool? { raw as? Bool }
    var int64: Int64? {
        switch raw {
        case let i as Int64: return i
        case let u as UInt64: return Int64(exactly: u)
        case let i as Int: return Int64(i)
        default: return nil
        }
    }
    var array: [MsgPackValue]? { (raw as? [Any?])?.map { MsgPackValue(raw: $0) } }
    var dict: [String: MsgPackValue]? {
        (raw as? [String: Any?])?.mapValues { MsgPackValue(raw: $0) }
    }
    subscript(key: String) -> MsgPackValue {
        dict?[key] ?? MsgPackValue(raw: nil)
    }
}

func msgpackDecode(_ data: Data) throws -> MsgPackValue {
    var idx = data.startIndex
    return MsgPackValue(raw: try _decode(data, idx: &idx))
}

private func _decode(_ d: Data, idx: inout Data.Index) throws -> Any? {
    guard idx < d.endIndex else { throw MsgPackError.unexpectedEnd }
    let byte = d[idx]; d.formIndex(after: &idx)
    switch byte {
    case 0xc0: return nil
    case 0xc2: return false
    case 0xc3: return true
    case 0x00...0x7f: return UInt64(byte)
    case 0xe0...0xff: return Int64(Int8(bitPattern: byte))
    case 0xcc: return UInt64(try _rb(d, &idx))
    case 0xcd: return UInt64(try _r16(d, &idx))
    case 0xce: return UInt64(try _r32(d, &idx))
    case 0xcf: return try _r64(d, &idx)
    case 0xd0: return Int64(Int8(bitPattern: try _rb(d, &idx)))
    case 0xd1: return Int64(Int16(bitPattern: try _r16(d, &idx)))
    case 0xd2: return Int64(Int32(bitPattern: try _r32(d, &idx)))
    case 0xd3: return Int64(bitPattern: try _r64(d, &idx))
    case 0xcb: return Double(bitPattern: try _r64(d, &idx))
    case 0xa0...0xbf: return try _rstr(d, &idx, Int(byte & 0x1f))
    case 0xd9: return try _rstr(d, &idx, Int(try _rb(d, &idx)))
    case 0xda: return try _rstr(d, &idx, Int(try _r16(d, &idx)))
    case 0xdb: return try _rstr(d, &idx, Int(try _r32(d, &idx)))
    case 0xc4: return try _rdata(d, &idx, Int(try _rb(d, &idx)))
    case 0xc5: return try _rdata(d, &idx, Int(try _r16(d, &idx)))
    case 0xc6: return try _rdata(d, &idx, Int(try _r32(d, &idx)))
    case 0x90...0x9f: return try _rarr(d, &idx, Int(byte & 0x0f))
    case 0xdc: return try _rarr(d, &idx, Int(try _r16(d, &idx)))
    case 0xdd: return try _rarr(d, &idx, Int(try _r32(d, &idx)))
    case 0x80...0x8f: return try _rmap(d, &idx, Int(byte & 0x0f))
    case 0xde: return try _rmap(d, &idx, Int(try _r16(d, &idx)))
    case 0xdf: return try _rmap(d, &idx, Int(try _r32(d, &idx)))
    default: throw MsgPackError.unknownFormat(byte)
    }
}

private func _rb(_ d: Data, _ i: inout Data.Index) throws -> UInt8 {
    guard i < d.endIndex else { throw MsgPackError.unexpectedEnd }
    let b = d[i]; d.formIndex(after: &i); return b
}
private func _r16(_ d: Data, _ i: inout Data.Index) throws -> UInt16 {
    (UInt16(try _rb(d, &i)) << 8) | UInt16(try _rb(d, &i))
}
private func _r32(_ d: Data, _ i: inout Data.Index) throws -> UInt32 {
    (UInt32(try _r16(d, &i)) << 16) | UInt32(try _r16(d, &i))
}
private func _r64(_ d: Data, _ i: inout Data.Index) throws -> UInt64 {
    (UInt64(try _r32(d, &i)) << 32) | UInt64(try _r32(d, &i))
}
private func _rdata(_ d: Data, _ i: inout Data.Index, _ n: Int) throws -> Data {
    let end = d.index(i, offsetBy: n)
    guard end <= d.endIndex else { throw MsgPackError.unexpectedEnd }
    let s = d[i..<end]; i = end; return Data(s)
}
private func _rstr(_ d: Data, _ i: inout Data.Index, _ n: Int) throws -> String {
    let bytes = try _rdata(d, &i, n)
    guard let s = String(data: bytes, encoding: .utf8) else { throw MsgPackError.typeMismatch }
    return s
}
private func _rarr(_ d: Data, _ i: inout Data.Index, _ n: Int) throws -> [Any?] {
    var arr = [Any?]()
    for _ in 0..<n { arr.append(try _decode(d, idx: &i)) }
    return arr
}
private func _rmap(_ d: Data, _ i: inout Data.Index, _ n: Int) throws -> [String: Any?] {
    var map = [String: Any?]()
    for _ in 0..<n {
        guard let k = try _decode(d, idx: &i) as? String else { throw MsgPackError.typeMismatch }
        map[k] = try _decode(d, idx: &i)
    }
    return map
}
