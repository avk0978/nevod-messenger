import Foundation

// App Store Guideline 1.2 (user-generated content) groundwork, 2026-09-28: reserved-name
// look-alike detection, the curator-signed "official account" list, and the abuse-report
// email. Blocking itself lives in AppStore (blockedCellIds) + the node (chat_blocks).

/// Mirror of node/names.py — keep the stems and the folding in sync with it. The node
/// refuses NEW registrations with these names (unless official); this client-side copy flags
/// look-alikes coming from nodes that don't run that check, or names registered before it
/// existed, so an impostor "administrator" gets a visible warning either way.
enum ReservedNames {
    private static let stems = [
        "administrator", "admin", "moderator", "support", "nevod", "registrar", "official",
        "security", "abuse",
        "администратор", "админ", "адмін", "модератор", "поддержка", "підтримка", "невод",
        "регистратор", "реєстратор", "официальный", "офіційний", "безопасность",
    ]

    private static let confusables: [Character: Character] = [
        "а": "a", "в": "b", "е": "e", "ё": "e", "к": "k", "м": "m", "н": "h", "о": "o",
        "р": "p", "с": "c", "т": "t", "у": "y", "х": "x", "і": "i", "ї": "i", "ј": "j",
        "ѕ": "s", "ԁ": "d", "ɡ": "g", "ո": "n",
        "α": "a", "β": "b", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p",
        "τ": "t", "υ": "u", "χ": "x",
        "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "@": "a", "$": "s",
        "!": "i", "|": "i", "l": "i",
    ]

    private static let foldedStems: [String] = stems.map(fold)

    static func fold(_ name: String) -> String {
        // NFKC first (collapses styled/full-width letters like 𝐚𝐝𝐦𝐢𝐧), then lowercase,
        // then look-alikes → Latin, then drop accents and everything that isn't a letter.
        let lowered = name.precomposedStringWithCompatibilityMapping.lowercased()
        let mapped = String(lowered.map { confusables[$0] ?? $0 })
        let scalars = mapped.decomposedStringWithCanonicalMapping.unicodeScalars.filter {
            $0.properties.generalCategory != .nonspacingMark && $0.properties.isAlphabetic
        }
        return String(String.UnicodeScalarView(scalars))
    }

    static func isReserved(_ name: String) -> Bool {
        let folded = fold(name)
        guard !folded.isEmpty else { return false }
        return foldedStems.contains { folded.contains($0) }
    }
}

/// Curator-signed list of official Nevod accounts (the "administrator" account that answers
/// abuse@/support@/privacy@ mail — in the app only, never by email). Same trust model as
/// NodeManifest: HTTPS is just transport, each entry's Ed25519 signature by the offline
/// curator key is what makes the badge meaningful. Signed with
/// `python -m node.curator_sign sign-official`, published by deploy_manifest.sh.
/// One verified official account. encPub/nodeId are present for the administrator (in-app
/// complaints are encrypted to encPub and routed to nodeId) and are covered by the signature.
struct OfficialAccount: Codable, Equatable {
    let role: String
    let name: String
    let encPub: String
    let nodeId: String
}

enum OfficialAccounts {
    static let remoteURL = URL(string: "https://node1.nevod.network/official.json")!

    private struct Entry: Decodable {
        let cellId: String
        let role: String
        let name: String?
        let encPub: String?
        let nodeId: String?
        let sig: String
        enum CodingKeys: String, CodingKey {
            case cellId = "cell_id", role, name, encPub = "enc_pub", nodeId = "node_id", sig
        }
    }

    /// cellId (lowercase hex) -> account, verified entries only.
    static func loadBundled() -> [String: OfficialAccount] {
        guard let url = Bundle.main.url(forResource: "official", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return [:] }
        return verify(data) ?? [:]
    }

    /// nil on any fetch failure (caller keeps what it has); [:] = fetched fine, nothing valid.
    static func fetchRemote() async -> [String: OfficialAccount]? {
        // Never from URLCache — see NodeManifest.fetchRemote (stale heuristic-cached copy
        // after the 2026-09-29 curator key rotation).
        var request = URLRequest(url: remoteURL, cachePolicy: .reloadIgnoringLocalCacheData)
        request.timeoutInterval = 10
        guard let (data, response) = try? await URLSession.shared.data(for: request),
              let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            return nil
        }
        return verify(data)
    }

    private static func verify(_ data: Data) -> [String: OfficialAccount]? {
        guard let curatorPub = Hex.decode(NodeManifest.curatorPublicKeyHex),
              let entries = try? JSONDecoder().decode([Entry].self, from: data) else { return nil }
        var result: [String: OfficialAccount] = [:]
        for e in entries {
            let cellId = e.cellId.lowercased()
            let encPub = (e.encPub ?? "").lowercased()
            let nodeId = (e.nodeId ?? "").lowercased()
            // Must match node/curator_sign.py canonical_official_message exactly. "official|"
            // domain-separates from node entries; encPub/nodeId are signed so a swapped key
            // can't redirect complaints to someone else.
            guard let sig = Hex.decode(e.sig) else { continue }
            let current = Data("official|\(cellId)|\(e.role)|\(encPub)|\(nodeId)".utf8)
            // Legacy 3-field form (first builds, 2026-09-28) — accepted only for entries with
            // no key/node, where it signs exactly the same information.
            let legacy = Data("official|\(cellId)|\(e.role)".utf8)
            guard ed25519Verify(signature: sig, data: current, publicKey: curatorPub)
                    || (encPub.isEmpty && nodeId.isEmpty
                        && ed25519Verify(signature: sig, data: legacy, publicKey: curatorPub))
            else { continue }
            result[cellId] = OfficialAccount(role: e.role, name: e.name ?? e.role,
                                             encPub: encPub, nodeId: nodeId)
        }
        return result
    }
}

/// The abuse report email — see ReportSheet. Always carries the reporter's own cellId, since
/// the administration answers in the Nevod app only (never by email), so it needs to know
/// whom to write to there.
/// Diagnostic log mail (DiagnosticsView). support@ is routed to the developer's mailbox.
enum DiagnosticReport {
    static let address = "support@nevod.network"
    /// In-app fallback (no Mail account): the log goes to this node's administrator as one
    /// message, base64 of raw-deflate text — node.py DIAG_LOG_PREFIX, keep in sync.
    static let inAppPrefix = "nevod-log:"
    /// The node refuses more than 8 MB unpacked; the log rotates at 3 MB anyway.
    static let inAppMaxLogBytes = 3_000_000

    static func subject(_ reason: String) -> String {
        let firstLine = reason.split(separator: "\n").first.map(String.init) ?? ""
        return "Nevod log: " + String(firstLine.prefix(60))
    }

    static func body(reason: String, cellId: String, nodeAddr: String) -> String {
        let info = Bundle.main.infoDictionary
        let version = info?["CFBundleShortVersionString"] as? String ?? "?"
        let build = info?["CFBundleVersion"] as? String ?? "?"
        var sys = utsname()
        uname(&sys)
        let model = withUnsafeBytes(of: &sys.machine) { String(decoding: $0.prefix { $0 != 0 }, as: UTF8.self) }
        return [
            "What happened / Что случилось:", reason, "",
            "App: \(version) (\(build))",
            "iOS: \(ProcessInfo.processInfo.operatingSystemVersionString), \(model)",
            "Node: \(nodeAddr)",
            "Cell id (reply in the Nevod app): \(cellId)",
        ].joined(separator: "\n")
    }
}

enum AbuseReport {
    static let address = "abuse@nevod.network"

    static func subject(reportedName: String) -> String {
        "Nevod report: \(reportedName)"
    }

    static func body(reporterCellId: String, reportedCellId: String, reportedName: String,
                     nodeId: String, nodeAddr: String, messageText: String?, messageDate: Date?,
                     comment: String) -> String {
        var lines = [
            "Reported account / Аккаунт: \(reportedName)",
            "Reported cell id: \(reportedCellId)",
            "Node: \(nodeAddr) (\(nodeId))",
            "Reporter cell id (reply in the Nevod app): \(reporterCellId)",
        ]
        if let messageText {
            let when = messageDate.map { ISO8601DateFormatter().string(from: $0) } ?? "?"
            lines += ["", "Message (\(when)):", messageText]
        }
        if !comment.isEmpty {
            lines += ["", "Comment / Комментарий:", comment]
        }
        return lines.joined(separator: "\n")
    }
}
