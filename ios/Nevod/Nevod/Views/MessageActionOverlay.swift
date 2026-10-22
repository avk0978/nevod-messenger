import SwiftUI

/// Lets MessageActionOverlay anchor its popup near the actual bubble that was long-pressed,
/// Telegram/iMessage-style, instead of a plain centered modal. Deliberately an Anchor<CGRect>
/// (via .anchorPreference), NOT a GeometryReader+.preference(value:) pumping resolved CGRects
/// up the tree — that first version (2026-08-26) reported every visible bubble's exact frame
/// on every scroll pixel and froze the chat scroll solid after one swipe. An Anchor is a lazy,
/// opaque reference — resolved into an actual CGRect via geo[anchor] only once, only for
/// whichever single message is actually under actionOverlayMsgId, only while the overlay is
/// showing (see ChatView's .overlayPreferenceValue call site).
///
/// Turned out even THIS still wasn't free enough attached unconditionally to every bubble —
/// confirmed on device 2026-08-27: fast repeated back-and-forth scrolling (LazyVStack
/// constantly recycling cells) still showed periodic stutter/stalling. See
/// ConditionalBubbleAnchor below, which is what actually fixed it: gate the anchor to only
/// the ONE bubble currently acting as the overlay's target, not every visible one.
struct BubbleAnchorPreferenceKey: PreferenceKey {
    static var defaultValue: [String: Anchor<CGRect>] = [:]
    static func reduce(value: inout [String: Anchor<CGRect>], nextValue: () -> [String: Anchor<CGRect>]) {
        value.merge(nextValue()) { _, new in new }
    }
}

/// See BubbleAnchorPreferenceKey's doc comment — applies the anchor preference only when
/// isActive (MessageBubble passes its own isActionOverlayTarget), so a bubble that isn't
/// currently long-pressed contributes nothing at all, not even a cheap Anchor registration.
struct ConditionalBubbleAnchor: ViewModifier {
    let isActive: Bool
    let msgId: String

    func body(content: Content) -> some View {
        if isActive {
            content.anchorPreference(key: BubbleAnchorPreferenceKey.self, value: .bounds) { anchor in
                [msgId: anchor]
            }
        } else {
            content
        }
    }
}

/// Replaces the system .contextMenu for message long-press — needed because ControlGroup
/// (the only way to get a horizontal button row inside a native context menu) hard-caps at 3
/// items per row before wrapping into a mismatched grid+list shape. Confirmed on device
/// 2026-08-26 at both 8 and 6 reactionChoices — not a count problem, a ControlGroup ceiling.
/// A custom overlay has no such limit: the reaction row below is a plain horizontally
/// scrolling HStack, same as Telegram's own.
struct MessageActionOverlay: View {
    let message: MessageViewData
    let anchorFrame: CGRect
    let onReact: (String) -> Void
    let onMore: () -> Void
    let onReply: () -> Void
    let onShare: () -> Void
    let onEdit: () -> Void
    let onDeleteEverywhere: () -> Void
    let onDelete: () -> Void
    let onReport: () -> Void
    let onDismiss: () -> Void

    // Text messages only, own messages only — matches editMessage()/deleteForEveryone()'s own
    // gating in AppStore, mirrored here purely for the button's visibility (not a security
    // boundary, both AppStore methods are safe to call regardless, they'd just no-op on a
    // fetch miss — this just keeps the menu from offering an action that wouldn't apply).
    private var canEdit: Bool { message.fromMe && message.type == .text }
    private var canDeleteEverywhere: Bool { message.fromMe }
    // Only someone else's message can be reported (App Store Guideline 1.2).
    private var canReport: Bool { !message.fromMe }

    // Far more room than the old ControlGroup could ever hold — the point of this overlay is
    // exactly that, with "+" still there (opens EmojiPickerSheet) for anything not listed.
    private static let quickReactions = [
        "❤️", "👍", "👎", "😂", "😮", "😢", "🙏", "🔥",
        "🎉", "👏", "😍", "🤔", "😱", "💯", "🥳",
    ]

    // Deterministic, not measured: base case is the reaction strip + exactly 3 action rows
    // (Reply, Share, Delete-for-me) = 232, tuned empirically. Edit/Delete-for-everyone are
    // conditional on the message (see canEdit/canDeleteEverywhere above), so the popup's real
    // height now varies per-message — still fully deterministic (known before layout, just not
    // a flat constant anymore), so this stays a computed row-count-based value rather than
    // wiring up a second GeometryReader pass to measure it.
    private static let baseHeight: CGFloat = 232
    private static let extraRowHeight: CGFloat = 44
    private var estimatedPopupHeight: CGFloat {
        var extraRows = 0
        if canEdit { extraRows += 1 }
        if canDeleteEverywhere { extraRows += 1 }
        if canReport { extraRows += 1 }
        return Self.baseHeight + CGFloat(extraRows) * Self.extraRowHeight
    }

    var body: some View {
        GeometryReader { screenGeo in
            let screenSize = screenGeo.size
            let popupWidth = min(screenSize.width - 32, 340)
            let placeAbove = anchorFrame.minY > estimatedPopupHeight + 60
            let popupTop = placeAbove
                ? anchorFrame.minY - estimatedPopupHeight - 10
                : anchorFrame.maxY + 10
            // Vertical clamp, same idea as popupLeading's existing horizontal one just below —
            // added 2026-08-28 after the popup grew taller (Edit/Delete-for-everyone rows,
            // see estimatedPopupHeight above): a message near the bottom of the screen could
            // place the popup (or its "below" fallback) partly off-screen, cutting off exactly
            // the LAST rows — confirmed on device to be "Удалить у меня"/"Удалить у всех",
            // since those render at the bottom of the action list.
            let clampedTop = min(max(popupTop, 16), screenSize.height - estimatedPopupHeight - 16)
            let idealLeading = message.fromMe ? anchorFrame.maxX - popupWidth : anchorFrame.minX
            let popupLeading = min(max(idealLeading, 16), screenSize.width - popupWidth - 16)

            ZStack {
                Color.black.opacity(0.28)
                    .ignoresSafeArea()
                    .onTapGesture { onDismiss() }

                popupContent
                    .frame(width: popupWidth)
                    .position(x: popupLeading + popupWidth / 2, y: clampedTop + estimatedPopupHeight / 2)
            }
        }
        .transition(.opacity)
    }

    private var popupContent: some View {
        VStack(spacing: 8) {
            HStack(spacing: 4) {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 10) {
                        ForEach(Self.quickReactions, id: \.self) { emoji in
                            Button {
                                onReact(emoji)
                                onDismiss()
                            } label: {
                                Text(emoji).font(.title2)
                                    .frame(width: 36, height: 36)
                                    .background(
                                        message.myReaction == emoji
                                            ? Color.accentColor.opacity(0.25) : Color.clear,
                                        in: Circle()
                                    )
                            }
                        }
                    }
                    .padding(.horizontal, 12)
                }
                Button(action: onMore) {
                    Image(systemName: "plus.circle.fill")
                        .font(.title2)
                        .foregroundStyle(.secondary)
                }
                .padding(.trailing, 8)
            }
            .padding(.vertical, 8)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 18))

            VStack(spacing: 0) {
                actionRow(String(localized: "Ответить"), systemImage: "arrowshape.turn.up.left", action: {
                    onReply(); onDismiss()
                })
                Divider().padding(.leading, 44)
                actionRow(String(localized: "Поделиться"), systemImage: "square.and.arrow.up", action: {
                    onShare(); onDismiss()
                })
                if canEdit {
                    Divider().padding(.leading, 44)
                    actionRow(String(localized: "Редактировать"), systemImage: "pencil", action: {
                        onEdit(); onDismiss()
                    })
                }
                Divider().padding(.leading, 44)
                actionRow(String(localized: "Удалить у меня"), systemImage: "trash", role: .destructive, action: {
                    onDelete(); onDismiss()
                })
                if canDeleteEverywhere {
                    Divider().padding(.leading, 44)
                    actionRow(String(localized: "Удалить у всех"), systemImage: "trash.fill", role: .destructive, action: {
                        onDeleteEverywhere(); onDismiss()
                    })
                }
                if canReport {
                    Divider().padding(.leading, 44)
                    actionRow(String(localized: "Пожаловаться"), systemImage: "flag", role: .destructive, action: {
                        onReport(); onDismiss()
                    })
                }
            }
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
        }
    }

    private func actionRow(_ title: String, systemImage: String, role: ButtonRole? = nil,
                           action: @escaping () -> Void) -> some View {
        Button(role: role, action: action) {
            HStack {
                Text(title)
                Spacer()
                Image(systemName: systemImage)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .foregroundStyle(role == .destructive ? .red : .primary)
        }
        .buttonStyle(.plain)
        .contentShape(Rectangle())
    }
}
