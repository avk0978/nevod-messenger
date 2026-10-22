import Foundation
import Combine
import UserNotifications
import SwiftData
#if os(iOS)
import UIKit
#elseif os(macOS)
import AppKit
#endif

@MainActor
final class AppStore: ObservableObject {

    @Published var contacts: [Contact] = []
    // In-memory cache of contact avatars, keyed by cellId (including our OWN cellId, for the
    // self-preview in Profile) — lazily populated by loadAvatarIfCached(for:) the first time a
    // view asks for one, refreshed immediately on receipt (deliverAvatar) or on send
    // (setOwnAvatar). Not persisted itself — the source of truth is nevod_avatars/*.jpg on
    // disk, this is purely a "don't re-read the file every render" cache.
    @Published var contactAvatars: [String: UIImage] = [:]
    @Published var identity: NevdIdentity?
    // Mirrors !IdentityStore.displayName.isEmpty — SwiftUI can't observe UserDefaults directly.
    // false = identity exists locally (generated silently at first launch, for browsing the open
    // discovery segment) but no display name/home node has been chosen yet; true = full member.
    @Published var isRegistered: Bool = false
    @Published var pendingCard: String? = nil
    @Published var pendingCardName: String? = nil  // sender's display name, when known — see contactAddNoticePrefix
    @Published var connectionStatus: String = "disconnected"
    @Published var nodeMembers: [NodeMember] = []
    @Published var publicNodes: [NevdClient.PublicNode] = []
    @Published var verifiedNodes: [String: VerifiedNodeInfo] = [:]
    // Curator-signed official accounts, cellId -> role (see OfficialAccounts in Safety.swift).
    @Published var officialAccounts: [String: OfficialAccount] = [:]
    // Users this device blocked (App Store Guideline 1.2). Enforced twice: the home node drops
    // everything they send us (chat_prefs {"blocked": true}, node/router.py), and
    // handleIncoming/handleReaction drop it here too — covers a node that hasn't been told
    // yet (block made offline) or doesn't run that check.
    @Published var blockedCellIds: Set<String> = []
    @Published var selectedTab: MainTab? = .chats
    // Set by AppDelegate's UNUserNotificationCenterDelegate when the user taps a message
    // push notification — ChatsListView watches this (both .onChange for an already-visible
    // list and .onAppear for the cold-launch-via-tap case, where the view doesn't exist yet
    // when the tap is handled) and pushes straight to that chat instead of leaving the user
    // on whatever screen happened to be open.
    @Published var pendingChatCellId: String? = nil
    @Published var chatIds: Set<String> = []
    @Published var chatSettings: [String: ChatSettings] = [:]  // chatId → settings
    @Published var messageProgress: [String: Double] = [:]  // msgId → 0…1
    /// Files still arriving, per chat — shown at the bottom of the chat so a push for a video
    /// that is still being assembled doesn't land on an empty chat (user report 2026-10-20:
    /// "push, empty chat, the video appears 1–2 minutes later — looks like a glitch").
    @Published var incomingTransfers: [String: [IncomingTransfer]] = [:]
    struct IncomingTransfer: Identifiable, Equatable {
        let id: String        // transfer id
        var mime: String      // "" until the header chunk arrives
        var received: Int
        let total: Int
        var fraction: Double { total > 0 ? Double(received) / Double(total) : 0 }
        /// Its row's identity in the chat. Not `id`: the transfer id is the message id, which
        /// the finished file's bubble uses in the same list — with both under one id SwiftUI
        /// kept showing the row at 97% where two delivered videos should have been (device
        /// screenshot 2026-10-21).
        var rowId: String { "transfer-" + id }
    }
    @Published var storageAlert: String? = nil
    @Published var messageSeq: Int = 0  // increments on every new message — use this (not chatIds) to trigger chat list refresh
    @Published var callLog: [CallLogEntry] = []  // newest first — see logCall()
    @Published var pendingDisplayNameUpdate: String? = nil  // set while offline, flushed on reconnect
    @Published var renameError: String? = nil  // shown by ProfileView when the node refused a rename
    private var renameRevertName: String? = nil
    // invite_mode="admin" registration channel — see MD_Discuss/DISCUSS_REGISTRATION_CHANNEL.md.
    // pendingInviteMode: set alongside connectionStatus=="invite required", tells SetupView
    // whether "Request access" is worth offering at all (nil = not in that state right now).
    @Published var pendingInviteMode: String? = nil
    // Mirrors IdentityStore.joinRequestPending (same reason as isRegistered mirroring
    // displayName above — SwiftUI can't observe UserDefaults directly).
    @Published var joinRequestPending: Bool = IdentityStore.joinRequestPending
    // Set when a JOIN_REQUEST_RESOLVED{approved:false} arrives (see NevdClient's own doc
    // comment on onJoinRequestResolved) while this device happens to still be connected at
    // the exact moment an admin denies — lets SetupView show a clear "denied" state instead
    // of leaving the waiting screen up forever with no explanation. Reset on every fresh
    // join_request_ack, so it can't leak into a later resubmitted request.
    @Published var joinRequestDenied: Bool = false
    // Set the moment the user taps "Request access", cleared only once join_request_ack(ok:true)
    // actually arrives — see sendJoinRequest/attemptSendJoinRequest's own comments for why this
    // exists: a device log (2026-09-11) showed the packet silently never leaving the client
    // because the socket wasn't up yet at tap time, with zero error surfaced and no retry.
    private var pendingJoinRequestNote: String? = nil

    private(set) var client: NevdClient?
    private var cancellables = Set<AnyCancellable>()
    private let contactsKey = "nevod.contacts"
    // Contacts' names are mirrored (cellId + alias only) into the App Group container —
    // SharedContactNames — so the Notification Service Extension, a separate sandboxed
    // process, can rewrite a push's generic "Nevod" title to the recipient's own local contact
    // name. The node itself never sees or sends this — sender_cell_id is the only thing that
    // rides in the push payload (see node/push.py), the alias lookup happens entirely on-device.
    private let nodeMembersKey = "nevod.nodeMembers"
    private let verifiedNodesKey = "nevod.verifiedNodes"
    private let officialAccountsKey = "nevod.officialAccounts"
    private let blockedKey = "nevod.blockedCellIds"
    // Block/unblock changes not yet confirmed sent to the node (made while offline) —
    // flushed on the next "connected". cellId -> blocked.
    private let pendingBlockSyncKey = "nevod.pendingBlockSync"

    var callSignalHandler: ((String, String) -> Void)?
    var onTurnCredentials: ((TurnInfo) -> Void)?
    var tempEncPubs: [String: Data] = [:]  // caller encPub extracted from vcall:offer
    private let quotaKey = "nevod.storageQuotaBytes"
    private let chatIdsKey = "nevod.chatIds.v2"
    private let chatSettingsKey = "nevod.chatSettings"
    private var deviceToken: String? = nil
    private var voipDeviceToken: String? = nil

    // MARK: - Storage

    var storageQuotaBytes: Int64 {
        get {
            // integer(forKey:) returns 0 when key absent; NSNumber doesn't cast to Int64 via as?
            guard LocalDefaults.shared.object(forKey: quotaKey) != nil else {
                return 1024 * 1024 * 1024  // default 1 GB
            }
            return Int64(LocalDefaults.shared.integer(forKey: quotaKey))
        }
        set { LocalDefaults.shared.set(Int(newValue), forKey: quotaKey) }
    }

    var mediaDirectory: URL { nevodMediaDirectory }

    private func saveMediaFile(data: Data, msgId: String, mime: String, name: String?) -> String {
        let ext: String
        if let name, !URL(fileURLWithPath: name).pathExtension.isEmpty {
            ext = MediaSafety.safeExtension(URL(fileURLWithPath: name).pathExtension)
        } else if mime.hasPrefix("image/jpeg") { ext = "jpg" }
        else if mime.hasPrefix("image/png")    { ext = "png" }
        else if mime.hasPrefix("audio/")       { ext = "m4a" }
        else if mime.hasPrefix("video/mp4")    { ext = "mp4" }
        else if mime.hasPrefix("video/quicktime") { ext = "mov" }
        else if mime.hasPrefix("application/pdf") { ext = "pdf" }
        else { ext = "bin" }
        let filename = "\(MediaSafety.safeToken(msgId)).\(ext)"
        try? data.write(to: mediaDirectory.appendingPathComponent(filename),
                        options: .completeFileProtectionUnlessOpen)
        return filename
    }

    // ZKI: nothing Nevod keeps on the phone may leave it through the system iCloud / computer
    // backup (not end-to-end encrypted unless the user turned on Advanced Data Protection —
    // Apple could read it). Excluding the whole Application Support tree covers the SwiftData
    // store (+ its -wal/-shm files), nevod_media/ and nevod_avatars/ in one go, including
    // files created later. The log lives in the App Group container and is re-marked on every
    // launch because rotation recreates the file. Keys: see keychainPinToThisDevice.
    private static func excludeLocalDataFromBackup() {
        let fm = FileManager.default
        var targets = [NevLogger.shared.logFileURL]
        if let support = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first {
            try? fm.createDirectory(at: support, withIntermediateDirectories: true)
            targets.append(support)
        }
        for target in targets {
            var url = target
            var values = URLResourceValues()
            values.isExcludedFromBackup = true
            do { try url.setResourceValues(values) }
            catch { nlog("backup-exclude failed \(url.lastPathComponent): \(error)") }
        }
    }

    /// The message history store, opened through NevodMigrationPlan (Models.swift) so a schema
    /// change in an update migrates the history instead of losing it. If it still can't be
    /// opened, the files are moved aside — never deleted — into
    /// Application Support/nevod-messages-unopened-<time>/ so a later build can bring them back,
    /// the app starts with an empty history, and the user is told once (storeRecoveryNotice).
    private static func openMessageStore() -> ModelContainer {
        let schema = Schema(versionedSchema: NevodSchemaV1.self)
        let config = ModelConfiguration("nevod-messages", schema: schema)
        do {
            let container = try ModelContainer(for: schema, migrationPlan: NevodMigrationPlan.self,
                                               configurations: config)
            nlog("message store: opened, schema \(NevodSchemaV1.versionIdentifier) via migration plan")
            return container
        } catch {
            nlog("message store: open/migration FAILED — \(error)")
        }
        // The store on phones today was created before versioning existed. Its models match V1
        // exactly, so the plan should accept it; if it ever doesn't, open it the old way rather
        // than set the history aside.
        do {
            let container = try ModelContainer(for: schema, configurations: config)
            nlog("message store: opened WITHOUT the migration plan (pre-versioning store)")
            return container
        } catch {
            nlog("message store: plain open FAILED too — \(error)")
        }
        moveMessageStoreAside()
        do {
            let container = try ModelContainer(for: schema, migrationPlan: NevodMigrationPlan.self,
                                               configurations: config)
            UserDefaults.standard.set(true, forKey: storeRecoveryKey)
            return container
        } catch {
            // Not even a fresh file opens (disk full?): keep the app usable for this launch.
            nlog("message store: fresh store FAILED too — \(error); history kept in memory only")
            UserDefaults.standard.set(true, forKey: storeRecoveryKey)
            let memory = ModelConfiguration("nevod-messages", schema: schema, isStoredInMemoryOnly: true)
            return try! ModelContainer(for: schema, configurations: memory)
        }
    }

    private static func moveMessageStoreAside() {
        let fm = FileManager.default
        guard let support = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
        else { return }
        let files = ((try? fm.contentsOfDirectory(at: support, includingPropertiesForKeys: nil)) ?? [])
            .filter { $0.lastPathComponent.contains("nevod-messages")
                      && !$0.lastPathComponent.contains("nevod-messages-unopened") }
        guard !files.isEmpty else { return }
        let stamp = ISO8601DateFormatter().string(from: Date()).replacingOccurrences(of: ":", with: "-")
        let aside = support.appendingPathComponent("nevod-messages-unopened-\(stamp)")
        do {
            try fm.createDirectory(at: aside, withIntermediateDirectories: true)
            for file in files {
                try fm.moveItem(at: file, to: aside.appendingPathComponent(file.lastPathComponent))
            }
            nlog("message store: \(files.count) file(s) moved aside to \(aside.lastPathComponent)")
        } catch {
            nlog("message store: moving aside failed — \(error)")
        }
    }

    /// Only on "Reset identity": the user asked for everything on this device to go.
    private static func removeMessageStoresSetAside() {
        let fm = FileManager.default
        guard let support = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
        else { return }
        for dir in (try? fm.contentsOfDirectory(at: support, includingPropertiesForKeys: nil)) ?? []
        where dir.lastPathComponent.hasPrefix("nevod-messages-unopened-") {
            try? fm.removeItem(at: dir)
        }
        UserDefaults.standard.removeObject(forKey: storeRecoveryKey)
    }

    static let storeRecoveryKey = "nevod.storeRecoveryNotice"

    // Media and avatars are unreadable while the phone is locked (Apple's Data Protection
    // class "complete unless open"): the files are encrypted with a key iOS discards ~10 s
    // after locking, so a locked or seized phone doesn't hand out photos/videos/voice
    // messages. New files can still be created and written while locked (a message that
    // arrives during a locked-screen call is saved normally); only reading waits for unlock.
    // The SwiftData store and UserDefaults deliberately keep the default class: a call
    // arriving on a locked phone after a cold start must be able to open them.
    static func protectFile(_ url: URL) {
        do {
            try FileManager.default.setAttributes([.protectionKey: FileProtectionType.completeUnlessOpen],
                                                  ofItemAtPath: url.path)
        } catch {
            nlog("protectFile failed \(url.lastPathComponent): \(error.localizedDescription)")
        }
    }

    /// Brings every existing file in nevod_media/ and nevod_avatars/ (including ones saved by
    /// builds before this existed) to the protected class. Cheap when nothing needs changing;
    /// runs at launch and each time the phone is unlocked.
    nonisolated static func protectStoredMedia() {
        let fm = FileManager.default
        var changed = 0
        for dir in [nevodMediaDirectory, nevodAvatarsDirectory] {
            try? fm.setAttributes([.protectionKey: FileProtectionType.completeUnlessOpen], ofItemAtPath: dir.path)
            for name in (try? fm.contentsOfDirectory(atPath: dir.path)) ?? [] {
                let path = dir.appendingPathComponent(name).path
                let current = (try? fm.attributesOfItem(atPath: path))?[.protectionKey] as? FileProtectionType
                guard current != .completeUnlessOpen, current != .complete else { continue }
                if (try? fm.setAttributes([.protectionKey: FileProtectionType.completeUnlessOpen],
                                          ofItemAtPath: path)) != nil { changed += 1 }
            }
        }
        if changed > 0 { nlog("protectStoredMedia: \(changed) file(s) moved to completeUnlessOpen") }
    }

    #if os(iOS)
    private var protectedDataObserver: NSObjectProtocol?

    private func observeProtectedData() {
        protectedDataObserver = NotificationCenter.default.addObserver(
            forName: UIApplication.protectedDataDidBecomeAvailableNotification,
            object: nil, queue: .main
        ) { [weak self] _ in
            MainActor.assumeIsolated { self?.onProtectedDataAvailable() }
        }
        if UIApplication.shared.isProtectedDataAvailable {
            Task.detached(priority: .utility) { AppStore.protectStoredMedia() }
        }
    }

    private func onProtectedDataAvailable() {
        Task.detached(priority: .utility) { AppStore.protectStoredMedia() }
        let ids = deferredAvatarIds
        deferredAvatarIds = []
        for id in ids { loadAvatarIfCached(for: id) }
    }
    #endif

    // Avatars asked for while the phone was locked (their files can't be read then) —
    // loaded once it is unlocked, see onProtectedDataAvailable.
    private var deferredAvatarIds: Set<String> = []

    var usedStorageBytes: Int64 {
        guard let support = FileManager.default.urls(
            for: .applicationSupportDirectory, in: .userDomainMask).first else { return 0 }
        return directorySize(at: support)
    }

    private func directorySize(at url: URL) -> Int64 {
        guard let enumerator = FileManager.default.enumerator(
            at: url, includingPropertiesForKeys: [.fileSizeKey],
            options: [.skipsHiddenFiles, .skipsPackageDescendants]) else { return 0 }
        var total: Int64 = 0
        for case let fileURL as URL in enumerator {
            if let size = try? fileURL.resourceValues(forKeys: [.fileSizeKey]).fileSize {
                total += Int64(size)
            }
        }
        return total
    }

    // Transfers refused or aborted by the MediaSafety limits, or already completed — their
    // remaining (or re-delivered) chunks are dropped on arrival.
    private var rejectedTransfers: Set<String> = []

    // Streaming receive: each chunk is written straight to its own place in a tmp file, never
    // accumulated in RAM — so chunks may arrive in any order, and a re-delivered one just
    // lands on the same spot.
    private final class StreamBuffer {
        let tmpURL: URL
        let handle: FileHandle
        let dataTotal: Int   // number of DATA chunks (total - 1, header not counted)
        let slot: Int        // raw bytes in every data chunk but the last
        var chatId = ""      // for incomingTransfers
        // From the header chunk (index 0), which — like any chunk — may come after data
        // chunks; nothing is delivered until it has arrived.
        var headerSeen = false
        var mime = ""
        var name: String?
        // Header was "avatar:MIME" instead of "stream:MIME" — see deliverAvatar. An avatar
        // completion never becomes a Message/chat bubble, unlike every other streamed file.
        var isAvatar = false
        var received = Set<Int>()   // data chunk indexes already written
        var bytesWritten = 0
        // Packet id of the LAST data chunk — the only one the sender sets to its own
        // Message.msgId (sendChunkedStream: `id: isLast ? msgId : nil`), whenever it arrives.
        var finalMsgId: String?
        var card: String?
        // Kept in memory while receiving, because the protected tmp file can't be read back
        // once the phone is locked (see AppStore.protectFile): the first bytes for the type
        // check, and every part of a transfer small enough to turn out to be an avatar.
        var head = Data()
        var smallParts: [Int: Data] = [:]
        let started = Date()
        init(tmpURL: URL, handle: FileHandle, dataTotal: Int, slot: Int) {
            self.tmpURL = tmpURL; self.handle = handle; self.dataTotal = dataTotal; self.slot = slot
        }
        /// Small enough to turn out to be an avatar once the header arrives.
        var mayBeAvatar: Bool { dataTotal <= MediaSafety.avatarMaxChunks(slot: slot) }
    }
    private var pendingStreams: [String: StreamBuffer] = [:]

    // Reactions that couldn't go out because the socket wasn't connected at tap time — see
    // toggleReaction(). Keyed by msgId so repeated taps on the same message (react, un-react,
    // react again, all while still offline) coalesce to just the final intended state instead
    // of replaying every intermediate one on reconnect. Flushed in the c.$status "connected"
    // handler below.
    private var pendingReactions: [String: (emoji: String?, chatId: String)] = [:]
    /// Files whose sending broke off (a dropped connection, the app sent to the background) —
    /// sent again by themselves on the next "connected", up to 3 times per file. The same
    /// transfer id, so the receiver only adds the chunks it's missing (device logs 2026-10-20:
    /// a video stopped when the sender left the app and stayed failed until "Повторить").
    private var interruptedMedia: [String: (contact: Contact, attempts: Int)] = [:]

    private let modelContainer: ModelContainer
    private let modelContext: ModelContext

    init() {
        Self.excludeLocalDataFromBackup()
        modelContainer = Self.openMessageStore()
        modelContext = ModelContext(modelContainer)
        modelContext.autosaveEnabled = false

        loadContacts()
        loadNodeMembers()
        loadVerifiedNodes()
        loadOfficialAccounts()
        blockedCellIds = Set(LocalDefaults.shared.stringArray(forKey: blockedKey) ?? [])
        loadCallLog()
        if let id = IdentityStore.load() {
            identity = id
            isRegistered = !IdentityStore.displayName.isEmpty
            if isRegistered { startClient(id) }
        } else if let id = try? generateIdentity() {
            // Fresh install: generate a browsing-only identity silently, no name/home node yet —
            // this is what lets NodesView's open discovery segment (planets, verified nodes,
            // published pages/bots) work before the user ever commits to a private messaging
            // identity. See RootView's isRegistered gate.
            try? IdentityStore.save(id)
            identity = id
        }
        requestPushPermissions()
        loadChatIds()
        loadChatSettings()
        #if os(iOS)
        observeProtectedData()
        #endif
        Task { await self.migrateDataUrlMessages() }
    }

    // MARK: - Push

    func onDeviceToken(_ token: String) {
        deviceToken = token
        client?.registerPushToken(token)
    }

    func onVoipToken(_ token: String) {
        voipDeviceToken = token
        client?.registerVoipPushToken(token)
    }

    private func requestPushPermissions() {
        #if !targetEnvironment(simulator)
        UNUserNotificationCenter.current()
            .requestAuthorization(options: [.alert, .badge, .sound]) { granted, _ in
                guard granted else { return }
                DispatchQueue.main.async {
                    #if os(iOS)
                    UIApplication.shared.registerForRemoteNotifications()
                    #elseif os(macOS)
                    NSApplication.shared.registerForRemoteNotifications()
                    #endif
                }
            }
        #endif
    }

    // MARK: - Identity / Client

    func createIdentity(displayName: String, inviteCode: String? = nil) throws {
        nlog("createIdentity name=\(displayName) hasInviteCode=\(inviteCode != nil) hadExistingIdentity=\(identity != nil)")
        // Reuse the browsing-only identity generated at first launch if one exists — generating
        // a fresh keypair here would silently orphan it (different cellId), losing continuity
        // with anything already done under it (e.g. a bot chat opened from the open segment
        // before registering). Only generate if somehow no identity exists yet at all.
        let id: NevdIdentity
        if let existing = identity {
            id = existing
        } else {
            id = try generateIdentity()
            try IdentityStore.save(id)
            identity = id
        }
        IdentityStore.displayName = displayName
        isRegistered = true
        startClient(id, inviteCode: inviteCode)
    }

    /// Silent registration for the "message a public bot" path — no form, no user-chosen name.
    /// "Guest" alone would collide (display_name is unique per node, see node.py's
    /// _handle_cell_register) the moment a second anonymous visitor showed up — the cellId
    /// prefix guarantees uniqueness without a network round trip. Rename later via Profile.
    ///
    /// nodeAddr MUST be the address of the node hosting the bot being messaged — startClient()
    /// connects via IdentityStore.nodeRoutes, which without this would still hold whatever
    /// address was last used (a stale/unreachable route from earlier testing, the shipped
    /// default, anything) and silently try to register there instead, hanging on "Подключение…"
    /// forever with no visible reason why.
    // MARK: - Invite links (nevod://join?t=…, from nevod.network/join/)

    /// Invite opened from a link, waiting for SetupView to pick it up (NodesView presents the
    /// form when this is set). Only for an identity not yet admitted anywhere.
    @Published var pendingInviteLink: CellInviteToken? = nil
    /// Node host of an invite link that arrived while this identity is already a member of a
    /// node — RootView explains instead of silently moving an established identity.
    @Published var inviteLinkForOtherNode: String? = nil

    func handleOpenURL(_ url: URL) {
        guard let raw = cellInviteTokenFromLink(url.absoluteString),
              let token = parseCellInviteToken(raw) else {
            nlog("handleOpenURL ignored scheme=\(url.scheme ?? "nil") host=\(url.host ?? "nil")")
            return
        }
        let status = connectionStatus
        nlog("handleOpenURL invite addr=\(token.address) registered=\(isRegistered) everConnected=\(IdentityStore.hasEverConnected) status=\(status)")
        if !isRegistered || !IdentityStore.hasEverConnected {
            pendingInviteLink = token
        } else if status == "invite required" || status == "invite invalid" {
            // A member whose node now asks for a code — same as Profile's invite field.
            IdentityStore.nodeAddr = token.address
            IdentityStore.nodeFingerprint = token.fingerprint
            client?.connect(to: [token.address], pinnedFingerprint: token.fingerprint,
                            inviteCode: token.code)
        } else {
            inviteLinkForOtherNode = String(token.address.split(separator: "/").first ?? "")
        }
    }

    // MARK: - BYOK AI bots

    /// Bumped whenever a key, a consent or a bot's provider choice changes — those live in the
    /// Keychain/UserDefaults, which SwiftUI doesn't observe.
    @Published var aiStateVersion = 0
    private let aiBotsKey = "nevod.aiBots"   // cellId → providers, from the node's published list
    private var pendingAIChecks: [String: CheckedContinuation<String, Never>] = [:]  // "cell|provider"

    /// Remembered when the user opens the bot from a planet (NodePlanetDetailView). Kept in
    /// UserDefaults rather than on Contact: no SwiftData schema change before the stage 4
    /// migration exists.
    func registerAIBot(cellId: String, providers: [String]) {
        var all = (LocalDefaults.shared.dictionary(forKey: aiBotsKey) as? [String: [String]]) ?? [:]
        guard all[cellId] != providers else { return }
        if providers.isEmpty { all.removeValue(forKey: cellId) } else { all[cellId] = providers }
        LocalDefaults.shared.set(all, forKey: aiBotsKey)
        aiStateVersion += 1
    }

    func aiProviders(for cellId: String) -> [AIProvider] {
        let all = (LocalDefaults.shared.dictionary(forKey: aiBotsKey) as? [String: [String]]) ?? [:]
        return (all[cellId] ?? []).compactMap(AIProvider.init(rawValue:))
    }

    func isAIBot(_ cellId: String) -> Bool { !aiProviders(for: cellId).isEmpty }

    private func aiBotProviderKey(_ cellId: String) -> String { "nevod.aiBotProvider.\(cellId.prefix(16))" }

    /// The provider this bot's messages go with: the one the user picked for it, else the first
    /// one it supports that the user has a key (and consent) for. nil = the chat asks for a key.
    func aiProvider(for cellId: String) -> AIProvider? {
        let usable = aiProviders(for: cellId).filter(AIKeyStore.hasConsent)
        if let raw = LocalDefaults.shared.string(forKey: aiBotProviderKey(cellId)),
           let picked = AIProvider(rawValue: raw), usable.contains(picked) { return picked }
        return usable.first
    }

    func setAIProvider(_ provider: AIProvider, for cellId: String) {
        LocalDefaults.shared.set(provider.rawValue, forKey: aiBotProviderKey(cellId))
        aiStateVersion += 1
    }

    func saveAIKey(_ key: String, for provider: AIProvider, bot cellId: String) throws {
        try AIKeyStore.save(key, for: provider)
        nlog("AI key saved provider=\(provider.rawValue)")
        setAIProvider(provider, for: cellId)
    }

    func deleteAIKey(_ provider: AIProvider) {
        AIKeyStore.delete(provider)
        nlog("AI key deleted provider=\(provider.rawValue)")
        aiStateVersion += 1
    }

    /// The free key check (decision 2026-09-28): the bot asks the provider for its model list.
    /// Returns "ok" or an error code (aiErrorText). Silent both ways — no bubble, no push.
    func checkAIKey(_ key: String, provider: AIProvider, bot contact: Contact) async -> String {
        guard let c = client, c.isConnected else { return "not_connected" }
        let slot = "\(contact.cellId)|\(provider.rawValue)"
        finishAICheck(slot, code: "failed")   // an older check for the same slot loses
        nlog("AI key check sent provider=\(provider.rawValue) bot=\(contact.cellId.prefix(8))")
        return await withCheckedContinuation { cont in
            pendingAIChecks[slot] = cont
            Task {
                do {
                    try await c.send(toCellId: contact.cellId, toNodeId: contact.nodeId ?? c.nodeId,
                                     recipientEncPub: contact.encPub,
                                     text: "\(AIWire.checkPrefix)\(provider.rawValue):\(key)",
                                     type: "msg_silent")
                } catch {
                    self.finishAICheck(slot, code: "not_connected")
                    return
                }
                try? await Task.sleep(nanoseconds: 30_000_000_000)
                self.finishAICheck(slot, code: "timeout")
            }
        }
    }

    private func finishAICheck(_ slot: String, code: String) {
        pendingAIChecks.removeValue(forKey: slot)?.resume(returning: code)
    }

    /// Silent answers from a BYOK bot. Returns true when `text` was one (no bubble then).
    private func handleAISignal(chatId: String, text: String) -> Bool {
        if text.hasPrefix(AIWire.checkResultPrefix) {
            let parts = text.dropFirst(AIWire.checkResultPrefix.count).split(separator: ":", maxSplits: 1)
            guard parts.count == 2 else { return true }
            nlog("AI key check result provider=\(parts[0]) code=\(parts[1])")
            finishAICheck("\(chatId)|\(parts[0])", code: String(parts[1]))
            return true
        }
        if text.hasPrefix(AIWire.errorPrefix) {
            let code = String(text.dropFirst(AIWire.errorPrefix.count).split(separator: ":").first ?? "failed")
            nlog("AI bot error code=\(code) from=\(chatId.prefix(8))")
            // Shown as a message from the bot, in the user's language — the bot doesn't know it.
            append(message: Message(id: UUID().uuidString, chatId: chatId, fromMe: false,
                                    text: "⚠️ " + Self.aiErrorText(code),
                                    timestamp: Date(), status: .delivered))
            return true
        }
        return false
    }

    static func aiErrorText(_ code: String) -> String {
        switch code {
        case "invalid_key": return String(localized: "The AI provider rejected the key. Check it and add it again.")
        case "no_credit": return String(localized: "Your AI account has no credit or quota left. Top it up with the provider.")
        case "rate_limited": return String(localized: "The AI provider is limiting requests. Try again in a minute.")
        case "provider_unavailable": return String(localized: "The AI provider is not responding. Try again later.")
        case "no_model": return String(localized: "No suitable chat model is available for this key.")
        case "unsupported_provider": return String(localized: "This bot doesn't work with that provider.")
        case "no_key": return String(localized: "The bot didn't receive a key with your message. Add your AI key.")
        case "timeout": return String(localized: "The bot didn't answer. Check the connection and try again.")
        case "not_connected": return String(localized: "No connection to the node.")
        default: return String(localized: "The bot couldn't get an answer. Try again later.")
        }
    }

    func registerAnonymously(nodeAddr: String) {
        guard !isRegistered, let id = identity else { return }
        IdentityStore.nodeAddr = nodeAddr
        try? createIdentity(displayName: "Guest-\(id.cellId.prefix(6))")
    }

    /// invite_mode="admin" registration channel — auto-fired from onInviteRequired the first
    /// time this node NACKs CELL_REGISTER with invite_mode="admin" (pendingJoinRequestNote set
    /// to "" there), over the still-live connection from that NACK. See NevdClient.sendJoinRequest's
    /// own comment for why isConnected doesn't gate this.
    ///
    /// Remembers the note (pendingJoinRequestNote) rather than just firing once: a device log
    /// (2026-09-11) showed the very first attempt landing in the exact instant the socket had
    /// dropped/was still reconnecting — sendJoinRequest threw notConnected, which the old code
    /// swallowed with try? and never retried, so the tester's request never reached the server
    /// at all and nothing told anyone it had failed. Every subsequent "invite required" NACK
    /// (onInviteRequired below) now re-attempts automatically until one actually gets through.
    private func attemptSendJoinRequest() {
        guard let note = pendingJoinRequestNote, let c = client else {
            nlog("attemptSendJoinRequest SKIP notePending=\(pendingJoinRequestNote != nil) hasClient=\(client != nil)")
            return
        }
        nlog("attemptSendJoinRequest sending noteLen=\(note.count)")
        Task {
            do {
                try await c.sendJoinRequest(note: note)
            } catch {
                nlog("attemptSendJoinRequest FAILED err=\(error) — will retry on next invite-required NACK")
            }
        }
    }

    /// Called on every app-foreground (NevdApp.swift's scenePhase hook) — cheap no-op unless
    /// a request is actually outstanding. A push wake tells the user "approved," but doesn't
    /// itself retry CELL_REGISTER — this does, either confirming it (server admits, status
    /// flips to "connected", the sink above clears the pending flag) or getting NACK'd again
    /// (still waiting, silently, no error surfaced to the user).
    ///
    /// Deliberately checks connectionStatus, not isRegistered — isRegistered mirrors
    /// IdentityStore.displayName being non-empty (see its own doc comment above), which is
    /// already true the moment the join request was sent (a display name was chosen before
    /// that point), long before the server has actually admitted the cell. At cold launch
    /// this same case is already covered by init()'s own `if isRegistered { startClient(id) }`
    /// — this method only needs to cover the already-running-in-foreground case.
    func retryPendingJoinRequestIfNeeded() {
        guard IdentityStore.joinRequestPending, connectionStatus != "connected",
              let id = identity else { return }
        startClient(id)
    }

    /// A "real" rename — re-sends cell_register with the new name (upsert server-side, see
    /// storage.py's register_cell), not just a local cosmetic change. Chats/contacts are keyed
    /// by cellId everywhere, never by name, so renaming touches nothing else. If offline right
    /// now, queues for the next reconnect instead of silently dropping it (same idiom as
    /// flushPendingReactions).
    func renameDisplayName(_ name: String) {
        let trimmed = name.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty, trimmed != IdentityStore.displayName else { return }
        // The node may refuse the new name (taken, or reserved — node/names.py). Remember the
        // old one so handleNameTaken() can roll back instead of leaving the app re-sending a
        // refused name on every reconnect, locked out (confirmed on device 2026-09-28: a
        // rename to "Admin" left the phone stuck on status "name taken").
        renameRevertName = IdentityStore.displayName
        let attempt = trimmed
        Task { @MainActor [weak self] in
            // Past this window, a later name_taken isn't about this rename any more.
            try? await Task.sleep(for: .seconds(20))
            if IdentityStore.displayName == attempt { self?.renameRevertName = nil }
        }
        IdentityStore.displayName = trimmed
        client?.displayName = trimmed
        if let c = client, c.isConnected {
            c.updateDisplayName(trimmed)
        } else {
            pendingDisplayNameUpdate = trimmed
            // Already stuck on a refused name: nothing will reconnect by itself, so retry now
            // with the new one.
            if connectionStatus == "name taken" { forceReconnect() }
        }
    }

    /// Node answered cell_register with name_taken. After a rename: restore the previous
    /// name, tell the user, reconnect under the old name. Not after a rename (first
    /// registration): SetupView handles it via status.
    private func handleNameTaken() {
        guard let old = renameRevertName, !old.isEmpty else { return }
        nlog("rename refused by node (name taken) — reverting to previous name")
        renameRevertName = nil
        IdentityStore.displayName = old
        client?.displayName = old
        pendingDisplayNameUpdate = nil
        renameError = String(localized: "Name already taken, choose another")
        forceReconnect()
    }

    /// NevdClient.isConnected can lie — it only flips false when the receive loop's next read
    /// actually fails, so a connection that silently died (network hiccup between calls, no
    /// clean close) can sit "connected" indefinitely until something forces a real read/write
    /// round trip. Confirmed via device logs 2026-08-02: a second call placed ~1s after the
    /// first one ended sent its offer/ICE candidates with no error (isConnected still true),
    /// but the peer never received any of it — the socket was already dead. Only worked again
    /// after the user fully reopened the app (forcing a fresh connect). CallManager calls this
    /// as a one-time recovery when an outgoing call gets no ring within a few seconds.
    func forceReconnect() {
        guard let c = client else { return }
        let pinned = IdentityStore.nodeFingerprint
        c.connect(to: IdentityStore.nodeRoutes, pinnedFingerprint: pinned.isEmpty ? nil : pinned)
    }

    private func startClient(_ id: NevdIdentity, inviteCode: String? = nil) {
        nlog("startClient cell=\(id.cellId.prefix(8)) routes=\(IdentityStore.nodeRoutes) hasInviteCode=\(inviteCode != nil)")
        // Replacing `client` without tearing the OLD one down first left its reconnect
        // loop running forever as an orphan (its own reconnectTask + Combine subscription
        // keep it alive with nothing ever deallocating it) — that zombie's status updates
        // kept firing into this SAME AppStore's connectionStatus via its still-active
        // .sink, fighting the new client for the shared property. Confirmed on device
        // 2026-09-18: a zombie stuck endlessly retrying a stale/unreachable route
        // (home.nevod.network, "error: no reachable route" every ~8s for over an hour)
        // kept flipping connectionStatus away from "connected" even though a SECOND,
        // newer client had genuinely connected via node1 moments later — calls still
        // worked (CallManager reads the current `client` directly) but sending a message
        // didn't, since ChatView gates purely on connectionStatus == "connected".
        if client != nil {
            nlog("startClient disconnecting previous client before creating a new one")
        }
        client?.disconnect()
        nlog("startClient creating NevdClient cell=\(id.cellId.prefix(8))")
        let c = NevdClient(identity: id)
        c.displayName = IdentityStore.displayName
        c.onMessage = { [weak self] from, msgId, text, card, replyTo, churchFont in
            Task { @MainActor in
                self?.handleIncoming(from: from, msgId: msgId, text: text, card: card, replyTo: replyTo, churchFont: churchFont)
            }
        }
        c.onInviteRequired = { [weak self] _, inviteMode in
            Task { @MainActor in
                nlog("onInviteRequired inviteMode=\(inviteMode)")
                self?.client?.status = "invite required"
                self?.pendingInviteMode = inviteMode
                // admin-approval nodes: send the join request automatically, no separate
                // "Request access" tap. There's no real decision for the user to make here —
                // they already chose to join this node — and a manual button only added an
                // extra screen state to keep in sync with RootView/SetupView's presentation
                // logic, which is exactly what broke three times in a row (dff123f, 59943c9,
                // 5b55f89). pendingJoinRequestNote is set once, on first NACK; every later
                // NACK just retries the same request over whatever socket it arrived on (see
                // sendJoinRequest's comment).
                if inviteMode == "admin" && self?.pendingJoinRequestNote == nil {
                    self?.pendingJoinRequestNote = ""
                }
                self?.attemptSendJoinRequest()
            }
        }
        c.onNameTaken = { [weak self] in
            Task { @MainActor in self?.handleNameTaken() }
        }
        c.onJoinRequestAck = { [weak self] ok, _ in
            guard ok else { return }
            Task { @MainActor in
                self?.pendingJoinRequestNote = nil
                self?.joinRequestDenied = false
                IdentityStore.joinRequestPending = true
                self?.joinRequestPending = true
            }
        }
        c.onJoinRequestResolved = { [weak self] approved in
            Task { @MainActor in
                nlog("onJoinRequestResolved approved=\(approved)")
                guard self?.joinRequestPending == true, let id = self?.identity else { return }
                if approved {
                    // Don't just flip local state to "connected" — that would show the
                    // requester as admitted before this socket's actual CELL_REGISTER
                    // (nacked, back when the request was first sent) ever succeeded.
                    // Re-run the real thing on a fresh connection so every side effect
                    // that normally follows (fetchNodeMembers, push token resend, etc.)
                    // actually happens; the existing "connected" handler in this same
                    // status sink is what clears joinRequestPending once that lands.
                    self?.startClient(id)
                } else {
                    IdentityStore.joinRequestPending = false
                    self?.joinRequestPending = false
                    self?.pendingInviteMode = nil
                    self?.joinRequestDenied = true
                }
            }
        }
        c.onCellRemoved = { [weak self] in
            Task { @MainActor in await self?.resetIdentity() }
        }
        c.onTurnCredentials = { [weak self] info in
            Task { @MainActor in self?.onTurnCredentials?(info) }
        }
        c.onAck = { [weak self] msgId, status in
            Task { @MainActor in self?.handleAck(msgId: msgId, status: status) }
        }
        c.onReaction = { [weak self] from, msgId, emoji in
            Task { @MainActor in self?.handleReaction(from: from, msgId: msgId, emoji: emoji) }
        }
        c.onDeleteMsg = { [weak self] from, msgId in
            Task { @MainActor in self?.handleDeleteSignal(from: from, msgId: msgId) }
        }
        c.onEditMsg = { [weak self] from, msgId, newText in
            Task { @MainActor in self?.handleEditSignal(from: from, msgId: msgId, newText: newText) }
        }
        c.onIdentityDeleted = { [weak self] from in
            Task { @MainActor in self?.handleIdentityDeleted(from: from) }
        }
        c.onMemberAdded = { [weak self] in
            Task { @MainActor in await self?.fetchNodeMembers() }
        }
        c.onMissedCall = { [weak self] from, ts in
            let cellId = String(from.split(separator: "@").first ?? Substring(from))
            Task { @MainActor in
                self?.logCall(cellId: cellId, isOutgoing: false,
                              timestamp: Date(timeIntervalSince1970: Double(ts)),
                              durationSecs: 0, outcome: .missed)
            }
        }
        client = c
        c.$status
            .receive(on: RunLoop.main)
            .sink { [weak self, weak c] status in
                self?.connectionStatus = status
                if status == "connected" {
                    Task { await self?.fetchNodeMembers() }
                    if let token = self?.deviceToken { self?.client?.registerPushToken(token) }
                    if let vtoken = self?.voipDeviceToken { self?.client?.registerVoipPushToken(vtoken) }
                    self?.flushPendingCallSignals()
                    self?.flushPendingReactions()
                    self?.resumeInterruptedMedia()
                    self?.flushPendingBlockSync()
                    Task { await self?.fetchOfficialAccounts() }
                    if let pending = self?.pendingDisplayNameUpdate {
                        self?.client?.updateDisplayName(pending)
                        self?.pendingDisplayNameUpdate = nil
                    }
                    // NevdClient.tryConnect() sets "connected" optimistically right after
                    // *sending* cell_register, before any nack has had a chance to arrive on
                    // the same connection (documented there as "success is implicit unless a
                    // nack follows"). Every reconnect attempt while still awaiting admin
                    // approval briefly pulses "connected" this way, an instant before the
                    // node's invite_required nack corrects it back.
                    //
                    // hasEverConnected MUST NOT be set on that optimistic pulse — it's a
                    // PERMANENT, persisted flag RootView uses to decide whether this identity
                    // has ever really joined a network at all (gating whether MainTabView's
                    // real UI is shown vs. the join/waiting flow). Setting it unconditionally
                    // here used to mark a still-pending, about-to-be-nacked identity as
                    // "connected" forever after just ~180ms — RootView then jumped straight
                    // to MainTabView's empty chat list, skipping the whole join-request UI
                    // (including its own joinRequestPending branch) entirely, and the user
                    // ended up sending real messages from an identity the server had never
                    // actually admitted. Confirmed on device 2026-09-19 — this is what made
                    // both "waiting for approval never shows" AND "read receipts stopped"
                    // happen together: same root cause, two symptoms of chatting from a
                    // technically-unadmitted cell. Wait a beat and only trust "connected"
                    // enough to set it (and clear any pending-request state) if the status
                    // hasn't already been walked back by then — a genuine
                    // approval/registration survives this trivially, a spurious pulse gets
                    // caught before any permanent state or UI reacts to it.
                    //
                    // The check reads the client itself, not connectionStatus: that mirror is
                    // delivered via RunLoop.main, which defers while the screen is being touched
                    // or scrolled, so a NACK that had already arrived could still read as
                    // "connected" here. That set hasEverConnected for a cell a closed node had
                    // only ever NACKed (device log 2026-10-16: relaunch showed the main screen,
                    // "everConnected=true", for an identity Kitaevo never admitted).
                    let nacksAtConnect = c?.nackCount
                    Task { @MainActor [weak self, weak c] in
                        try? await Task.sleep(nanoseconds: 1_500_000_000)
                        guard let c, self?.client === c, c.status == "connected",
                              c.nackCount == nacksAtConnect else { return }
                        if !IdentityStore.hasEverConnected {
                            IdentityStore.hasEverConnected = true
                            // Not @Published (it lives in UserDefaults) — RootView gates the
                            // first switch to MainTabView on it, so tell it to look again.
                            self?.objectWillChange.send()
                        }
                        if self?.joinRequestPending == true {
                            IdentityStore.joinRequestPending = false
                            self?.joinRequestPending = false
                        }
                        self?.pendingInviteMode = nil
                    }
                } else if status == "invite required" || status == "invite invalid" {
                    self?.nodeMembers = []
                }
            }
            .store(in: &cancellables)
        let pinned = IdentityStore.nodeFingerprint
        nlog("startClient calling connect() cell=\(id.cellId.prefix(8)) routes=\(IdentityStore.nodeRoutes) pinned=\(pinned.isEmpty ? "no" : "yes")")
        c.connect(to: IdentityStore.nodeRoutes, pinnedFingerprint: pinned.isEmpty ? nil : pinned,
                  inviteCode: inviteCode)
        nlog("startClient connect() call returned (async work continues on NevdClient's own log lines)")
    }

    // MARK: - Migration

    // Repairs messages where decodeMediaBody failed (browser base64 has newlines) and the raw
    // data-URL was stored as plain text. Now that we pass .ignoreUnknownCharacters, re-decode
    // and promote to proper media messages. Also removes them from the 500KB-text problem.
    private func migrateDataUrlMessages() async {
        let descriptor = FetchDescriptor<Message>(
            predicate: #Predicate { $0.typeRaw == "text" }
        )
        guard let candidates = try? modelContext.fetch(descriptor) else { return }
        let bad = candidates.filter { $0.text.hasPrefix("data:") }
        guard !bad.isEmpty else { return }
        nlog("migration: found \(bad.count) data-url text messages to repair")
        var changed = false
        for msg in bad {
            if let media = decodeMediaBody(msg.text) {
                let filename = saveMediaFile(data: media.data, msgId: msg.msgId,
                                            mime: media.mime, name: media.name)
                msg.text     = media.name ?? media.mime
                msg.typeRaw  = media.type.rawValue
                msg.mediaMime = media.mime
                msg.mediaName = media.name
                msg.mediaSize = media.data.count
                msg.mediaFile = filename
                msg.mediaData = nil
                nlog("migration: repaired \(String(msg.msgId.prefix(8))) as \(media.type.rawValue)")
            } else {
                msg.text = "⚠️ [медиа не загрузилось]"
                nlog("migration: truncated undecodable message \(String(msg.msgId.prefix(8)))")
            }
            changed = true
        }
        if changed {
            try? modelContext.save()
            messageSeq += 1
        }
    }

    // MARK: - Messages (SwiftData)

    func messages(for chatId: String) -> [Message] {
        let descriptor = FetchDescriptor<Message>(
            predicate: #Predicate { $0.chatId == chatId },
            sortBy: [SortDescriptor(\.timestamp)]
        )
        return (try? modelContext.fetch(descriptor)) ?? []
    }

    // Maps messages to lightweight Sendable structs WITHOUT touching mediaData.
    // Delegates to the existing, tested messages(for:) fetch.
    func messageViewData(for chatId: String) -> [MessageViewData] {
        messages(for: chatId).map { $0.toViewData() }
    }

    // Fallback loader for legacy messages that still have mediaData in SwiftData.
    // New messages use mediaFile and are loaded off-thread directly in MessageBubble.
    func loadMediaLegacy(msgId: String) -> Data? {
        let descriptor = FetchDescriptor<Message>(
            predicate: #Predicate { $0.msgId == msgId }
        )
        return (try? modelContext.fetch(descriptor))?.first?.mediaData
    }

    func hasMessages(for chatId: String) -> Bool {
        var descriptor = FetchDescriptor<Message>(
            predicate: #Predicate { $0.chatId == chatId }
        )
        descriptor.fetchLimit = 1
        return (try? modelContext.fetchCount(descriptor)) ?? 0 > 0
    }

    private func append(message: Message) {
        if !message.fromMe, let sender = earlyDeletes.removeValue(forKey: message.msgId),
           sender == message.chatId {
            nlog("message msgId=\(message.msgId.prefix(8)) arrived after its delete — stored as deleted")
            if let file = message.mediaFile {
                try? FileManager.default.removeItem(at: mediaDirectory.appendingPathComponent(file))
            }
            message.isRemoved = true
            message.text = ""
            message.mediaFile = nil; message.mediaMime = nil; message.mediaName = nil; message.mediaSize = nil
        }
        modelContext.insert(message)
        try? modelContext.save()
        chatIds.insert(message.chatId)
        saveChatIds()
        messageSeq += 1
    }

    private func loadChatIds() {
        // Cache in UserDefaults — avoids fetching all message objects (each loads text inline)
        if let arr = LocalDefaults.shared.stringArray(forKey: chatIdsKey) {
            chatIds = Set(arr)
            return
        }
        // First launch after this version: build once from DB, then never full-scan again
        let descriptor = FetchDescriptor<Message>()
        if let all = try? modelContext.fetch(descriptor) {
            chatIds = Set(all.map(\.chatId))
            saveChatIds()
        }
    }

    private func saveChatIds() {
        LocalDefaults.shared.set(Array(chatIds), forKey: chatIdsKey)
    }

    private func handleIncoming(from: String, msgId: String, text: String, card: String?,
                                replyTo: String? = nil, churchFont: Bool = false) {
        let chatId = String(from.split(separator: "@").first ?? Substring(from))
        // Only the protocol tag goes to the log (chunk/vcall/data/…), never message text: the
        // log file stays on the phone and gets shared for diagnostics.
        let tag = text.firstIndex(of: ":").map { String(text[..<$0]) } ?? ""
        let kind = !tag.isEmpty && tag.count <= 12 && tag.allSatisfy({ $0.isASCII && $0.isLetter }) ? tag : "text"
        nlog("incoming len=\(text.count) kind=\(kind) from=\(String(chatId.prefix(8)))")

        if isBlocked(chatId) {
            nlog("incoming DROPPED — sender \(chatId.prefix(8)) is blocked")
            return
        }
        if text.hasPrefix("vcall:") {
            callSignalHandler?(chatId, text)
            return
        }
        if text.hasPrefix("ai-"), isAIBot(chatId), handleAISignal(chatId: chatId, text: text) {
            return
        }
        if text.hasPrefix("chunk:") {
            receiveChunk(chatId: chatId, msgId: msgId, text: text, card: card)
            return
        }
        deliverMessage(chatId: chatId, msgId: msgId, text: text, card: card, replyTo: replyTo, churchFont: churchFont)
    }

    // A file arrives as "chunk:TRANSFER_ID:INDEX/TOTAL/SLOT\nBODY": index 0 is the header
    // ("stream:MIME" or "avatar:MIME", optionally ";name=NAME%20URL%20encoded"), 1...TOTAL-1
    // are base64 data. Each data chunk is written at its own offset — every chunk but the
    // last is exactly SLOT raw bytes (MediaSafety.streamChunkBytes; older builds send no
    // SLOT and use legacyStreamChunkBytes) — so the order chunks arrive in doesn't
    // matter, and one re-delivered after a dropped connection (the node re-queues anything
    // that was in flight, router.py on_connection_lost) is simply skipped. msgId is this
    // packet's own id; see StreamBuffer.finalMsgId for which one names the message.
    private func receiveChunk(chatId: String, msgId: String, text: String, card: String?) {
        guard let nl = text.firstIndex(of: "\n") else { return }
        let header = String(text[..<nl])
        let body = text[text.index(after: nl)...]

        let fields = header.split(separator: ":", maxSplits: 2)
        guard fields.count == 3 else { return }
        let transferId = String(fields[1])
        let idxTotal = fields[2].split(separator: "/")
        guard idxTotal.count == 2 || idxTotal.count == 3,
              let index = Int(idxTotal[0]),
              let total = Int(idxTotal[1]) else { return }
        let slot = idxTotal.count == 3 ? Int(idxTotal[2]) ?? 0 : MediaSafety.legacyStreamChunkBytes

        if rejectedTransfers.contains(transferId) { return }
        nlog("streamChunk \(index)/\(total) bodyLen=\(body.count) tid=\(String(transferId.prefix(8)))")

        let dataTotal = total - 1
        guard [MediaSafety.streamChunkBytes, MediaSafety.legacyStreamChunkBytes].contains(slot),
              dataTotal >= 1, dataTotal <= MediaSafety.maxStreamDataChunks(slot: slot),
              index >= 0, index <= dataTotal else {
            nlog("stream REJECTED \(index)/\(total) — over limits")
            if let buf = pendingStreams[transferId] { return abortStream(transferId, buf, "over limits") }
            return rejectTransfer(transferId)
        }
        guard let buf = pendingStreams[transferId] ?? openStream(transferId, dataTotal: dataTotal, slot: slot) else { return }
        guard buf.dataTotal == dataTotal, buf.slot == slot else {
            return abortStream(transferId, buf, "chunk total changed")
        }
        if buf.card == nil { buf.card = card }
        buf.chatId = chatId
        defer { showIncomingTransfer(transferId, buf) }

        if index == 0 {
            if buf.headerSeen { return }   // re-delivered
            let bodyStr = String(body)
            let isAvatar = bodyStr.hasPrefix("avatar:")
            guard isAvatar || bodyStr.hasPrefix("stream:") else {
                return abortStream(transferId, buf, "not a stream header")
            }
            let inner = String(bodyStr.dropFirst(7))  // "stream:" and "avatar:" are both 7 chars
            var mime = inner
            var name: String? = nil
            if let sc = inner.firstIndex(of: ";") {
                mime = String(inner[..<sc])
                let rest = String(inner[inner.index(after: sc)...])
                if rest.hasPrefix("name=") {
                    name = String(rest.dropFirst(5)).removingPercentEncoding
                }
            }
            if isAvatar {
                let known = contacts.contains(where: { $0.cellId == chatId })
                         || nodeMembers.contains(where: { $0.cellId == chatId })
                guard known, buf.mayBeAvatar,
                      buf.bytesWritten <= MediaSafety.maxAvatarBytes else {
                    nlog("avatar stream IGNORED from \(chatId.prefix(8)) known=\(known) chunks=\(dataTotal)")
                    return abortStream(transferId, buf, "avatar not accepted")
                }
            }
            buf.headerSeen = true
            buf.mime = mime; buf.name = name; buf.isAvatar = isAvatar
        } else {
            if buf.received.contains(index) {
                nlog("streamChunk DUPLICATE \(index)/\(total) tid=\(String(transferId.prefix(8)))")
                return
            }
            if body.utf8.count > slot / 3 * 4 + 1024 { return abortStream(transferId, buf, "chunk too big") }
            guard let raw = Data(base64Encoded: String(body)) else {
                return abortStream(transferId, buf, "chunk \(index) not base64")
            }
            // Fixed-size slots are what place chunk i at (i-1) * slot.
            let isLast = index == dataTotal
            guard isLast ? raw.count <= slot : raw.count == slot else {
                return abortStream(transferId, buf, "chunk \(index) is \(raw.count) bytes")
            }
            let byteLimit = buf.isAvatar ? MediaSafety.maxAvatarBytes : MediaSafety.maxIncomingFileBytes
            guard buf.bytesWritten + raw.count <= byteLimit else {
                return abortStream(transferId, buf, "over \(byteLimit) bytes")
            }
            do {
                try buf.handle.seek(toOffset: UInt64(index - 1) * UInt64(slot))
                try buf.handle.write(contentsOf: raw)
            } catch {
                return abortStream(transferId, buf, "write failed: \(error)")
            }
            buf.received.insert(index)
            buf.bytesWritten += raw.count
            if index == 1 { buf.head = raw.prefix(16) }
            if buf.mayBeAvatar { buf.smallParts[index] = raw }
            if isLast { buf.finalMsgId = msgId }
        }

        guard buf.headerSeen, buf.received.count == dataTotal else { return }
        try? buf.handle.close()
        pendingStreams.removeValue(forKey: transferId)
        #if os(iOS)
        if pendingStreams.isEmpty { receiveBackgroundTask.end() }
        #endif
        rejectTransfer(transferId)   // done — a re-delivered chunk of it is just dropped
        if buf.isAvatar {
            try? FileManager.default.removeItem(at: buf.tmpURL)
            var bytes = Data()
            for i in 1...dataTotal { bytes.append(buf.smallParts[i] ?? Data()) }
            deliverAvatar(bytes, chatId: chatId)
        } else {
            deliverStreamFile(tmpURL: buf.tmpURL, mime: buf.mime, head: buf.head, name: buf.name,
                              chatId: chatId, msgId: buf.finalMsgId ?? msgId, card: buf.card)
        }
    }

    /// Opens the tmp file for a transfer on whichever of its chunks arrives first.
    private func openStream(_ transferId: String, dataTotal: Int, slot: Int) -> StreamBuffer? {
        // Full: drop the oldest unfinished stream (most likely abandoned mid-way).
        if pendingStreams.count >= MediaSafety.maxPendingTransfers,
           let oldest = pendingStreams.min(by: { $0.value.started < $1.value.started }) {
            abortStream(oldest.key, oldest.value, "too many unfinished transfers")
        }
        let safeTid = MediaSafety.safeToken(transferId)
        guard !safeTid.isEmpty else { return nil }
        let tmpURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("nevod_\(safeTid).bin")
        // Not completeUnlessOpen: createFile closes the file right away, and such a file can't be
        // reopened while the phone is locked — FileHandle failed silently for every chunk, so
        // photos sent during a lock-screen call were acked but never appeared (device log
        // 2026-10-19: 2 of 3 photos lost). The tmp file lives only until the last chunk;
        // deliverStreamFile moves it into nevod_media/ and protectFile/protectStoredMedia
        // bring it to completeUnlessOpen.
        FileManager.default.createFile(atPath: tmpURL.path, contents: nil,
                                       attributes: [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication])
        guard let handle = try? FileHandle(forWritingTo: tmpURL) else {
            nlog("openStream FAILED tid=\(String(transferId.prefix(8))) — tmp file not writable")
            return nil
        }
        let buf = StreamBuffer(tmpURL: tmpURL, handle: handle, dataTotal: dataTotal, slot: slot)
        pendingStreams[transferId] = buf
        return buf
    }

    /// Updates (or, once the transfer is finished/aborted, removes) its row in incomingTransfers.
    /// Avatars never show: a small transfer is listed only once its header says it's a file.
    private func showIncomingTransfer(_ transferId: String, _ buf: StreamBuffer) {
        var rows = incomingTransfers[buf.chatId] ?? []
        rows.removeAll { $0.id == transferId }
        let done = pendingStreams[transferId] !== buf
        if !done, !buf.isAvatar, buf.headerSeen || !buf.mayBeAvatar {
            rows.append(IncomingTransfer(id: transferId, mime: buf.mime,
                                         received: buf.received.count, total: buf.dataTotal))
        }
        if rows.isEmpty { incomingTransfers.removeValue(forKey: buf.chatId) } else { incomingTransfers[buf.chatId] = rows }
    }

    private func abortStream(_ transferId: String, _ buf: StreamBuffer, _ why: String) {
        nlog("stream ABORTED tid=\(String(transferId.prefix(8))) — \(why)")
        try? buf.handle.close()
        try? FileManager.default.removeItem(at: buf.tmpURL)
        pendingStreams.removeValue(forKey: transferId)
        rejectTransfer(transferId)
        showIncomingTransfer(transferId, buf)
    }

    private func rejectTransfer(_ transferId: String) {
        if rejectedTransfers.count > 256 { rejectedTransfers.removeAll() }
        rejectedTransfers.insert(transferId)
    }

    /// Completion for an "avatar:"-tagged stream — unlike deliverStreamFile, this never
    /// becomes a Message/chat bubble. Overwrites any previous avatar for this cellId (no
    /// history kept) and refreshes the in-memory cache so SwiftUI re-renders immediately.
    private func deliverAvatar(_ data: Data, chatId: String) {
        let safeId = MediaSafety.safeToken(chatId)
        guard !safeId.isEmpty else { return }
        // The received bytes are never shown or kept: MediaSafety redraws them into our own
        // small JPEG (see its header comment), and only that is saved.
        guard let clean = MediaSafety.sanitizedAvatarJPEG(data: data) else {
            nlog("deliverAvatar REJECTED avatar from cellId=\(chatId.prefix(8)) — not a plain JPEG/PNG within limits")
            return
        }
        let destURL = nevodAvatarsDirectory.appendingPathComponent("\(safeId)\(Self.avatarSuffix).jpg")
        try? FileManager.default.removeItem(at: nevodAvatarsDirectory.appendingPathComponent("\(safeId).jpg"))
        guard (try? clean.write(to: destURL, options: .completeFileProtectionUnlessOpen)) != nil else { return }
        contactAvatars[chatId] = UIImage(data: clean)
        nlog("deliverAvatar saved avatar for cellId=\(chatId.prefix(8))")
    }

    private func deliverStreamFile(tmpURL: URL, mime: String, head: Data, name: String?,
                                   chatId: String, msgId: String, card: String?) {
        nlog("deliverStreamFile mime=\(mime) name=\(name ?? "nil")")
        let alreadyKnown = contacts.contains(where: { $0.cellId == chatId })
                        || nodeMembers.contains(where: { $0.cellId == chatId })
        // Real incoming chat content from this contact — see bumpStuckSentMessages's doc comment.
        bumpStuckSentMessages(chatId: chatId, to: .read, reason: "file received")
        let mime = MediaSafety.safeMime(claimed: mime, header: head)
        let type = Message.MessageType(mime: mime)

        let fileSize = Int64((try? tmpURL.resourceValues(forKeys: [.fileSizeKey]))?.fileSize ?? 0)
        guard usedStorageBytes + fileSize <= storageQuotaBytes else {
            let fsize = ByteCountFormatter.string(fromByteCount: fileSize, countStyle: .file)
            let used  = ByteCountFormatter.string(fromByteCount: usedStorageBytes, countStyle: .file)
            let quota = ByteCountFormatter.string(fromByteCount: storageQuotaBytes, countStyle: .file)
            storageAlert = String(localized: "Не удалось сохранить файл (\(fsize)): хранилище заполнено (\(used) из \(quota)).")
            try? FileManager.default.removeItem(at: tmpURL)
            return
        }

        let ext: String
        if let n = name, !URL(fileURLWithPath: n).pathExtension.isEmpty {
            ext = MediaSafety.safeExtension(URL(fileURLWithPath: n).pathExtension)
        } else if mime.hasPrefix("image/jpeg")    { ext = "jpg" }
        else if mime.hasPrefix("image/png")        { ext = "png" }
        else if mime.hasPrefix("audio/")           { ext = "m4a" }
        else if mime.hasPrefix("video/mp4")        { ext = "mp4" }
        else if mime.hasPrefix("video/quicktime")  { ext = "mov" }
        else if mime.hasPrefix("application/pdf")  { ext = "pdf" }
        else { ext = "bin" }

        let filename = "\(MediaSafety.safeToken(msgId)).\(ext)"
        let destURL = nevodMediaDirectory.appendingPathComponent(filename)
        do {
            try FileManager.default.moveItem(at: tmpURL, to: destURL)
        } catch {
            try? FileManager.default.removeItem(at: tmpURL)
            return
        }
        Self.protectFile(destURL)

        append(message: Message(id: msgId, chatId: chatId, fromMe: false,
                                text: name ?? mime, timestamp: Date(), status: .delivered,
                                type: type, mediaData: nil, mediaMime: mime, mediaName: name,
                                mediaSize: Int(fileSize), mediaFile: filename))
        if let card, !alreadyKnown { pendingCard = card }
    }

    private func deliverMessage(chatId: String, msgId: String, text: String, card: String?,
                                replyTo: String? = nil, churchFont: Bool = false) {
        nlog("deliverMessage len=\(text.count) isData=\(text.hasPrefix("data:"))")
        let alreadyKnown = contacts.contains(where: { $0.cellId == chatId })
                        || nodeMembers.contains(where: { $0.cellId == chatId })
        if text.hasPrefix(contactAddNoticePrefix) {
            let senderName = String(text.dropFirst(contactAddNoticePrefix.count))
            nlog("contact-add notice from=\(chatId.prefix(8)) name=\(senderName)")
            if let card, !alreadyKnown {
                pendingCard = card
                pendingCardName = senderName
            }
            return  // not a chat message — no bubble, and no bump below: a system notice isn't
                     // evidence they were actually in the chat reading it, unlike real content
        }
        // Real incoming chat content from this contact — see bumpStuckSentMessages's doc comment.
        bumpStuckSentMessages(chatId: chatId, to: .read, reason: "message received")

        if let media = decodeMediaBody(text) {
            nlog("decodeMedia ok mime=\(media.mime) bytes=\(media.data.count)")
            let mediaFile = saveMediaFile(data: media.data, msgId: msgId, mime: media.mime, name: media.name)
            let fileExists = FileManager.default.fileExists(
                atPath: nevodMediaDirectory.appendingPathComponent(mediaFile).path)
            nlog("decodeMedia saved file=\(mediaFile) exists=\(fileExists)")
            let msg = Message(id: msgId, chatId: chatId, fromMe: false,
                              text: media.name ?? media.mime, timestamp: Date(), status: .delivered,
                              type: media.type, mediaData: nil,
                              mediaMime: media.mime, mediaName: media.name,
                              mediaSize: media.data.count, mediaFile: mediaFile)
            append(message: msg)
        } else {
            nlog("decodeMedia FAILED — storing as text len=\(text.count)")
            append(message: Message(id: msgId, chatId: chatId, fromMe: false,
                                    text: text, timestamp: Date(), status: .delivered,
                                    replyToMsgId: replyTo, churchFont: churchFont))
        }

        if let card, !alreadyKnown { pendingCard = card }
    }

    // MARK: - Send

    // Call signals that couldn't be written — no connection, or it was being replaced (a
    // woken phone's answer went out 8 ms into a reconnect and was lost, device logs
    // 2026-10-21). Sent first thing on the next connect, in order; see flushPendingCallSignals.
    private var pendingCallSignals: [(text: String, cellId: String, offer: Bool, at: Date)] = []

    private func queueCallSignal(_ text: String, to cellId: String, offer: Bool) {
        nlog("call signal QUEUED until connected signal=\(text.prefix(20)) to=\(cellId.prefix(8))")
        pendingCallSignals.append((text, cellId, offer, Date()))
    }

    /// Drops what's older than 30 s, and anything but an end-of-call signal made before the
    /// call with that peer ended.
    private func flushPendingCallSignals() {
        guard !pendingCallSignals.isEmpty, client?.isConnected == true else { return }
        let queued = pendingCallSignals
        pendingCallSignals.removeAll()
        Task {
            for s in queued {
                let isEnd = ["vcall:hangup", "vcall:reject", "vcall:busy"].contains { s.text.hasPrefix($0) }
                let endedAt = NevdClient.callEndedAt[s.cellId] ?? 0
                if Date().timeIntervalSince(s.at) > 30 || (!isEnd && endedAt >= Int64(s.at.timeIntervalSince1970)) {
                    nlog("call signal DROPPED, too late signal=\(s.text.prefix(20)) to=\(s.cellId.prefix(8))")
                    continue
                }
                if s.offer {
                    try? await sendCallOffer(s.text, to: s.cellId)
                } else {
                    try? await sendSignal(s.text, to: s.cellId)
                }
            }
        }
    }

    func sendSignal(_ text: String, to cellId: String) async throws {
        guard let c = client, c.isConnected else {
            queueCallSignal(text, to: cellId, offer: false)
            return
        }
        let encPub: Data
        var targetNodeId = c.nodeId
        if let contact = contacts.first(where: { $0.cellId == cellId }) {
            encPub = contact.encPub
            targetNodeId = contact.nodeId ?? c.nodeId
        } else if let member = nodeMembers.first(where: { $0.cellId == cellId }) {
            encPub = member.encPub
        } else if let pub = tempEncPubs[cellId] {
            encPub = pub
        } else {
            nlog("sendSignal SKIP no encPub signal=\(text.prefix(20)) to=\(cellId.prefix(8))")
            return
        }
        // vcall_signal, not the default "msg" type — ring/answer/ice/reject/hangup/busy still
        // get buffered normally if the recipient isn't connected, but must never trigger a
        // regular "New message" push: only the initial offer (sendCallOffer) should ever wake
        // a killed app, and a stray alert banner right before/instead of the CallKit screen
        // was confusing during testing.
        do {
            try await c.send(toCellId: cellId, toNodeId: targetNodeId,
                             recipientEncPub: encPub, text: text, type: "vcall_signal")
        } catch {
            queueCallSignal(text, to: cellId, offer: false)
            return
        }
        nlog("sendSignal OK signal=\(text.prefix(40)) to=\(cellId.prefix(8))")
    }

    // Only the initial call offer needs its own wire type — everything else about a call
    // (ring/answer/ice/hangup/busy) stays as a normal signal via sendSignal(). The node
    // can't distinguish a vcall: text from any other message (both E2E encrypted), so this
    // is what lets it send a VoIP push instead of a regular one specifically for the offer.
    func sendCallOffer(_ text: String, to cellId: String) async throws {
        guard let c = client, c.isConnected else {
            queueCallSignal(text, to: cellId, offer: true)
            return
        }
        let encPub: Data
        var targetNodeId = c.nodeId
        if let contact = contacts.first(where: { $0.cellId == cellId }) {
            encPub = contact.encPub
            targetNodeId = contact.nodeId ?? c.nodeId
        } else if let member = nodeMembers.first(where: { $0.cellId == cellId }) {
            encPub = member.encPub
        } else if let pub = tempEncPubs[cellId] {
            encPub = pub
        } else {
            nlog("sendCallOffer SKIP no encPub to=\(cellId.prefix(8))")
            throw NevdError.notConnected
        }
        // Cleartext caller_name (not just the one buried in `text`'s encrypted JSON) —
        // the receiving node needs it in the open to put a real name in a VoIP push,
        // since it generally can't resolve a cross-node caller's name locally.
        do {
            try await c.send(toCellId: cellId, toNodeId: targetNodeId,
                             recipientEncPub: encPub, text: text, type: "vcall_offer",
                             callerName: IdentityStore.displayName)
        } catch {
            queueCallSignal(text, to: cellId, offer: true)
        }
    }

    // Best-known name for a cellId, for display purposes (Calls tab, etc.) — prefers a
    // saved contact's alias, then a fellow node member's self-declared name, then the raw
    // id. Same priority as CallManager's resolvedCallerName, minus the push-payload
    // fallback (irrelevant here — we're not resolving a live incoming call).
    func displayName(for cellId: String) -> String {
        if let c = contacts.first(where: { $0.cellId == cellId }), !c.alias.isEmpty {
            return c.alias
        }
        if let m = nodeMembers.first(where: { $0.cellId == cellId }), !m.displayName.isEmpty {
            return m.displayName
        }
        return String(cellId.prefix(8)) + "…"
    }

    private func loadCallLog() {
        let descriptor = FetchDescriptor<CallLogEntry>(sortBy: [SortDescriptor(\.timestamp, order: .reverse)])
        callLog = (try? modelContext.fetch(descriptor)) ?? []
    }

    func deleteCallLogEntry(_ entry: CallLogEntry) {
        modelContext.delete(entry)
        try? modelContext.save()
        callLog.removeAll { $0.id == entry.id }
    }

    /// Called by CallManager's reset() at the end of every call — writes one entry to the
    /// local, on-device call history (the "Calls" tab). Deliberately local-only, no network
    /// send: each side of a call already independently knows what happened to it (dialed
    /// out and got no answer; received an offer and either answered or didn't), so there's
    /// nothing to sync. This replaced an earlier version that auto-sent a "Missed call at
    /// H:M" chat message — worked, but the user reported it cluttered the conversation like
    /// spam (2026-07-31); a dedicated history list is the standard fix (same as any phone).
    func logCall(cellId: String, isOutgoing: Bool, timestamp: Date, durationSecs: Int,
                 outcome: CallLogEntry.Outcome, isVideo: Bool = false) {
        let entry = CallLogEntry(id: UUID().uuidString, cellId: cellId, isOutgoing: isOutgoing,
                                 timestamp: timestamp, durationSecs: durationSecs, outcome: outcome,
                                 isVideo: isVideo)
        modelContext.insert(entry)
        try? modelContext.save()
        callLog.insert(entry, at: 0)
    }

    /// Returns false when it couldn't go out (the bubble shows the retry line then).
    @discardableResult
    func send(text: String, to contact: Contact, replyTo: String? = nil, churchFont: Bool = false) async throws -> Bool {
        let msgId = UUID().uuidString
        let msg = Message(id: msgId, chatId: contact.cellId, fromMe: true,
                          text: text, timestamp: Date(), status: .sent,
                          replyToMsgId: replyTo, churchFont: churchFont)
        append(message: msg)
        let savedContactMatch = contacts.first(where: { $0.cellId == contact.cellId })
        nlog("send text to=\(contact.cellId.prefix(16)) toNodeId=\((contact.nodeId ?? client?.nodeId ?? "nil").prefix(16)) "
             + "encPub=\(contact.encPub.map { String(format: "%02x", $0) }.joined().prefix(16)) "
             + "savedContact=\(savedContactMatch != nil) "
             + "nodeMemberEncPub=\(nodeMembers.first(where: { $0.cellId == contact.cellId })?.encPub.map { String(format: "%02x", $0) }.joined().prefix(16) ?? "n/a")")
        return await transmit(msgId: msgId, to: contact)
    }

    /// Sends a message row that's already in the store — a fresh one or a retry. Any failure
    /// (no connection, socket dropped mid-send on a bad network) marks it .failed instead of
    /// throwing: the bubble then says "Сообщение не отправлено. Повторить отправку?" in the
    /// user's language (retrySend), rather than ChatView printing the raw, untranslated
    /// socket error under the chat (seen on device 2026-10-13: "Connection failed:
    /// POSIXErrorCode(rawValue: 89): Operation canceled").
    @discardableResult
    private func transmit(msgId: String, to contact: Contact) async -> Bool {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        guard let msg = (try? modelContext.fetch(descriptor))?.first else { return false }
        // Copied out before the first await — the row itself isn't touched across suspensions.
        let type = msg.type, text = msg.text, churchFont = msg.churchFont, replyTo = msg.replyToMsgId
        let mediaFile = msg.mediaFile, mime = msg.mediaMime, name = msg.mediaName
        guard let c = client, c.isConnected else {
            nlog("transmit SKIP not connected msgId=\(msgId.prefix(8))")
            markFailed(msgId: msgId, chatId: contact.cellId)
            return false
        }
        do {
            if type == .text {
                var wireText = churchFont ? "slavonic:\n\(text)" : text
                wireText = replyTo.map { "reply:\($0)\n\(wireText)" } ?? wireText
                // BYOK bot: the user's key rides on the wire copy only — the stored row (and so
                // a retry, which re-reads it here) never contains it.
                if let provider = aiProvider(for: contact.cellId), let key = AIKeyStore.key(for: provider) {
                    wireText = "\(AIWire.keyPrefix)\(provider.rawValue):\(key)\n\(wireText)"
                }
                try await c.send(toCellId: contact.cellId, toNodeId: contact.nodeId ?? c.nodeId,
                                  recipientEncPub: contact.encPub, text: wireText, id: msgId)
            } else {
                // Stream from the copy already on disk instead of also base64-encoding the
                // whole thing into a second in-RAM copy (sendChunked/encodeMediaBody) — on a
                // low-RAM device, sending several photos this way at once was enough to get
                // the app killed and drop the node's WebSocket mid-send.
                guard let mediaFile, let mime else { throw NevdError.invalidData }
                // A few more seconds to finish if the user leaves the app mid-send; whatever
                // doesn't make it is resumed on the next connect (interruptedMedia).
                // Ended by the expiration handler too: a file now waits out a whole call
                // (NevdClient.callInProgress), and iOS kills an app that overruns its background time.
                #if os(iOS)
                let bgTask = BackgroundTaskBox()
                bgTask.id = UIApplication.shared.beginBackgroundTask(withName: "nevod-send") { bgTask.end() }
                defer { bgTask.end() }
                #endif
                try await sendChunkedStream(fileURL: mediaDirectory.appendingPathComponent(mediaFile),
                                            mime: mime, name: name, msgId: msgId, contact: contact, client: c)
            }
        } catch {
            nlog("transmit FAILED msgId=\(msgId.prefix(8)) type=\(type.rawValue) err=\(error)")
            markFailed(msgId: msgId, chatId: contact.cellId)
            if type != .text {
                // attempts = failed sends so far; resumed while fewer than 3 (3 sends in all —
                // the check was <= 3, so the log showed "attempt=4").
                let attempts = (interruptedMedia[msgId]?.attempts ?? 0) + 1
                if attempts < 3 {
                    interruptedMedia[msgId] = (contact, attempts)
                } else {
                    interruptedMedia.removeValue(forKey: msgId)
                }
            }
            return false
        }
        interruptedMedia.removeValue(forKey: msgId)
        return true
    }

    /// The failed bubble's "Повторить отправку?": the same row, same msgId, sent again.
    /// Safe if the first attempt actually got through after all — msgId is unique on the
    /// receiving side too (a text re-delivery just overwrites the same row; a media file's
    /// destination name is derived from msgId, so the second copy is dropped).
    func retrySend(msgId: String, to contact: Contact) {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        guard let msg = (try? modelContext.fetch(descriptor))?.first,
              msg.fromMe, msg.status == .failed, !msg.isRemoved else { return }
        nlog("retrySend msgId=\(msgId.prefix(8)) type=\(msg.type.rawValue)")
        msg.status = .sent
        try? modelContext.save()
        messageSeq += 1
        Task { await transmit(msgId: msgId, to: contact) }
    }

    /// Sets/toggles my own reaction on a message — tapping the same emoji again clears it,
    /// tapping a different one replaces it. Applies locally right away (optimistic, same as
    /// how a sent message shows immediately rather than waiting on a round trip). If the socket
    /// isn't connected at tap time — confirmed on device 2026-08-26: reaction shown locally,
    /// nothing ever reached the node's router, no retry — the send is now queued in
    /// pendingReactions and flushed once c.$status reports "connected" again, same idiom as
    /// ChatView's markChatRead-on-reconnect.
    func toggleReaction(msgId: String, emoji: String, chatId: String) {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        guard let msg = (try? modelContext.fetch(descriptor))?.first else { return }
        let newValue: String? = msg.myReaction == emoji ? nil : emoji
        msg.myReaction = newValue
        try? modelContext.save()
        messageSeq += 1
        guard let c = client, c.isConnected else {
            pendingReactions[msgId] = (emoji: newValue, chatId: chatId)
            return
        }
        let contact = contacts.first(where: { $0.cellId == chatId })
        c.sendReaction(msgId: msgId, emoji: newValue, toCellId: chatId, toNodeId: contact?.nodeId ?? c.nodeId)
    }

    private func resumeInterruptedMedia() {
        guard !interruptedMedia.isEmpty, client?.isConnected == true else { return }
        for (msgId, entry) in interruptedMedia {
            nlog("resume interrupted media msgId=\(msgId.prefix(8)) attempt=\(entry.attempts + 1)")
            retrySend(msgId: msgId, to: entry.contact)
        }
    }

    private func flushPendingReactions() {
        guard !pendingReactions.isEmpty, let c = client, c.isConnected else { return }
        let queued = pendingReactions
        pendingReactions.removeAll()
        for (msgId, entry) in queued {
            let contact = contacts.first(where: { $0.cellId == entry.chatId })
            c.sendReaction(msgId: msgId, emoji: entry.emoji, toCellId: entry.chatId,
                           toNodeId: contact?.nodeId ?? c.nodeId)
        }
    }

    func send(mediaData: Data, mime: String, name: String? = nil, to contact: Contact) async throws {
        let type = Message.MessageType(mime: mime)
        let msgId = UUID().uuidString
        let mediaFile = saveMediaFile(data: mediaData, msgId: msgId, mime: mime, name: name)
        let msg = Message(id: msgId, chatId: contact.cellId, fromMe: true,
                          text: name ?? mime, timestamp: Date(), status: .sent,
                          type: type, mediaData: nil, mediaMime: mime, mediaName: name,
                          mediaSize: mediaData.count, mediaFile: mediaFile)
        append(message: msg)
        await transmit(msgId: msgId, to: contact)
    }

    #if os(iOS)
    /// Leaving the app while a file is still arriving: iOS gives a few more seconds (about
    /// 30) to finish before it suspends the app and its connection.
    private let receiveBackgroundTask = BackgroundTaskBox()

    func appDidEnterBackground() {
        guard !pendingStreams.isEmpty, receiveBackgroundTask.id == .invalid else { return }
        nlog("background: \(pendingStreams.count) incoming transfer(s) unfinished, asking for background time")
        receiveBackgroundTask.id = UIApplication.shared.beginBackgroundTask(withName: "nevod-receive") { [weak self] in
            nlog("background time for incoming transfers expired")
            self?.receiveBackgroundTask.end()
        }
    }

    func appDidBecomeActive() {
        receiveBackgroundTask.end()
    }

    private final class BackgroundTaskBox {
        var id = UIBackgroundTaskIdentifier.invalid
        @MainActor func end() {
            guard id != .invalid else { return }
            UIApplication.shared.endBackgroundTask(id)
            id = .invalid
        }
    }
    #endif

    // MARK: - Streaming file send (no full file in RAM)

    func send(fileURL: URL, mime: String, name: String, to contact: Contact) async throws {
        let fileSize = (try? fileURL.resourceValues(forKeys: [.fileSizeKey]))?.fileSize ?? 0
        let fileSize64 = Int64(fileSize)
        guard usedStorageBytes + fileSize64 <= storageQuotaBytes else {
            let fsize = ByteCountFormatter.string(fromByteCount: fileSize64, countStyle: .file)
            let used  = ByteCountFormatter.string(fromByteCount: usedStorageBytes, countStyle: .file)
            let quota = ByteCountFormatter.string(fromByteCount: storageQuotaBytes, countStyle: .file)
            storageAlert = String(localized: "Не удалось сохранить файл (\(fsize)): хранилище заполнено (\(used) из \(quota)).")
            return
        }

        let type = Message.MessageType(mime: mime)
        let rawExt = URL(fileURLWithPath: name).pathExtension
        let ext = rawExt.isEmpty ? "bin" : rawExt
        let msgId = UUID().uuidString
        let filename = "\(msgId).\(ext)"
        let destURL = nevodMediaDirectory.appendingPathComponent(filename)

        // Copy to nevod_media/ off-thread — kernel copy, no file content in RAM
        try await Task.detached(priority: .userInitiated) {
            try FileManager.default.copyItem(at: fileURL, to: destURL)
        }.value
        Self.protectFile(destURL)

        let msg = Message(id: msgId, chatId: contact.cellId, fromMe: true,
                          text: name, timestamp: Date(), status: .sent,
                          type: type, mediaData: nil, mediaMime: mime, mediaName: name,
                          mediaSize: fileSize, mediaFile: filename)
        append(message: msg)
        await transmit(msgId: msgId, to: contact)
    }

    // MARK: - Avatar

    /// Sets our own avatar (called from ProfileView's picker) and broadcasts it to every
    /// current contact as a disguised media send (see sendChunkedStream's headerTag: "avatar"
    /// — receiveChunk/deliverAvatar on the OTHER end never turns this into a chat
    /// bubble). Resized/compressed here rather than trusting whatever the picker handed back —
    /// a full-resolution photo has no business being sent as a profile picture.
    func setOwnAvatar(_ image: UIImage) async {
        guard let ownId = identity, let data = Self.resizedAvatarJPEG(image) else { return }
        let ownFile = nevodAvatarsDirectory.appendingPathComponent("\(MediaSafety.safeToken(ownId.cellId))\(Self.avatarSuffix).jpg")
        try? data.write(to: ownFile, options: .completeFileProtectionUnlessOpen)
        contactAvatars[ownId.cellId] = UIImage(data: data)

        let tmpURL = FileManager.default.temporaryDirectory.appendingPathComponent("\(UUID().uuidString).jpg")
        try? data.write(to: tmpURL)
        defer { try? FileManager.default.removeItem(at: tmpURL) }
        guard let c = client, c.isConnected else { return }
        // Best-effort per contact — one failing (offline, etc.) shouldn't block the rest, and
        // there's no per-contact retry queue for this (same tier as a normal message send:
        // if it fails, the recipient just doesn't have the new avatar yet, no error surfaced).
        for contact in contacts {
            try? await sendChunkedStream(fileURL: tmpURL, mime: "image/jpeg", name: nil,
                                         msgId: UUID().uuidString, contact: contact, client: c,
                                         headerTag: "avatar")
        }
    }

    /// Downscales to at most 512px on the long side and re-encodes as JPEG — a profile picture
    /// has no business being multi-megabyte, and every contact receives a full copy of this.
    private static func resizedAvatarJPEG(_ image: UIImage, maxDimension: CGFloat = 512,
                                          quality: CGFloat = 0.8) -> Data? {
        let size = image.size
        let scale = min(1, maxDimension / max(size.width, size.height))
        let targetSize = CGSize(width: size.width * scale, height: size.height * scale)
        let renderer = UIGraphicsImageRenderer(size: targetSize)
        let resized = renderer.image { _ in image.draw(in: CGRect(origin: .zero, size: targetSize)) }
        return resized.jpegData(compressionQuality: quality)
    }

    /// Lazy per-contact loader — call from a view's .onAppear/.task, mirrors MessageBubble's
    /// own cachedImage/.task(id:) pattern for message photos. No-ops if already cached in
    /// memory or if this cellId has no avatar file on disk yet.
    func loadAvatarIfCached(for cellId: String) {
        guard contactAvatars[cellId] == nil else { return }
        #if os(iOS)
        guard UIApplication.shared.isProtectedDataAvailable else {
            deferredAvatarIds.insert(cellId)
            return
        }
        #endif
        let safeId = MediaSafety.safeToken(cellId)
        guard !safeId.isEmpty else { return }
        let url = nevodAvatarsDirectory.appendingPathComponent("\(safeId)\(Self.avatarSuffix).jpg")
        if !FileManager.default.fileExists(atPath: url.path) {
            // Saved by a build before avatars were sanitized: the file holds the sender's
            // original bytes. Re-sanitize once (same path as a fresh receive) instead of
            // decoding it as is.
            let legacy = nevodAvatarsDirectory.appendingPathComponent("\(safeId).jpg")
            guard FileManager.default.fileExists(atPath: legacy.path) else { return }
            let clean = MediaSafety.sanitizedAvatarJPEG(from: legacy)
            try? FileManager.default.removeItem(at: legacy)
            guard let clean, (try? clean.write(to: url, options: .completeFileProtectionUnlessOpen)) != nil else { return }
        }
        guard let img = UIImage(contentsOfFile: url.path) else { return }
        contactAvatars[cellId] = img
    }

    /// Avatar files written after sanitizing (or by our own resize) carry this suffix, which
    /// tells them apart from older files holding a peer's original bytes — see loadAvatarIfCached.
    private static let avatarSuffix = "_s"

    private func sendChunkedStream(fileURL: URL, mime: String, name: String?,
                                   msgId: String, contact: Contact, client c: NevdClient,
                                   headerTag: String = "stream") async throws {
        let rawChunkSize = MediaSafety.streamChunkBytes   // 98304 bytes → 131072 base64 chars
        let fileSize = (try? fileURL.resourceValues(forKeys: [.fileSizeKey]))?.fileSize ?? 0
        let dataChunks = max(1, (fileSize + rawChunkSize - 1) / rawChunkSize)
        let totalChunks = dataChunks + 1       // +1 for header chunk at index 0

        // The message's own id, not a fresh UUID: "Повторить отправку" re-sends the same transfer,
        // so the receiver keeps the chunks it already has (duplicates are skipped by index) and
        // completes from either attempt. With a new id every retry started a second full copy
        // next to the first one still trickling in from the node's buffer — device logs
        // 2026-10-20: one 12 MB video in flight three times at once, nothing completed.
        let transferId = msgId
        messageProgress[msgId] = 0.0
        defer { messageProgress.removeValue(forKey: msgId) }

        // Chunk 0: metadata only, signals streaming format to receiver. headerTag is "stream"
        // for a normal chat media message, "avatar" for setOwnAvatar's broadcast — same framing
        // otherwise, see receiveChunk's header-chunk branch for the receiving side.
        let safeName = name.flatMap { $0.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) } ?? ""
        let headerBody = safeName.isEmpty ? "\(headerTag):\(mime)" : "\(headerTag):\(mime);name=\(safeName)"
        try await c.send(toCellId: contact.cellId, toNodeId: contact.nodeId ?? c.nodeId,
                         recipientEncPub: contact.encPub,
                         text: "chunk:\(transferId):0/\(totalChunks)/\(rawChunkSize)\n\(headerBody)",
                         type: "msg_chunk", fileData: true)

        // Data chunks: read rawChunkSize bytes at a time off MainActor, encode, send. The file is
        // opened once for the whole transfer: media files are protected "complete unless
        // open" (see protectFile), so a handle opened now keeps working if the phone gets
        // locked mid-send, while reopening it per chunk would fail.
        let reader = try ChunkReader(url: fileURL)
        defer { reader.close() }
        var sentBytes = 0
        for i in 1...dataChunks {
            let offset = UInt64(i - 1) * UInt64(rawChunkSize)
            let rcs = rawChunkSize
            let (raw, b64): (Data, String) = await Task.detached(priority: .userInitiated) {
                let chunk = reader.read(at: offset, length: rcs)
                return (chunk, chunk.base64EncodedString())
            }.value
            if raw.isEmpty && fileSize > 0 { throw NevdError.invalidData }

            let isLast = i == dataChunks
            // Only the last chunk is push-eligible (type "msg") — the node can't see
            // chunk index/total itself (E2E encrypted), so it relies on us to mark
            // every other fragment "msg_chunk" to avoid one push per chunk.
            try await c.send(toCellId: contact.cellId, toNodeId: contact.nodeId ?? c.nodeId,
                             recipientEncPub: contact.encPub,
                             text: "chunk:\(transferId):\(i)/\(totalChunks)/\(rawChunkSize)\n\(b64)",
                             id: isLast ? msgId : nil,
                             type: isLast ? "msg" : "msg_chunk", fileData: true)

            sentBytes += raw.count
            let p  = Double(sentBytes) / Double(max(1, fileSize))
            let nd = Int(p * 10)
            let pd = Int(Double(sentBytes - raw.count) / Double(max(1, fileSize)) * 10)
            if nd > pd || i == dataChunks { messageProgress[msgId] = p }
        }
    }

    func deleteMessage(_ message: Message) {
        let chatId = message.chatId
        // Diagnostic for the "handleAck NO MATCHING MESSAGE" mystery (see that log line's own
        // comment) — an in-flight ack landing after the message was deleted here would explain
        // it perfectly without any actual lookup bug; no way to tell those apart without this.
        nlog("deleteMessage msgId=\(message.msgId.prefix(8)) chatId=\(chatId.prefix(8)) status=\(message.status.rawValue)")
        if let file = message.mediaFile {
            try? FileManager.default.removeItem(at: mediaDirectory.appendingPathComponent(file))
        }
        modelContext.delete(message)
        try? modelContext.save()
        if !hasMessages(for: chatId) { chatIds.remove(chatId); saveChatIds() }
        messageSeq += 1
    }

    func deleteMessage(msgId: String, chatId: String) {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        if let msg = (try? modelContext.fetch(descriptor))?.first {
            nlog("deleteMessage msgId=\(msgId.prefix(8)) chatId=\(chatId.prefix(8)) status=\(msg.status.rawValue)")
            if let file = msg.mediaFile {
                try? FileManager.default.removeItem(at: mediaDirectory.appendingPathComponent(file))
            }
            modelContext.delete(msg)
            try? modelContext.save()
        }
        if !hasMessages(for: chatId) { chatIds.remove(chatId); saveChatIds() }
        messageSeq += 1
    }

    /// "Delete for everyone" — only ever called for a message that's ours (fromMe == true;
    /// the UI gates the action, this doesn't re-check). Unlike deleteMessage() above (hard
    /// delete, "delete for me"), this SOFT-deletes: the row stays so a "Сообщение удалено"
    /// placeholder can render where the bubble used to be, on both sides. No time limit, per
    /// the user's own choice — see project plan.
    func deleteForEveryone(msgId: String, chatId: String) {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        let matches = (try? modelContext.fetch(descriptor)) ?? []
        guard !matches.isEmpty else {
            nlog("deleteForEveryone NO MATCHING MESSAGE msgId=\(msgId.prefix(8))")
            return
        }
        // Multiple-row handling kept even though the duplicate-row theory (2026-09-12 device
        // logs: rows=1 every single time, 7/7) turned out NOT to be the cause — the real bug
        // was the Message.isRemoved rename right below (see its own doc comment: isDeleted
        // silently never persisted, name collision with NSManagedObject's built-in property of
        // the same name). Harmless to keep as defensive coverage regardless.
        if matches.count > 1 {
            nlog("deleteForEveryone DUPLICATE ROWS msgId=\(msgId.prefix(8)) count=\(matches.count)")
        }
        for msg in matches {
            if let file = msg.mediaFile {
                try? FileManager.default.removeItem(at: mediaDirectory.appendingPathComponent(file))
            }
            msg.isRemoved = true
            msg.text = ""
            msg.mediaFile = nil; msg.mediaMime = nil; msg.mediaName = nil; msg.mediaSize = nil
        }
        do {
            try modelContext.save()
            let verify = (try? modelContext.fetch(descriptor)) ?? []
            nlog("deleteForEveryone SAVED msgId=\(msgId.prefix(8)) rows=\(verify.count) allRemoved=\(verify.allSatisfy { $0.isRemoved })")
        } catch {
            nlog("deleteForEveryone SAVE FAILED msgId=\(msgId.prefix(8)) err=\(error)")
        }
        messageSeq += 1
        guard let c = client, let contact = contacts.first(where: { $0.cellId == chatId }) else { return }
        Task {
            try? await c.send(toCellId: chatId, toNodeId: contact.nodeId ?? c.nodeId,
                              recipientEncPub: contact.encPub, text: "delete:\(msgId)\n", type: "msg_silent")
        }
    }

    /// Applies a "delete:" signal received from the other party — mirrors deleteForEveryone's
    /// local mutation exactly (same soft-delete shape), just triggered by the wire instead of
    /// a local UI action. No fromMe check needed here: only the ORIGINAL sender's client would
    /// ever emit this signal in the first place (the UI only offers "delete for everyone" on
    /// your own messages), so by construction this only ever fires on a message that was
    /// theirs from this device's point of view.
    // A delete that arrived before its message — a node handed out the delete first and the
    // message stayed (2026-10-21). Applied when the message shows up, if it comes from the
    // same sender (see append). In memory only: the gap is seconds, not app launches.
    private var earlyDeletes: [String: String] = [:]   // msgId → sender cellId

    private func handleDeleteSignal(from: String, msgId: String) {
        nlog("handleDeleteSignal recv msgId=\(msgId.prefix(8))")
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        let matches = (try? modelContext.fetch(descriptor)) ?? []
        guard !matches.isEmpty else {
            nlog("handleDeleteSignal NO MATCHING MESSAGE msgId=\(msgId.prefix(8)) — kept until it arrives")
            if earlyDeletes.count > 500 { earlyDeletes.removeAll() }
            earlyDeletes[msgId] = String(from.split(separator: "@").first ?? Substring(from))
            return
        }
        // See deleteForEveryone's matching comment — duplicate rows weren't the cause, kept as
        // defensive coverage anyway.
        if matches.count > 1 {
            nlog("handleDeleteSignal DUPLICATE ROWS msgId=\(msgId.prefix(8)) count=\(matches.count)")
        }
        for msg in matches {
            if let file = msg.mediaFile {
                try? FileManager.default.removeItem(at: mediaDirectory.appendingPathComponent(file))
            }
            msg.isRemoved = true
            msg.text = ""
            msg.mediaFile = nil; msg.mediaMime = nil; msg.mediaName = nil; msg.mediaSize = nil
        }
        do {
            try modelContext.save()
            let verify = (try? modelContext.fetch(descriptor)) ?? []
            nlog("handleDeleteSignal SAVED msgId=\(msgId.prefix(8)) rows=\(verify.count) allRemoved=\(verify.allSatisfy { $0.isRemoved })")
        } catch {
            nlog("handleDeleteSignal SAVE FAILED msgId=\(msgId.prefix(8)) err=\(error)")
        }
        messageSeq += 1
    }

    /// Text messages only (UI gates this), only ever called on our own message. Mutates the
    /// existing row in place — the message's own text field holds the latest content, no
    /// separate edit-history is stored, just the isEdited flag for the "изменено" label.
    func editMessage(msgId: String, chatId: String, newText: String) {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        guard let msg = (try? modelContext.fetch(descriptor))?.first else { return }
        msg.text = newText
        msg.isEdited = true
        try? modelContext.save()
        messageSeq += 1
        guard let c = client, let contact = contacts.first(where: { $0.cellId == chatId }) else { return }
        Task {
            try? await c.send(toCellId: chatId, toNodeId: contact.nodeId ?? c.nodeId,
                              recipientEncPub: contact.encPub, text: "edit:\(msgId)\n\(newText)", type: "msg_silent")
        }
    }

    private func handleEditSignal(from: String, msgId: String, newText: String) {
        nlog("handleEditSignal recv msgId=\(msgId.prefix(8))")
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        guard let msg = (try? modelContext.fetch(descriptor))?.first else {
            nlog("handleEditSignal NO MATCHING MESSAGE msgId=\(msgId.prefix(8))")
            return
        }
        msg.text = newText
        msg.isEdited = true
        try? modelContext.save()
        messageSeq += 1
    }

    func isIdentityDeleted(cellId: String) -> Bool {
        contacts.first(where: { $0.cellId == cellId })?.identityDeleted == true
    }

    private func handleIdentityDeleted(from: String) {
        let cellId = String(from.split(separator: "@").first ?? Substring(from))
        guard let idx = contacts.firstIndex(where: { $0.cellId == cellId }) else { return }
        contacts[idx].identityDeleted = true
        saveContacts()
    }

    func deleteChat(chatId: String) {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.chatId == chatId })
        if let msgs = try? modelContext.fetch(descriptor) {
            for msg in msgs {
                if let file = msg.mediaFile {
                    try? FileManager.default.removeItem(at: mediaDirectory.appendingPathComponent(file))
                }
                modelContext.delete(msg)
            }
            try? modelContext.save()
        }
        chatIds.remove(chatId)
        saveChatIds()
        messageSeq += 1
    }

    private func markFailed(msgId: String, chatId: String) {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        if let msg = (try? modelContext.fetch(descriptor))?.first {
            msg.status = .failed
            try? modelContext.save()
            messageSeq += 1   // so the open chat redraws the bubble with its retry line
        }
    }

    // Applies an incoming ack ("offline"/"delivered"/"read") to the outgoing message it
    // references. Only ever moves status forward (see MessageStatus.rank) — a reordered or
    // duplicate ack can't undo further progress the message has already made.
    private func handleAck(msgId: String, status: String) {
        // Ack for a chunk/msg_silent packet — no message row behind it by design.
        if msgId.hasPrefix(NevdClient.untrackedIdPrefix) { return }
        nlog("handleAck recv msgId=\(msgId.prefix(8)) status=\(status)")
        let newStatus: Message.MessageStatus
        switch status {
        case "offline":   newStatus = .offline
        case "delivered": newStatus = .delivered
        case "read":      newStatus = .read
        // Sent by the node's router when the recipient cell doesn't exist there at all
        // (self-deregistered/identity reset, or never registered) — a terminal "this will
        // never be delivered", not "queued" like "offline". Without this case the message
        // just sat stuck at .sent forever: the node dropped it with zero feedback, no ack
        // of any kind ever arrived. See node/router.py's _notify_undeliverable.
        case "failed":    newStatus = .failed
        default:
            nlog("handleAck unknown status=\(status)")
            return
        }
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        guard let msg = (try? modelContext.fetch(descriptor))?.first else {
            // totalCount sanity-checks the fetch itself isn't the problem (an empty/broken
            // context would show 0 here) — if it's a normal nonzero number, the message for
            // THIS msgId specifically is genuinely gone (deleted — see deleteMessage's own
            // nlog, now logged too — or never actually saved), not a context-wide glitch.
            let totalCount = (try? modelContext.fetchCount(FetchDescriptor<Message>())) ?? -1
            nlog("handleAck NO MATCHING MESSAGE msgId=\(msgId.prefix(8)) totalMessagesInStore=\(totalCount)")
            return
        }
        // "failed" is terminal but NOT a forward-rank move (Message.MessageStatus gives it
        // rank 0, same as .sent) — bypass the rank check for it specifically, same as any
        // other forward transition, as long as the message hasn't already reached a real
        // confirmed state.
        guard msg.fromMe, msg.status != .failed,
              (newStatus == .failed ? msg.status.rank < Message.MessageStatus.delivered.rank
                                     : newStatus.rank > msg.status.rank) else {
            nlog("handleAck SKIP msgId=\(msgId.prefix(8)) fromMe=\(msg.fromMe) current=\(msg.status.rawValue) new=\(newStatus.rawValue)")
            return
        }
        nlog("handleAck APPLY msgId=\(msgId.prefix(8)) \(msg.status.rawValue) -> \(newStatus.rawValue)")
        msg.status = newStatus
        try? modelContext.save()
        messageSeq += 1
    }

    /// Mitigates a known "stuck offline forever" bug (see handleAck's two silent-drop paths
    /// above — a lost ack packet on reconnect, or the NO-MATCHING-MESSAGE lookup failure now
    /// being diagnosed) rather than fixing either root cause: when there's fresh, concrete
    /// evidence the other side's device is actually reachable and engaged, bump any of OUR OWN
    /// still-pending sent messages to them forward. Same rank-based, never-regress guard as
    /// handleAck itself, so this can never un-read an already-read message or resurrect a
    /// failed one — agreed with the user 2026-08-26.
    ///
    /// Two call sites, two different target statuses (user's own distinction): a connected call
    /// only proves the device was ONLINE at that moment (could be answered from the lock screen
    /// without the chat ever being opened) → .delivered. A new incoming message or reaction from
    /// them proves they were actually IN the chat → .read.
    private func bumpStuckSentMessages(chatId: String, to newStatus: Message.MessageStatus, reason: String) {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.chatId == chatId && $0.fromMe })
        guard let msgs = try? modelContext.fetch(descriptor) else { return }
        var changed = false
        for msg in msgs where msg.status != .failed && newStatus.rank > msg.status.rank {
            nlog("bumpStuckSentMessages msgId=\(msg.msgId.prefix(8)) \(msg.status.rawValue) -> \(newStatus.rawValue) reason=\(reason)")
            msg.status = newStatus
            changed = true
        }
        guard changed else { return }
        try? modelContext.save()
        messageSeq += 1
    }

    /// Call site: CallManager, once ICE actually connects (audio flowing) — see
    /// bumpStuckSentMessages's doc comment for why this maps to .delivered, not .read.
    func markReachableByCall(chatId: String) {
        bumpStuckSentMessages(chatId: chatId, to: .delivered, reason: "call connected")
    }

    /// bumpStuckSentMessages only reacts to a NEW event arriving after the fact — a message
    /// that got stuck BEFORE this feature existed, with the contact's replies already sitting
    /// right below it in history, never triggers it (confirmed on device 2026-08-26: exactly
    /// this case, rebuilding alone did not fix an already-stuck message). This is the
    /// retroactive counterpart, called once from ChatView.loadChat(): if there's already a
    /// message FROM them dated after one of OUR stuck ones, that's the same evidence standard
    /// bumpStuckSentMessages uses for a live incoming message, just read from history instead
    /// of from a live event.
    func reconcileStuckMessages(chatId: String) {
        let descriptor = FetchDescriptor<Message>(
            predicate: #Predicate { $0.chatId == chatId },
            sortBy: [SortDescriptor(\.timestamp)]
        )
        guard let msgs = try? modelContext.fetch(descriptor),
              let theirLatest = msgs.last(where: { !$0.fromMe })?.timestamp else { return }
        var changed = false
        for msg in msgs where msg.fromMe && msg.timestamp < theirLatest
                            && msg.status != .failed && Message.MessageStatus.read.rank > msg.status.rank {
            nlog("reconcileStuckMessages msgId=\(msg.msgId.prefix(8)) \(msg.status.rawValue) -> read (history)")
            msg.status = .read
            changed = true
        }
        guard changed else { return }
        try? modelContext.save()
        messageSeq += 1
    }

    // Applies an incoming reaction from the other party — always theirReaction, regardless of
    // whether the target message was originally ours or theirs (this is who's reacting, not
    // who sent the original text). emoji nil clears it (they tapped the same one again).
    private func handleReaction(from: String, msgId: String, emoji: String?) {
        nlog("handleReaction recv msgId=\(msgId.prefix(8)) emoji=\(emoji ?? "(clear)")")
        if isBlocked(String(from.split(separator: "@").first ?? Substring(from))) { return }
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.msgId == msgId })
        guard let msg = (try? modelContext.fetch(descriptor))?.first else {
            nlog("handleReaction NO MATCHING MESSAGE msgId=\(msgId.prefix(8))")
            return
        }
        msg.theirReaction = emoji
        // nil (they cleared their reaction) leaves nothing to draw attention to — only an
        // actual emoji marks the message as having an unseen reaction to pop on next open.
        msg.theirReactionSeen = (emoji == nil)
        // Reacting (or un-reacting) requires having actually been in the chat looking at this
        // message — see bumpStuckSentMessages's doc comment. msg.chatId, not a re-parse of
        // `from`, since we already have the fetched message right here.
        bumpStuckSentMessages(chatId: msg.chatId, to: .read, reason: "reaction received")
        try? modelContext.save()
        messageSeq += 1
    }

    /// Snapshot-then-clear, same idiom as markChatRead()/firstUnreadMsgId: caller must read
    /// which messages currently have an unseen reaction BEFORE calling this, since it flips
    /// them all to seen immediately.
    func unseenReactionMsgIds(for chatId: String) -> [String] {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate {
            $0.chatId == chatId && !$0.theirReactionSeen
        })
        return (try? modelContext.fetch(descriptor))?.map(\.msgId) ?? []
    }

    func markReactionsSeen(chatId: String) {
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate {
            $0.chatId == chatId && !$0.theirReactionSeen
        })
        guard let msgs = try? modelContext.fetch(descriptor), !msgs.isEmpty else { return }
        for msg in msgs { msg.theirReactionSeen = true }
        try? modelContext.save()
    }

    // Tells the sender of every unread incoming message in this chat that we've now seen it.
    // Call when a chat becomes visible and whenever new messages arrive while it's open.
    func markChatRead(chatId: String) {
        guard let c = client, c.isConnected else {
            nlog("markChatRead SKIP not connected chatId=\(chatId.prefix(8))")
            return
        }
        // Filter in Swift, not in #Predicate: negation + 3-way && in one predicate silently
        // failed to match anything on this SwiftData version (every other predicate in this
        // file sticks to plain ==, which is the one pattern confirmed reliable here).
        let descriptor = FetchDescriptor<Message>(predicate: #Predicate { $0.chatId == chatId })
        guard let all = try? modelContext.fetch(descriptor) else {
            nlog("markChatRead fetch FAILED chatId=\(chatId.prefix(8))")
            return
        }
        let unread = all.filter { !$0.fromMe && !$0.readAckSent }
        nlog("markChatRead chatId=\(chatId.prefix(8)) all=\(all.count) unread=\(unread.count)")
        guard !unread.isEmpty else { return }
        let targetNodeId = contacts.first(where: { $0.cellId == chatId })?.nodeId ?? c.nodeId
        for msg in unread {
            msg.readAckSent = true
            nlog("markChatRead sending read-ack msgId=\(msg.msgId.prefix(8)) toNodeId=\(targetNodeId.prefix(16))")
            c.sendReadReceipt(msgId: msg.msgId, toCellId: chatId, toNodeId: targetNodeId)
        }
        try? modelContext.save()
    }

    // MARK: - Contacts

    func resetIdentity() async {
        nlog("resetIdentity START cell=\(identity?.cellId.prefix(8) ?? "nil") contactsCount=\(contacts.count) chatIdsCount=\(chatIds.count) hasClient=\(client != nil)")
        // Best-effort: let every contact know this identity is gone before deregistering (which
        // disconnects) — otherwise a message to this cellId later just silently hangs "sent"
        // forever with no explanation. Must fully finish before deregister() disconnects, so
        // this awaits in a loop rather than firing off a detached Task.
        // Deliberately doesn't gate on c.isConnected — same lesson as sendJoinRequest's own
        // comment: that flag can read false even while the underlying socket is still usable
        // (or true while it's actually dead), so it was silently skipping this ENTIRE loop
        // with zero trace whenever the flag happened to be wrong at reset time. Confirmed on
        // device 2026-09-13: a contact never saw the other side greyed out after a reset —
        // no identity_deleted signal ever reached them, and nothing in the log said why.
        if let c = client {
            // Broader than just `contacts` (the formally added address book) — chatIds
            // covers every cellId with real message history, including a node member you
            // replied to without either side tapping "add contact." Notifying only
            // `contacts` silently missed anyone who never explicitly added THIS device
            // back on their own side: confirmed on device 2026-09-18 — a chat partner who
            // had exchanged real messages never saw the other side grey out after a reset,
            // because resetIdentity() never had a reason to address them at all.
            let recipients = Set(contacts.map { $0.cellId }).union(chatIds)
            for cellId in recipients {
                guard let contact = resolveContact(cellId: cellId) else {
                    nlog("resetIdentity notify SKIP unresolvable cellId=\(cellId.prefix(8))")
                    continue
                }
                do {
                    try await c.send(toCellId: contact.cellId, toNodeId: contact.nodeId ?? c.nodeId,
                                     recipientEncPub: contact.encPub, text: "identity_deleted:", type: "msg_silent")
                    nlog("resetIdentity notified cellId=\(contact.cellId.prefix(8))")
                } catch {
                    nlog("resetIdentity notify FAILED cellId=\(contact.cellId.prefix(8)) err=\(error)")
                }
            }
        }
        nlog("resetIdentity deregistering client=\(client != nil)")
        client?.deregister()
        client = nil
        cancellables.removeAll()
        IdentityStore.delete()
        // Scoped to the OLD identity's registration attempt — leaving these set would leak
        // into the fresh identity generated below: RootView shows SetupView's waiting/denied
        // screen purely off joinRequestPending/joinRequestDenied (2026-09-19 fix, see its own
        // comment), so a stale `true` here would show a phantom "waiting for approval" for a
        // request that was actually about this now-deleted identity, before the fresh one has
        // done anything at all. Found while adding that same RootView branch — never actually
        // observed on device yet (would need a reset mid-pending-request to trigger), fixed
        // proactively rather than waiting for a confusing report.
        nlog("resetIdentity clearing join-request state (was pending=\(joinRequestPending) denied=\(joinRequestDenied) inviteMode=\(pendingInviteMode ?? "nil"))")
        IdentityStore.joinRequestPending = false
        joinRequestPending = false
        joinRequestDenied = false
        pendingInviteMode = nil
        pendingJoinRequestNote = nil
        LocalDefaults.shared.removeObject(forKey: contactsKey)
        LocalDefaults.shared.removeObject(forKey: nodeMembersKey)
        SharedContactNames.remove()
        try? modelContext.delete(model: Message.self)
        try? modelContext.delete(model: CallLogEntry.self)
        try? modelContext.save()
        callLog = []
        try? FileManager.default.removeItem(at: mediaDirectory)
        Self.removeMessageStoresSetAside()
        contacts = []
        nodeMembers = []
        chatIds = []
        rejectedTransfers = []
        for (_, buf) in pendingStreams {
            try? buf.handle.close()
            try? FileManager.default.removeItem(at: buf.tmpURL)
        }
        pendingStreams = [:]
        connectionStatus = "disconnected"
        IdentityStore.displayName = ""
        IdentityStore.hasEverConnected = false
        // The user's AI keys go too: a reset hands the device to "nobody", and a key is billed
        // to whoever owns the provider account.
        AIKeyStore.deleteAll()
        LocalDefaults.shared.removeObject(forKey: aiBotsKey)
        aiStateVersion += 1
        // Land back in the open discovery segment (NodesView), not a bare setup form — browsing
        // is the universal fallback state, not something reserved for the very first launch.
        //
        // Also reset the server route/pinned fingerprint back to the app's own default —
        // neither is scoped to an identity, so they survive a reset untouched otherwise,
        // silently pre-filling SetupView's server field with whatever address ANY past
        // identity last used (a completely unrelated test server from days ago, in one
        // real case) for anyone reaching it via NodesView's generic "Start messaging"
        // button rather than a specific planet's "Join this node" (which overwrites this
        // anyway right before presenting the form). Confirmed on device 2026-09-19: a
        // fresh identity's setup form showed "home.nevod.network" — unreachable from that
        // network — and the connection attempt cycled "connecting…"/"error: no reachable
        // route" for a full minute with no indication anything was wrong, until the
        // address was manually corrected.
        IdentityStore.nodeRoutes = [IdentityStore.defaultNodeAddr]
        IdentityStore.nodeFingerprint = ""
        if let id = try? generateIdentity() {
            try? IdentityStore.save(id)
            identity = id
            nlog("resetIdentity generated fresh browsing identity cell=\(id.cellId.prefix(8))")
        } else {
            identity = nil
            nlog("resetIdentity generateIdentity FAILED — identity left nil")
        }
        isRegistered = false
        nlog("resetIdentity DONE isRegistered=\(isRegistered) hasEverConnected=\(IdentityStore.hasEverConnected)")
    }

    func addContact(_ contact: Contact) {
        guard contacts.first(where: { $0.cellId == contact.cellId }) == nil else {
            nlog("addContact SKIP already a contact cellId=\(contact.cellId.prefix(8))")
            return
        }
        contacts.append(contact); saveContacts()
        // Node members already see each other via "On this node" — the proactive
        // notice is only useful for genuinely external contacts (different node,
        // discovered via card/QR), so they don't have to wait for our first real
        // chat message to find out we added them.
        let isNodeMember = nodeMembers.contains(where: { $0.cellId == contact.cellId })
        nlog("addContact cellId=\(contact.cellId.prefix(8)) nodeId=\((contact.nodeId ?? "nil").prefix(16)) "
             + "isNodeMember=\(isNodeMember) clientConnected=\(client?.isConnected ?? false)")
        guard !isNodeMember, let c = client, c.isConnected else { return }
        let toNodeId = contact.nodeId ?? c.nodeId
        Task {
            do {
                try await c.sendContactAddNotice(toCellId: contact.cellId, toNodeId: toNodeId,
                                                 recipientEncPub: contact.encPub)
                nlog("addContact notice sent OK to=\(contact.cellId.prefix(8)) toNodeId=\(toNodeId.prefix(16))")
            } catch {
                nlog("addContact notice FAILED to=\(contact.cellId.prefix(8)) error=\(error)")
            }
        }
    }

    func updateContactAlias(cellId: String, alias: String) {
        guard let idx = contacts.firstIndex(where: { $0.cellId == cellId }) else { return }
        contacts[idx].alias = alias; saveContacts()
    }

    func removeContact(cellId: String) {
        contacts.removeAll { $0.cellId == cellId }; saveContacts()
    }

    private func loadContacts() {
        guard let data = LocalDefaults.shared.data(forKey: contactsKey),
              let loaded = try? JSONDecoder().decode([Contact].self, from: data) else { return }
        contacts = loaded
        syncContactsToSharedGroup()  // backfills the extension's copy for installs that
                                      // predate this feature — saveContacts() alone would
                                      // leave it stale until the next contact edit.
    }

    private func saveContacts() {
        guard let data = try? JSONEncoder().encode(contacts) else { return }
        LocalDefaults.shared.set(data, forKey: contactsKey)
        syncContactsToSharedGroup()
    }

    private func syncContactsToSharedGroup() {
        SharedContactNames.write(contacts)
    }

    // MARK: - Chat settings (sound toggle + "is locked" flag — passwords themselves live in
    // Keychain via ChatLockStore, never here)

    private func loadChatSettings() {
        guard let data = LocalDefaults.shared.data(forKey: chatSettingsKey),
              let loaded = try? JSONDecoder().decode([String: ChatSettings].self, from: data) else { return }
        chatSettings = loaded
    }

    private func saveChatSettings() {
        guard let data = try? JSONEncoder().encode(chatSettings) else { return }
        LocalDefaults.shared.set(data, forKey: chatSettingsKey)
    }

    func settings(for chatId: String) -> ChatSettings {
        chatSettings[chatId] ?? ChatSettings(chatId: chatId)
    }

    /// Updates the local flag, persists, and tells the node (which is what actually decides
    /// whether to include "sound" in the APNs payload — see node/push.py). Fire-and-forget,
    /// same as registerPushToken: no round-trip confirmation needed, and NevdClient already
    /// re-registers on reconnect for tokens; this preference is persisted server-side once
    /// received, so no equivalent resend-on-reconnect is needed here.
    func updateSoundEnabled(chatId: String, enabled: Bool) {
        var s = settings(for: chatId)
        s.soundEnabled = enabled
        chatSettings[chatId] = s
        saveChatSettings()
        client?.sendChatPrefs(peerCellId: chatId, soundEnabled: enabled)
    }

    func updateChatLock(chatId: String, isLocked: Bool) {
        var s = settings(for: chatId)
        s.isLocked = isLocked
        chatSettings[chatId] = s
        saveChatSettings()
    }

    // Cached so "On this node" chats don't flash empty on every app relaunch —
    // nodeMembers otherwise starts empty and only refills after fetchNodeMembers()
    // completes post-reconnect, which briefly looked like the chat had disappeared.
    private func loadNodeMembers() {
        guard let data = LocalDefaults.shared.data(forKey: nodeMembersKey),
              let loaded = try? JSONDecoder().decode([NodeMember].self, from: data) else { return }
        nodeMembers = loaded
    }

    private func saveNodeMembers() {
        guard let data = try? JSONEncoder().encode(nodeMembers) else { return }
        LocalDefaults.shared.set(data, forKey: nodeMembersKey)
    }

    // Same persisted-cache shape as nodeMembers above, but for the curator-signed verified-node
    // manifest (see NodeManifest.swift) — falls back to the bundled seed only if nothing has
    // ever been fetched live, so a live update survives relaunch even offline.
    private func loadVerifiedNodes() {
        if let data = LocalDefaults.shared.data(forKey: verifiedNodesKey),
           let decoded = try? JSONDecoder().decode([String: VerifiedNodeInfo].self, from: data),
           !decoded.isEmpty {
            verifiedNodes = decoded
            return
        }
        verifiedNodes = NodeManifest.loadBundled()
    }

    private func saveVerifiedNodes() {
        guard let data = try? JSONEncoder().encode(verifiedNodes) else { return }
        LocalDefaults.shared.set(data, forKey: verifiedNodesKey)
    }

    // MARK: - Node members

    func memberAsContact(_ member: NodeMember) -> Contact {
        contacts.first(where: { $0.cellId == member.cellId })
            ?? Contact(cellId: member.cellId, nodeAddr: IdentityStore.nodeAddr,
                       encPub: member.encPub, alias: member.displayName)
    }

    /// Used by ChatsListView to resolve pendingChatCellId (a bare cellId from a push
    /// notification's userInfo) into a navigable Contact — checks saved contacts first,
    /// then nodeMembers, same precedence as elsewhere in the app.
    func resolveContact(cellId: String) -> Contact? {
        if let c = contacts.first(where: { $0.cellId == cellId }) { return c }
        if let m = nodeMembers.first(where: { $0.cellId == cellId }) { return memberAsContact(m) }
        nlog("resolveContact MISS cellId=\(cellId.prefix(8)) contactsCount=\(contacts.count) "
             + "nodeMembersCount=\(nodeMembers.count)")
        return nil
    }

    /// Public node directory — not persisted (unlike nodeMembers, whose caching avoids a
    /// "flash empty" on relaunch for chat-relevant identity resolution); this is just an
    /// on-demand browse list, re-fetched whenever NodesView appears.
    func fetchPublicNodes() async {
        guard let nodes = try? await client?.getPublicNodes() else { return }
        publicNodes = nodes
    }

    /// Live refresh of the curator-signed bootstrap manifest — triggered from NodesView.refresh()
    /// on the same cadence as fetchPublicNodes(), not on its own timer. Best-effort: a failed
    /// fetch (offline, host down, malformed response) silently leaves verifiedNodes exactly as it
    /// was — never regresses to empty, never surfaces an error, matching this codebase's
    /// try?-heavy defensive style for non-critical metadata.
    func fetchVerifiedNodes() async {
        guard let fetched = await NodeManifest.fetchRemote() else { return }
        verifiedNodes = fetched
        saveVerifiedNodes()
    }

    // MARK: - Official accounts / impersonation (Guideline 1.2 prep)

    private func loadOfficialAccounts() {
        if let data = LocalDefaults.shared.data(forKey: officialAccountsKey),
           let decoded = try? JSONDecoder().decode([String: OfficialAccount].self, from: data) {
            officialAccounts = decoded
            return
        }
        officialAccounts = OfficialAccounts.loadBundled()
    }

    /// Same best-effort pattern as fetchVerifiedNodes — a failed fetch keeps what we have.
    func fetchOfficialAccounts() async {
        guard let fetched = await OfficialAccounts.fetchRemote() else { return }
        officialAccounts = fetched
        if let data = try? JSONEncoder().encode(fetched) {
            LocalDefaults.shared.set(data, forKey: officialAccountsKey)
        }
        showAdministratorWelcomeIfNeeded()
    }

    func isOfficial(_ cellId: String) -> Bool { officialAccounts[cellId.lowercased()] != nil }

    /// The administrator of the node this identity lives on, as a sendable contact — nil until
    /// that node's administrator is curator-signed into official.json (with its encryption
    /// key). Every node has its own built-in administrator cell whose operator answers from
    /// the node's admin panel, so a complaint goes to the administrator who can actually act
    /// on it — the user's own node. No signed administrator for this node → nil, and
    /// ReportSheet falls back to the abuse@ e-mail.
    var administratorContact: Contact? {
        guard let myNodeId = client?.nodeId.lowercased(), !myNodeId.isEmpty,
              let admin = officialAccounts.first(where: {
                  $0.value.role == "administrator" && $0.value.nodeId.lowercased() == myNodeId
              }),
              let encPub = Hex.decode(admin.value.encPub) else { return nil }
        return Contact(cellId: admin.key, nodeAddr: "", encPub: encPub, alias: admin.value.name,
                       nodeId: admin.value.nodeId)
    }

    /// Diagnostics without a Mail account (DiagnosticsView): the description as a normal
    /// message — it shows in the chat with the administrator and on the node's Обращения page —
    /// then the log itself as one untracked message, no chat bubble; the node stores it and
    /// links it in that thread.
    func sendDiagnosticsInApp(text: String, to admin: Contact) async throws -> Bool {
        guard let c = client, c.isConnected else { return false }
        guard try await send(text: text, to: admin) else { return false }
        let raw = (try? Data(contentsOf: NevLogger.shared.logFileURL)) ?? Data()
        let packed = try (raw.suffix(DiagnosticReport.inAppMaxLogBytes) as NSData).compressed(using: .zlib) as Data
        nlog("diagnostics in-app log raw=\(raw.count) packed=\(packed.count) to=\(admin.cellId.prefix(8))")
        try await c.send(toCellId: admin.cellId, toNodeId: admin.nodeId ?? c.nodeId,
                         recipientEncPub: admin.encPub,
                         text: DiagnosticReport.inAppPrefix + packed.base64EncodedString())
        return true
    }

    /// One-time greeting from this node's ✓ administrator, the first time this identity is
    /// connected to a node whose administrator is curator-signed. Created here rather than
    /// sent by the node, so it's in the user's own language (the node doesn't know it). A
    /// reply goes to the real administrator — the node's "Обращения" page — like any message
    /// to it. Called after both the member list and official.json arrive, whichever is last.
    private func showAdministratorWelcomeIfNeeded() {
        guard connectionStatus == "connected", let me = identity?.cellId,
              let admin = administratorContact, let nodeId = admin.nodeId, !nodeId.isEmpty,
              // Listed only once the node has admitted us (an invite-only node withholds the
              // member list until then) — and the chat needs it to show the partner.
              nodeMembers.contains(where: { $0.cellId == admin.cellId }) else { return }
        let key = "nevod.adminWelcome.\(me.prefix(16)).\(nodeId.lowercased().prefix(16))"
        guard !LocalDefaults.shared.bool(forKey: key) else { return }
        LocalDefaults.shared.set(true, forKey: key)
        nlog("administrator welcome shown node=\(nodeId.prefix(8))")
        append(message: Message(id: UUID().uuidString, chatId: admin.cellId, fromMe: false,
                                text: String(localized: "Здравствуйте! Я администратор этой ноды Nevod. Если что-то не работает или вы хотите сообщить о нарушении, напишите сюда — отвечает оператор ноды. Мы никогда не пишем по e-mail и никогда не просим ключи, пароли или коды."),
                                timestamp: Date(), status: .delivered))
    }

    /// A name that claims an official role (administrator, support, …) on an account that
    /// isn't in the curator-signed list — shown with a warning wherever the name appears.
    func looksLikeImpersonation(cellId: String, name: String) -> Bool {
        !isOfficial(cellId) && ReservedNames.isReserved(name)
    }

    // MARK: - Blocking (Guideline 1.2)

    func isBlocked(_ cellId: String) -> Bool { blockedCellIds.contains(cellId) }

    func setBlocked(_ cellId: String, _ blocked: Bool) {
        if blocked { blockedCellIds.insert(cellId) } else { blockedCellIds.remove(cellId) }
        LocalDefaults.shared.set(Array(blockedCellIds), forKey: blockedKey)
        nlog("setBlocked cell=\(cellId.prefix(8)) blocked=\(blocked)")
        var pending = pendingBlockSync
        pending[cellId] = blocked
        if client?.sendChatPrefs(peerCellId: cellId, blocked: blocked) == true {
            pending.removeValue(forKey: cellId)
        }
        pendingBlockSync = pending
        messageSeq += 1  // refresh chat list / open chat
    }

    private var pendingBlockSync: [String: Bool] {
        get { (LocalDefaults.shared.dictionary(forKey: pendingBlockSyncKey) as? [String: Bool]) ?? [:] }
        set { LocalDefaults.shared.set(newValue, forKey: pendingBlockSyncKey) }
    }

    private func flushPendingBlockSync() {
        var pending = pendingBlockSync
        for (cellId, blocked) in pending where client?.sendChatPrefs(peerCellId: cellId, blocked: blocked) == true {
            pending.removeValue(forKey: cellId)
        }
        pendingBlockSync = pending
    }

    private func fetchNodeMembers() async {
        guard let members = try? await client?.getGroupMembers() else { return }
        guard connectionStatus == "connected" else { return }
        let selfId = identity?.cellId ?? ""
        nodeMembers = members
            .filter { $0.cellId != selfId }
            .map { NodeMember(cellId: $0.cellId, encPub: $0.encPubkey, displayName: $0.displayName) }
        saveNodeMembers()
        // The home node's AI bots are members too: a bot opened from Contacts never went through
        // a planet (NodePlanetDetailView.handleTap), so the chat didn't know it was an AI bot —
        // no "Add AI key", and the bot's silent "ai-error:no_key:" showed as text (device test
        // 2026-10-19).
        if let cells = try? await client?.getNodeCells() {
            for cell in cells where !cell.aiProviders.isEmpty {
                registerAIBot(cellId: cell.cellId, providers: cell.aiProviders)
            }
        }
        // dismiss AddContactBanner if sender turned out to be a node member
        if let card = pendingCard, let contact = parseCard(card) {
            if nodeMembers.contains(where: { $0.cellId == contact.cellId }) {
                pendingCard = nil; pendingCardName = nil
            }
        }
        // The member list only comes back once the node has really admitted us (unlike the
        // optimistic "connected" status) — the right moment for a first-time greeting.
        showAdministratorWelcomeIfNeeded()
    }
}

/// One read handle shared by a whole chunked send — see sendChunkedStream. Reads happen one at
/// a time (each chunk is awaited before the next), so the handle is never used concurrently.
private final class ChunkReader: @unchecked Sendable {
    private let handle: FileHandle
    init(url: URL) throws { handle = try FileHandle(forReadingFrom: url) }
    func read(at offset: UInt64, length: Int) -> Data {
        guard (try? handle.seek(toOffset: offset)) != nil else { return Data() }
        return (try? handle.read(upToCount: length)) ?? Data()
    }
    func close() { try? handle.close() }
}
