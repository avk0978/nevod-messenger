import Foundation
import Security
import CryptoKit

/// Keychain-backed storage for per-chat lock passwords — the "unlock" password and a
/// "duress" password (entering it instead of the real one silently wipes the chat, see
/// ChatLockEntryView). Modeled on IdentityStore.swift's Keychain wrapper, but deliberately
/// NOT sharing its helpers: this uses a stricter kSecAttrAccessibleWhenUnlockedThisDeviceOnly
/// (no background access needed, and — unlike identity keys, which must keep working after a
/// restore — must never sync via iCloud Keychain to another of the user's devices, which
/// would defeat the point of a per-device duress code). Only hashes are ever stored, never
/// the plaintext password, even though Keychain is itself already OS-encrypted.
enum ChatLockStore {
    enum VerifyResult { case unlock, duress, wrong }

    private static func unlockKey(_ chatId: String) -> String { "nevod.chatlock.unlock.\(chatId)" }
    private static func duressKey(_ chatId: String) -> String { "nevod.chatlock.duress.\(chatId)" }

    @discardableResult
    static func setPasswords(chatId: String, unlock: String, duress: String) -> Bool {
        let a = keychainSave(key: unlockKey(chatId), data: hash(chatId: chatId, password: unlock))
        let b = keychainSave(key: duressKey(chatId), data: hash(chatId: chatId, password: duress))
        return a && b
    }

    static func clear(chatId: String) {
        keychainDelete(key: unlockKey(chatId))
        keychainDelete(key: duressKey(chatId))
    }

    /// entered's hash is compared against BOTH stored hashes — whichever matches (if either)
    /// determines the result. Callers must treat .duress exactly like .wrong in the UI (see
    /// ChatLockEntryView's own doc comment) — the whole point of a duress code is that
    /// entering it looks identical to a mistyped password from the outside.
    static func verify(chatId: String, entered: String) -> VerifyResult {
        let candidate = hash(chatId: chatId, password: entered)
        if let stored = keychainLoad(key: unlockKey(chatId)), stored == candidate { return .unlock }
        if let stored = keychainLoad(key: duressKey(chatId)), stored == candidate { return .duress }
        return .wrong
    }

    private static func hash(chatId: String, password: String) -> Data {
        // chatId folded into the hash so identical passcodes reused across two different
        // chats don't produce identical Keychain values.
        Data(SHA256.hash(data: Data("\(chatId):\(password)".utf8)))
    }
}

@discardableResult
private func keychainSave(key: String, data: Data) -> Bool {
    let query: [CFString: Any] = [kSecClass: kSecClassGenericPassword, kSecAttrAccount: key]
    SecItemDelete(query as CFDictionary)
    let attrs: [CFString: Any] = [
        kSecClass: kSecClassGenericPassword, kSecAttrAccount: key,
        kSecValueData: data, kSecAttrAccessible: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
    ]
    return SecItemAdd(attrs as CFDictionary, nil) == errSecSuccess
}

private func keychainLoad(key: String) -> Data? {
    let query: [CFString: Any] = [
        kSecClass: kSecClassGenericPassword, kSecAttrAccount: key,
        kSecReturnData: true, kSecMatchLimit: kSecMatchLimitOne,
    ]
    var result: AnyObject?
    guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess else { return nil }
    return result as? Data
}

private func keychainDelete(key: String) {
    SecItemDelete([kSecClass: kSecClassGenericPassword, kSecAttrAccount: key] as CFDictionary)
}
