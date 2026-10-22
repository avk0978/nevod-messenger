import Foundation
import Security

enum IdentityStore {
    private static let keychainKey   = "nevod.identity"
    private static let displayNameKey = "nevod.displayName"
    private static let nodeAddrKey    = "nevod.nodeAddr"      // legacy single-address key, read once for migration
    private static let nodeRoutesKey  = "nevod.nodeRoutes"
    private static let nodeFingerprintKey = "nevod.nodeFingerprint"
    private static let joinRequestPendingKey = "nevod.joinRequestPending"
    private static let hasEverConnectedKey = "nevod.hasEverConnected"

    static func load() -> NevdIdentity? {
        guard let data = keychainLoad(key: keychainKey) else { return nil }
        keychainPinToThisDevice(key: keychainKey)
        return try? JSONDecoder().decode(NevdIdentity.self, from: data)
    }

    static func save(_ identity: NevdIdentity) throws {
        let data = try JSONEncoder().encode(identity)
        try keychainSave(key: keychainKey, data: data)
    }

    static func delete() { keychainDelete(key: keychainKey) }

    /// Where a fresh install (or a reset identity) starts: Nevod Open, the public node anyone
    /// can register on. Existing installs keep whatever route they have saved.
    static let defaultNodeAddr = "open.nevod.network/nevod-ws"

    static var displayName: String {
        get { LocalDefaults.shared.string(forKey: displayNameKey) ?? "" }
        set { LocalDefaults.shared.set(newValue, forKey: displayNameKey) }
    }

    // Ordered list of ways to reach "our" node — e.g. a home node's LAN address (fast,
    // used when on the same Wi-Fi) and its external/public address (used everywhere
    // else). Index 0 is always "the one to try first" — NevdClient promotes whichever
    // address last actually worked to the front and persists that here, so the
    // preference survives an app relaunch. One-time migration below seeds this from the
    // old single-address key the first time it's read on an existing install.
    static var nodeRoutes: [String] {
        get {
            if let saved = LocalDefaults.shared.stringArray(forKey: nodeRoutesKey), !saved.isEmpty {
                return saved
            }
            let legacy = LocalDefaults.shared.string(forKey: nodeAddrKey) ?? defaultNodeAddr
            return [legacy]
        }
        set { LocalDefaults.shared.set(newValue, forKey: nodeRoutesKey) }
    }

    // Back-compat wrapper over nodeRoutes for every call site that only ever dealt with
    // "the" address (display strings, contact cards, switching to a whole different
    // node via an invite token). Getting returns the current primary route; setting
    // REPLACES the entire list with one entry — exactly what "switch server" already
    // meant at every existing call site, so none of them need to change.
    static var nodeAddr: String {
        get { nodeRoutes.first ?? defaultNodeAddr }
        set { nodeRoutes = [newValue] }
    }

    // SHA-256 fingerprint of the node's self-signed TLS cert — empty means "no
    // pinning, use default system trust" (the prod path: nginx fronts the node
    // with a real CA-issued cert). Set when connecting via a cell-invite token
    // that bundles a node's own self-signed cert (e.g. a home node with no
    // nginx in front of it) — see NevdClient's pinnedFingerprint.
    static var nodeFingerprint: String {
        get { LocalDefaults.shared.string(forKey: nodeFingerprintKey) ?? "" }
        set { LocalDefaults.shared.set(newValue, forKey: nodeFingerprintKey) }
    }

    // Set once a JOIN_REQUEST_ACK{ok:true} comes back (invite_mode="admin" registration
    // channel) — survives app relaunch so AppStore.retryPendingJoinRequestIfNeeded() knows
    // to keep quietly retrying CELL_REGISTER instead of showing the plain setup form again.
    // Cleared once registration actually succeeds (see AppStore's connected-status handler).
    static var joinRequestPending: Bool {
        get { LocalDefaults.shared.bool(forKey: joinRequestPendingKey) }
        set { LocalDefaults.shared.set(newValue, forKey: joinRequestPendingKey) }
    }

    // Set the first time this identity's CELL_REGISTER actually succeeds (connectionStatus
    // becomes "connected") — RootView.swift uses this to tell "brand new identity, still
    // waiting to find out whether this node needs admin approval" apart from "an established
    // member having a normal transient reconnect blip." Without it, RootView had only
    // isRegistered to go on, which flips true synchronously at createIdentity() — long before
    // the server round trip resolves — so it swapped away from NodesView (tearing down
    // SetupView's sheet with it) before an invite_required NACK could ever be shown. Confirmed
    // on device 2026-09-13: tapping "Join this node" → "Get started" landed straight on the
    // empty chat list, the Request-access UI never had a chance to render. Reset alongside
    // everything else in AppStore.resetIdentity().
    static var hasEverConnected: Bool {
        get { LocalDefaults.shared.bool(forKey: hasEverConnectedKey) }
        set { LocalDefaults.shared.set(newValue, forKey: hasEverConnectedKey) }
    }
}

/// The user's own AI provider keys for BYOK bots — one per provider, shared by every bot
/// (user decision 2026-10-16). Same Keychain class as the identity: this device only, never in
/// a backup. Leaves the phone only inside an E2E message to a bot (AppStore.transmit), which
/// uses it for that one request and doesn't keep it (node/bot.py).
enum AIKeyStore {
    private static func account(_ p: AIProvider) -> String { "nevod.aiKey.\(p.rawValue)" }
    private static func consentKey(_ p: AIProvider) -> String { "nevod.aiConsent.\(p.rawValue)" }

    static func key(for p: AIProvider) -> String? {
        keychainLoad(key: account(p)).flatMap { String(data: $0, encoding: .utf8) }
    }

    static func save(_ key: String, for p: AIProvider) throws {
        try keychainSave(key: account(p), data: Data(key.utf8))
        LocalDefaults.shared.set(true, forKey: consentKey(p))
    }

    static func delete(_ p: AIProvider) {
        keychainDelete(key: account(p))
        LocalDefaults.shared.removeObject(forKey: consentKey(p))
    }

    static var savedProviders: [AIProvider] { AIProvider.allCases.filter { key(for: $0) != nil } }

    /// Consent to pass messages to this provider (Guideline 5.1.2(i)) — given in AIKeySheet
    /// together with saving the key, withdrawn by deleting it.
    static func hasConsent(_ p: AIProvider) -> Bool {
        LocalDefaults.shared.bool(forKey: consentKey(p)) && key(for: p) != nil
    }

    static func deleteAll() { AIProvider.allCases.forEach(delete) }
}

private func keychainSave(key: String, data: Data) throws {
    let query: [CFString: Any] = [kSecClass: kSecClassGenericPassword, kSecAttrAccount: key]
    SecItemDelete(query as CFDictionary)
    let attrs: [CFString: Any] = [
        kSecClass: kSecClassGenericPassword, kSecAttrAccount: key,
        kSecValueData: data, kSecAttrAccessible: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
    ]
    let status = SecItemAdd(attrs as CFDictionary, nil)
    guard status == errSecSuccess else { throw KeychainError.saveFailed(status) }
}

// ZKI: the identity keys must never leave this phone — including via the system iCloud /
// computer backup, which is not end-to-end encrypted unless the user turned on Advanced
// Data Protection. Items saved before 2026-09-29 used plain AfterFirstUnlock (migratory:
// included in backups and restored onto a new device); re-pin on load (called once, from
// AppStore.init). SecItemUpdate on an already-ThisDeviceOnly item is a harmless no-op.
private func keychainPinToThisDevice(key: String) {
    let query: [CFString: Any] = [kSecClass: kSecClassGenericPassword, kSecAttrAccount: key]
    let update: [CFString: Any] = [kSecAttrAccessible: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly]
    let status = SecItemUpdate(query as CFDictionary, update as CFDictionary)
    nlog("keychain: pin identity to this device status=\(status)")
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

enum KeychainError: LocalizedError {
    case saveFailed(OSStatus)
    var errorDescription: String? { "Keychain save failed" }
}

/// App state that must stay on this phone: contacts, the chat list, chat settings, the node
/// address, flags — everything the app used to keep in UserDefaults under "nevod.*". UserDefaults
/// goes into the iCloud/computer backup, which Apple can read unless the user turned on Advanced
/// Data Protection; this file sits in Application Support, which AppStore excludes from backup
/// (ZKI gap stage B, 2026-10-16 — stage A moved keys and history out in 68041cf).
///
/// Same read/write calls as UserDefaults. On every launch any "nevod.*" key still in
/// UserDefaults (an install from before this, or a stray write) is moved here and then removed
/// there — only after the file was written. Two keys stay in UserDefaults because SwiftUI's
/// @AppStorage reads them: the accepted Terms version and the one-time store-recovery alert,
/// neither of which says anything about the user.
final class LocalDefaults: @unchecked Sendable {
    static let shared = LocalDefaults()

    private static let staysInUserDefaults: Set<String> = [
        "nevod.termsAcceptedVersion", "nevod.storeRecoveryNotice",
    ]

    private let lock = NSLock()
    private let url: URL
    private var values: [String: Any]

    private init() {
        let fm = FileManager.default
        let support = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        try? fm.createDirectory(at: support, withIntermediateDirectories: true)
        url = support.appendingPathComponent("nevod-local.plist")
        if let data = try? Data(contentsOf: url),
           let dict = try? PropertyListSerialization.propertyList(from: data, format: nil) as? [String: Any] {
            values = dict
        } else {
            values = [:]
        }
        moveOutOfUserDefaults()
    }

    func object(forKey key: String) -> Any? { lock.withLock { values[key] } }
    func string(forKey key: String) -> String? { object(forKey: key) as? String }
    func stringArray(forKey key: String) -> [String]? { object(forKey: key) as? [String] }
    func data(forKey key: String) -> Data? { object(forKey: key) as? Data }
    func dictionary(forKey key: String) -> [String: Any]? { object(forKey: key) as? [String: Any] }
    func bool(forKey key: String) -> Bool { (object(forKey: key) as? Bool) ?? false }
    func integer(forKey key: String) -> Int { (object(forKey: key) as? Int) ?? 0 }

    func set(_ value: Any?, forKey key: String) {
        lock.withLock {
            if let value { values[key] = value } else { values.removeValue(forKey: key) }
            _ = write()
        }
    }

    func removeObject(forKey key: String) { set(nil, forKey: key) }

    /// Caller holds the lock. Readable after the first unlock since boot, like UserDefaults —
    /// a call arriving on a locked phone after a cold start must be able to read contacts.
    private func write() -> Bool {
        do {
            let data = try PropertyListSerialization.data(fromPropertyList: values, format: .binary, options: 0)
            try data.write(to: url, options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
            return true
        } catch {
            nlog("LocalDefaults: write failed — \(error)")
            return false
        }
    }

    private func moveOutOfUserDefaults() {
        let ud = UserDefaults.standard
        let legacy = ud.dictionaryRepresentation().filter {
            $0.key.hasPrefix("nevod.") && !Self.staysInUserDefaults.contains($0.key)
        }
        guard !legacy.isEmpty else { return }
        lock.withLock {
            for (key, value) in legacy where values[key] == nil { values[key] = value }
            guard write() else { return }   // keep the UserDefaults copy if the file isn't there
            for key in legacy.keys { ud.removeObject(forKey: key) }
            nlog("LocalDefaults: moved \(legacy.count) key(s) out of UserDefaults (no longer in backups)")
        }
    }
}

/// The contacts' names for the notification extension (a separate process that can't read the
/// app's own files): only cellId + alias, in the App Group container, excluded from backup.
/// NotificationService.lookupAlias reads the same file.
enum SharedContactNames {
    private static let group = "group.com.avk.Nevod"
    static let fileName = "nevod-contact-names.json"

    private struct Entry: Codable { let cellId: String; let alias: String }

    static func write(_ contacts: [Contact]) {
        guard let dir = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: group)
        else { return }
        var url = dir.appendingPathComponent(fileName)
        let entries = contacts.map { Entry(cellId: $0.cellId, alias: $0.alias) }
        guard let data = try? JSONEncoder().encode(entries) else { return }
        do {
            try data.write(to: url, options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
            var values = URLResourceValues()
            values.isExcludedFromBackup = true
            try url.setResourceValues(values)
        } catch {
            nlog("SharedContactNames: write failed — \(error)")
        }
        // The old copy (full contacts in the App Group's UserDefaults, which is backed up).
        UserDefaults(suiteName: group)?.removeObject(forKey: "nevod.contacts")
    }

    static func remove() {
        if let dir = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: group) {
            try? FileManager.default.removeItem(at: dir.appendingPathComponent(fileName))
        }
        UserDefaults(suiteName: group)?.removeObject(forKey: "nevod.contacts")
    }
}
