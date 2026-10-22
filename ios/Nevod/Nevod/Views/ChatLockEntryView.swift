import SwiftUI

/// Passcode gate shown instead of ChatView when the chat has lock protection enabled (see
/// ChatGateView). First such "locked until unlocked" screen in the app — no existing
/// LocalAuthentication/biometric infrastructure to build on, so this is deliberately simple:
/// one SecureField, one button, nothing fancier.
struct ChatLockEntryView: View {
    let contact: Contact
    @EnvironmentObject var store: AppStore

    @State private var entered = ""
    @State private var showError = false
    @State private var unlocked = false

    private var displayName: String {
        if !contact.alias.isEmpty { return contact.alias }
        let member = store.nodeMembers.first(where: { $0.cellId == contact.cellId })
        return member?.displayName.isEmpty == false ? member!.displayName : String(contact.cellId.prefix(8))
    }

    var body: some View {
        if unlocked {
            ChatView(contact: contact)
        } else {
            VStack(spacing: 20) {
                Spacer()
                Image(systemName: "lock.fill").font(.system(size: 44)).foregroundStyle(.secondary)
                Text(displayName).font(.title3.bold())
                SecureField("Пароль", text: $entered)
                    .textFieldStyle(.roundedBorder)
                    .submitLabel(.go)
                    .onSubmit(submit)
                    .padding(.horizontal, 40)
                if showError {
                    Text("Неверный пароль").font(.footnote).foregroundStyle(.red)
                }
                Button("Войти", action: submit)
                    .buttonStyle(.borderedProminent)
                    .disabled(entered.isEmpty)
                Spacer()
                Spacer()
            }
            .navigationTitle(displayName)
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    // .duress is deliberately handled identically to .wrong from this view's perspective —
    // the whole point of a duress code is that using it looks exactly like a typo to anyone
    // watching. See ChatLockStore.VerifyResult's own doc comment.
    private func submit() {
        switch ChatLockStore.verify(chatId: contact.cellId, entered: entered) {
        case .unlock:
            unlocked = true
        case .duress:
            store.deleteChat(chatId: contact.cellId)
            ChatLockStore.clear(chatId: contact.cellId)
            store.updateChatLock(chatId: contact.cellId, isLocked: false)
            entered = ""
            showError = true
        case .wrong:
            entered = ""
            showError = true
        }
    }
}
