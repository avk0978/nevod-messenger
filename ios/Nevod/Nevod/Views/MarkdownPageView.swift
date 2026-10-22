import SwiftUI

/// Renders a node-published "landing page" cell (kind="page", NODE_CELLS_REQUEST's landing_md)
/// — the "лендинг ноды без реального сайта" from the Cluster Б design discussion. A small
/// line-based renderer, not a full CommonMark implementation: headings (#/##/###), bullet
/// lists (-/*), a horizontal rule (---), blank-line paragraph breaks, plus inline bold/italic/
/// links via SwiftUI's native LocalizedStringKey markdown support — enough for a short
/// informational page, not arbitrary Markdown.
struct MarkdownPageView: View {
    let title: String
    let markdown: String

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                if markdown.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    Text("Эта страница пока пуста.")
                        .foregroundStyle(.white.opacity(0.5))
                } else {
                    ForEach(MarkdownBlock.parse(markdown)) { block in
                        block.view
                    }
                }
            }
            .padding(20)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .background(NodeSkyBackground())
        .navigationTitle(title)
        .skyNavigationTitle(Text(verbatim: title))
    }
}

private struct MarkdownBlock: Identifiable {
    let id = UUID()
    enum Kind { case heading(Int), bullet, rule, paragraph }
    let kind: Kind
    let text: String

    @ViewBuilder
    var view: some View {
        switch kind {
        case .heading(let level):
            Text(LocalizedStringKey(text))
                .font(level <= 1 ? .title.bold() : level == 2 ? .title2.bold() : .headline)
                .foregroundStyle(.white)
        case .bullet:
            HStack(alignment: .top, spacing: 8) {
                Text("•").foregroundStyle(.white.opacity(0.6))
                Text(LocalizedStringKey(text))
                    .foregroundStyle(.white.opacity(0.85))
                    .fixedSize(horizontal: false, vertical: true)
            }
        case .rule:
            Rectangle().fill(Color.white.opacity(0.15)).frame(height: 1)
        case .paragraph:
            Text(LocalizedStringKey(text))
                .foregroundStyle(.white.opacity(0.85))
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    static func parse(_ markdown: String) -> [MarkdownBlock] {
        var blocks: [MarkdownBlock] = []
        var paragraphLines: [String] = []
        func flushParagraph() {
            guard !paragraphLines.isEmpty else { return }
            blocks.append(MarkdownBlock(kind: .paragraph, text: paragraphLines.joined(separator: " ")))
            paragraphLines = []
        }
        for rawLine in markdown.components(separatedBy: "\n") {
            let line = rawLine.trimmingCharacters(in: .whitespaces)
            if line.isEmpty {
                flushParagraph()
            } else if line == "---" || line == "***" {
                flushParagraph()
                blocks.append(MarkdownBlock(kind: .rule, text: ""))
            } else if line.hasPrefix("### ") {
                flushParagraph()
                blocks.append(MarkdownBlock(kind: .heading(3), text: String(line.dropFirst(4))))
            } else if line.hasPrefix("## ") {
                flushParagraph()
                blocks.append(MarkdownBlock(kind: .heading(2), text: String(line.dropFirst(3))))
            } else if line.hasPrefix("# ") {
                flushParagraph()
                blocks.append(MarkdownBlock(kind: .heading(1), text: String(line.dropFirst(2))))
            } else if line.hasPrefix("- ") || line.hasPrefix("* ") {
                flushParagraph()
                blocks.append(MarkdownBlock(kind: .bullet, text: String(line.dropFirst(2))))
            } else {
                paragraphLines.append(line)
            }
        }
        flushParagraph()
        return blocks
    }
}
