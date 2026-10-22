import UserNotifications

/// Rewrites a message push's generic title ("Nevod" — see router.py's _send_push, which
/// deliberately can't know your private local contact names) with the recipient's OWN local
/// alias for the sender, read from the file the app mirrors contact names into
/// (group.com.avk.Nevod container, nevod-contact-names.json — see lookupAlias). Only runs for pushes the node sent with "mutable-content": 1 (push.py).
/// Never touches message content — the body stays the generic "New message" the server sent;
/// this only ever reads sender_cell_id (already public routing metadata, present in every push
/// regardless of this extension) and a purely local, never-transmitted alias.
class NotificationService: UNNotificationServiceExtension {

    var contentHandler: ((UNNotificationContent) -> Void)?
    var bestAttemptContent: UNMutableNotificationContent?

    override func didReceive(_ request: UNNotificationRequest,
                             withContentHandler contentHandler: @escaping (UNNotificationContent) -> Void) {
        self.contentHandler = contentHandler
        bestAttemptContent = (request.content.mutableCopy() as? UNMutableNotificationContent)

        guard let bestAttemptContent else {
            contentHandler(request.content)
            return
        }

        if let cellId = bestAttemptContent.userInfo["sender_cell_id"] as? String,
           let alias = Self.lookupAlias(for: cellId) {
            bestAttemptContent.title = alias
        }
        if let localized = Self.localizedBody(for: bestAttemptContent.body) {
            bestAttemptContent.body = localized
        }

        contentHandler(bestAttemptContent)
    }

    /// The node sends a fixed, language-neutral body (it can't know the recipient's phone
    /// language, and every already-deployed node would need updating if it tried) — so the
    /// translation happens here, on the device, against this extension's own string catalog.
    /// Only the exact server-side texts are mapped (router.py "New message", node.py's
    /// join-approved push); anything else is left untouched rather than guessed at.
    private static func localizedBody(for body: String) -> String? {
        switch body {
        case "New message":
            return String(localized: "New message")
        case "Заявка одобрена — откройте Nevod":
            return String(localized: "Your request was approved — open Nevod")
        default:
            return nil
        }
    }

    override func serviceExtensionTimeWillExpire() {
        // Apple's own budget for this extension ran out — deliver whatever we have (possibly
        // still the unmodified generic title) rather than let the notification vanish entirely.
        if let contentHandler, let bestAttemptContent {
            contentHandler(bestAttemptContent)
        }
    }

    /// Minimal decode target — only needs the two fields this lookup actually uses, not the
    /// full Contact shape (encPub, nodeAddr, …). Codable ignores JSON keys it doesn't declare,
    /// so this reads the exact same "nevod.contacts" blob AppStore.swift writes without either
    /// side needing to share a type.
    private struct SharedContact: Decodable {
        let cellId: String
        let alias: String
    }

    private static func lookupAlias(for cellId: String) -> String? {
        // Since 2026-10-16 the app writes only cellId + alias into a file excluded from backup
        // (SharedContactNames in IdentityStore.swift); the App Group UserDefaults copy is only
        // there until the app has run once after the update.
        let group = "group.com.avk.Nevod"
        let fileData = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: group)
            .flatMap { try? Data(contentsOf: $0.appendingPathComponent("nevod-contact-names.json")) }
        guard let data = fileData ?? UserDefaults(suiteName: group)?.data(forKey: "nevod.contacts"),
              let contacts = try? JSONDecoder().decode([SharedContact].self, from: data) else {
            return nil
        }
        guard let match = contacts.first(where: { $0.cellId == cellId }),
              !match.alias.isEmpty else {
            return nil
        }
        return match.alias
    }
}
