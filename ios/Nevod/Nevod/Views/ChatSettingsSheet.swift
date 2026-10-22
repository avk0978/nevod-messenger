import SwiftUI

/// Per-chat settings — modeled on AddContactSheet's Form-in-a-sheet shape (ContactsView.swift).
/// Three independent settings today: display name (was a separate pencil-icon alert in
/// ChatView's toolbar — folded in here 2026-08-26 to declutter the nav bar down to just
/// call/gear), notifications on/off — mutes sound AND suppresses push entirely, not just
/// silences it (cross-stack, see AppStore.updateSoundEnabled and router.py's _send_push mute
/// check) — and password lock with a duress code (fully local, see ChatLockStore).
struct ChatSettingsSheet: View {
    let contact: Contact
    @EnvironmentObject var store: AppStore
    @Environment(\.dismiss) var dismiss

    @State private var aliasInput = ""
    @State private var soundEnabled = true
    @State private var lockToggleOn = false
    // Only shown when actually entering/changing passwords — if the chat is already locked,
    // opening settings shows a plain "passwords are set" state instead of blank fields you'd
    // have to needlessly refill just to leave things as they are.
    @State private var showPasswordFields = false
    @State private var unlockPassword = ""
    @State private var duressPassword = ""
    @State private var lockError: String? = nil
    @State private var reportTarget: ReportTarget? = nil
    @State private var confirmBlock = false
    @State private var idCopied = false

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    // No separate "save name" button (user feedback 2026-09-28) — the name is
                    // saved when the sheet closes, whether via "Готово" or a swipe down.
                    TextField("Имя", text: $aliasInput).autocorrectionDisabled()
                } header: {
                    Text("Имя")
                }
                Section {
                    Toggle("Уведомления", isOn: $soundEnabled)
                        .onChange(of: soundEnabled) { _, new in
                            store.updateSoundEnabled(chatId: contact.cellId, enabled: new)
                        }
                } header: {
                    Text("Уведомления")
                } footer: {
                    Text("Выключено — для этого чата не будет ни звука, ни push-уведомлений.")
                }
                Section {
                    Toggle("Защита паролем", isOn: $lockToggleOn)
                        .onChange(of: lockToggleOn) { old, new in
                            if new && !old {
                                showPasswordFields = true
                            } else if !new {
                                ChatLockStore.clear(chatId: contact.cellId)
                                store.updateChatLock(chatId: contact.cellId, isLocked: false)
                                unlockPassword = ""; duressPassword = ""
                                lockError = nil; showPasswordFields = false
                            }
                        }
                    if lockToggleOn {
                        if showPasswordFields {
                            SecureField("Пароль для входа", text: $unlockPassword)
                                .textContentType(.newPassword)
                            SecureField("Пароль-паника", text: $duressPassword)
                                .textContentType(.newPassword)
                            if let lockError {
                                Text(lockError).font(.footnote).foregroundStyle(.red)
                            }
                        } else {
                            Text("Пароли заданы").foregroundStyle(.secondary)
                            Button("Изменить пароли") { showPasswordFields = true }
                        }
                    }
                } header: {
                    Text("Безопасность")
                } footer: {
                    // Deliberately doesn't spell out what the "panic" password does here —
                    // the whole point is that it isn't obvious from looking at the phone.
                    if lockToggleOn && showPasswordFields {
                        Text("Оба пароля должны быть заданы и отличаться друг от друга.")
                    }
                }
                // App Store Guideline 1.2: report + block reachable from every chat.
                Section {
                    Button("Пожаловаться") {
                        reportTarget = ReportTarget(cellId: contact.cellId, name: peerName,
                                                    messageText: nil, messageDate: nil)
                    }
                    if store.isBlocked(contact.cellId) {
                        Button("Разблокировать") { store.setBlocked(contact.cellId, false) }
                    } else {
                        Button("Заблокировать", role: .destructive) { confirmBlock = true }
                    }
                } footer: {
                    Text("Заблокированный пользователь не сможет писать и звонить вам. Он об этом не узнает.")
                }
                // The peer's ID, visible and copyable — needed to report them by email by hand,
                // and to tell the administration exactly who it's about (user feedback 2026-09-28:
                // "не понятно как найти ID пользователя").
                Section {
                    Text(contact.cellId)
                        .font(.caption.monospaced())
                        .textSelection(.enabled)
                    Button {
                        UIPasteboard.general.string = contact.cellId
                        idCopied = true
                    } label: {
                        Label(idCopied ? "Скопировано" : "Скопировать ID", systemImage: idCopied ? "checkmark" : "doc.on.doc")
                    }
                } header: {
                    Text("ID пользователя")
                }
            }
            .sheet(item: $reportTarget) { target in ReportSheet(target: target) }
            .confirmationDialog("Заблокировать пользователя?", isPresented: $confirmBlock,
                                titleVisibility: .visible) {
                Button("Заблокировать", role: .destructive) { store.setBlocked(contact.cellId, true) }
                Button("Заблокировать и пожаловаться", role: .destructive) {
                    store.setBlocked(contact.cellId, true)
                    // Let the dialog finish dismissing before presenting the report sheet.
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) {
                        reportTarget = ReportTarget(cellId: contact.cellId, name: peerName,
                                                    messageText: nil, messageDate: nil)
                    }
                }
                Button("Отмена", role: .cancel) {}
            }
            .navigationTitle("Настройки чата")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) { Button("Готово") { done() } }
            }
            .onAppear {
                aliasInput = contact.alias
                let s = store.settings(for: contact.cellId)
                soundEnabled = s.soundEnabled
                lockToggleOn = s.isLocked
                showPasswordFields = !s.isLocked
            }
            // onDisappear, not the Done button, so a swipe-down dismiss saves the name too.
            .onDisappear { saveAlias() }
        }
    }

    // Same logic ChatView's old pencil-icon rename alert used: renaming a chat that isn't
    // a saved contact yet (a nodeMember-derived chat) saves it as one, alias and all.
    private func saveAlias() {
        let alias = aliasInput.trimmingCharacters(in: .whitespaces)
        guard !alias.isEmpty, alias != contact.alias else { return }
        if store.contacts.contains(where: { $0.cellId == contact.cellId }) {
            store.updateContactAlias(cellId: contact.cellId, alias: alias)
        } else {
            var c = contact; c.alias = alias; store.addContact(c)
        }
    }

    /// "Готово" is the only save action (no per-field save buttons, user feedback
    /// 2026-09-28): passwords typed in are saved here. If they're filled in but invalid, stay
    /// open and show why instead of silently dropping them. Name is saved in onDisappear.
    private func done() {
        if lockToggleOn && showPasswordFields && !(unlockPassword.isEmpty && duressPassword.isEmpty) {
            guard canSave else {
                lockError = String(localized: "Оба пароля должны быть заданы и отличаться друг от друга.")
                return
            }
            savePasswords()
            guard lockError == nil else { return }
        }
        dismiss()
    }

    /// The name the peer uses (their own display name when known), not our local alias — a
    /// report should identify them the way the node knows them.
    private var peerName: String {
        if let m = store.nodeMembers.first(where: { $0.cellId == contact.cellId }), !m.displayName.isEmpty {
            return m.displayName
        }
        return contact.alias.isEmpty ? String(contact.cellId.prefix(12)) : contact.alias
    }

    private var canSave: Bool {
        !unlockPassword.isEmpty && !duressPassword.isEmpty && unlockPassword != duressPassword
    }

    private func savePasswords() {
        guard canSave else { return }
        guard ChatLockStore.setPasswords(chatId: contact.cellId, unlock: unlockPassword, duress: duressPassword) else {
            lockError = String(localized: "Не удалось сохранить пароли")
            return
        }
        store.updateChatLock(chatId: contact.cellId, isLocked: true)
        unlockPassword = ""; duressPassword = ""
        lockError = nil; showPasswordFields = false
    }
}
