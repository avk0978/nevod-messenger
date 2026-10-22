import SwiftUI

/// Thin router in front of ChatView — shows the passcode gate (ChatLockEntryView) instead if
/// this chat has lock protection enabled, otherwise goes straight to ChatView as before.
/// Replaces `ChatView(contact:)` at every navigation call site (ChatsListView, ContactsView)
/// so lock-checking lives in exactly one place rather than three.
struct ChatGateView: View {
    let contact: Contact
    @EnvironmentObject var store: AppStore

    var body: some View {
        if store.settings(for: contact.cellId).isLocked {
            ChatLockEntryView(contact: contact)
        } else {
            ChatView(contact: contact)
        }
    }
}
