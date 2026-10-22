import SwiftUI

struct ContactsView: View {
    @EnvironmentObject var store: AppStore
    @EnvironmentObject var callManager: CallManager
    @State private var showAddSheet = false

    var body: some View {
        NavigationStack {
            List {
                if !store.contacts.isEmpty {
                    Section("My contacts") {
                        ForEach(store.contacts) { contact in
                            let stillOnNode = store.nodeMembers.contains(where: { $0.cellId == contact.cellId })
                            HStack {
                                NavigationLink(destination: ChatGateView(contact: contact)) {
                                    MemberRow(name: contact.alias.isEmpty ? "No alias" : contact.alias,
                                              cellId: contact.cellId, systemImage: "person.circle.fill")
                                }
                                callButton(cellId: contact.cellId,
                                          name: contact.alias.isEmpty ? "No alias" : contact.alias)
                            }
                            .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                Button(role: .destructive) {
                                    store.removeContact(cellId: contact.cellId)
                                } label: {
                                    // If they're still a node member, this just moves them back
                                    // to "On this node" (removeContact only drops the saved-offline
                                    // copy) — otherwise it's a plain delete since there's nothing
                                    // else to fall back to.
                                    Label(stillOnNode ? "Move to On this node" : "Delete",
                                          systemImage: stillOnNode ? "arrow.uturn.backward" : "trash")
                                }
                            }
                        }
                    }
                }
                let uncontacted = store.nodeMembers.filter { m in
                    !store.contacts.contains(where: { $0.cellId == m.cellId })
                }
                if !uncontacted.isEmpty {
                    Section("On this node") {
                        ForEach(uncontacted) { member in
                            let contact = store.memberAsContact(member)
                            HStack {
                                NavigationLink(destination: ChatGateView(contact: contact)) {
                                    MemberRow(name: member.displayName.isEmpty ? "Unknown" : member.displayName,
                                              cellId: member.cellId, systemImage: "person.crop.circle.badge.checkmark")
                                }
                                callButton(cellId: member.cellId,
                                          name: member.displayName.isEmpty ? "Unknown" : member.displayName)
                            }
                            .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                Button { store.addContact(contact) } label: {
                                    Label("Add to My Contacts", systemImage: "person.badge.plus")
                                }
                                .tint(.accentColor)
                            }
                        }
                    }
                }
            }
            .listStyle(.plain)
            .navigationTitle("Contacts")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showAddSheet = true } label: { Image(systemName: "person.badge.plus") }
                }
            }
            .overlay {
                if store.contacts.isEmpty && store.nodeMembers.isEmpty && store.connectionStatus != "connected" {
                    ContentUnavailableView("No contacts", systemImage: "person.2",
                        description: Text("Connect to a node to see members, or tap + to add manually"))
                }
            }
            .sheet(isPresented: $showAddSheet) { AddContactSheet() }
        }
    }

    // Sibling to the NavigationLink, not nested inside its label — .plain buttonStyle
    // keeps List from treating a tap here as also activating the row's navigation.
    @ViewBuilder
    private func callButton(cellId: String, name: String) -> some View {
        Button {
            callManager.startCall(to: cellId, contactName: name)
        } label: {
            Image(systemName: "phone.fill").font(.title3).foregroundStyle(.tint)
        }
        .buttonStyle(.plain)
        .disabled(!callManager.state.isIdle || store.isIdentityDeleted(cellId: cellId))
        .padding(.leading, 6)
    }
}

struct MemberRow: View {
    @EnvironmentObject var store: AppStore
    let name: String
    let cellId: String
    let systemImage: String

    var body: some View {
        HStack {
            if store.isIdentityDeleted(cellId: cellId) {
                Circle().fill(Color(.systemGray4)).frame(width: 28, height: 28)
            } else if let avatar = store.contactAvatars[cellId] {
                Image(uiImage: avatar)
                    .resizable().scaledToFill()
                    .frame(width: 28, height: 28)
                    .clipShape(Circle())
            } else {
                Image(systemName: systemImage).font(.title2).foregroundStyle(.tint)
            }
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 4) {
                    Text(name).font(.headline)
                    OfficialNameBadge(cellId: cellId, name: name)
                }
                if store.isIdentityDeleted(cellId: cellId) {
                    Text("Личность удалена").font(.caption).foregroundStyle(.secondary)
                } else {
                    Text(String(cellId.prefix(16)) + "…")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
        }
        .onAppear { store.loadAvatarIfCached(for: cellId) }
    }
}

struct AddContactSheet: View {
    @EnvironmentObject var store: AppStore
    @Environment(\.dismiss) var dismiss
    @State private var cardText = ""
    @State private var alias = ""
    @State private var error: String? = nil
    @State private var showScanner = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Contact card") {
                    HStack {
                        TextField("cell_id@node|enc_pub", text: $cardText, axis: .vertical)
                            .autocorrectionDisabled().textInputAutocapitalization(.never)
                        Button { showScanner = true } label: {
                            Image(systemName: "qrcode.viewfinder").font(.title2)
                        }
                    }
                }
                Section("Alias") { TextField("Name", text: $alias) }
                if let err = error { Section { Text(err).foregroundStyle(.red) } }
            }
            .navigationTitle("Add Contact").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Add") { addContact() }.bold()
                        .disabled(cardText.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .sheet(isPresented: $showScanner) {
                QRScannerSheet { code in cardText = code }
            }
        }
    }

    private func addContact() {
        guard var contact = parseCard(cardText.trimmingCharacters(in: .whitespacesAndNewlines)) else {
            error = String(localized: "Invalid card format"); return
        }
        contact.alias = alias.trimmingCharacters(in: .whitespaces)
        store.addContact(contact); dismiss()
    }
}

struct AddContactBanner: View {
    @EnvironmentObject var store: AppStore
    let card: String
    let suggestedName: String
    @State private var alias: String

    init(card: String, suggestedName: String) {
        self.card = card
        self.suggestedName = suggestedName
        _alias = State(initialValue: suggestedName)
    }

    var body: some View {
        VStack(spacing: 8) {
            Text(suggestedName.isEmpty ? "New contact wants to chat" : "\(suggestedName) added you as a contact")
                .font(.headline)
            TextField("Give them an alias", text: $alias).textFieldStyle(.roundedBorder).padding(.horizontal)
            HStack(spacing: 16) {
                Button("Ignore", role: .destructive) {
                    store.pendingCard = nil; store.pendingCardName = nil
                }.buttonStyle(.bordered)
                Button("Add") {
                    if var contact = parseCard(card) {
                        contact.alias = alias.trimmingCharacters(in: .whitespaces)
                        store.addContact(contact)
                        store.pendingCard = nil; store.pendingCardName = nil
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(alias.trimmingCharacters(in: .whitespaces).isEmpty)
            }
        }
        .padding().background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 16)).shadow(radius: 4).padding()
    }
}
