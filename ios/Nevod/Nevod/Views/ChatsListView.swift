import SwiftUI

struct ChatsListView: View {
    @EnvironmentObject var store: AppStore
    // Optional-item selection (not NavigationPath) so a push-notification tap can
    // programmatically navigate straight to the right chat — see AppStore.pendingChatCellId
    // and the deep-link handling below. NavigationPath-based push (`path.append`, what this
    // used to be) turned out to break the system edge-swipe-back gesture for chats pushed
    // through it — found in testing 2026-08-27, traced back to the commit that introduced it
    // (`ee1fabe`). `.navigationDestination(item:)` is the same pattern already used
    // successfully elsewhere in this app for the identical destination (see
    // NodePlanetDetailView.swift's `chatContact`) — no NavigationPath involved there either.
    @State private var selectedContact: Contact? = nil

    private var chats: [Contact] {
        let result = store.contacts.filter { store.chatIds.contains($0.cellId) }
        let known = Set(result.map(\.cellId))
        let memberChats = store.nodeMembers
            .filter { store.chatIds.contains($0.cellId) && !known.contains($0.cellId) }
            .map { store.memberAsContact($0) }
        return result + memberChats
    }

    var body: some View {
        NavigationStack {
            List {
                ForEach(chats) { contact in
                    Button {
                        selectedContact = contact
                    } label: {
                        HStack {
                            ChatRowView(contact: contact)
                            Image(systemName: "chevron.right")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(.tertiary)
                        }
                    }
                    .buttonStyle(.plain)
                    .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                        Button(role: .destructive) {
                            store.deleteChat(chatId: contact.cellId)
                        } label: {
                            Label("Удалить", systemImage: "trash")
                        }
                    }
                }
            }
            .listStyle(.plain)
            .navigationTitle("Chats")
            .navigationDestination(item: $selectedContact) { contact in
                ChatGateView(contact: contact)
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Circle()
                        .fill(store.client?.isConnected == true ? Color.green : Color.red)
                        .frame(width: 10, height: 10)
                }
            }
            .overlay {
                if chats.isEmpty {
                    ContentUnavailableView("No chats yet", systemImage: "bubble.left",
                        description: Text("Add a contact and start messaging"))
                }
            }
        }
        // .onAppear covers a cold launch via notification tap (this view doesn't exist yet
        // when AppDelegate sets pendingChatCellId); .onChange covers a tap while the app (and
        // this view) is already alive. Both funnel through the same helper.
        .onAppear { openPendingChatIfNeeded() }
        .onChange(of: store.pendingChatCellId) { _, _ in openPendingChatIfNeeded() }
    }

    private func openPendingChatIfNeeded() {
        guard let cellId = store.pendingChatCellId else { return }
        store.pendingChatCellId = nil
        guard let contact = store.resolveContact(cellId: cellId) else {
            nlog("openPendingChatIfNeeded FAILED — no contact resolved for cellId=\(cellId.prefix(8)), "
                 + "staying on chat list")
            return
        }
        nlog("openPendingChatIfNeeded pushing contact=\(contact.alias.isEmpty ? contact.cellId.prefix(8).description : contact.alias)")
        selectedContact = contact
    }
}

struct ChatRowView: View {
    @EnvironmentObject var store: AppStore
    let contact: Contact
    @State private var lastMsg: Message? = nil
    // Computed the same way markChatRead() does (fetch chat's messages, filter in Swift) —
    // NOT a SwiftData #Predicate with "!fromMe && !readAckSent" combined, which silently
    // matched nothing on this SwiftData version (see markChatRead's history).
    @State private var unreadCount = 0

    var body: some View {
        HStack {
            if store.isIdentityDeleted(cellId: contact.cellId) {
                Circle().fill(Color(.systemGray4)).frame(width: 28, height: 28)
            } else if let avatar = store.contactAvatars[contact.cellId] {
                Image(uiImage: avatar)
                    .resizable().scaledToFill()
                    .frame(width: 28, height: 28)
                    .clipShape(Circle())
            } else {
                Image(systemName: "person.circle.fill").font(.title2).foregroundStyle(.tint)
            }
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 4) {
                    Text(contact.alias.isEmpty ? String(contact.cellId.prefix(12)) + "…" : contact.alias)
                        .font(.headline)
                        .fontWeight(unreadCount > 0 ? .bold : .regular)
                    OfficialNameBadge(cellId: contact.cellId, name: contact.alias)
                    if store.isBlocked(contact.cellId) {
                        Image(systemName: "nosign").font(.caption).foregroundStyle(.secondary)
                    }
                }
                if store.isIdentityDeleted(cellId: contact.cellId) {
                    Text("Личность удалена").font(.subheadline).foregroundStyle(.secondary).lineLimit(1)
                } else if let msg = lastMsg {
                    Text(preview(msg)).font(.subheadline).foregroundStyle(.secondary).lineLimit(1)
                }
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 6) {
                if let msg = lastMsg {
                    Text(msg.timestamp, style: .time).font(.caption).foregroundStyle(.secondary)
                }
                if unreadCount > 0 {
                    Text(unreadCount > 99 ? "99+" : "\(unreadCount)")
                        .font(.caption2.bold())
                        .foregroundStyle(.white)
                        .padding(.horizontal, 6).padding(.vertical, 2)
                        .frame(minWidth: 18)
                        .background(Color.accentColor, in: Capsule())
                }
            }
        }
        .padding(.vertical, 4)
        .onAppear { refresh(); store.loadAvatarIfCached(for: contact.cellId) }
        .onChange(of: store.messageSeq) { _, _ in refresh() }
    }

    /// The last message as one line: a kind for media (its text is a MIME type like
    /// "image/jpeg" or a file name), and text without the Markdown marks bot replies use.
    private func preview(_ msg: Message) -> String {
        if msg.isRemoved { return String(localized: "Сообщение удалено") }
        switch msg.type {
        case .image: return "📷 " + String(localized: "Фото")
        case .video: return "🎥 " + String(localized: "Видео")
        case .audio: return "🎤 " + String(localized: "Голосовое сообщение")
        case .file:  return "📎 " + (msg.mediaName ?? String(localized: "Файл"))
        case .text:
            let plain = (try? AttributedString(markdown: msg.text, options: .init(
                interpretedSyntax: .inlineOnlyPreservingWhitespace))).map { String($0.characters) } ?? msg.text
            return plain.replacingOccurrences(of: "\n", with: " ")
        }
    }

    private func refresh() {
        let all = store.messages(for: contact.cellId)
        lastMsg = all.last
        unreadCount = all.filter { !$0.fromMe && !$0.readAckSent }.count
    }
}
