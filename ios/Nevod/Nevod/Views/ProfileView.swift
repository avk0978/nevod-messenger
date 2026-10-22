import SwiftUI
import PhotosUI

struct ProfileView: View {
    @EnvironmentObject var store: AppStore
    @State private var showCard = false
    @State private var avatarPickerItem: PhotosPickerItem? = nil
    @State private var inviteCode: String? = nil          // short human-readable code
    @State private var inviteQRPayload: String? = nil     // combined token when available, else same as inviteCode
    @State private var inviteError: String? = nil
    @State private var inviteInput: String = ""
    @State private var scannedTokenAddress: String? = nil // set when inviteInput came from a combined token
    @State private var scannedTokenFingerprint: String = ""
    @State private var showResetConfirm = false
    @State private var showScanner = false
    @State private var usedBytes: Int64 = 0
    @State private var routes: [String] = IdentityStore.nodeRoutes
    @State private var showChurchKeyboardInfo = false
    @State private var showRename = false
    @State private var renameInput = ""
    @State private var profileReport: ReportTarget? = nil

    private let quotaOptions: [(label: String, bytes: Int64)] = [
        ("500 MB",   500 * 1024 * 1024),
        ("1 GB",   1024 * 1024 * 1024),
        ("2 GB", 2 * 1024 * 1024 * 1024),
        ("5 GB", 5 * 1024 * 1024 * 1024),
    ]

    var body: some View {
        NavigationStack {
            List {
                Section("Identity") {
                    if let id = store.identity {
                        PhotosPicker(selection: $avatarPickerItem, matching: .images) {
                            HStack {
                                Text("Аватар")
                                Spacer()
                                if let img = store.contactAvatars[id.cellId] {
                                    Image(uiImage: img)
                                        .resizable().scaledToFill()
                                        .frame(width: 40, height: 40)
                                        .clipShape(Circle())
                                } else {
                                    Image(systemName: "person.circle.fill")
                                        .font(.system(size: 32))
                                        .foregroundStyle(.tertiary)
                                }
                            }
                        }
                        .onAppear { store.loadAvatarIfCached(for: id.cellId) }
                        LabeledContent("Cell ID") {
                            Text(String(id.cellId.prefix(16)) + "…")
                                .font(.caption.monospaced()).foregroundStyle(.secondary)
                        }
                        LabeledContent("Display name") {
                            Button {
                                renameInput = IdentityStore.displayName
                                showRename = true
                            } label: {
                                Text(IdentityStore.displayName.isEmpty ? "—" : IdentityStore.displayName)
                            }
                        }
                    }
                }
                Section {
                    // A home node is often reachable two ways — a fast local-network
                    // address (when on the same Wi-Fi) and a slower external/public one
                    // (everywhere else). Whichever one last actually worked becomes
                    // primary automatically (NevdClient); this list is just for adding/
                    // editing/removing candidates, not for manually picking "the" one.
                    ForEach(routes.indices, id: \.self) { i in
                        HStack(spacing: 10) {
                            Circle()
                                .fill(!routes[i].isEmpty && routes[i] == store.client?.activeAddr
                                      ? Color.green : Color.gray.opacity(0.35))
                                .frame(width: 8, height: 8)
                            TextField("Server address", text: Binding(
                                get: { routes[i] },
                                set: { routes[i] = $0; persistRoutes() }
                            ))
                            .font(.caption)
                            .autocorrectionDisabled()
                            .textInputAutocapitalization(.never)
                        }
                    }
                    .onDelete(perform: routes.count > 1 ? deleteRoutes : nil)
                    Button {
                        routes.append("")
                    } label: {
                        Label("Add route", systemImage: "plus.circle")
                    }
                    LabeledContent("Status") {
                        HStack(spacing: 6) {
                            Circle().fill(store.client?.isConnected == true ? Color.green : Color.orange)
                                .frame(width: 8, height: 8)
                            Text(store.connectionStatus).foregroundStyle(.secondary)
                        }
                    }
                } header: {
                    Text("Connection")
                } footer: {
                    Text("Add more than one address if your node is reachable multiple ways (e.g. a home node's local network and external address).")
                }
                .onAppear { routes = IdentityStore.nodeRoutes }
                let needsCode = store.connectionStatus == "invite required"
                    || store.connectionStatus == "invite invalid"
                if needsCode {
                    Section("Enter invite code") {
                        if store.connectionStatus == "invite invalid" {
                            Text("Invalid or expired code — get a new one")
                                .font(.caption).foregroundStyle(.red)
                        }
                        if scannedTokenAddress != nil {
                            Text("Will switch server to connect").font(.caption2).foregroundStyle(.secondary)
                        }
                        HStack {
                            TextField("XXXX-XXXX", text: $inviteInput)
                                .autocorrectionDisabled()
                                .textInputAutocapitalization(.characters)
                                .font(.title3.monospaced())
                                .onChange(of: inviteInput) { _, newValue in applyInviteInput(newValue) }
                            Button { showScanner = true } label: {
                                Image(systemName: "qrcode.viewfinder").font(.title2)
                            }
                            Button("Connect") { connectWithInviteInput() }
                            .disabled(inviteInput.trimmingCharacters(in: .whitespaces).isEmpty)
                            .buttonStyle(.borderedProminent)
                        }
                    }
                }

                Section("Storage") {
                    let quota = store.storageQuotaBytes
                    let fraction = quota > 0 ? Double(usedBytes) / Double(quota) : 0.0
                    VStack(alignment: .leading, spacing: 6) {
                        ProgressView(value: min(fraction, 1.0))
                            .tint(fraction > 0.9 ? .red : fraction > 0.7 ? .orange : .accentColor)
                        HStack {
                            Text(ByteCountFormatter.string(fromByteCount: usedBytes, countStyle: .file))
                                .font(.caption).foregroundStyle(.secondary)
                            Spacer()
                            Text(ByteCountFormatter.string(fromByteCount: quota, countStyle: .file))
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                    Picker("Quota", selection: Binding(
                        get: { store.storageQuotaBytes },
                        set: { store.storageQuotaBytes = $0 }
                    )) {
                        ForEach(quotaOptions, id: \.bytes) { opt in
                            Text(opt.label).tag(opt.bytes)
                        }
                    }
                }
                .onAppear { usedBytes = store.usedStorageBytes }

                Section("Actions") {
                    Button("Share my card") { showCard = true }
                    Button("Invite someone") { Task { await generateInvite() } }
                    Button("Церковнославянская клавиатура") { showChurchKeyboardInfo = true }
                }
                Section("Безопасность") {
                    NavigationLink("Заблокированные") { BlockedUsersView() }
                    NavigationLink("AI keys") { AIKeysView() }
                    Link("Условия использования", destination: NevodLinks.terms)
                    Link("Конфиденциальность", destination: NevodLinks.privacy)
                    Button {
                        profileReport = ReportTarget(cellId: "", name: "", messageText: nil, messageDate: nil)
                    } label: {
                        LabeledContent("Сообщить о нарушении", value: AbuseReport.address)
                    }
                }
                Section {
                    NavigationLink("Диагностика") { DiagnosticsView() }
                    NavigationLink("Лицензии") { LicensesView() }
                }
                Section {
                    Button("Reset identity…", role: .destructive) { showResetConfirm = true }
                }
                if let code = inviteCode {
                    Section("Invite code") {
                        HStack {
                            Text(code).font(.title2.monospaced().bold()).foregroundStyle(.tint)
                            Spacer()
                            Button { UIPasteboard.general.string = inviteQRPayload ?? code } label: {
                                Image(systemName: "doc.on.doc")
                            }
                        }
                        if let qr = qrCodeImage(from: inviteQRPayload ?? code) {
                            HStack {
                                Spacer()
                                Image(uiImage: qr).interpolation(.none).resizable()
                                    .frame(width: 180, height: 180)
                                Spacer()
                            }
                            Text("Scan this to connect straight away — no server address to type.")
                                .font(.caption2).foregroundStyle(.secondary)
                        }
                    }
                }
                if let err = inviteError {
                    Section { Text(err).foregroundStyle(.red) }
                }

                Section {
                    LabeledContent("Version") { Text(appVersionString).foregroundStyle(.secondary) }
                }
            }
            .navigationTitle("Profile")
            .alert(Text(store.renameError ?? ""), isPresented: Binding(
                get: { store.renameError != nil },
                set: { if !$0 { store.renameError = nil } }
            )) {
                Button("OK") { store.renameError = nil }
            }
            .alert("Изменить имя", isPresented: $showRename) {
                TextField("Имя", text: $renameInput)
                Button("Сохранить") { store.renameDisplayName(renameInput) }
                Button("Отмена", role: .cancel) {}
            }
            .sheet(isPresented: $showResetConfirm) {
                ResetIdentityConfirmSheet(onConfirm: { Task { await store.resetIdentity() } })
            }
            .sheet(isPresented: $showCard) {
                if let id = store.identity {
                    CardShareSheet(card: formatCard(identity: id, nodeAddr: IdentityStore.nodeAddr,
                                                    nodeId: store.client?.nodeId ?? ""))
                }
            }
            .sheet(isPresented: $showScanner) {
                QRScannerSheet { code in inviteInput = code }
            }
            .sheet(isPresented: $showChurchKeyboardInfo) {
                ChurchKeyboardInfoSheet()
            }
            .sheet(item: $profileReport) { target in ReportSheet(target: target) }
            .onChange(of: avatarPickerItem) { _, item in
                guard let item else { return }
                Task {
                    if let data = try? await item.loadTransferable(type: Data.self),
                       let img = UIImage(data: data) {
                        await store.setOwnAvatar(img)
                    }
                    avatarPickerItem = nil
                }
            }
        }
    }

    private var appVersionString: String {
        let info = Bundle.main.infoDictionary
        let version = info?["CFBundleShortVersionString"] as? String ?? "?"
        let build   = info?["CFBundleVersion"] as? String ?? "?"
        return "\(version) (\(build))"
    }

    /// Persists whatever's non-empty in `routes` and hands it straight to the live
    /// client (NevdClient.updateRoutes) so an already-running session picks it up on
    /// its next reconnect — without this, edits here would only take effect after the
    /// app is relaunched. Never persists down to zero: if the user has fully cleared
    /// the text of the only route to retype it, keep the last known-good list until
    /// they've typed something valid again, rather than leaving nothing to connect to.
    private func persistRoutes() {
        let cleaned = routes.map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
        guard !cleaned.isEmpty else { return }
        IdentityStore.nodeRoutes = cleaned
        store.client?.updateRoutes(cleaned)
    }

    private func deleteRoutes(at offsets: IndexSet) {
        routes.remove(atOffsets: offsets)
        persistRoutes()
    }

    private func generateInvite() async {
        inviteCode = nil; inviteQRPayload = nil; inviteError = nil
        do {
            let result = try await store.client?.createInvite()
            guard result?.ok == true, let code = result?.code else {
                inviteError = result?.reason ?? String(localized: "Could not create invite")
                return
            }
            inviteCode = code
            // An empty fingerprint is normal (node behind a proxy with a real certificate —
            // every production node); it used to drop the QR back to a bare code there.
            // The link form opens from the phone's own camera too, not only Nevod's scanner.
            if let addr = result?.address, !addr.isEmpty {
                inviteQRPayload = cellInviteLink(token: formatCellInviteToken(
                    address: addr, fingerprint: result?.fingerprint ?? "", code: code))
            } else {
                inviteQRPayload = code
            }
        } catch { inviteError = error.localizedDescription }
    }

    /// Mirrors SetupView's applyInviteInput — detects a combined cell-invite
    /// token vs. a bare short code as the user types/pastes/scans.
    private func applyInviteInput(_ raw: String) {
        if let token = parseCellInviteToken(raw) {
            scannedTokenAddress = token.address
            scannedTokenFingerprint = token.fingerprint
            inviteInput = formatInviteCode(token.code)
            return
        }
        let formatted = formatInviteCode(raw)
        if formatted != raw { inviteInput = formatted }
    }

    /// A bare code just registers on the node we're already connected to (unchanged
    /// behavior). A combined token switches to the node it names first — this is
    /// what lets a friend's QR from a different node "just work" from this same box,
    /// instead of requiring a manual reset + server-address change beforehand.
    private func connectWithInviteInput() {
        if let addr = scannedTokenAddress {
            IdentityStore.nodeAddr = addr
            IdentityStore.nodeFingerprint = scannedTokenFingerprint
            store.client?.connect(to: [addr], pinnedFingerprint: scannedTokenFingerprint,
                                  inviteCode: inviteInput)
        } else {
            store.client?.registerWithCode(inviteInput)
        }
        inviteInput = ""; scannedTokenAddress = nil; scannedTokenFingerprint = ""
    }
}

struct CardShareSheet: View {
    @Environment(\.dismiss) var dismiss
    let card: String

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Text("Your contact card").font(.headline)
                if let qr = qrCodeImage(from: card) {
                    Image(uiImage: qr).interpolation(.none).resizable()
                        .frame(width: 200, height: 200)
                }
                Text(card).font(.caption.monospaced()).padding()
                    .background(Color(.systemGray6)).clipShape(RoundedRectangle(cornerRadius: 12))
                    .textSelection(.enabled).padding(.horizontal)
                Button { UIPasteboard.general.string = card } label: {
                    Label("Copy to clipboard", systemImage: "doc.on.doc").frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent).padding(.horizontal)
                ShareLink(item: card) {
                    Label("Share…", systemImage: "square.and.arrow.up").frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered).padding(.horizontal)
                Spacer()
            }
            .padding(.top, 24)
            .navigationTitle("My Card").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .topBarTrailing) { Button("Done") { dismiss() } } }
        }
    }
}

/// Explains the bundled Church Slavonic keyboard extension and explicitly asks the user
/// whether they want it — iOS gives no API for an app to enable a keyboard extension for
/// the user (Apple reserves that for the person, via Settings, for every app including
/// Gboard/SwiftKey), so the most Nevod can do is explain what it is and hand them a direct
/// link to the right place, never enable it silently on their behalf.
struct ChurchKeyboardInfoSheet: View {
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                Image(systemName: "textformat.alt")
                    .font(.system(size: 44)).foregroundStyle(.tint)
                Text("В Nevod встроена дополнительная клавиатура для набора церковнославянского текста историческими буквами (ѡ, ѣ, ѕ, ѳ, ѵ и др.), шрифтом Ponomar Unicode.")
                    .multilineTextAlignment(.center).padding(.horizontal)
                Text("Она не включается сама — iOS разрешает включать клавиатуры только вручную, самому пользователю, для любого приложения. Если она вам не нужна, ничего делать не надо.")
                    .font(.caption).foregroundStyle(.secondary)
                    .multilineTextAlignment(.center).padding(.horizontal)
                VStack(alignment: .leading, spacing: 6) {
                    Text("Чтобы включить:").font(.caption.bold())
                    Text("Настройки → Основные → Клавиатура → Клавиатуры → Новая клавиатура… → выбрать клавиатуру Nevod")
                        .font(.caption).foregroundStyle(.secondary)
                }
                .padding(.horizontal)
                Button {
                    if let url = URL(string: UIApplication.openSettingsURLString) {
                        UIApplication.shared.open(url)
                    }
                    dismiss()
                } label: {
                    Label("Открыть Настройки", systemImage: "gear").frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent).padding(.horizontal)
                Button("Не нужна") { dismiss() }
                    .buttonStyle(.bordered).padding(.horizontal)
                Spacer()
            }
            .padding(.top, 24)
            .navigationTitle("Церковная клавиатура")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .topBarTrailing) { Button("Готово") { dismiss() } } }
        }
    }
}

struct ResetIdentityConfirmSheet: View {
    @Environment(\.dismiss) var dismiss
    let onConfirm: () -> Void
    @State private var typed = ""
    private let confirmWord = "DELETE"

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 44)).foregroundStyle(.red)
                Text("This will permanently delete your identity, contacts, and messages on this device. This cannot be undone.")
                    .multilineTextAlignment(.center).padding(.horizontal)
                Text("Your registration on the node is deleted as well.")
                    .font(.caption).foregroundStyle(.secondary)
                    .multilineTextAlignment(.center).padding(.horizontal)
                VStack(alignment: .leading, spacing: 6) {
                    Text("Type \(confirmWord) to confirm").font(.caption).foregroundStyle(.secondary)
                    TextField(confirmWord, text: $typed)
                        .textFieldStyle(.roundedBorder).autocorrectionDisabled()
                        .textInputAutocapitalization(.characters)
                }
                .padding(.horizontal)
                Button("Reset identity") {
                    dismiss()
                    onConfirm()
                }
                .buttonStyle(.borderedProminent).tint(.red)
                .disabled(typed != confirmWord)
                .padding(.horizontal)
                Spacer()
            }
            .padding(.top, 24)
            .navigationTitle("Reset identity")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
            }
        }
    }
}
