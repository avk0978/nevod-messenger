import SwiftUI
import PhotosUI
import UniformTypeIdentifiers
import AVFoundation
import Photos
import ImageIO
import QuickLook
import UIKit

private let maxFileSizeBytes = 50 * 1024 * 1024  // 50 MB hard limit

/// One-line summary used for reply previews (input plate + quoted block in bubbles).
private func messagePreviewText(_ m: MessageViewData) -> String {
    switch m.type {
    case .image: return String(localized: "📷 Photo")
    case .audio: return String(localized: "🎤 Voice message")
    case .video: return String(localized: "🎬 Video")
    case .file:  return m.mediaName.map { String(localized: "📎 \($0)") } ?? String(localized: "📎 File")
    case .text:  return m.text
    }
}

/// Poster frame + duration for a video bubble. Only decodes the one frame it needs.
private func loadVideoPoster(url: URL, maxPixels: CGFloat) async -> (UIImage?, Double?) {
    // Same signature check as on receive — also covers files received before it existed.
    guard MediaSafety.safeMime(claimed: "video/mp4", fileURL: url) == "video/mp4" else { return (nil, nil) }
    let asset = AVURLAsset(url: url)
    let gen = AVAssetImageGenerator(asset: asset)
    gen.appliesPreferredTrackTransform = true   // portrait clips otherwise come out sideways
    gen.maximumSize = CGSize(width: maxPixels, height: maxPixels)
    let secs = (try? await asset.load(.duration)).map { CMTimeGetSeconds($0) }
    let cg = try? await gen.image(at: .zero).image
    return (cg.map { UIImage(cgImage: $0) }, secs.flatMap { $0.isFinite ? $0 : nil })
}

/// A video from PhotosPicker, received as a file copy rather than Data — loading a clip as
/// Data would pull the whole thing into RAM (see AppStore's notes on the old in-RAM send bug).
struct PickedMovie: Transferable {
    let url: URL
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(contentType: .movie) { SentTransferredFile($0.url) } importing: { received in
            let dst = FileManager.default.temporaryDirectory
                .appendingPathComponent(UUID().uuidString)
                .appendingPathExtension(received.file.pathExtension)
            try FileManager.default.copyItem(at: received.file, to: dst)
            return PickedMovie(url: dst)
        }
    }
}

/// Memory-efficient image thumbnail. For JPEG uses DCT downscaling — only reads needed pixels.
/// maxPixels: longest side in physical pixels (e.g. 480 * scale for @3x → 1440).
private func loadImageThumbnail(url: URL, maxPixels: Int) -> UIImage? {
    // Same signature check as on receive — also covers files received before it existed.
    guard MediaSafety.safeMime(claimed: "image/jpeg", fileURL: url) == "image/jpeg" else { return nil }
    let srcOpts = [kCGImageSourceShouldCache: false] as CFDictionary
    guard let src = CGImageSourceCreateWithURL(url as CFURL, srcOpts) else { return nil }
    let thumbOpts: [CFString: Any] = [
        kCGImageSourceThumbnailMaxPixelSize: maxPixels,
        kCGImageSourceCreateThumbnailFromImageIfAbsent: true,
        kCGImageSourceCreateThumbnailWithTransform: true,
        kCGImageSourceShouldCacheImmediately: true,
    ]
    if let cg = CGImageSourceCreateThumbnailAtIndex(src, 0, thumbOpts as CFDictionary) {
        return UIImage(cgImage: cg)
    }
    // Fallback for non-JPEG (PNG, GIF, etc.) — still off-thread, but full decode
    return UIImage(contentsOfFile: url.path)
}

// UIKit doesn't expose "the current first responder" directly — this is the standard technique
// (walk the responder chain via a no-op action with a nil target). Needed for auto-detecting the
// active keyboard: `UITextInputMode.activeInputModes` (tried previously) lists every keyboard the
// user has EVER enabled, not the one currently on screen — confirmed via a real device log to
// never flip back off after switching away from SLKey. `textInputMode` read off the actual first
// responder is scoped to what's showing right now, which is what "current" actually means here.
extension UIResponder {
    private static weak var _currentFirstResponder: UIResponder?
    static var currentFirstResponder: UIResponder? {
        _currentFirstResponder = nil
        UIApplication.shared.sendAction(#selector(reportAsFirstResponder), to: nil, from: nil, for: nil)
        return _currentFirstResponder
    }
    @objc private func reportAsFirstResponder() {
        UIResponder._currentFirstResponder = self
    }
}

struct ChatView: View {
    @EnvironmentObject var store: AppStore
    @EnvironmentObject var callManager: CallManager
    let contact: Contact

    // MessageViewData has NO mediaData — fetching it never triggers SwiftData faults
    @State private var cachedMessages: [MessageViewData] = []
    // Snapshot taken once, right before markChatRead() clears the unread state — the divider
    // in the message list stays put for this viewing session even as messages below it get
    // marked read, same as Telegram/iMessage. nil once everything was already read on open.
    @State private var firstUnreadMsgId: String? = nil
    // Snapshot taken the same way as firstUnreadMsgId, just before markReactionsSeen() clears
    // it — MessageBubble plays its attention-grabbing pop-in for exactly these msgIds on
    // appear, so a reaction that arrived while the chat was closed still gets noticed once
    // it's opened, not just one arriving live while already open (see AppStore.swift's
    // handleReaction/theirReactionSeen doc comments).
    @State private var unseenReactionMsgIds: Set<String> = []
    // Custom long-press overlay state (MessageActionOverlay) — replaces .contextMenu, see
    // that file's doc comment for why (ControlGroup's 3-per-row ceiling). Each bubble's
    // position is carried as a lazy Anchor via BubbleAnchorPreferenceKey (see that type's own
    // doc comment for why NOT a plain CGRect preference — the first version of this froze
    // scrolling solid), resolved via .overlayPreferenceValue below only for whichever single
    // message is under actionOverlayMsgId, only while the overlay is actually showing.
    @State private var actionOverlayMsgId: String? = nil
    @State private var emojiPickerTargetId: String? = nil
    @State private var overlayShareContent: ShareContent? = nil
    @State private var inputText = ""
    @State private var errorMsg: String? = nil
    @State private var showChatSettings = false
    @State private var reportTarget: ReportTarget? = nil
    @State private var photoItems: [PhotosPickerItem] = []
    @State private var showPhotosPicker = false
    @State private var showFilePicker = false
    // True while a picked video is being re-encoded (compressVideo) — that step takes a few
    // seconds before any bubble exists, so without this the tap would look like it did nothing.
    @State private var isPreparingVideo = false
    @State private var isRecording = false
    @State private var recorder: AVAudioRecorder? = nil
    @State private var recordingURL: URL? = nil
    @State private var recordingSeconds: Int = 0
    @State private var recordingTimer: Timer? = nil
    @State private var oversizedAlert: String? = nil
    @State private var replyingTo: MessageViewData? = nil
    // Mutually exclusive with replyingTo — starting an edit clears any active reply and vice
    // versa (see the "Редактировать" action's onEdit closure and sendText() below). Holds the
    // ORIGINAL message's msgId being edited; the compose field itself is repurposed to hold the
    // in-progress edited text rather than a separate editor UI.
    @State private var editingMsgId: String? = nil
    // Not content-sniffing — SLKey types plain Unicode Cyrillic under the hood, so there's no
    // reliable way to detect "this text should render as Church Slavonic" from its content
    // alone. See Message.churchFont's doc comment for the full story. Auto-follows the active
    // keyboard below (via the compose field's own textInputMode, not activeInputModes — see the
    // UIResponder extension above for why that distinction matters); kept as a manual toggle too
    // since the button doesn't hurt as a fallback/override.
    @State private var churchFontEnabled = false
    @FocusState private var composeFieldFocused: Bool
    @State private var showAIKeySheet = false

    // BYOK AI bot (empty for everyone else) and the provider its messages go with now.
    private var aiProviders: [AIProvider] { _ = store.aiStateVersion; return store.aiProviders(for: contact.cellId) }
    private var aiProvider: AIProvider? { _ = store.aiStateVersion; return store.aiProvider(for: contact.cellId) }
    private var isAIBot: Bool { !aiProviders.isEmpty }

    // `body` itself was hitting "unable to type-check this expression in reasonable time" once
    // split out the ForEach (messageBubbleView) wasn't enough — the WHOLE chain below it
    // (toolbar, 3 sheets, 2 alerts, an overlayPreferenceValue+nested GeometryReader, 3
    // onChange, a fileImporter) is one giant expression too. Split into chatContent (the
    // actual screen) plus a handful of `<Content: View> -> some View` helper functions, each
    // checked independently against its own signature instead of all at once — same fix as
    // messageBubbleView, just for the modifier chain rather than the ForEach body. Confirmed
    // this is exactly what a body-only vs. whole-expression compiler error distinguishes.
    var body: some View {
        withMediaPickers(
            withChatAlertsAndChanges(
                withActionOverlayAndPickers(
                    chatContent
                        .navigationTitle(displayName)
                        .navigationBarTitleDisplayMode(.inline)
                        .toolbar { chatToolbar }
                        .sheet(isPresented: $showChatSettings) {
                            ChatSettingsSheet(contact: contact)
                        }
                        .background {
                            // Own anchor view so it doesn't share a modifier chain with the
                            // settings sheet above.
                            Color.clear.sheet(isPresented: $showAIKeySheet) {
                                AIKeySheet(contact: contact, providers: aiProviders, current: aiProvider)
                            }
                        }
                )
            )
        )
    }

    private var chatContent: some View {
        VStack(spacing: 0) {
            if store.looksLikeImpersonation(cellId: contact.cellId, name: displayName) {
                ImpersonationWarningBanner()
            }
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 8) {
                        ForEach(cachedMessages) { msg in
                            if msg.msgId == firstUnreadMsgId {
                                unreadDivider
                            }
                            messageBubbleView(for: msg, proxy: proxy)
                                .id(msg.msgId)
                        }
                        ForEach(store.incomingTransfers[contact.cellId] ?? [], id: \.rowId) { transfer in
                            IncomingTransferRow(transfer: transfer)
                        }
                    }
                    .padding()
                }
                .onChange(of: cachedMessages.count) { oldCount, newCount in
                    // Only auto-scroll when the count actually GREW (a new message arrived) —
                    // deleting a message ("delete for me", hard-delete) also changes this count
                    // but should never jump the view anywhere. Found on device 2026-08-28:
                    // deleting a message you were looking at yanked the scroll straight to the
                    // bottom of the whole chat, very disorienting. "Delete for everyone" never
                    // had this problem in the first place — it soft-deletes (row stays, isRemoved
                    // flips), so the count never changes and this handler never fires for it.
                    guard newCount > oldCount, let last = cachedMessages.last else { return }
                    withAnimation { proxy.scrollTo(last.msgId, anchor: .bottom) }
                }
                // Runs every time the chat becomes visible (not just when the message count
                // changes) — user feedback 2026-08-25: reopening a chat landed wherever it was
                // last scrolled instead of the new messages, because relying on the count-change
                // handler alone misses the case where this view instance was reused (still in
                // the nav stack from a backgrounded session) and its cachedMessages had already
                // been updated to the new count while off-screen, so onChange never re-fired.
                // Lands on the first unread message (with the divider above it), not blindly at
                // the very bottom, so a burst of missed messages is scrolled TO, not past.
                .onAppear {
                    loadChat()
                    // Two hops, not one: cachedMessages just went from empty (or stale) to its
                    // real content this same tick, and LazyVStack needs a render pass to actually
                    // create rows for the new ids before scrollTo(id:) can find them — a single
                    // async still lands before that pass on first appearance, so scrollTo silently
                    // no-ops and the view is left wherever it happened to be. Confirmed on device
                    // 2026-08-25: single-hop version still failed to land on open.
                    DispatchQueue.main.async {
                        DispatchQueue.main.async {
                            if let firstUnread = firstUnreadMsgId {
                                proxy.scrollTo(firstUnread, anchor: .top)
                            } else if let last = cachedMessages.last {
                                proxy.scrollTo(last.msgId, anchor: .bottom)
                            }
                        }
                    }
                }
            }

            if let err = errorMsg {
                Text(err).font(.caption).foregroundStyle(.red).padding(.horizontal)
            }
            Divider()

            if let r = replyingTo {
                HStack(spacing: 8) {
                    Rectangle().fill(Color.accentColor).frame(width: 3)
                    VStack(alignment: .leading, spacing: 1) {
                        Text(r.fromMe ? String(localized: "Вы") : displayName)
                            .font(.caption.bold()).foregroundStyle(Color.accentColor)
                        Text(messagePreviewText(r))
                            .font(.caption).foregroundStyle(.secondary).lineLimit(3)
                    }
                    Spacer()
                    Button { replyingTo = nil } label: {
                        Image(systemName: "xmark.circle.fill").foregroundStyle(.secondary)
                    }
                }
                .padding(.horizontal, 12).padding(.vertical, 6)
                .background(Color(.systemGray6))
            }

            if editingMsgId != nil {
                HStack(spacing: 8) {
                    Rectangle().fill(Color.accentColor).frame(width: 3)
                    Image(systemName: "pencil").font(.caption).foregroundStyle(Color.accentColor)
                    Text("Редактирование").font(.caption.bold()).foregroundStyle(Color.accentColor)
                    Spacer()
                    Button { editingMsgId = nil; inputText = "" } label: {
                        Image(systemName: "xmark.circle.fill").foregroundStyle(.secondary)
                    }
                }
                .padding(.horizontal, 12).padding(.vertical, 6)
                .background(Color(.systemGray6))
            }

            if store.isIdentityDeleted(cellId: contact.cellId) {
                Text("Личность удалена — переписка недоступна")
                    .font(.footnote).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity).padding()
            } else if store.isBlocked(contact.cellId) {
                BlockedChatBar(cellId: contact.cellId)
            } else if isAIBot && aiProvider == nil {
                AIKeyNeededBar { showAIKeySheet = true }
            } else if isRecording {
                HStack(spacing: 12) {
                    Circle().fill(.red).frame(width: 10, height: 10)
                    Text(String(format: "%d:%02d", recordingSeconds / 60, recordingSeconds % 60))
                        .font(.headline.monospacedDigit())
                    Spacer()
                    Button(action: cancelRecording) {
                        Image(systemName: "xmark.circle").font(.title2).foregroundStyle(.secondary)
                    }
                    Button(action: stopAndSendRecording) {
                        Image(systemName: "checkmark.circle.fill").font(.title2).foregroundStyle(.green)
                    }
                }
                .padding()
            } else {
                // Sending before the client has actually finished connecting used to just throw
                // NevdError.notConnected ("Not connected") and silently lose the typed message —
                // a real pre-existing gap, newly exposed by the browse→register→bot-chat path
                // being fast enough to reach this screen before the connect handshake finishes.
                // Disabling instead of letting the tap fail avoids that dead end; the caption
                // tells the user why, rather than a greyed-out button with no explanation.
                if store.connectionStatus != "connected" {
                    Text(store.connectionStatus == "disconnected" ? "Нет соединения" : "Подключение…")
                        .font(.caption).foregroundStyle(.secondary)
                        .padding(.horizontal).padding(.top, 4)
                }
                if isPreparingVideo {
                    HStack(spacing: 6) {
                        ProgressView().controlSize(.small)
                        Text("Подготовка видео…")
                    }
                    .font(.caption).foregroundStyle(.secondary)
                    .padding(.horizontal).padding(.top, 4)
                }
                if let p = aiProvider {
                    HStack {
                        Text(String(format: String(localized: "Answers via %@ · your key"), p.displayName))
                        Spacer()
                        Button("Change") { showAIKeySheet = true }
                    }
                    .font(.caption).foregroundStyle(.secondary)
                    .padding(.horizontal).padding(.top, 4)
                }
                HStack(spacing: 8) {
                    // Single "+" replacing 3 separate icons (photo/file/church-font) — user
                    // feedback 2026-08-24: three buttons ate too much width from the text field.
                    // The "+" itself picks up the accent color whenever church font is on, so
                    // that state stays visible at a glance without needing its own dedicated
                    // button — same idea as the compose field's own font already showing it.
                    Menu {
                        // An AI bot answers text only (node/bot.py) — no media for it.
                        if !isAIBot {
                            Button { showPhotosPicker = true } label: {
                                Label("Фото или видео", systemImage: "photo.on.rectangle")
                            }
                            Button { showFilePicker = true } label: {
                                Label("Файл", systemImage: "paperclip")
                            }
                        }
                        Button { churchFontEnabled.toggle() } label: {
                            Label("Церковный шрифт", systemImage: churchFontEnabled ? "checkmark" : "textformat.alt")
                        }
                    } label: {
                        Image(systemName: "plus.circle.fill").font(.title2)
                            .foregroundStyle(churchFontEnabled ? Color.accentColor : .secondary)
                    }
                    .photosPicker(isPresented: $showPhotosPicker, selection: $photoItems,
                                  matching: .any(of: [.images, .videos]))
                    TextField("Message", text: $inputText, axis: .vertical)
                        .textFieldStyle(.roundedBorder).lineLimit(1...5)
                        .font(churchFontEnabled ? .custom("Ponomar-Regular", size: 17) : .body)
                        .focused($composeFieldFocused)
                        .onReceive(NotificationCenter.default.publisher(for: UITextInputMode.currentInputModeDidChangeNotification)) { _ in
                            guard composeFieldFocused else { return }
                            churchFontEnabled = UIResponder.currentFirstResponder?.textInputMode?.primaryLanguage == "cu"
                        }
                    if !isAIBot {
                        Button(action: startRecording) {
                            Image(systemName: "mic.circle.fill").font(.title2).foregroundStyle(.tint)
                        }
                        .disabled(store.connectionStatus != "connected")
                    }
                    Button(action: sendText) {
                        Image(systemName: "arrow.up.circle.fill").font(.title2)
                    }
                    .disabled(inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                              || store.connectionStatus != "connected")
                }
                .padding()
            }
        }
    }

    @ToolbarContentBuilder
    private var chatToolbar: some ToolbarContent {
        ToolbarItem(placement: .principal) {
            HStack(spacing: 8) {
                if store.isIdentityDeleted(cellId: contact.cellId) {
                    Circle().fill(Color(.systemGray4)).frame(width: 28, height: 28)
                } else if let avatar = store.contactAvatars[contact.cellId] {
                    Image(uiImage: avatar)
                        .resizable().scaledToFill()
                        .frame(width: 28, height: 28)
                        .clipShape(Circle())
                }
                if store.isIdentityDeleted(cellId: contact.cellId) {
                    VStack(alignment: .leading, spacing: 0) {
                        Text(displayName).font(.headline)
                        Text("Личность удалена").font(.caption2).foregroundStyle(.secondary)
                    }
                } else {
                    Text(displayName).font(.headline)
                    OfficialNameBadge(cellId: contact.cellId, name: displayName)
                }
            }
            .onAppear { store.loadAvatarIfCached(for: contact.cellId) }
        }
        ToolbarItem(placement: .topBarTrailing) {
            HStack(spacing: 16) {
                Button {
                    callManager.startCall(to: contact.cellId, contactName: displayName)
                } label: {
                    Image(systemName: "phone.fill")
                }
                .disabled(!callManager.state.isIdle || store.isIdentityDeleted(cellId: contact.cellId)
                          || store.isBlocked(contact.cellId) || isAIBot)
                if !isSavedContact {
                    Button { store.addContact(contact) } label: {
                        Image(systemName: "person.badge.plus")
                    }
                }
                Button { showChatSettings = true } label: {
                    Image(systemName: "gearshape")
                }
            }
        }
    }

    @ViewBuilder
    private func withChatAlertsAndChanges<Content: View>(_ content: Content) -> some View {
        content
        .onChange(of: store.messageSeq) { _, _ in
            cachedMessages = store.messageViewData(for: contact.cellId)
            // A message arriving while the chat is already open is being watched live, not
            // "left unread and come back to" — doesn't retroactively grow the divider snapshot.
            store.markChatRead(chatId: contact.cellId)
            // Same reasoning for reactions: MessageBubble's own live .transition already
            // animates a reaction that just arrived while this chat is open, so mark it seen
            // right away rather than leaving it queued to pop again on the next open.
            store.markReactionsSeen(chatId: contact.cellId)
        }
        // markChatRead() no-ops while the socket isn't connected yet (e.g. chat opened
        // straight from a push tap before the connect/failover pass finishes) — retry
        // once it's up.
        .onChange(of: store.connectionStatus) { _, status in
            if status == "connected" { store.markChatRead(chatId: contact.cellId) }
        }
        .alert("Файл слишком большой", isPresented: .init(
            get: { oversizedAlert != nil }, set: { if !$0 { oversizedAlert = nil } }
        )) { Button("OK") { oversizedAlert = nil } } message: { Text(oversizedAlert ?? "") }
        .alert("Хранилище заполнено", isPresented: .init(
            get: { store.storageAlert != nil }, set: { if !$0 { store.storageAlert = nil } }
        )) { Button("OK") { store.storageAlert = nil } } message: { Text(store.storageAlert ?? "") }
    }

    @ViewBuilder
    private func withActionOverlayAndPickers<Content: View>(_ content: Content) -> some View {
        content
        // Attached to the VStack that WRAPS the ScrollView, not to anything inside it — a
        // ScrollView clips its content to its own bounds, so an overlay on a bubble deep
        // inside it can't paint a full-screen dim or extend past the visible scroll area.
        // Sibling-to-the-ScrollView is what lets this actually cover the whole chat screen.
        // overlayPreferenceValue's GeometryReader is what turns a bubble's lazy Anchor into an
        // actual CGRect (geo[anchor]) — deliberately done here, once, only for the one message
        // under actionOverlayMsgId, not per-bubble per-scroll-frame (see
        // BubbleAnchorPreferenceKey's doc comment).
        .overlayPreferenceValue(BubbleAnchorPreferenceKey.self) { anchors in
            GeometryReader { geo in
                if let id = actionOverlayMsgId,
                   let msg = cachedMessages.first(where: { $0.msgId == id }),
                   let anchor = anchors[id] {
                    MessageActionOverlay(
                        message: msg,
                        anchorFrame: geo[anchor],
                        onReact: { emoji in store.toggleReaction(msgId: id, emoji: emoji, chatId: msg.chatId) },
                        onMore: {
                            actionOverlayMsgId = nil
                            emojiPickerTargetId = id
                        },
                        onReply: { replyingTo = msg; editingMsgId = nil },
                        onShare: { shareOverlayMessage(msg) },
                        onEdit: { editingMsgId = id; replyingTo = nil; inputText = msg.text },
                        onDeleteEverywhere: { store.deleteForEveryone(msgId: id, chatId: msg.chatId) },
                        onDelete: { store.deleteMessage(msgId: id, chatId: msg.chatId) },
                        onReport: {
                            reportTarget = ReportTarget(cellId: contact.cellId, name: displayName,
                                                        messageText: msg.text, messageDate: msg.timestamp)
                        },
                        onDismiss: { actionOverlayMsgId = nil }
                    )
                }
            }
        }
        .animation(.easeOut(duration: 0.15), value: actionOverlayMsgId)
        .sheet(item: .init(
            get: { emojiPickerTargetId.map(EmojiPickerTarget.init) },
            set: { if $0 == nil { emojiPickerTargetId = nil } }
        )) { target in
            EmojiPickerSheet { emoji in
                store.toggleReaction(msgId: target.id, emoji: emoji, chatId: contact.cellId)
            }
        }
        .sheet(item: $reportTarget) { target in
            ReportSheet(target: target)
        }
        .sheet(item: $overlayShareContent) { shareContent in
            ActivityView(items: shareContent.items)
        }
    }

    @ViewBuilder
    private func withMediaPickers<Content: View>(_ content: Content) -> some View {
        content
        .onChange(of: photoItems) { _, items in
            guard !items.isEmpty else { return }
            Task {
                // Sequential, not concurrent — sendChunkedStream already streams one file at a
                // time off disk (see AppStore's own notes on the old whole-file-in-RAM bug);
                // firing every picked photo's send at once would just contend for the same
                // socket/chunking pipeline for no real speed gain.
                for item in items {
                    if item.supportedContentTypes.contains(where: { $0.conforms(to: .movie) }) {
                        await sendPickedVideo(item)
                        continue
                    }
                    if let data = try? await item.loadTransferable(type: Data.self),
                       let compressed = compressImage(data, maxDimension: 1280, quality: 0.72) {
                        do { try await store.send(mediaData: compressed, mime: "image/jpeg", name: nil, to: contact) }
                        catch { errorMsg = String(localized: "Сообщение не отправлено") }
                    }
                }
                photoItems = []
            }
        }
        .fileImporter(isPresented: $showFilePicker,
                      allowedContentTypes: [.data, .pdf, .plainText, .audio],
                      allowsMultipleSelection: false) { result in
            guard let url = try? result.get().first else { return }
            let accessing = url.startAccessingSecurityScopedResource()
            // Read file size from metadata — no file content loaded into RAM
            let fileSize = (try? url.resourceValues(forKeys: [.fileSizeKey]))?.fileSize ?? 0
            guard fileSize <= maxFileSizeBytes else {
                if accessing { url.stopAccessingSecurityScopedResource() }
                let size = ByteCountFormatter.string(fromByteCount: Int64(fileSize), countStyle: .file)
                let maxSize = ByteCountFormatter.string(fromByteCount: Int64(maxFileSizeBytes), countStyle: .file)
                oversizedAlert = String(localized: "\(url.lastPathComponent) (\(size))\n\nМаксимальный размер — \(maxSize).")
                return
            }
            let mime = UTType(filenameExtension: url.pathExtension)?.preferredMIMEType ?? "application/octet-stream"
            let name = url.lastPathComponent
            Task {
                defer { if accessing { url.stopAccessingSecurityScopedResource() } }
                do { try await store.send(fileURL: url, mime: mime, name: name, to: contact) }
                catch { await MainActor.run { errorMsg = String(localized: "Сообщение не отправлено") } }
            }
        }
    }

    // MARK: - Helpers

    private var displayName: String {
        if !contact.alias.isEmpty { return contact.alias }
        let member = store.nodeMembers.first(where: { $0.cellId == contact.cellId })
        return member?.displayName.isEmpty == false ? member!.displayName : String(localized: "Chat")
    }

    private var isSavedContact: Bool {
        store.contacts.contains(where: { $0.cellId == contact.cellId })
    }

    private var unreadDivider: some View {
        HStack(spacing: 8) {
            Rectangle().fill(Color.accentColor.opacity(0.4)).frame(height: 1)
            Text("Новые")
                .font(.caption2.bold())
                .foregroundStyle(Color.accentColor)
            Rectangle().fill(Color.accentColor.opacity(0.4)).frame(height: 1)
        }
        .padding(.vertical, 2)
    }

    /// Pulled out of the ForEach body as its own function with an explicit return type —
    /// MessageBubble's initializer call inline (message/progress/legacyLoadMedia ternary/
    /// replyPreview closure/4 action closures/needsReactionRevealPop/onLongPress/onJumpToReply
    /// closure, all in one expression) made the compiler give up with "unable to type-check
    /// this expression in reasonable time" once onLongPress/needsReactionRevealPop were added
    /// (confirmed on device 2026-08-26/27 build). Splitting it here lets the compiler infer
    /// each piece against this function's own signature instead of the whole call at once.
    @ViewBuilder
    private func messageBubbleView(for msg: MessageViewData, proxy: ScrollViewProxy) -> some View {
        MessageBubble(
            message: msg,
            progress: store.messageProgress[msg.msgId],
            legacyLoadMedia: msg.mediaFile == nil
                ? { store.loadMediaLegacy(msgId: msg.msgId) }
                : nil,
            replyPreview: msg.replyToMsgId.flatMap { rid in
                cachedMessages.first(where: { $0.msgId == rid })
            },
            onDelete: { store.deleteMessage(msgId: msg.msgId, chatId: msg.chatId) },
            onReply: { replyingTo = msg },
            onReact: { emoji in store.toggleReaction(msgId: msg.msgId, emoji: emoji, chatId: msg.chatId) },
            needsReactionRevealPop: unseenReactionMsgIds.contains(msg.msgId),
            onLongPress: { if !msg.isRemoved { actionOverlayMsgId = msg.msgId } },
            isActionOverlayTarget: actionOverlayMsgId == msg.msgId,
            onJumpToReply: { rid in
                withAnimation { proxy.scrollTo(rid, anchor: .center) }
            },
            onRetry: { store.retrySend(msgId: msg.msgId, to: contact) },
            showsMarkdown: !msg.fromMe && store.isAIBot(contact.cellId)
        )
    }

    /// Real Message objects (not the lighter MessageViewData) specifically so
    /// firstUnreadMsgId can read readAckSent — see that field's own doc comment.
    /// Must run BEFORE markChatRead(), which is what clears the state being snapshotted.
    private func loadChat() {
        let real = store.messages(for: contact.cellId)
        firstUnreadMsgId = real.first(where: { !$0.fromMe && !$0.readAckSent })?.msgId
        unseenReactionMsgIds = Set(store.unseenReactionMsgIds(for: contact.cellId))
        // Before snapshotting cachedMessages — see this method's own doc comment for why
        // bumpStuckSentMessages alone doesn't catch a message that was already stuck.
        store.reconcileStuckMessages(chatId: contact.cellId)
        cachedMessages = store.messageViewData(for: contact.cellId)
        store.markChatRead(chatId: contact.cellId)
        store.markReactionsSeen(chatId: contact.cellId)
    }

    /// MessageActionOverlay's "Поделиться" — deliberately a fresh, simpler implementation
    /// rather than reusing MessageBubble's own shareThisMessage()/shareMedia(): those depend
    /// on that specific bubble instance's local mediaData @State (still needed there for the
    /// audio player's own inline share button, so left untouched), which isn't reachable from
    /// here. Text and on-disk-media cases need nothing but the message itself; only the
    /// legacy no-mediaFile fallback needs an explicit load, via the same
    /// store.loadMediaLegacy() MessageBubble's own legacyLoadMedia closure calls.
    private func shareOverlayMessage(_ msg: MessageViewData) {
        if msg.type == .text {
            overlayShareContent = ShareContent(items: [msg.text])
            return
        }
        if let filename = msg.mediaFile {
            overlayShareContent = ShareContent(items: [nevodMediaDirectory.appendingPathComponent(filename)])
            return
        }
        guard let data = store.loadMediaLegacy(msgId: msg.msgId) else { return }
        let name = msg.mediaName ?? (msg.type == .audio ? "voice.m4a" : "file")
        let url = FileManager.default.temporaryDirectory.appendingPathComponent(name)
        try? data.write(to: url)
        overlayShareContent = ShareContent(items: [url])
    }

    private func sendText() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        if let editId = editingMsgId {
            inputText = ""; errorMsg = nil; editingMsgId = nil
            store.editMessage(msgId: editId, chatId: contact.cellId, newText: text)
            return
        }
        let replyId = replyingTo?.msgId
        let usesChurchFont = churchFontEnabled
        inputText = ""; errorMsg = nil; replyingTo = nil
        Task {
            do { try await store.send(text: text, to: contact, replyTo: replyId, churchFont: usesChurchFont) }
            catch { errorMsg = String(localized: "Сообщение не отправлено") }
        }
    }

    // MARK: - Voice recording

    private func startRecording() {
        AVAudioApplication.requestRecordPermission { granted in
            guard granted else { return }
            DispatchQueue.main.async {
                let url = FileManager.default.temporaryDirectory
                    .appendingPathComponent(UUID().uuidString + ".m4a")
                let settings: [String: Any] = [
                    AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                    AVSampleRateKey: 22050,
                    AVNumberOfChannelsKey: 1,
                    AVEncoderBitRateKey: 32000,
                ]
                do {
                    try AVAudioSession.sharedInstance()
                        .setCategory(.playAndRecord, mode: .default, options: .defaultToSpeaker)
                    try AVAudioSession.sharedInstance().setActive(true)
                    self.recorder = try AVAudioRecorder(url: url, settings: settings)
                    self.recorder?.record()
                    self.recordingURL = url
                    self.recordingSeconds = 0
                    self.isRecording = true
                    self.recordingTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { _ in
                        self.recordingSeconds += 1
                    }
                } catch { self.errorMsg = error.localizedDescription }
            }
        }
    }

    private func stopAndSendRecording() {
        recordingTimer?.invalidate(); recordingTimer = nil
        recorder?.stop(); recorder = nil
        isRecording = false
        guard let url = recordingURL else { return }
        recordingURL = nil
        if let data = try? Data(contentsOf: url) {
            Task {
                do { try await store.send(mediaData: data, mime: "audio/m4a", name: "voice.m4a", to: contact) }
                catch { errorMsg = String(localized: "Сообщение не отправлено") }
            }
        }
        try? FileManager.default.removeItem(at: url)
        try? AVAudioSession.sharedInstance().setActive(false)
    }

    private func cancelRecording() {
        recordingTimer?.invalidate(); recordingTimer = nil
        recorder?.stop(); recorder = nil
        isRecording = false
        if let url = recordingURL { try? FileManager.default.removeItem(at: url) }
        recordingURL = nil
        try? AVAudioSession.sharedInstance().setActive(false)
    }

    /// Picked video → file on disk (never Data in RAM) → re-encoded to 720p MP4 → streamed
    /// like any other file. Re-encoding is what makes this usable at all: a raw iPhone clip is
    /// HEVC 4K at roughly 6 MB per 10 s, so even a short one blows past maxFileSizeBytes.
    private func sendPickedVideo(_ item: PhotosPickerItem) async {
        isPreparingVideo = true
        defer { isPreparingVideo = false }
        guard let picked = try? await item.loadTransferable(type: PickedMovie.self) else {
            errorMsg = String(localized: "Не удалось загрузить видео")
            return
        }
        defer { try? FileManager.default.removeItem(at: picked.url) }
        guard let out = await compressVideo(picked.url) else {
            errorMsg = String(localized: "Не удалось сжать видео")
            return
        }
        defer { try? FileManager.default.removeItem(at: out.deletingLastPathComponent()) }
        let size = (try? out.resourceValues(forKeys: [.fileSizeKey]))?.fileSize ?? 0
        guard size <= maxFileSizeBytes else {
            let sizeStr = ByteCountFormatter.string(fromByteCount: Int64(size), countStyle: .file)
            let maxSize = ByteCountFormatter.string(fromByteCount: Int64(maxFileSizeBytes), countStyle: .file)
            oversizedAlert = String(localized: "\(out.lastPathComponent) (\(sizeStr))\n\nМаксимальный размер — \(maxSize).")
            return
        }
        isPreparingVideo = false   // the bubble's own progress bar takes over from here
        do { try await store.send(fileURL: out, mime: "video/mp4", name: out.lastPathComponent, to: contact) }
        catch { errorMsg = String(localized: "Сообщение не отправлено") }
    }

    /// Tries 720p first; if that still doesn't fit the limit (a long clip), falls back to
    /// MediumQuality (~360p, much lower bitrate) rather than refusing outright. Returns the
    /// last successful attempt either way — the caller does the final size check. Each
    /// attempt gets its own tmp subfolder so the file itself can carry a readable name.
    private func compressVideo(_ src: URL) async -> URL? {
        let asset = AVURLAsset(url: src)
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd_HH-mm-ss"
        let name = "video_\(fmt.string(from: Date())).mp4"
        var result: URL? = nil
        for preset in [AVAssetExportPreset1280x720, AVAssetExportPresetMediumQuality] {
            guard let session = AVAssetExportSession(asset: asset, presetName: preset) else { continue }
            let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
            try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            let out = dir.appendingPathComponent(name)
            session.outputURL = out
            session.outputFileType = .mp4
            session.shouldOptimizeForNetworkUse = true
            await session.export()
            guard session.status == .completed else {
                nlog("video export failed preset=\(preset) err=\(session.error?.localizedDescription ?? "nil")")
                try? FileManager.default.removeItem(at: dir)
                continue
            }
            if let prev = result { try? FileManager.default.removeItem(at: prev.deletingLastPathComponent()) }
            result = out
            let size = (try? out.resourceValues(forKeys: [.fileSizeKey]))?.fileSize ?? 0
            nlog("video export preset=\(preset) size=\(size / 1024)KB")
            if size <= maxFileSizeBytes { break }
        }
        return result
    }

    private func compressImage(_ data: Data, maxDimension: CGFloat, quality: CGFloat) -> Data? {
        guard let src = UIImage(data: data) else { return nil }
        let longest = max(src.size.width, src.size.height)
        let scale   = longest > maxDimension ? maxDimension / longest : 1.0
        let newSize = CGSize(width: src.size.width * scale, height: src.size.height * scale)
        let renderer = UIGraphicsImageRenderer(size: newSize)
        let resized  = renderer.image { _ in src.draw(in: CGRect(origin: .zero, size: newSize)) }
        return resized.jpegData(compressionQuality: quality)
    }
}

// MARK: - Message Bubble
// Takes MessageViewData (no binary) + a lazy loader closure.
// No @EnvironmentObject → SwiftUI skips re-render when other store properties change.

struct MessageBubble: View {
    let message: MessageViewData
    let progress: Double?
    /// Non-nil only for legacy messages that still have mediaData stored in SwiftData.
    /// New messages use message.mediaFile and load off main thread.
    let legacyLoadMedia: (() -> Data?)?
    /// The message this one replies to, looked up from cachedMessages — nil if
    /// message.replyToMsgId is nil, or if the original has scrolled out of the loaded window.
    let replyPreview: MessageViewData?
    let onDelete: () -> Void
    let onReply: () -> Void
    let onReact: (String) -> Void
    /// True for exactly the messages ChatView snapshotted as having an unseen reaction when
    /// this chat was opened — drives the extra attention-grabbing pop on appear, on top of
    /// (not instead of) the live .transition below.
    let needsReactionRevealPop: Bool
    /// Long-press anywhere on the bubble — ChatView owns what happens next (MessageActionOverlay,
    /// positioned from the Anchor this bubble reports via BubbleAnchorPreferenceKey below).
    /// Replaced .contextMenu entirely 2026-08-26 — see MessageActionOverlay.swift's doc comment
    /// for why.
    let onLongPress: () -> Void
    /// True for exactly the one bubble currently under ChatView's actionOverlayMsgId — gates
    /// .anchorPreference below to that single bubble instead of every bubble reporting one
    /// unconditionally. Confirmed on device 2026-08-27: even the lazy Anchor version (not the
    /// original eager-CGRect one, already fixed once) still added enough per-cell overhead
    /// that fast repeated scrolling made LazyVStack's constant cell recycling visibly stutter
    /// and periodically stall. A message is only ever the active overlay target for the brief
    /// window the overlay is open, so this reduces "how many bubbles pay this cost, ever" from
    /// "every visible one, every frame" to "at most one, only while pressed."
    let isActionOverlayTarget: Bool
    let onJumpToReply: (String) -> Void
    /// Tap on the failed bubble's "Сообщение не отправлено. Повторить отправку?" line.
    var onRetry: () -> Void = {}
    /// An AI bot's reply: its Markdown (bold, italic, links, headings, bullets) is drawn rather
    /// than shown as "**…**" (App Store screenshots 2026-10-21). People's messages stay
    /// literal, so a stray "*" in what someone typed changes nothing.
    var showsMarkdown = false

    // Only consulted when needsReactionRevealPop is true (see reactionBadges below) — every
    // other bubble ignores this and renders its badge in final state immediately, same as
    // before this feature existed.
    @State private var reactionRevealed = false
    @State private var isLongPressing = false
    @State private var mediaData: Data? = nil
    @State private var cachedImage: UIImage? = nil
    // Bumped when the phone is unlocked so a bubble that appeared while media files were
    // unreadable (protected, see AppStore.protectFile) loads them then.
    @State private var unlockRetry = 0
    @State private var mediaLoaded = false
    // A single Identifiable optional instead of separate `shareItems`/`showShare` bools —
    // .sheet(isPresented:) reading a SEPARATE @State var for its content is a known SwiftUI
    // race (confirmed via device screenshots 2026-08-22: the share sheet opened blank — no
    // filename, no preview, no app row — on the first tap every time, then showed the right
    // content on a second, unrelated tap). A 0.5s delay before setting the two vars did NOT
    // fix it, ruling out a context-menu-dismissal timing issue — the real cause is that
    // .sheet(isPresented:)'s content closure can capture shareItems' value from BEFORE that
    // same action's assignment actually committed. .sheet(item:) hands the unwrapped value
    // straight to the content closure as a parameter, which SwiftUI guarantees is never stale.
    @State private var shareContent: ShareContent? = nil
    @State private var photoSaved = false
    @State private var videoDuration: Double? = nil
    @State private var previewURL: URL? = nil

    var body: some View {
        HStack {
            if message.fromMe { Spacer(minLength: 40) }
            VStack(alignment: message.fromMe ? .trailing : .leading, spacing: 2) {
                if message.replyToMsgId != nil { replyQuoteView }
                bubbleContent
                    // Photos already clip themselves to rounded corners (imageBubble) and read
                    // better edge-to-edge — the tinted bubble behind them was just a colored
                    // border, not a background anything shows through (user feedback 2026-08-25).
                    .background(message.type == .image || message.type == .video ? Color.clear
                                : (message.fromMe ? Color.accentColor : Color(.systemGray5)))
                    .foregroundStyle(message.fromMe ? .white : .primary)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .scaleEffect(isLongPressing ? 0.97 : 1.0)
                    .animation(.easeOut(duration: 0.15), value: isLongPressing)
                    // Reports this bubble's position as a lazy Anchor, gated to only fire when
                    // THIS bubble is the active overlay target — see ConditionalBubbleAnchor's
                    // and BubbleAnchorPreferenceKey's doc comments for why it has to be
                    // conditional, not just lazy: an unconditional (but still lazy) version
                    // still stuttered under fast repeated scrolling (confirmed on device
                    // 2026-08-27).
                    .modifier(ConditionalBubbleAnchor(isActive: isActionOverlayTarget, msgId: message.msgId))
                    .onLongPressGesture(minimumDuration: 0.35, maximumDistance: 24, pressing: { pressing in
                        isLongPressing = pressing
                    }, perform: {
                        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                        onLongPress()
                    })
                if message.myReaction != nil || message.theirReaction != nil {
                    reactionBadges
                        // Scale+fade in/out rather than just popping into existence — user
                        // feedback 2026-08-24: wanted a Telegram-like attention-grabbing
                        // appearance instead of the badge silently materializing on the next
                        // unrelated re-render. Covers a reaction arriving while this chat is
                        // already open (theirReaction flips from nil to non-nil, a real value
                        // change SwiftUI's transition machinery reacts to).
                        .transition(.scale(scale: 0.5).combined(with: .opacity))
                        // A reaction that was already there when the chat opened (user was away
                        // when it arrived) is NOT a value change on mount, so the .transition
                        // above never fires for it — nothing would draw the eye to it at all.
                        // User feedback 2026-08-26: "принимающая сторона может реакции не
                        // заметить" (the recipient might miss the reaction). This separately
                        // pops it in on first appear, once, only for messages ChatView flagged
                        // as unseen (needsReactionRevealPop) — every other bubble is unaffected.
                        .scaleEffect(needsReactionRevealPop && !reactionRevealed ? 0.4 : 1.0)
                        .opacity(needsReactionRevealPop && !reactionRevealed ? 0 : 1)
                        .onAppear {
                            guard needsReactionRevealPop, !reactionRevealed else { return }
                            withAnimation(.spring(response: 0.35, dampingFraction: 0.55).delay(0.15)) {
                                reactionRevealed = true
                            }
                        }
                }
                HStack(spacing: 4) {
                    if message.isEdited && !message.isRemoved {
                        Text("изменено").font(.caption2).foregroundStyle(.secondary)
                    }
                    Text(message.timestamp, style: .time)
                        .font(.caption2).foregroundStyle(.secondary)
                    if message.fromMe { statusIcon }
                }
                if message.fromMe && message.status == .offline {
                    Text("Ожидает получателя")
                        .font(.caption2).foregroundStyle(.orange)
                }
                // Either the send itself failed (no connection, socket dropped mid-send on a
                // bad network) or a terminal "failed" ack came from the node — the recipient
                // doesn't exist or has blocked this sender (deliberately indistinguishable, see
                // router.py). Both are stored as .failed, so both get the same retry offer.
                if message.fromMe && message.status == .failed && !message.isRemoved {
                    Button(action: onRetry) {
                        Text("Сообщение не отправлено. Повторить отправку?")
                            .font(.caption2).foregroundStyle(.red)
                            .multilineTextAlignment(.trailing)
                    }
                    .buttonStyle(.plain)
                }
            }
            if !message.fromMe { Spacer(minLength: 40) }
        }
        // Keyed to just these two fields (not wrapped around the whole-list refresh in
        // ChatView) so ONLY a reaction actually changing animates — an unrelated re-render
        // (new message arriving elsewhere in the list, a status tick updating) doesn't
        // accidentally re-trigger this bubble's transition.
        .animation(.spring(response: 0.3, dampingFraction: 0.6), value: message.myReaction)
        .animation(.spring(response: 0.3, dampingFraction: 0.6), value: message.theirReaction)
        // Load media once after the cell appears — never blocks body/scroll
        .onReceive(NotificationCenter.default.publisher(for: UIApplication.protectedDataDidBecomeAvailableNotification)) { _ in
            if !mediaLoaded { unlockRetry += 1 }
        }
        .task(id: "\(message.msgId)#\(unlockRetry)") {
            guard !mediaLoaded else { return }
            // Locked phone: the files can't be read yet — try again on unlock (see above).
            if message.type != .text, !UIApplication.shared.isProtectedDataAvailable { return }
            mediaLoaded = true

            let tid = String(message.msgId.prefix(8))
            nlog("task start type=\(message.type.rawValue) file=\(message.mediaFile ?? "nil") id=\(tid)")

            switch message.type {
            case .text:
                return
            case .video:
                // Poster frame only — the video itself is never loaded into RAM, Quick Look
                // plays it straight from disk on tap.
                guard let filename = message.mediaFile else { return }
                let url = nevodMediaDirectory.appendingPathComponent(filename)
                let maxPx = CGFloat(480 * Int(UIScreen.main.scale))
                let (img, secs) = await loadVideoPoster(url: url, maxPixels: maxPx)
                if img == nil { nlog("video poster FAILED id=\(tid)") }
                cachedImage = img
                videoDuration = secs
            case .file where message.mediaFile != nil:
                // fileBubble uses name + size only; share uses URL — no data in RAM
                nlog("task skip (file, has mediaFile) id=\(tid)")
                return
            case .image:
                if let filename = message.mediaFile {
                    let url = nevodMediaDirectory.appendingPathComponent(filename)
                    let fileSize = (try? url.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0
                    nlog("image load start size=\(fileSize/1024)KB id=\(tid)")
                    let scale = Int(UIScreen.main.scale)
                    let img = await Task.detached(priority: .userInitiated) {
                        loadImageThumbnail(url: url, maxPixels: 480 * scale)
                    }.value
                    if img == nil {
                        nlog("image load FAILED — thumbnail nil, fileExists=\(FileManager.default.fileExists(atPath: url.path)) id=\(tid)")
                    } else {
                        nlog("image load done img=\(Int(img!.size.width))x\(Int(img!.size.height)) id=\(tid)")
                    }
                    cachedImage = img
                } else if let d = legacyLoadMedia?() {
                    nlog("image legacy load size=\(d.count/1024)KB id=\(tid)")
                    cachedImage = await Task.detached(priority: .userInitiated) {
                        UIImage(data: d)
                    }.value
                    nlog("image legacy decode done id=\(tid)")
                }
            default:
                if let filename = message.mediaFile {
                    let url = nevodMediaDirectory.appendingPathComponent(filename)
                    let fileSize = (try? url.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0
                    nlog("audio/file load start size=\(fileSize/1024)KB id=\(tid)")
                    mediaData = await Task.detached(priority: .userInitiated) {
                        try? Data(contentsOf: url)
                    }.value
                    nlog("audio/file load done bytes=\(mediaData?.count ?? 0) id=\(tid)")
                } else {
                    mediaData = legacyLoadMedia?()
                }
            }
            nlog("task end id=\(tid)")
        }
        .sheet(item: $shareContent) { content in
            ActivityView(items: content.items)
        }
        .quickLookPreview($previewURL)
    }

    @ViewBuilder
    private var bubbleContent: some View {
        if message.isRemoved {
            deletedPlaceholder
        } else {
            switch message.type {
            case .image: imageBubble
            case .video: videoBubble
            case .audio: audioBubble
            case .file:  fileBubble
            case .text:  textBubble
            }
        }
    }

    // Renders in place of the original content for a "delete for everyone" message, on both
    // sides (sender sees this too, not just the recipient) — same fallback idiom as
    // replyQuoteView's "Исходное сообщение недоступно" below.
    private var deletedPlaceholder: some View {
        Text("Сообщение удалено")
            .italic()
            .foregroundStyle(.secondary)
            .padding(.horizontal, 12).padding(.vertical, 8)
    }

    // MARK: Image

    @ViewBuilder
    private var imageBubble: some View {
        ZStack(alignment: .bottomTrailing) {
            if let img = cachedImage {
                Image(uiImage: img)
                    .resizable().scaledToFit()
                    .frame(minWidth: 120, maxWidth: 240, minHeight: 80, maxHeight: 240)
                    .clipShape(RoundedRectangle(cornerRadius: 14))
                    .onTapGesture {
                        if let filename = message.mediaFile {
                            previewURL = namedURL(forDiskFilename: filename)
                        }
                    }
            } else {
                RoundedRectangle(cornerRadius: 14)
                    .fill(Color(.systemGray4))
                    .frame(width: 200, height: 150)
                    .overlay { ProgressView() }
            }
            if cachedImage != nil {
                HStack(spacing: 6) {
                    // Saving your OWN already-sent photo back to Photos is redundant (it came
                    // from there, or from the camera, either way it's already on this device) —
                    // only received photos get the save button. Sharing onward (AirDrop/other
                    // apps) is useful either way, so that one isn't gated by sender.
                    if !message.fromMe {
                        Button {
                            if let img = cachedImage { saveImageToPhotos(img) }
                        } label: {
                            Image(systemName: photoSaved ? "checkmark" : "square.and.arrow.down")
                                .font(.caption).padding(6)
                                .background(.ultraThinMaterial).clipShape(Circle())
                        }
                    }
                    Button(action: shareMedia) {
                        Image(systemName: "square.and.arrow.up")
                            .font(.caption).padding(6)
                            .background(.ultraThinMaterial).clipShape(Circle())
                    }
                }
                .padding(6)
            }
            if let p = progress {
                RoundedRectangle(cornerRadius: 14).fill(.black.opacity(0.45))
                VStack(spacing: 6) {
                    ProgressView(value: p).tint(.white).frame(width: 160)
                    Text("\(Int(p * 100))%").font(.caption.bold()).foregroundStyle(.white)
                }
            }
        }
    }

    // MARK: Video

    private var videoBubble: some View {
        ZStack {
            if let img = cachedImage {
                Image(uiImage: img)
                    .resizable().scaledToFit()
                    .frame(minWidth: 120, maxWidth: 240, minHeight: 80, maxHeight: 240)
            } else {
                Color(.systemGray4).frame(width: 200, height: 150)
            }
            if progress == nil {
                Image(systemName: "play.fill")
                    .font(.title2).foregroundStyle(.white)
                    .padding(14).background(.black.opacity(0.45)).clipShape(Circle())
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .contentShape(Rectangle())
        .onTapGesture {
            guard progress == nil, let filename = message.mediaFile else { return }
            previewURL = namedURL(forDiskFilename: filename)
        }
        .overlay(alignment: .bottomLeading) {
            if let d = videoDuration {
                Text(formatDuration(d))
                    .font(.caption2.monospacedDigit()).foregroundStyle(.white)
                    .padding(.horizontal, 6).padding(.vertical, 2)
                    .background(.black.opacity(0.5)).clipShape(Capsule())
                    .padding(6)
            }
        }
        .overlay(alignment: .bottomTrailing) {
            if progress == nil && message.mediaFile != nil {
                HStack(spacing: 6) {
                    // Same rule as imageBubble: only received videos get "save to Photos".
                    if !message.fromMe {
                        Button(action: saveVideoToPhotos) {
                            Image(systemName: photoSaved ? "checkmark" : "square.and.arrow.down")
                                .font(.caption).padding(6)
                                .background(.ultraThinMaterial).clipShape(Circle())
                        }
                    }
                    Button(action: shareMedia) {
                        Image(systemName: "square.and.arrow.up")
                            .font(.caption).padding(6)
                            .background(.ultraThinMaterial).clipShape(Circle())
                    }
                }
                .padding(6)
            }
        }
        .overlay {
            if let p = progress {
                RoundedRectangle(cornerRadius: 14).fill(.black.opacity(0.45))
                VStack(spacing: 6) {
                    ProgressView(value: p).tint(.white).frame(width: 160)
                    Text("\(Int(p * 100))%").font(.caption.bold()).foregroundStyle(.white)
                }
            }
        }
    }

    private func formatDuration(_ secs: Double) -> String {
        let t = Int(secs.rounded())
        return String(format: "%d:%02d", t / 60, t % 60)
    }

    // MARK: Audio

    private var audioBubble: some View {
        LazyAudioBubble(data: mediaData, onShare: shareMedia)
    }

    // MARK: File — uses mediaSize only, never touches mediaData during render

    private var fileDisplayName: String {
        if let name = message.mediaName, !name.isEmpty { return name }
        // text might be a MIME type (e.g. "application/pdf") when name was absent in data-URL
        let t = message.text
        if t.contains("/"), let file = message.mediaFile {
            let ext = URL(fileURLWithPath: file).pathExtension
            if !ext.isEmpty { return "document.\(ext)" }
        }
        return t
    }

    private var fileBubble: some View {
        Button {
            // Tap anywhere on the card → Quick Look preview
            if let filename = message.mediaFile {
                previewURL = namedURL(forDiskFilename: filename)
            }
        } label: {
            HStack(spacing: 8) {
                Image(systemName: "doc.fill").font(.title3)
                VStack(alignment: .leading, spacing: 2) {
                    Text(fileDisplayName)
                        .font(.subheadline).lineLimit(2)
                    if let sz = message.mediaSize, sz > 0 {
                        Text(ByteCountFormatter.string(fromByteCount: Int64(sz), countStyle: .file))
                            .font(.caption2).opacity(0.7)
                    }
                }
                Spacer(minLength: 0)
                Button(action: shareMedia) {
                    Image(systemName: "square.and.arrow.up").font(.title3)
                }
                if let p = progress {
                    ProgressView(value: p).frame(width: 40)
                }
            }
            .padding(.horizontal, 12).padding(.vertical, 8)
        }
        .buttonStyle(.plain)
    }

    // Plain Text(String) never makes URLs tappable — user report 2026-09-29: links in chat
    // (https://…) didn't open. NSDataDetector finds them (including a bare "nevod.network")
    // and marks them as .link runs, which Text opens through the environment's openURL
    // (Safari, or the owning app for a universal link).
    private static let linkDetector = try? NSDataDetector(
        types: NSTextCheckingResult.CheckingType.link.rawValue)

    private func linkified(_ s: String) -> AttributedString {
        var attr = AttributedString(s)
        addLinks(&attr)
        return attr
    }

    private func addLinks(_ attr: inout AttributedString) {
        guard let detector = Self.linkDetector else { return }
        let s = String(attr.characters)
        for m in detector.matches(in: s, range: NSRange(s.startIndex..., in: s)) {
            guard let url = m.url, let r = Range(m.range, in: s) else { continue }
            let lo = attr.characters.index(attr.startIndex, offsetBy: s.distance(from: s.startIndex, to: r.lowerBound))
            let hi = attr.characters.index(lo, offsetBy: s.distance(from: r.lowerBound, to: r.upperBound))
            guard attr[lo..<hi].link == nil else { continue }   // already a Markdown link
            attr[lo..<hi].link = url
            attr[lo..<hi].underlineStyle = .single
        }
    }

    /// Inline Markdown as Apple parses it, plus the two block forms bots use most: a
    /// "## heading" line becomes bold, a "- item" / "* item" line a "• item".
    private func markdownRendered(_ s: String) -> AttributedString {
        let md = s.components(separatedBy: "\n").map { line -> String in
            if let r = line.range(of: #"^#{1,6}\s+"#, options: .regularExpression) {
                return "**" + String(line[r.upperBound...]) + "**"
            }
            if let r = line.range(of: #"^\s*[-*]\s+"#, options: .regularExpression) {
                return "• " + String(line[r.upperBound...])
            }
            return line
        }.joined(separator: "\n")
        guard var attr = try? AttributedString(markdown: md, options: .init(
            interpretedSyntax: .inlineOnlyPreservingWhitespace)) else { return linkified(s) }
        addLinks(&attr)
        return attr
    }

    private var textBubble: some View {
        // Guard: a data-URL stored as text (decodeMediaBody failure) can be 500KB+
        // and will break SwiftUI layout. Show a placeholder instead.
        let body = message.text.count > 4096 ? String(localized: "⚠️ [медиа не загрузилось]") : message.text
        return Text(showsMarkdown ? markdownRendered(body) : linkified(body))
            .font(message.churchFont ? .custom("Ponomar-Regular", size: 17) : .body)
            // Link runs are drawn in the tint color — the default accent would vanish on my
            // own (accent-colored) bubbles.
            .tint(message.fromMe ? .white : .accentColor)
            .padding(.horizontal, 12).padding(.vertical, 8)
            // No .lineLimit() here — this is the actual message text, never truncated by
            // design. But without an explicit vertical fixedSize, SwiftUI can still silently
            // compress a Text to whatever height its parent proposes and ellipsize it, even
            // with no lineLimit set at all — confirmed on a real device 2026-08-24 (a bubble
            // cut off mid-word). This forces the view to always take its full natural height.
            .fixedSize(horizontal: false, vertical: true)
    }

    @ViewBuilder
    private var replyQuoteView: some View {
        Button {
            if let rid = message.replyToMsgId { onJumpToReply(rid) }
        } label: {
            HStack(spacing: 6) {
                Rectangle().fill(Color.accentColor).frame(width: 3)
                Text(replyPreview.map { messagePreviewText($0) } ?? String(localized: "Исходное сообщение недоступно"))
                    .font(.caption)
                    .foregroundStyle(message.fromMe ? .white.opacity(0.85) : .secondary)
            }
            .padding(.horizontal, 8).padding(.vertical, 4)
            .background(.black.opacity(message.fromMe ? 0.12 : 0.06))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(.plain)
        .padding(.horizontal, 4)
    }

    // Small pill(s) under the bubble — either side (or both, if each party reacted) can be
    // set at once since this is a 1:1 chat, not a group needing a per-sender tally. Tapping my
    // own pill clears it (same toggle as picking the same emoji again from the context menu);
    // theirs is just a static display.
    @ViewBuilder
    private var reactionBadges: some View {
        HStack(spacing: 4) {
            if let mine = message.myReaction {
                Button { onReact(mine) } label: {
                    Text(mine).font(.footnote)
                        .padding(.horizontal, 6).padding(.vertical, 2)
                        .background(Color.accentColor.opacity(0.2))
                        .clipShape(Capsule())
                }
                .buttonStyle(.plain)
            }
            if let theirs = message.theirReaction {
                Text(theirs).font(.footnote)
                    .padding(.horizontal, 6).padding(.vertical, 2)
                    .background(Color(.systemGray5))
                    .clipShape(Capsule())
            }
        }
    }

    @ViewBuilder private var statusIcon: some View {
        switch message.status {
        case .sent:
            if let p = progress {
                ProgressView(value: p).frame(width: 28).tint(.secondary)
            } else {
                Image(systemName: "circle").font(.caption2).foregroundStyle(.secondary)
            }
        case .offline:
            Image(systemName: "clock").font(.caption2).foregroundStyle(.orange)
        case .delivered:
            Image(systemName: "checkmark").font(.caption2).foregroundStyle(.secondary)
        case .read:
            HStack(spacing: -6) {
                Image(systemName: "checkmark")
                Image(systemName: "checkmark")
            }
            .font(.caption2).foregroundStyle(.tint)
        case .failed:
            Image(systemName: "exclamationmark.circle").font(.caption2).foregroundStyle(.red)
        }
    }

    /// Files are stored on disk under their (UUID) msgId, not the original filename.
    /// Quick Look / the share sheet must show the original name, so both go through a
    /// renamed copy in tmp instead of handing out the raw on-disk URL.
    ///
    /// Previously used a symlink (cheaper, no data duplication) instead of a copy — confirmed
    /// via device testing 2026-08-07 that Quick Look doesn't reliably follow it: it showed a
    /// generic "document / symbolic link / 157 bytes" info screen instead of the actual image,
    /// rather than transparently resolving to the real file. A real copy has no such
    /// dependency on the consumer (Quick Look, the share sheet, or whatever app AirDrop/share
    /// hands it to) choosing to follow a symlink.
    private func namedURL(forDiskFilename filename: String) -> URL? {
        let srcURL = nevodMediaDirectory.appendingPathComponent(filename)
        guard FileManager.default.fileExists(atPath: srcURL.path) else { return nil }
        let name = message.mediaName ?? fileDisplayName
        let tmpURL = FileManager.default.temporaryDirectory.appendingPathComponent(name)
        try? FileManager.default.removeItem(at: tmpURL)
        if (try? FileManager.default.copyItem(at: srcURL, to: tmpURL)) != nil {
            return tmpURL
        }
        return srcURL  // fallback: UUID filename
    }

    private func shareMedia() {
        if let filename = message.mediaFile {
            guard let url = namedURL(forDiskFilename: filename) else { return }
            shareContent = ShareContent(items: [url])
        } else if let data = mediaData {
            let name = message.mediaName ?? (message.type == .audio ? "voice.m4a" : "file")
            let url = FileManager.default.temporaryDirectory.appendingPathComponent(name)
            Task.detached(priority: .userInitiated) {
                try? data.write(to: url)
                await MainActor.run { shareContent = ShareContent(items: [url]) }
            }
        }
    }

    private func saveVideoToPhotos() {
        guard let filename = message.mediaFile else { return }
        let url = nevodMediaDirectory.appendingPathComponent(filename)
        PHPhotoLibrary.requestAuthorization(for: .addOnly) { status in
            guard status == .authorized || status == .limited else { return }
            PHPhotoLibrary.shared().performChanges({
                PHAssetChangeRequest.creationRequestForAssetFromVideo(atFileURL: url)
            }) { ok, _ in
                if ok { DispatchQueue.main.async { photoSaved = true } }
            }
        }
    }

    private func saveImageToPhotos(_ image: UIImage) {
        PHPhotoLibrary.requestAuthorization(for: .addOnly) { status in
            guard status == .authorized || status == .limited else { return }
            UIImageWriteToSavedPhotosAlbum(image, nil, nil, nil)
            DispatchQueue.main.async { photoSaved = true }
        }
    }
}

// MARK: - Share sheet

/// Wraps the items for .sheet(item:) — a fresh id per share action so re-sharing (even the
/// exact same items again) reliably re-triggers the sheet.
struct ShareContent: Identifiable {
    let id = UUID()
    let items: [Any]
}

/// Wraps a bare msgId as Identifiable so the emoji-picker sheet can use .sheet(item:) — the
/// standard fix for .sheet(isPresented:) reading stale content on first presentation (same
/// reasoning as MessageBubble's own ShareContent, see its doc comment).
private struct EmojiPickerTarget: Identifiable {
    let id: String
}

struct ActivityView: UIViewControllerRepresentable {
    let items: [Any]
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }
    func updateUIViewController(_ vc: UIActivityViewController, context: Context) {}
}

// MARK: - Audio Bubble
// data is passed in from @State — already loaded async, never from SwiftData in body

struct LazyAudioBubble: View {
    let data: Data?
    let onShare: () -> Void
    @State private var isPlaying = false
    @State private var player: AVAudioPlayerWrapper? = nil

    var body: some View {
        HStack(spacing: 10) {
            Button {
                if isPlaying {
                    player?.stop(); isPlaying = false
                } else {
                    guard let data else { return }
                    player = AVAudioPlayerWrapper(data: data) { isPlaying = false }
                    player?.play(); isPlaying = true
                }
            } label: {
                if data == nil {
                    ProgressView().frame(width: 28, height: 28)
                } else {
                    Image(systemName: isPlaying ? "stop.circle.fill" : "play.circle.fill")
                        .font(.title2)
                }
            }
            Image(systemName: "waveform").font(.title3).opacity(0.7)
            Spacer(minLength: 0)
            if data != nil {
                Button(action: onShare) {
                    Image(systemName: "square.and.arrow.up").font(.title3)
                }
            }
        }
        .padding(.horizontal, 12).padding(.vertical, 8)
    }
}

// MARK: - BYOK AI bot

/// Shown instead of the compose bar in a BYOK bot's chat until the user has a key for one of
/// the providers it supports — the action sits where it's needed, not in Profile.
private struct AIKeyNeededBar: View {
    let onAdd: () -> Void
    var body: some View {
        VStack(spacing: 8) {
            Text("This bot answers using your own AI key.")
                .font(.footnote).foregroundStyle(.secondary).multilineTextAlignment(.center)
            Button("Add AI key", action: onAdd).buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity).padding()
    }
}

/// Add / pick the user's own key for a BYOK bot. The key is checked through the bot (a free
/// "list models" call at the provider, decision 2026-09-28) before it's saved; saving it also
/// records the consent to pass this bot's messages to that provider (Guideline 5.1.2(i)).
struct AIKeySheet: View {
    @EnvironmentObject var store: AppStore
    @Environment(\.dismiss) private var dismiss
    let contact: Contact
    let providers: [AIProvider]
    @State private var provider: AIProvider
    @State private var key = ""
    @State private var agreed = false
    @State private var checking = false
    @State private var error: String? = nil

    init(contact: Contact, providers: [AIProvider], current: AIProvider?) {
        self.contact = contact
        self.providers = providers
        _provider = State(initialValue: current ?? providers.first(where: AIKeyStore.hasConsent)
                          ?? providers.first ?? .anthropic)
    }

    private var savedKey: String? {
        _ = store.aiStateVersion
        return AIKeyStore.hasConsent(provider) ? AIKeyStore.key(for: provider) : nil
    }

    var body: some View {
        NavigationStack {
            Form {
                if providers.count > 1 {
                    Picker("Provider", selection: $provider) {
                        ForEach(providers) { Text(verbatim: $0.displayName).tag($0) }
                    }
                }
                if let saved = savedKey {
                    Section {
                        Button(String(format: String(localized: "Use saved key ••••%@"), String(saved.suffix(4)))) {
                            store.setAIProvider(provider, for: contact.cellId)
                            dismiss()
                        }
                    }
                }
                Section {
                    SecureField("Paste your API key", text: $key)
                        .textInputAutocapitalization(.never).autocorrectionDisabled()
                    Link("Where do I get a key?", destination: provider.keyPageURL)
                } header: {
                    Text(verbatim: provider.displayName)
                } footer: {
                    Text("The key is stored only on this device.")
                }
                Section {
                    Text(String(format: String(localized: "Messages you send to this bot are passed to %@ and processed under its terms. Your key goes to the bot encrypted, with each message, and the bot does not keep it."), provider.company))
                        .font(.footnote)
                    Toggle("I agree", isOn: $agreed)
                }
                if let error {
                    Section { Text(error).foregroundStyle(.red) }
                }
                Section {
                    Button {
                        Task { await checkAndSave() }
                    } label: {
                        if checking {
                            HStack(spacing: 8) { ProgressView(); Text("Checking the key…") }
                        } else {
                            Text("Check and save")
                        }
                    }
                    .disabled(key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !agreed || checking)
                }
            }
            .navigationTitle("AI key")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
            }
            .onChange(of: provider) { _, _ in error = nil; key = "" }
        }
    }

    private func checkAndSave() async {
        let k = key.trimmingCharacters(in: .whitespacesAndNewlines)
        checking = true; error = nil
        let code = await store.checkAIKey(k, provider: provider, bot: contact)
        checking = false
        guard code == "ok" else { error = AppStore.aiErrorText(code); return }
        do {
            try store.saveAIKey(k, for: provider, bot: contact.cellId)
            dismiss()
        } catch {
            self.error = error.localizedDescription
        }
    }
}

/// Profile → "AI keys": what's saved on this device, to delete (which also withdraws the consent).
struct AIKeysView: View {
    @EnvironmentObject var store: AppStore
    var body: some View {
        let saved: [AIProvider] = { _ = store.aiStateVersion; return AIKeyStore.savedProviders }()
        List {
            Section {
                if saved.isEmpty {
                    Text("No AI keys saved").foregroundStyle(.secondary)
                }
                ForEach(saved) { p in
                    HStack {
                        Text(verbatim: p.displayName)
                        Spacer()
                        Text(verbatim: "••••" + String(AIKeyStore.key(for: p)?.suffix(4) ?? ""))
                            .foregroundStyle(.secondary).monospaced()
                    }
                    .swipeActions {
                        Button("Delete key", role: .destructive) { store.deleteAIKey(p) }
                    }
                }
            } footer: {
                Text("The key is stored only on this device.")
            }
        }
        .navigationTitle("AI keys")
    }
}

/// A file from this contact still arriving (AppStore.incomingTransfers) — where its bubble
/// will appear, so the chat a push opened isn't just empty for a minute.
private struct IncomingTransferRow: View {
    let transfer: AppStore.IncomingTransfer

    private var label: LocalizedStringKey {
        if transfer.mime.hasPrefix("video/") { return "Загружается видео…" }
        if transfer.mime.hasPrefix("image/") { return "Загружается фото…" }
        return "Загружается файл…"
    }
    private var icon: String {
        if transfer.mime.hasPrefix("video/") { return "video" }
        if transfer.mime.hasPrefix("image/") { return "photo" }
        return "doc"
    }

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon).foregroundStyle(.secondary)
            VStack(alignment: .leading, spacing: 6) {
                Text(label).font(.subheadline)
                ProgressView(value: transfer.fraction)
                    .frame(width: 160)
            }
            Text(verbatim: "\(Int(transfer.fraction * 100))%")
                .font(.caption.monospacedDigit()).foregroundStyle(.secondary)
        }
        .padding(10)
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 14))
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
