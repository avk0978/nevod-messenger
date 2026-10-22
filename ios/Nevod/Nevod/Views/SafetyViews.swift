import SwiftUI
import MessageUI
import UIKit

// App Store Guideline 1.2 (user-generated content), 2026-09-28: terms acceptance, report,
// block, official-account badge. Logic lives in Storage/Safety.swift and AppStore.

enum NevodLinks {
    static let terms   = URL(string: "https://nevod.network/terms")!
    static let privacy = URL(string: "https://nevod.network/privacy")!
    /// Bump when the terms change in a way users must re-accept.
    static let termsVersion = 1
}

// MARK: - Official badge / impersonation warning

/// Shown right after a name wherever one appears (chat header, chat list, contacts).
/// ✓ for a curator-signed official account; ⚠︎ for a name that claims an official role
/// (administrator, support, …) on an account that isn't one.
struct OfficialNameBadge: View {
    @EnvironmentObject var store: AppStore
    let cellId: String
    let name: String

    var body: some View {
        if store.isOfficial(cellId) {
            Image(systemName: "checkmark.seal.fill")
                .foregroundStyle(.blue)
                .accessibilityLabel(Text("Официальный аккаунт Nevod"))
        } else if store.looksLikeImpersonation(cellId: cellId, name: name) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(.orange)
                .accessibilityLabel(Text("Не официальный аккаунт"))
        }
    }
}

/// Banner at the top of a chat whose name claims an official role but isn't official.
struct ImpersonationWarningBanner: View {
    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: "exclamationmark.triangle.fill").foregroundStyle(.orange)
            Text("Это не официальный аккаунт Nevod. Администрация пишет только с аккаунта administrator со значком ✓ и никогда не просит пароли, ключи или коды.")
                .font(.footnote)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.orange.opacity(0.12))
    }
}

// MARK: - Blocked chat input replacement

struct BlockedChatBar: View {
    @EnvironmentObject var store: AppStore
    let cellId: String

    var body: some View {
        VStack(spacing: 6) {
            Text("Вы заблокировали этого пользователя")
                .font(.footnote).foregroundStyle(.secondary)
            Button("Разблокировать") { store.setBlocked(cellId, false) }
                .font(.footnote.bold())
        }
        .frame(maxWidth: .infinity)
        .padding()
    }
}

// MARK: - Report

/// What's being reported — a whole account, or one message in the chat with it.
struct ReportTarget: Identifiable {
    let id = UUID()
    let cellId: String
    let name: String
    let messageText: String?
    let messageDate: Date?
}

struct ReportSheet: View {
    @EnvironmentObject var store: AppStore
    @Environment(\.dismiss) var dismiss
    @Environment(\.openURL) var openURL
    let target: ReportTarget

    @State private var comment = ""
    @State private var offenderId = ""
    @State private var alsoBlock = true
    @State private var showMail = false
    @State private var noMailApp = false
    @State private var sentInApp = false
    @State private var sendError: String? = nil

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text("Жалоба уйдёт письмом администрации на \(AbuseReport.address).")
                    Text("Сообщения в Nevod зашифрованы, и администрация их не видит. Поэтому текст сообщения, на которое вы жалуетесь, будет вложен в письмо вами.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                if target.cellId.isEmpty {
                    // Opened from Profile, not from a chat — let the user say who it's about.
                    Section {
                        TextField("ID пользователя (необязательно)", text: $offenderId)
                            .font(.caption.monospaced())
                            .autocorrectionDisabled()
                            .textInputAutocapitalization(.never)
                    } footer: {
                        Text("Проще пожаловаться из самого чата: Настройки чата → Пожаловаться. Там ID подставится сам. Его также можно скопировать в Настройках чата.")
                    }
                }
                if let text = target.messageText {
                    Section("Сообщение") {
                        Text(text).font(.callout).lineLimit(6)
                    }
                }
                Section("Комментарий (необязательно)") {
                    TextField("Что произошло?", text: $comment, axis: .vertical).lineLimit(2...6)
                }
                if !target.cellId.isEmpty && !store.isBlocked(target.cellId) {
                    Section {
                        Toggle("Также заблокировать", isOn: $alsoBlock)
                    }
                }
                Section {
                    if store.administratorContact != nil {
                        // Primary path (user decision 2026-09-28): straight to the administrator
                        // inside Nevod — no mail app needed, the reply lands in that same chat.
                        Button("Отправить администратору в Nevod") { sendInApp() }
                            .disabled(sentInApp)
                        Button("Отправить на e-mail") { send() }
                    } else {
                        Button("Отправить жалобу") { send() }
                    }
                    if sentInApp {
                        Label("Жалоба отправлена. Ответ придёт в чат с administrator.", systemImage: "checkmark.circle")
                            .foregroundStyle(.green)
                    }
                    if let sendError {
                        Text(sendError).font(.footnote).foregroundStyle(.red)
                    }
                } footer: {
                    Text("Ответ придёт только в приложении Nevod от аккаунта administrator со значком ✓. Мы никогда не отвечаем по e-mail и не просим пароли, ключи или коды.")
                }
                if noMailApp {
                    Section {
                        Text("Почтовое приложение не найдено. Напишите на \(AbuseReport.address) — текст жалобы скопирован.")
                            .font(.footnote)
                    }
                }
            }
            .navigationTitle("Пожаловаться")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Отмена") { dismiss() } }
            }
            .sheet(isPresented: $showMail, onDismiss: { dismiss() }) {
                MailComposer(to: AbuseReport.address, subject: subject, body: mailBody)
                    .ignoresSafeArea()
            }
        }
    }

    private var reportedCellId: String {
        target.cellId.isEmpty ? offenderId.trimmingCharacters(in: .whitespacesAndNewlines) : target.cellId
    }
    private var subject: String { AbuseReport.subject(reportedName: target.name.isEmpty ? reportedCellId : target.name) }
    private var mailBody: String {
        AbuseReport.body(reporterCellId: store.identity?.cellId ?? "?",
                         reportedCellId: reportedCellId.isEmpty ? "?" : reportedCellId,
                         reportedName: target.name.isEmpty ? "?" : target.name,
                         nodeId: store.client?.nodeId ?? "?", nodeAddr: IdentityStore.nodeAddr,
                         messageText: target.messageText, messageDate: target.messageDate,
                         comment: comment.trimmingCharacters(in: .whitespacesAndNewlines))
    }

    private func sendInApp() {
        guard let admin = store.administratorContact else { return }
        if alsoBlock && !target.cellId.isEmpty && !store.isBlocked(target.cellId) {
            store.setBlocked(target.cellId, true)
        }
        nlog("report sendInApp target=\(reportedCellId.prefix(8)) admin=\(admin.cellId.prefix(8))")
        Task {
            do {
                guard try await store.send(text: "🚩 " + subject + "\n\n" + mailBody, to: admin) else {
                    sendError = String(localized: "Сообщение не отправлено")
                    return
                }
                sentInApp = true
                sendError = nil
            } catch {
                sendError = error.localizedDescription
            }
        }
    }

    private func send() {
        if alsoBlock && !target.cellId.isEmpty && !store.isBlocked(target.cellId) {
            store.setBlocked(target.cellId, true)
        }
        nlog("report send target=\(reportedCellId.prefix(8)) hasMessage=\(target.messageText != nil) canSendMail=\(MFMailComposeViewController.canSendMail())")
        if MFMailComposeViewController.canSendMail() {
            showMail = true
            return
        }
        // No Mail account configured — hand it to whatever mail app handles mailto:.
        var comps = URLComponents()
        comps.scheme = "mailto"
        comps.path = AbuseReport.address
        comps.queryItems = [URLQueryItem(name: "subject", value: subject),
                            URLQueryItem(name: "body", value: mailBody)]
        UIPasteboard.general.string = mailBody
        // Not canOpenURL — that returns false for any scheme not listed in
        // LSApplicationQueriesSchemes; just try it and look at the result.
        guard let url = comps.url else { noMailApp = true; return }
        openURL(url) { accepted in
            if accepted { dismiss() } else { noMailApp = true }
        }
    }
}

struct MailComposer: UIViewControllerRepresentable {
    let to: String
    let subject: String
    let body: String
    var attachment: (data: Data, mime: String, name: String)? = nil

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIViewController(context: Context) -> MFMailComposeViewController {
        let vc = MFMailComposeViewController()
        vc.mailComposeDelegate = context.coordinator
        vc.setToRecipients([to])
        vc.setSubject(subject)
        vc.setMessageBody(body, isHTML: false)
        if let attachment { vc.addAttachmentData(attachment.data, mimeType: attachment.mime, fileName: attachment.name) }
        return vc
    }

    func updateUIViewController(_ vc: MFMailComposeViewController, context: Context) {}

    final class Coordinator: NSObject, MFMailComposeViewControllerDelegate {
        func mailComposeController(_ controller: MFMailComposeViewController,
                                   didFinishWith result: MFMailComposeResult, error: Error?) {
            controller.dismiss(animated: true)
        }
    }
}

// MARK: - Profile sub-screens

struct BlockedUsersView: View {
    @EnvironmentObject var store: AppStore

    var body: some View {
        List {
            if store.blockedCellIds.isEmpty {
                Text("Нет заблокированных").foregroundStyle(.secondary)
            }
            ForEach(store.blockedCellIds.sorted(), id: \.self) { cellId in
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(name(for: cellId))
                        Text(String(cellId.prefix(16)) + "…")
                            .font(.caption.monospaced()).foregroundStyle(.secondary)
                    }
                    Spacer()
                    Button("Разблокировать") { store.setBlocked(cellId, false) }
                        .buttonStyle(.borderless)
                }
            }
        }
        .navigationTitle("Заблокированные")
    }

    private func name(for cellId: String) -> String {
        if let c = store.contacts.first(where: { $0.cellId == cellId }), !c.alias.isEmpty { return c.alias }
        if let m = store.nodeMembers.first(where: { $0.cellId == cellId }), !m.displayName.isEmpty { return m.displayName }
        return String(cellId.prefix(12)) + "…"
    }
}

/// Debug log → developers. Always by mail to DiagnosticReport.address with a required
/// description: the system share sheet let users pick any app, and they sent the bare log
/// wherever (or couldn't — they don't know the developer's Telegram), with no word on what
/// went wrong (user request 2026-10-19).
struct DiagnosticsView: View {
    @EnvironmentObject var store: AppStore
    @State private var reason = ""
    @State private var showMail = false
    @State private var noMail = false
    @State private var sentInApp = false
    @State private var sending = false
    @State private var sendError: String?

    private var trimmedReason: String { reason.trimmingCharacters(in: .whitespacesAndNewlines) }

    var body: some View {
        List {
            Section {
                TextField("Например: не дошли 2 фото из 3, около 21:00", text: $reason, axis: .vertical)
                    .lineLimit(3...8)
                Button {
                    send()
                } label: {
                    Label("Отправить разработчикам", systemImage: "envelope")
                }
                .disabled(trimmedReason.isEmpty || sending || sentInApp)
                if sentInApp {
                    Label("Отправлено администратору. Ответ придёт в чат с ним в Nevod.", systemImage: "checkmark.circle")
                        .foregroundStyle(.green)
                }
                if let sendError {
                    Text(sendError).foregroundStyle(.red).font(.footnote)
                }
            } header: {
                Text("Что случилось?")
            } footer: {
                Text("Описание и журнал уйдут письмом на \(DiagnosticReport.address), а если на телефоне не настроена почта — администратору в Nevod. Журнал хранится только на этом устройстве и не содержит текста сообщений.")
            }
            Section {
                Button("Clear log", role: .destructive) { NevLogger.shared.clear() }
            }
        }
        .navigationTitle("Диагностика")
        .sheet(isPresented: $showMail) {
            MailComposer(to: DiagnosticReport.address, subject: DiagnosticReport.subject(trimmedReason),
                         body: DiagnosticReport.body(reason: trimmedReason, cellId: store.identity?.cellId ?? "?",
                                                     nodeAddr: IdentityStore.nodeAddr),
                         attachment: (try? Data(contentsOf: NevLogger.shared.logFileURL))
                            .map { ($0, "text/plain", "nevod.log") })
                .ignoresSafeArea()
        }
        .alert("Почта не настроена", isPresented: $noMail) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("Чтобы отправить журнал, добавьте почтовый ящик в приложении «Почта» и повторите.")
        }
    }

    private func send() {
        let admin = store.administratorContact
        nlog("diagnostics send reasonLen=\(trimmedReason.count) canSendMail=\(MFMailComposeViewController.canSendMail()) admin=\(admin != nil)")
        if MFMailComposeViewController.canSendMail() { showMail = true; return }
        guard let admin else { noMail = true; return }
        let text = "📋 " + DiagnosticReport.subject(trimmedReason) + "\n\n"
            + DiagnosticReport.body(reason: trimmedReason, cellId: store.identity?.cellId ?? "?",
                                    nodeAddr: IdentityStore.nodeAddr)
        sending = true
        sendError = nil
        Task {
            defer { sending = false }
            do {
                if try await store.sendDiagnosticsInApp(text: text, to: admin) {
                    sentInApp = true
                } else {
                    sendError = String(localized: "Сообщение не отправлено")
                }
            } catch {
                sendError = error.localizedDescription
            }
        }
    }
}

struct LicensesView: View {
    // The licenses themselves (BSD for WebRTC, OFL for Ponomar) require reproducing the
    // ORIGINAL text — that's the legally binding one. So every language shows a translation
    // (Localizable.xcstrings, keys "license.*") followed by the English original; English
    // alone shows just the original once.
    private static let webrtcOriginal = "Copyright (c) 2011, The WebRTC project authors. All rights reserved.\n\nRedistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:\n\n• Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.\n• Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.\n• Neither the name of Google nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.\n\nTHIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
    private static let ponomarOriginal = "Ponomar Unicode — Copyright 2025 The Ponomar Project Authors (https://github.com/slavonic/ponomar). Licensed under the SIL Open Font License, Version 1.1 (https://openfontlicense.org)."

    private var isEnglish: Bool { Bundle.main.preferredLocalizations.first == "en" }

    var body: some View {
        List {
            licenseSection("WebRTC", translationKey: "license.webrtc", original: Self.webrtcOriginal)
            licenseSection("Ponomar Unicode", translationKey: "license.ponomar", original: Self.ponomarOriginal)
        }
        .navigationTitle("Лицензии")
    }

    @ViewBuilder
    private func licenseSection(_ title: String, translationKey: String.LocalizationValue,
                                original: String) -> some View {
        Section(header: Text(verbatim: title)) {
            if !isEnglish {
                Text(String(localized: translationKey))
                    .font(.caption2).foregroundStyle(.secondary)
                DisclosureGroup("Оригинальный текст (English)") {
                    Text(verbatim: original).font(.caption2).foregroundStyle(.secondary)
                }
                .font(.caption)
            } else {
                Text(verbatim: original).font(.caption2).foregroundStyle(.secondary)
            }
        }
    }
}

// MARK: - Terms acceptance (first launch, and again when termsVersion is bumped)

struct TermsAcceptanceView: View {
    @AppStorage("nevod.termsAcceptedVersion") private var acceptedVersion = 0
    @State private var agreed = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Добро пожаловать в Nevod").font(.title2.bold())
                    Text("Чтобы пользоваться Nevod, примите Условия использования. Главное из них:")
                    VStack(alignment: .leading, spacing: 10) {
                        Label("Никакой терпимости к незаконному, оскорбительному, угрожающему контенту, травле и спаму. Нарушителей блокируют.", systemImage: "hand.raised.fill")
                        Label("Любого пользователя можно заблокировать и на него пожаловаться. Жалобы: abuse@nevod.network.", systemImage: "flag.fill")
                        Label("Администрация отвечает только в приложении, с аккаунта administrator со значком ✓. Никогда по e-mail и никогда не просит пароли, ключи или коды.", systemImage: "checkmark.seal.fill")
                    }
                    .font(.callout)
                    HStack(spacing: 16) {
                        Link("Условия использования", destination: NevodLinks.terms)
                        Link("Конфиденциальность", destination: NevodLinks.privacy)
                    }
                    .font(.callout.bold())
                    Toggle("Я принимаю Условия использования", isOn: $agreed)
                    Button {
                        acceptedVersion = NevodLinks.termsVersion
                    } label: {
                        Text("Продолжить").frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!agreed)
                }
                .padding()
            }
        }
    }
}
