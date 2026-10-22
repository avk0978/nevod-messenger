import SwiftUI

/// Full emoji grid opened from "+" in MessageActionOverlay's quick-reaction row (see that
/// file's doc comment for why the quick row is a custom overlay, not a native context menu) —
/// this is where literally any emoji lives, matching the Telegram/iMessage "expand to full
/// picker" pattern the user asked for (2026-08-26).
///
/// The emoji list is generated at runtime from standard Unicode block ranges, filtered by
/// `Unicode.Scalar.Properties.isEmojiPresentation` — not a hand-typed list. That's deliberate:
/// a manually authored list of thousands of emoji characters is exactly the kind of place a
/// transcription error hides, and it goes stale the moment Apple ships new ones. Iterating the
/// official block ranges and asking the OS which code points in them are actually emoji stays
/// correct automatically as iOS's Unicode/ICU data updates — the tradeoff is these sections are
/// named after their Unicode block, not Apple's own (unpublished) keyboard category groupings,
/// so the split is close but won't be pixel-identical to the system emoji keyboard's tabs.
/// Flag emoji (regional-indicator pairs) are deliberately not generated here — enumerating only
/// the valid ISO country-code combinations correctly needs a curated list of its own, which is
/// the same risk this whole approach exists to avoid; add them later as their own curated
/// section if wanted, not more relevant.
struct EmojiPickerSheet: View {
    let onSelect: (String) -> Void
    @Environment(\.dismiss) private var dismiss

    private struct Category: Identifiable {
        let id = UUID()
        let name: String
        let emoji: [String]
    }

    private static func range(_ from: UInt32, _ to: UInt32) -> [String] {
        (from...to).compactMap { value in
            guard let scalar = Unicode.Scalar(value), scalar.properties.isEmojiPresentation else { return nil }
            return String(scalar)
        }
    }

    // Computed once per process, not per view instance — building these ~1500 strings on every
    // sheet presentation would be wasteful for something that never changes at runtime.
    private static let categories: [Category] = [
        Category(name: String(localized: "Смайлы и эмоции"), emoji: range(0x1F600, 0x1F64F)),
        Category(name: String(localized: "Символы и пиктограммы"), emoji: range(0x1F300, 0x1F5FF)),
        Category(name: String(localized: "Транспорт и места"), emoji: range(0x1F680, 0x1F6FF)),
        Category(name: String(localized: "Дополнительные пиктограммы"), emoji: range(0x1F900, 0x1F9FF)),
        Category(name: String(localized: "Новые пиктограммы"), emoji: range(0x1FA70, 0x1FAFF)),
        Category(name: String(localized: "Прочие символы"), emoji: range(0x2600, 0x26FF)),
        Category(name: String(localized: "Дингбаты"), emoji: range(0x2700, 0x27BF)),
    ]

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 4), count: 8)

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 16, pinnedViews: [.sectionHeaders]) {
                    ForEach(Self.categories) { category in
                        Section {
                            LazyVGrid(columns: columns, spacing: 8) {
                                ForEach(category.emoji, id: \.self) { emoji in
                                    Button {
                                        onSelect(emoji)
                                        dismiss()
                                    } label: {
                                        Text(emoji).font(.title2)
                                    }
                                    .frame(maxWidth: .infinity, minHeight: 40)
                                }
                            }
                            .padding(.horizontal)
                        } header: {
                            Text(category.name)
                                .font(.caption.bold())
                                .foregroundStyle(.secondary)
                                .padding(.horizontal)
                                .padding(.vertical, 4)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(.bar)
                        }
                    }
                }
                .padding(.vertical)
            }
            .navigationTitle("Реакция")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Готово") { dismiss() }
                }
            }
        }
    }
}
