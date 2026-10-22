import Foundation
import CryptoKit

// MARK: - Hex

enum Hex {
    static func encode(_ data: Data) -> String {
        data.map { String(format: "%02x", $0) }.joined()
    }
    static func decode(_ hex: String) -> Data? {
        guard hex.count % 2 == 0 else { return nil }
        var data = Data(capacity: hex.count / 2)
        var i = hex.startIndex
        while i < hex.endIndex {
            let j = hex.index(i, offsetBy: 2)
            guard let byte = UInt8(hex[i..<j], radix: 16) else { return nil }
            data.append(byte); i = j
        }
        return data
    }
}

// MARK: - Identity

struct NevdIdentity: Codable {
    let signingPriv: Data
    let signingPub:  Data
    let encPriv:     Data
    let encPub:      Data
    var cellId: String { Hex.encode(signingPub) }
}

func generateIdentity() throws -> NevdIdentity {
    let signingKey = Curve25519.Signing.PrivateKey()
    let encKey     = Curve25519.KeyAgreement.PrivateKey()
    return NevdIdentity(
        signingPriv: signingKey.rawRepresentation,
        signingPub:  signingKey.publicKey.rawRepresentation,
        encPriv:     encKey.rawRepresentation,
        encPub:      encKey.publicKey.rawRepresentation
    )
}

// MARK: - Schnorr ZKP

private let L = BigUInt(hexString: "1000000000000000000000000000000014def9dea2f79cd65812631a5cf5d3ed")!
private let DOMAIN = "nevod-schnorr-v1".data(using: .utf8)!

func privkeyToScalar(_ seed: Data) -> BigUInt {
    var hash = Data(SHA512.hash(data: seed))
    hash[0] &= 248; hash[31] &= 127; hash[31] |= 64
    return BigUInt(littleEndianBytes: Data(hash.prefix(32))) % L
}

struct SchnorrCommit {
    let rBytes: Data
    let R: Data
}

func schnorrCommit() throws -> SchnorrCommit {
    let rBytes = randomBytes(32)
    let key = try Curve25519.Signing.PrivateKey(rawRepresentation: rBytes)
    return SchnorrCommit(rBytes: rBytes, R: key.publicKey.rawRepresentation)
}

func schnorrChallenge(R_prover: Data, X_prover: Data, R_verifier: Data, X_verifier: Data) -> BigUInt {
    let combined = DOMAIN + R_prover + X_prover + R_verifier + X_verifier
    return BigUInt(littleEndianBytes: Data(SHA256.hash(data: combined))) % L
}

func schnorrProve(signingPriv: Data, rBytes: Data, c: BigUInt) -> Data {
    let x = privkeyToScalar(signingPriv)
    let r = privkeyToScalar(rBytes)
    return ((r + c * x) % L).toLittleEndianBytes(count: 32)
}

// MARK: - Ed25519 Signatures

func ed25519Sign(data: Data, seed: Data) throws -> Data {
    try Curve25519.Signing.PrivateKey(rawRepresentation: seed).signature(for: data)
}

func ed25519Verify(signature: Data, data: Data, publicKey: Data) -> Bool {
    guard let key = try? Curve25519.Signing.PublicKey(rawRepresentation: publicKey) else { return false }
    return key.isValidSignature(signature, for: data)
}

// MARK: - E2E Encryption

struct EncryptedMessage {
    let ephPub: Data
    let nonce: Data
    let ciphertext: Data
}

func encryptMsg(plaintext: Data, recipientEncPub: Data) throws -> EncryptedMessage {
    let ephPriv  = Curve25519.KeyAgreement.PrivateKey()
    let recvPub  = try Curve25519.KeyAgreement.PublicKey(rawRepresentation: recipientEncPub)
    let shared   = try ephPriv.sharedSecretFromKeyAgreement(with: recvPub)
    let keyBytes = Data(SHA256.hash(data: shared.withUnsafeBytes { Data($0) }))
    let nonce    = randomBytes(12)
    let box      = try ChaChaPoly.seal(plaintext, using: SymmetricKey(data: keyBytes),
                                        nonce: ChaChaPoly.Nonce(data: nonce))
    return EncryptedMessage(ephPub: ephPriv.publicKey.rawRepresentation,
                             nonce: nonce, ciphertext: box.ciphertext + box.tag)
}

func decryptMsg(ciphertext: Data, nonce: Data, ephPub: Data, myEncPriv: Data) throws -> Data {
    let myPriv   = try Curve25519.KeyAgreement.PrivateKey(rawRepresentation: myEncPriv)
    let theirPub = try Curve25519.KeyAgreement.PublicKey(rawRepresentation: ephPub)
    let shared   = try myPriv.sharedSecretFromKeyAgreement(with: theirPub)
    let keyBytes = Data(SHA256.hash(data: shared.withUnsafeBytes { Data($0) }))
    guard ciphertext.count >= 16 else { throw CryptoError.decryptFailed }
    let box = try ChaChaPoly.SealedBox(nonce: ChaChaPoly.Nonce(data: nonce),
                                        ciphertext: ciphertext.dropLast(16),
                                        tag: ciphertext.suffix(16))
    return try ChaChaPoly.open(box, using: SymmetricKey(data: keyBytes))
}

enum CryptoError: Error { case decryptFailed }

func randomBytes(_ count: Int) -> Data {
    var bytes = [UInt8](repeating: 0, count: count)
    _ = SecRandomCopyBytes(kSecRandomDefault, count, &bytes)
    return Data(bytes)
}
