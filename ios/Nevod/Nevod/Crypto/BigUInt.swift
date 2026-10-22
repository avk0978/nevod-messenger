import Foundation

struct BigUInt: Equatable {
    var words: [UInt64]

    init(_ v: UInt64 = 0) { words = [v] }

    init(littleEndianBytes: Data) {
        words = []
        var i = littleEndianBytes.startIndex
        while i < littleEndianBytes.endIndex {
            var word: UInt64 = 0
            for shift in 0..<8 {
                if i < littleEndianBytes.endIndex {
                    word |= UInt64(littleEndianBytes[i]) << (shift * 8)
                    i = littleEndianBytes.index(after: i)
                }
            }
            words.append(word)
        }
        if words.isEmpty { words = [0] }
        trim()
    }

    init?(hexString: String) {
        guard let d = Hex.decode(hexString) else { return nil }
        self.init(bigEndianBytes: d)
    }

    init(bigEndianBytes: Data) {
        self.init(littleEndianBytes: Data(bigEndianBytes.reversed()))
    }

    mutating func trim() {
        while words.count > 1 && words.last == 0 { words.removeLast() }
    }

    var isZero: Bool { words.allSatisfy { $0 == 0 } }

    var bitWidth: Int {
        guard let top = words.last, top != 0 else {
            return words.count > 1 ? (words.count - 1) * 64 : 0
        }
        return (words.count - 1) * 64 + (64 - top.leadingZeroBitCount)
    }

    func toLittleEndianBytes(count: Int) -> Data {
        var out = Data(repeating: 0, count: count)
        var byteIdx = 0
        for word in words {
            for shift in 0..<8 {
                if byteIdx < count {
                    out[byteIdx] = UInt8((word >> (shift * 8)) & 0xff)
                    byteIdx += 1
                }
            }
        }
        return out
    }

    static func < (lhs: BigUInt, rhs: BigUInt) -> Bool {
        let n = max(lhs.words.count, rhs.words.count)
        for i in stride(from: n - 1, through: 0, by: -1) {
            let lw = i < lhs.words.count ? lhs.words[i] : 0
            let rw = i < rhs.words.count ? rhs.words[i] : 0
            if lw < rw { return true }
            if lw > rw { return false }
        }
        return false
    }

    static func + (lhs: BigUInt, rhs: BigUInt) -> BigUInt {
        let n = max(lhs.words.count, rhs.words.count)
        var result = BigUInt(); result.words = []
        var carry: UInt64 = 0
        for i in 0..<n {
            let lw = i < lhs.words.count ? lhs.words[i] : 0
            let rw = i < rhs.words.count ? rhs.words[i] : 0
            let (s1, o1) = lw.addingReportingOverflow(rw)
            let (s2, o2) = s1.addingReportingOverflow(carry)
            result.words.append(s2)
            carry = (o1 ? 1 : 0) + (o2 ? 1 : 0)
        }
        if carry > 0 { result.words.append(carry) }
        return result
    }

    static func - (lhs: BigUInt, rhs: BigUInt) -> BigUInt {
        var result = BigUInt(); result.words = Array(repeating: 0, count: lhs.words.count)
        var borrow: UInt64 = 0
        for i in 0..<lhs.words.count {
            let lw = lhs.words[i]
            let rw = i < rhs.words.count ? rhs.words[i] : 0
            let (d1, o1) = lw.subtractingReportingOverflow(rw)
            let (d2, o2) = d1.subtractingReportingOverflow(borrow)
            result.words[i] = d2
            borrow = (o1 ? 1 : 0) + (o2 ? 1 : 0)
        }
        result.trim(); return result
    }

    static func * (lhs: BigUInt, rhs: BigUInt) -> BigUInt {
        var result = BigUInt()
        result.words = Array(repeating: 0, count: lhs.words.count + rhs.words.count)
        for i in 0..<lhs.words.count {
            var carry: UInt64 = 0
            for j in 0..<rhs.words.count {
                let (hi, lo) = lhs.words[i].multipliedFullWidth(by: rhs.words[j])
                let (s1, o1) = result.words[i+j].addingReportingOverflow(lo)
                let (s2, o2) = s1.addingReportingOverflow(carry)
                result.words[i+j] = s2
                carry = hi + (o1 ? 1 : 0) + (o2 ? 1 : 0)
            }
            result.words[i + rhs.words.count] = carry
        }
        result.trim(); return result
    }

    func shiftedLeft1() -> BigUInt {
        var result = self; var carry: UInt64 = 0
        for i in 0..<result.words.count {
            let newCarry = result.words[i] >> 63
            result.words[i] = (result.words[i] << 1) | carry
            carry = newCarry
        }
        if carry != 0 { result.words.append(carry) }
        return result
    }

    func shiftedRight1() -> BigUInt {
        var result = self; var carry: UInt64 = 0
        for i in stride(from: result.words.count - 1, through: 0, by: -1) {
            let newCarry = result.words[i] & 1
            result.words[i] = (result.words[i] >> 1) | (carry << 63)
            carry = newCarry
        }
        result.trim(); return result
    }

    // Binary long division — O(bitWidth) iterations, correct for all sizes
    static func % (lhs: BigUInt, rhs: BigUInt) -> BigUInt {
        var remainder = lhs; remainder.trim()
        var divisor = rhs; divisor.trim()
        if remainder < divisor { return remainder }
        if divisor.isZero { fatalError("division by zero") }
        let shift = remainder.bitWidth - divisor.bitWidth
        var d = divisor
        for _ in 0..<shift { d = d.shiftedLeft1() }
        for _ in 0...shift {
            if !(remainder < d) { remainder = remainder - d }
            d = d.shiftedRight1()
        }
        remainder.trim(); return remainder
    }
}
