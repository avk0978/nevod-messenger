import Foundation
import ImageIO
import SwiftData

struct Contact: Identifiable, Codable, Hashable {
    var id: String { cellId }
    var cellId:   String
    var nodeAddr: String
    var encPub:   Data
    var alias:    String
    // Optional (not just absent-defaulted) so Codable's synthesized decoder keeps
    // reading contacts saved before this field existed — nil means "unknown, treat
    // as living on our own node", which is exactly the old behavior.
    var nodeId: String? = nil
    // Same Optional-for-Codable-backcompat trick as nodeId above — true once this contact's
    // "identity_deleted:" signal has been received (they reset their identity). nil/false both
    // mean "still a live contact."
    var identityDeleted: Bool? = nil
}

/// Per-chat preferences, keyed by chatId (== the contact's cellId) rather than tied to a
/// saved Contact — mirrors chatIds' own independence from Contact existence, since a chat
/// can exist with someone who's only a nodeMember, never saved as a Contact. Chat lock
/// passwords themselves are NOT here — they live in Keychain via ChatLockStore; this struct
/// only holds the non-secret "is a lock configured" flag alongside the sound toggle.
struct ChatSettings: Codable {
    var chatId: String
    var soundEnabled: Bool = true
    var isLocked: Bool = false
}

@Model final class Message {
    @Attribute(.unique) var msgId: String
    var chatId:    String
    var fromMe:    Bool
    var text:      String
    var timestamp: Date
    var statusRaw: String
    var typeRaw:   String
    @Attribute(.externalStorage) var mediaData: Data?  // legacy: kept for old messages only
    var mediaMime: String?
    var mediaName: String?
    var mediaSize: Int?   // nil for messages saved before this field was added
    var mediaFile: String? // filename in nevod_media/; preferred over mediaData for new messages
    var readAckSent: Bool = false // incoming messages only: whether we've told the sender we read it
    var replyToMsgId: String? = nil // text messages only — msgId of the message this replies to
    // Explicit "render this in the Hirmos UCS font" flag (text messages only), set by the
    // sender's compose toggle and carried over the wire. Not derivable from the text itself —
    // OrtodoxKeyboard's Church Slavonic keys type plain ASCII/Cyrillic letters under the hood
    // (the font is what makes them LOOK like Church Slavonic on that keyboard's own keys), so
    // there's no Unicode range to sniff; which font to use has to travel as data, not be guessed.
    var churchFont: Bool = false
    // One reaction slot per side — this is a 1:1 chat, not a group, so there's no need for a
    // per-sender map. Either can be nil (no reaction) or a single emoji string. Re-picking the
    // same emoji clears it (toggle); picking a different one replaces it.
    var myReaction: String? = nil
    var theirReaction: String? = nil
    // Defaults true so existing/migrated rows never retroactively "pop" — only a reaction that
    // actually arrives after this field exists starts false. Flipped true by
    // AppStore.markReactionsSeen() (called from ChatView.loadChat(), same snapshot-before-mark
    // idiom as firstUnreadMsgId) once the chat has been opened with it visible — drives the
    // attention-grabbing pop-in MessageBubble plays on appear for a reaction you hadn't
    // noticed yet, not just one arriving live while the chat's already open.
    var theirReactionSeen: Bool = true
    // Soft-delete — the row stays (so a "Сообщение удалено" placeholder can render where the
    // bubble used to be) but text/media fields are cleared. Set either locally ("delete for
    // me", pre-existing deleteMessage()) or via the delete: wire signal ("delete for everyone",
    // see AppStore.deleteForEveryone/handleDeleteSignal) — same flag either way, the UI doesn't
    // need to distinguish which.
    //
    // Named isRemoved, NOT isDeleted (2026-09-12): a stored property literally named
    // `isDeleted` on an @Model class silently never persisted — every save()/re-fetch round
    // trip on a real device came back with it still false while sibling fields (text,
    // mediaFile) in the exact same save DID persist correctly. That collides with
    // NSManagedObject's own built-in `isDeleted` (Core Data still underlies SwiftData) —
    // the framework's reserved meaning ("marked for deletion from the context") apparently
    // wins over a user @Model attribute of the same name. Confirmed reproducible 7/7 times
    // across two devices before renaming.
    var isRemoved: Bool = false
    // Text messages only (see AppStore.editMessage) — set when this message's text was replaced
    // via the edit: wire signal after it was originally sent/received. Purely a display flag
    // ("изменено" label next to the timestamp); the message's own text field already holds the
    // latest edited content, there's no separate edit-history stored.
    var isEdited: Bool = false

    var status: MessageStatus {
        get { MessageStatus(rawValue: statusRaw) ?? .sent }
        set { statusRaw = newValue.rawValue }
    }

    var type: MessageType {
        get { MessageType(rawValue: typeRaw) ?? .text }
        set { typeRaw = newValue.rawValue }
    }

    // Ordering matters: handleAck() only ever advances a message forward along this line,
    // never lets a late/reordered ack regress it (e.g. a stray "offline" notice arriving
    // after "delivered" must not undo it).
    enum MessageStatus: String {
        case sent, offline, delivered, read, failed

        var rank: Int {
            switch self {
            case .sent: return 0
            case .offline: return 1
            case .delivered: return 2
            case .read: return 3
            case .failed: return 0
            }
        }
    }
    enum MessageType:   String {
        case text, image, audio, file, video

        /// Single source of truth for "what kind of bubble does this MIME get" — used on both
        /// the send and receive paths. An older build receiving video/* has no .video case and
        /// falls back to .file (a plain attachment card), so this is wire-compatible.
        init(mime: String) {
            if mime.hasPrefix("image/") { self = .image }
            else if mime.hasPrefix("audio/") { self = .audio }
            else if mime.hasPrefix("video/") { self = .video }
            else { self = .file }
        }
    }

    init(id: String, chatId: String, fromMe: Bool, text: String,
         timestamp: Date, status: MessageStatus,
         type: MessageType = .text, mediaData: Data? = nil,
         mediaMime: String? = nil, mediaName: String? = nil,
         mediaSize: Int? = nil, mediaFile: String? = nil,
         replyToMsgId: String? = nil, churchFont: Bool = false) {
        self.msgId     = id
        self.chatId    = chatId
        self.fromMe    = fromMe
        self.text      = text
        self.timestamp = timestamp
        self.statusRaw = status.rawValue
        self.typeRaw   = type.rawValue
        self.mediaData = mediaData
        self.mediaMime = mediaMime
        self.mediaName = mediaName
        self.mediaSize = mediaSize
        self.mediaFile = mediaFile
        self.replyToMsgId = replyToMsgId
        self.churchFont = churchFont
    }
}

// One row in the "Calls" tab — written locally by CallManager.reset() at the end of every
// call (see AppStore.logCall). No network sync: each device independently knows its own
// side of a call (dialed out and got no answer; received an offer and either answered or
// didn't), so there's nothing to reconcile between devices.
@Model final class CallLogEntry {
    @Attribute(.unique) var id: String
    var cellId: String
    var isOutgoing: Bool
    var timestamp: Date
    var durationSecs: Int
    var outcomeRaw: String
    var isVideo: Bool = false  // defaulted so existing rows (pre-video-calls) migrate cleanly

    enum Outcome: String { case answered, missed }

    var outcome: Outcome {
        get { Outcome(rawValue: outcomeRaw) ?? .missed }
        set { outcomeRaw = newValue.rawValue }
    }

    init(id: String, cellId: String, isOutgoing: Bool, timestamp: Date,
         durationSecs: Int, outcome: Outcome, isVideo: Bool = false) {
        self.id = id
        self.cellId = cellId
        self.isOutgoing = isOutgoing
        self.timestamp = timestamp
        self.durationSecs = durationSecs
        self.outcomeRaw = outcome.rawValue
        self.isVideo = isVideo
    }
}

// MARK: - Schema versions (stage 4, 2026-10-16): the message store is MIGRATED, never wiped
//
// V1 = the schema the first App Store release ships with: the top-level Message and
// CallLogEntry above, exactly as they are. The store on a phone only ever moves forward
// through NevodMigrationPlan — before this, a schema change deleted the whole history.
//
// To change a stored model later (Apple's documented way):
// 1. Copy the CURRENT Message and CallLogEntry class bodies verbatim into NevodSchemaV1 as
//    nested @Model classes (the frozen V1 — never edited again) and list those in V1.models.
// 2. Make the change on the top-level classes and add NevodSchemaV2 listing them.
// 3. Add the V1→V2 stage to NevodMigrationPlan: .lightweight for an added property with a
//    default or optional, a removed one, or a rename via @Attribute(originalName: "old");
//    .custom only when values must be computed. Then test on a device: install the old build,
//    write history, update — the history must be there.
// Never rename a stored property without @Attribute(originalName:), and never name one after
// an NSManagedObject property (isDeleted — see Message.isRemoved).
enum NevodSchemaV1: VersionedSchema {
    static var versionIdentifier: Schema.Version { Schema.Version(1, 0, 0) }
    static var models: [any PersistentModel.Type] { [Message.self, CallLogEntry.self] }
}

enum NevodMigrationPlan: SchemaMigrationPlan {
    static var schemas: [any VersionedSchema.Type] { [NevodSchemaV1.self] }
    static var stages: [MigrationStage] { [] }
}

// Lightweight view-model — Sendable, contains NO binary data.
// Used as the data source for the chat list so SwiftData never faults
// (loads mediaData) during list rendering or initial fetch.
struct MessageViewData: Identifiable, Sendable {
    var id: String { msgId }
    let msgId: String
    let chatId: String
    let fromMe: Bool
    let text: String
    let timestamp: Date
    let statusRaw: String
    let typeRaw: String
    let mediaName: String?
    let mediaSize: Int?
    let mediaFile: String?  // filename in nevod_media/ — non-nil for all new messages
    let replyToMsgId: String?
    let churchFont: Bool
    let myReaction: String?
    let theirReaction: String?
    let theirReactionSeen: Bool
    let isRemoved: Bool
    let isEdited: Bool

    var status: Message.MessageStatus { Message.MessageStatus(rawValue: statusRaw) ?? .sent }
    var type: Message.MessageType    { Message.MessageType(rawValue: typeRaw) ?? .text }
}

extension Message {
    func toViewData() -> MessageViewData {
        MessageViewData(msgId: msgId, chatId: chatId, fromMe: fromMe, text: text,
                        timestamp: timestamp, statusRaw: statusRaw, typeRaw: typeRaw,
                        mediaName: mediaName, mediaSize: mediaSize, mediaFile: mediaFile,
                        replyToMsgId: replyToMsgId, churchFont: churchFont,
                        myReaction: myReaction, theirReaction: theirReaction,
                        theirReactionSeen: theirReactionSeen,
                        isRemoved: isRemoved, isEdited: isEdited)
    }
}


// Not actor-isolated: global computed var, callable from any Task or thread context.
// FileManager directory creation is thread-safe.
var nevodMediaDirectory: URL {
    let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)
        .first ?? URL(fileURLWithPath: NSTemporaryDirectory())
    let dir = base.appendingPathComponent("nevod_media")
    try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    return dir
}

// Separate from nevodMediaDirectory deliberately — avatars are one small file PER CONTACT
// (keyed by cellId, overwritten on change, never accumulate history), not one file per
// message; a dedicated directory keeps that lookup-by-cellId pattern clean regardless of
// nevod_media/'s own per-msgId naming. Note: AppStore.usedStorageBytes walks the WHOLE
// Application Support tree (not just nevod_media/), so this directory's files still count
// toward the storage-quota total shown in Profile — deliberately not excluded, since avatar
// files are tiny (a resized JPEG per contact) against a multi-hundred-MB quota floor; not
// worth special-casing the quota walk for.
var nevodAvatarsDirectory: URL {
    let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)
        .first ?? URL(fileURLWithPath: NSTemporaryDirectory())
    let dir = base.appendingPathComponent("nevod_avatars")
    try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    return dir
}

struct NodeMember: Identifiable, Codable {
    var id: String { cellId }
    let cellId: String
    let encPub: Data
    let displayName: String
}

// Card format: "cellId@nodeAddr|nodeId|hexEncPub" (3-part, current) or the older
// "cellId@nodeAddr|hexEncPub" (2-part — no node_id, predates cross-node contacts).
// nodeAddr is a display/reconnect hint; nodeId is the actual routing key the wire
// protocol needs ("cellId@nodeId" — see AppStore's send paths), which is why old
// 2-part cards decode to nodeId=nil rather than being rejected outright.
func parseCard(_ card: String) -> Contact? {
    let parts = card.split(separator: "|", maxSplits: 2, omittingEmptySubsequences: false)
    guard parts.count == 2 || parts.count == 3 else { return nil }
    let atParts = parts[0].split(separator: "@", maxSplits: 1)
    guard atParts.count == 2 else { return nil }
    let encPubHex = parts.count == 3 ? parts[2] : parts[1]
    guard let encPub = Hex.decode(String(encPubHex)) else { return nil }
    let nodeId = parts.count == 3 ? String(parts[1]) : nil
    return Contact(cellId: String(atParts[0]), nodeAddr: String(atParts[1]), encPub: encPub,
                   alias: "", nodeId: nodeId)
}

func formatCard(identity: NevdIdentity, nodeAddr: String, nodeId: String) -> String {
    "\(identity.cellId)@\(nodeAddr)|\(nodeId)|\(Hex.encode(identity.encPub))"
}

// MARK: - Contact-add notice

/// Wire-text prefix for a proactive "I just added you as a contact" notice — sent
/// once, right when addContact() runs, instead of only letting the recipient
/// auto-discover the sender whenever their first real chat message happens to
/// arrive. Rides the same envelope as a normal text send (card: line still gets
/// auto-prepended by NevdClient.send), so the recipient gets the sender's card for
/// free; the prefix just tells deliverMessage to surface a system prompt instead of
/// a chat bubble. Everything after the prefix is the sender's display name.
let contactAddNoticePrefix = "notify:contact_added:"

// MARK: - BYOK AI bots

/// Providers a BYOK bot can run on with the user's own key — raw values match
/// node/ai_providers.py and the node's published-cell "ai_providers" list.
enum AIProvider: String, CaseIterable, Identifiable {
    case anthropic, openai, gemini
    var id: String { rawValue }
    /// Product names, the same in every language.
    var displayName: String {
        switch self {
        case .anthropic: return "Claude"
        case .openai: return "ChatGPT"
        case .gemini: return "Gemini"
        }
    }
    /// Company that processes the messages — named in the consent text.
    var company: String {
        switch self {
        case .anthropic: return "Anthropic"
        case .openai: return "OpenAI"
        case .gemini: return "Google"
        }
    }
    /// Where the user creates a key in their own account.
    var keyPageURL: URL {
        switch self {
        case .anthropic: return URL(string: "https://console.anthropic.com/settings/keys")!
        case .openai: return URL(string: "https://platform.openai.com/api-keys")!
        case .gemini: return URL(string: "https://aistudio.google.com/apikey")!
        }
    }
}

/// Wire lines between the app and a BYOK bot, inside the E2E payload after the card: line —
/// must match node/bot.py byte-for-byte.
enum AIWire {
    static let keyPrefix = "ai-key:"                    // + provider:key\n, on every message
    static let checkPrefix = "ai-check:"                // + provider:key, silent
    static let checkResultPrefix = "ai-check-result:"   // + provider:code, silent, from the bot
    static let errorPrefix = "ai-error:"                // + code:provider, silent, from the bot
}

// MARK: - Invite code

/// Strips anything that isn't a letter/digit, uppercases, caps at 8 chars, and
/// re-inserts the "XXXX-XXXX" dash — lets a TextField auto-format as the user types
/// instead of requiring them to type the dash themselves.
func formatInviteCode(_ raw: String) -> String {
    let cleaned = raw.uppercased().filter { $0.isLetter || $0.isNumber }
    let capped = String(cleaned.prefix(8))
    guard capped.count > 4 else { return capped }
    let splitIndex = capped.index(capped.startIndex, offsetBy: 4)
    return String(capped[..<splitIndex]) + "-" + String(capped[splitIndex...])
}

// MARK: - Cell invite token (bundled address + TLS fingerprint + code)

struct CellInviteToken: Equatable {
    let address: String
    let fingerprint: String
    let code: String
}

/// Combined one-tap invite format: "ADDRESS|SHA256_FINGERPRINT|CODE" — mirrors the
/// node-invite-token format already used for node-to-node joins. Lets a QR/shared
/// link carry which node to connect to (and its self-signed cert's fingerprint,
/// since a node without a CA-issued cert in front of it needs manual pinning —
/// see NevdClient's pinnedFingerprint) alongside the invite code itself, so the
/// recipient doesn't have to know or type a server address at all. A bare
/// "XXXX-XXXX" code has no "|" in it, so callers can tell the two apart first.
/// The fingerprint segment may be empty — that means "no pinning needed, use
/// normal system CA trust" (a node fronted by a reverse proxy with a real
/// certificate, e.g. prod's nginx), as opposed to a bare code where there's no
/// address at all.
func parseCellInviteToken(_ raw: String) -> CellInviteToken? {
    var trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
    if let unwrapped = cellInviteTokenFromLink(trimmed) { trimmed = unwrapped }
    let parts = trimmed.split(separator: "|", maxSplits: 2, omittingEmptySubsequences: false)
    guard parts.count == 3 else { return nil }
    let address = String(parts[0]), fingerprint = String(parts[1]), code = String(parts[2])
    guard !address.isEmpty, !code.isEmpty else { return nil }
    return CellInviteToken(address: address, fingerprint: fingerprint, code: code)
}

func formatCellInviteToken(address: String, fingerprint: String, code: String) -> String {
    "\(address)|\(fingerprint)|\(code)"
}

/// Link form of the token, for QR codes and sharing: the phone's own camera opens an https
/// link, while a bare token only worked from the scanner inside Nevod (device test
/// 2026-10-16). The token sits in the #fragment, so nevod.network's web server never sees it;
/// the /join/ page passes it on as nevod://join?t=… (see node/protocol.py make_cell_invite_link).
let cellInviteLinkBase = "https://nevod.network/join/#t="

func cellInviteLink(token: String) -> String {
    var allowed = CharacterSet.alphanumerics
    allowed.insert(charactersIn: "-._~")
    return cellInviteLinkBase + (token.addingPercentEncoding(withAllowedCharacters: allowed) ?? token)
}

/// The token inside either link form — https://nevod.network/join/#t=TOKEN (scanned or pasted)
/// or nevod://join?t=TOKEN (opened from the /join/ page) — or nil if `raw` is neither.
func cellInviteTokenFromLink(_ raw: String) -> String? {
    guard let url = URL(string: raw) else { return nil }
    let query: String?
    if url.scheme == "nevod", url.host == "join" {
        query = url.query
    } else if url.scheme == "https", url.host == "nevod.network", url.path.hasPrefix("/join") {
        query = url.fragment
    } else {
        return nil
    }
    guard let query else { return nil }
    for pair in query.split(separator: "&") where pair.hasPrefix("t=") {
        return String(pair.dropFirst(2)).removingPercentEncoding
    }
    return nil
}

// MARK: - Media message encoding/decoding

struct MediaBody {
    let data: Data
    let mime: String
    let name: String?
    var type: Message.MessageType { Message.MessageType(mime: mime) }
}

/// Parses a data-URL body back into MediaBody, or nil if it's plain text.
func decodeMediaBody(_ body: String) -> MediaBody? {
    guard body.hasPrefix("data:") else { return nil }
    let inner = String(body.dropFirst(5))
    guard let commaIdx = inner.firstIndex(of: ",") else { return nil }
    let header = String(inner[inner.startIndex..<commaIdx])
    let b64    = String(inner[inner.index(after: commaIdx)...])
    // .ignoreUnknownCharacters handles newlines browsers insert every 76 chars
    guard let data = Data(base64Encoded: b64, options: .ignoreUnknownCharacters) else { return nil }

    var parts = header.split(separator: ";").map(String.init)
    let mime  = parts.removeFirst()
    var name: String? = nil
    for part in parts {
        if part.hasPrefix("name=") {
            name = String(part.dropFirst(5))
                .removingPercentEncoding ?? String(part.dropFirst(5))
        }
    }
    return MediaBody(data: data, mime: MediaSafety.safeMime(claimed: mime, header: data.prefix(16)), name: name)
}

// MARK: - Incoming media safety
//
// Everything a peer sends is untrusted input. The system image/video decoders are the usual
// target of "zero-click" exploits (a crafted file that is parsed automatically, before the user
// taps anything), so incoming media is checked by its actual bytes before anything decodes it:
// - a claimed image/audio/video mime is kept only if the file's signature matches a format we
//   actually expect; otherwise it becomes application/octet-stream — shown as a plain file
//   bubble, never decoded inline (it can still be opened by an explicit tap);
// - avatars are never shown as received: dimensions are read from the header only, then the
//   image is redrawn into a small thumbnail and re-encoded as our own JPEG;
// - names that end up in file paths are reduced to a safe character set.
enum MediaSafety {
    /// Largest incoming file we accept. The sender caps attachments at 50 MB (ChatView's
    /// maxFileSizeBytes); the margin covers encoding overhead.
    static let maxIncomingFileBytes = 60 * 1024 * 1024
    /// Raw bytes per streamed data chunk (see AppStore.sendChunkedStream): 128 KB of base64 on
    /// the wire. A call signal written after a chunk waits for at most that much to go out —
    /// with 512 KB chunks a hangup sat 10–16 s behind a video (device logs 2026-10-21).
    static let streamChunkBytes = 98_304
    /// What builds before 2026-10-21 used; their chunk lines ("i/total") don't name a size.
    static let legacyStreamChunkBytes = 393_216
    static func maxStreamDataChunks(slot: Int) -> Int { (maxIncomingFileBytes + slot - 1) / slot }
    /// An avatar fits in this many chunks of `slot` bytes.
    static func avatarMaxChunks(slot: Int) -> Int { (maxAvatarBytes + slot - 1) / slot }
    /// Transfers being assembled at once, per kind — a flood of unfinished headers can't pile up.
    static let maxPendingTransfers = 16

    static let maxAvatarBytes = 512 * 1024
    static let maxAvatarSourcePixels = 4096
    static let avatarPixels = 256

    private enum Kind { case jpeg, png, gif, heif, isoVideo, isoAudio, other }

    private static func sniff(_ h: Data) -> Kind {
        let b = [UInt8](h.prefix(16))
        if b.count >= 3, b[0] == 0xFF, b[1] == 0xD8, b[2] == 0xFF { return .jpeg }
        if b.count >= 8, b[0..<8] == [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A] { return .png }
        if b.count >= 6, let s = String(bytes: b[0..<6], encoding: .ascii), s == "GIF87a" || s == "GIF89a" { return .gif }
        // ISO base media file (MP4 / MOV / M4A / HEIF): bytes 4..7 = "ftyp", 8..11 = major brand
        if b.count >= 12, String(bytes: b[4..<8], encoding: .ascii) == "ftyp",
           let brand = String(bytes: b[8..<12], encoding: .ascii)?.lowercased() {
            if ["heic", "heix", "heim", "heis", "hevc", "hevx", "mif1", "msf1", "avif"].contains(brand) { return .heif }
            if brand.hasPrefix("m4a") || brand.hasPrefix("m4b") { return .isoAudio }
            return .isoVideo
        }
        return .other
    }

    /// The mime to store and render with, given what the sender claimed and the file's first bytes.
    static func safeMime(claimed: String, header: Data) -> String {
        let kind = sniff(header)
        let c = claimed.lowercased()
        let ok: Bool
        if c.hasPrefix("image/") { ok = [Kind.jpeg, .png, .gif, .heif].contains(kind) }
        else if c.hasPrefix("video/") { ok = kind == .isoVideo }
        else if c.hasPrefix("audio/") { ok = kind == .isoAudio || kind == .isoVideo }
        else { return isPlainMime(claimed) ? claimed : "application/octet-stream" }
        if !ok { nlog("MediaSafety: claimed \(claimed) does not match content — treated as a plain file") }
        return ok ? claimed : "application/octet-stream"
    }

    static func safeMime(claimed: String, fileURL: URL) -> String {
        guard let h = try? FileHandle(forReadingFrom: fileURL) else { return "application/octet-stream" }
        defer { try? h.close() }
        return safeMime(claimed: claimed, header: (try? h.read(upToCount: 16)) ?? Data())
    }

    private static let tokenChars = Set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")

    private static func isPlainMime(_ m: String) -> Bool {
        let parts = m.split(separator: "/", omittingEmptySubsequences: false)
        return m.count <= 100 && parts.count == 2
            && parts.allSatisfy { !$0.isEmpty && $0.allSatisfy { tokenChars.contains($0) || $0 == "." || $0 == "+" } }
    }

    /// Letters, digits, "-" and "_" only — for ids and extensions that become part of a file name.
    static func safeToken(_ s: String, maxLength: Int = 80) -> String {
        String(s.filter { tokenChars.contains($0) }.prefix(maxLength))
    }

    static func safeExtension(_ ext: String) -> String {
        let e = safeToken(ext, maxLength: 10).lowercased()
        return e.isEmpty ? "bin" : e
    }

    /// Received avatar file -> our own small JPEG, or nil if it isn't a plain, reasonably sized
    /// JPEG/PNG. The original bytes are only ever touched by ImageIO's thumbnail path with the
    /// pixel size checked first from the header.
    static func sanitizedAvatarJPEG(from url: URL) -> Data? {
        guard let size = (try? url.resourceValues(forKeys: [.fileSizeKey]))?.fileSize,
              size > 0, size <= maxAvatarBytes,
              let data = try? Data(contentsOf: url) else { return nil }
        return sanitizedAvatarJPEG(data: data)
    }

    static func sanitizedAvatarJPEG(data: Data) -> Data? {
        let kind = sniff(data)
        guard kind == .jpeg || kind == .png, data.count <= maxAvatarBytes else { return nil }
        let opts = [kCGImageSourceShouldCache: false] as CFDictionary
        guard let src = CGImageSourceCreateWithData(data as CFData, opts),
              CGImageSourceGetCount(src) == 1,
              let props = CGImageSourceCopyPropertiesAtIndex(src, 0, opts) as? [CFString: Any],
              let w = props[kCGImagePropertyPixelWidth] as? Int,
              let h = props[kCGImagePropertyPixelHeight] as? Int,
              w > 0, h > 0, w <= maxAvatarSourcePixels, h <= maxAvatarSourcePixels else { return nil }
        let thumbOpts: [CFString: Any] = [kCGImageSourceCreateThumbnailFromImageAlways: true,
                         kCGImageSourceCreateThumbnailWithTransform: true,
                         kCGImageSourceShouldCacheImmediately: true,
                         kCGImageSourceThumbnailMaxPixelSize: avatarPixels]
        guard let thumb = CGImageSourceCreateThumbnailAtIndex(src, 0, thumbOpts as CFDictionary) else { return nil }
        let out = NSMutableData()
        guard let dest = CGImageDestinationCreateWithData(out as CFMutableData, "public.jpeg" as CFString, 1, nil) else { return nil }
        CGImageDestinationAddImage(dest, thumb, [kCGImageDestinationLossyCompressionQuality: 0.85] as CFDictionary)
        guard CGImageDestinationFinalize(dest) else { return nil }
        return out as Data
    }
}
