import Foundation

/// Curator-signed bootstrap manifest — see MD_Discuss/DISCUSS_NODE_ADMISSION.md, "2. Сертификат
/// кураторов". This is a purely advisory, client-side trust layer: it does NOT gate node
/// admission (that stays fully open, see node_join_mode in node/identity.py) or discovery (the
/// live node list still comes from node_list_request — NodesView.swift). It decides whether a
/// node discovered live gets a "verified" badge + purpose label, based on a signature from a
/// keypair that belongs to no node — the curator key, kept offline by the project author. Its
/// `address` also OVERRIDES the node's own self-reported one for matched entries (see
/// NodesView.allNodes) — found in practice to matter: a node behind a reverse proxy can
/// self-report an internal address nothing outside can dial, while the manifest is hand-curated
/// specifically to be the real externally-reachable one.
///
/// Signed with `python -m node.curator_sign sign` (see that file). The manifest is fetched live
/// from `remoteURL` (see AppStore.fetchVerifiedNodes(), triggered from NodesView) so a rename,
/// address migration, or new verified node doesn't require an app rebuild — HTTPS is the
/// transport but NOT the trust anchor, every entry's own Ed25519 signature (verified below) is
/// what actually makes "verified" meaningful, so a compromised/MITM'd host can serve garbage but
/// can't forge a signature. The bundled copy of nodes.json is only the offline-install seed
/// (AppStore falls back to it if nothing has ever been fetched successfully) — actual live state
/// lives in AppStore.verifiedNodes, persisted across launches once a fetch has succeeded.
///
/// This type itself holds no state — it's a namespace for the trust anchor, the shared
/// signature-verification logic, and the two ways of obtaining manifest data (bundled / remote).
enum NodeManifest {
    /// Hardcoded trust anchor — the ONLY thing that makes a "verified" badge meaningful. If this
    /// is ever rotated (key loss/compromise), every existing signed manifest entry needs
    /// re-signing with the new key, and this constant updated in step.
    // Internal, not private — OfficialAccounts (Storage/Safety.swift) verifies against the
    // same curator key.
    static let curatorPublicKeyHex =
        "cdb8ac2df5d20663c1049df145615881ee93755a3daac9a412b267fb909cdab5"

    /// Where the live manifest is fetched from — currently hosted alongside the (otherwise
    /// undeployed) PWA static root on Node1's shared nginx, see deploy_manifest.sh.
    static let remoteURL = URL(string: "https://node1.nevod.network/nodes.json")!

    /// Bundled seed — used only when nothing has ever been persisted from a live fetch (fresh
    /// install, or an install that's never had connectivity since). Synchronous/local.
    static func loadBundled() -> [String: VerifiedNodeInfo] {
        guard let url = Bundle.main.url(forResource: "nodes", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return [:] }
        return verify(data) ?? [:]
    }

    /// Fetches and verifies the live manifest. Returns nil on ANY failure (network, non-2xx,
    /// malformed JSON) — nil means "caller changes nothing," matching this codebase's
    /// try?-heavy defensive style for non-critical metadata. A response that parses fine but
    /// verifies to zero entries returns [:] (not nil), which the caller DOES apply — that's a
    /// real "success" (a manifest that legitimately lists nothing verified), not a fetch failure.
    static func fetchRemote() async -> [String: VerifiedNodeInfo]? {
        // Always from the server, never URLCache: the host sends no Cache-Control, so iOS
        // applies heuristic freshness (~10% of the file's age) and could keep serving a
        // stale copy for hours — seen 2026-09-29 right after the curator key rotation, when
        // the cached old-key manifest failed verification and every badge disappeared.
        var request = URLRequest(url: remoteURL, cachePolicy: .reloadIgnoringLocalCacheData)
        request.timeoutInterval = 10  // best-effort metadata — don't let refresh() hang on a dead host
        guard let (data, response) = try? await URLSession.shared.data(for: request),
              let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            return nil
        }
        return verify(data)
    }

    /// node_id (hex) -> info, for entries whose verified_sig actually checks out against
    /// curatorPublicKeyHex. An entry with a missing/invalid signature is dropped entirely here
    /// (not shown with a downgraded badge) — the manifest carries no data this UI needs beyond
    /// the verified purpose label, so a bad signature just means "nothing to show" for that
    /// entry; the node itself, if genuinely open, still appears in the live list unbadged.
    /// Shared by loadBundled() and fetchRemote() so there's exactly one definition of "verified."
    /// nil = data isn't parseable manifest JSON at all (vs. [:] = parsed fine, nothing verified).
    private static func verify(_ data: Data) -> [String: VerifiedNodeInfo]? {
        guard let curatorPub = Hex.decode(curatorPublicKeyHex),
              let entries = try? JSONDecoder().decode([ManifestEntry].self, from: data) else {
            return nil
        }

        var result: [String: VerifiedNodeInfo] = [:]
        for entry in entries where entry.verified {
            let canonical = [entry.nodeId, entry.address, entry.tlsFingerprint, entry.purpose]
                .joined(separator: "|")
            guard let sig = Hex.decode(entry.verifiedSig),
                  let msg = canonical.data(using: .utf8),
                  ed25519Verify(signature: sig, data: msg, publicKey: curatorPub) else { continue }
            result[entry.nodeId] = VerifiedNodeInfo(purpose: entry.purpose, name: entry.name,
                                                    address: entry.address,
                                                    tlsFingerprint: entry.tlsFingerprint)
        }
        return result
    }

    private struct ManifestEntry: Codable {
        let nodeId: String
        let address: String
        let tlsFingerprint: String
        let name: String
        let purpose: String
        let verified: Bool
        let verifiedSig: String

        enum CodingKeys: String, CodingKey {
            case nodeId = "node_id", address, tlsFingerprint = "tls_fingerprint"
            case name, purpose, verified, verifiedSig = "verified_sig"
        }
    }
}

struct VerifiedNodeInfo: Codable, Sendable {
    let purpose: String
    let name: String
    let address: String
    let tlsFingerprint: String
}
