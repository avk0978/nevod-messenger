//
//  KeyboardViewController.swift
//  SLKey
//
//  Created by Andrey Kolpakov on 23.05.2018.
//  Copyright © 2018 Andrey Kolpakov. All rights reserved.
//

import UIKit


class KeyboardViewController: UIInputViewController, SlavonicKeyboard {


    let linesSmallButton = [topLine, firstLine, secondLine, thirdLine, bottomLine]
    let rowsSmallLetters = [smallLetterRowTop, smallLetterRow1, smallLetterRow2, smallLetterRow3, smallLetterRowBottom]

    let linesBigButton = [bigTopLine, bigFirstLine, bigSecondLine, bigThirdLine, bigBottomLine]
    let rowsBigLetters = [bigLetterRowTop, bigLetterRow1, bigLetterRow2, bigLetterRow3, bigLetterRowBottom]

    // Shrunk to 3 rows (user request 2026-08-23) — Church Slavonic has no use for the
    // digits/ASCII-symbol rows the small/big letter layouts don't need either.
    let linesSymbolButton = [symbolTopLine, symbolFirstLine, symbolSecondLine]
    let rowsSymbolLetters = [symbolLetterRowTop, symbolLetterRow1, symbolLetterRow2]


    var shift = false
    var symbol = false

    // Single source of truth for the row math — addConstraintsOnThe(...) below is called with
    // these same two numbers, and keyboardHeight is derived from them, so bumping either one
    // (as happened going from 40/2 to 46/4 for bigger keys) can never again silently exceed
    // whatever height the extension actually requests from the system.
    private let rowHeight: CGFloat = 46
    private let rowSpacing: CGFloat = 4
    private func height(forRows n: Int) -> CGFloat { CGFloat(n) * rowHeight + CGFloat(max(n - 1, 0)) * rowSpacing }
    private var keyboardHeight: CGFloat { height(forRows: linesSmallButton.count) }
    // The symbol layout has fewer rows than the letter layouts, so it needs its own (shorter)
    // requested height rather than sharing one fixed constant for every layout.
    private var symbolKeyboardHeight: CGFloat { height(forRows: linesSymbolButton.count) }
    private var heightConstraint: NSLayoutConstraint!

    // Long-press alternates popup (e.g. titlo → the raised "выносные" letters) — see Key.alternates.
    private var alternatesPopup: UIView?
    private weak var alternatesPopupOwner: Key?


    override func viewDidLoad() {
        super.viewDidLoad()
        // Explicit dark background regardless of system light/dark appearance — matches the
        // redesigned dark key palette (KeyModel.swift) rather than relying on whatever the
        // extension's default background happened to inherit.
        self.view.backgroundColor = UIColor(white: 0.05, alpha: 1)
        // Custom keyboard extensions get a system-suggested default height, which doesn't know
        // in advance that our rows got taller (bigger touch targets, per redesign) — without
        // explicitly requesting the real content height here, the 5th row silently renders
        // past the view's actual (too-short) bounds. Confirmed via a real device screenshot
        // 2026-08-23: only 4 of 5 rows visible, and the SAME undersized-on-first-layout state
        // is the likely reason the keyboard also needed a second open attempt to appear at all
        // — setting this before any panel is built means the correct height is requested from
        // the very first layout pass, not fixed up on a later one.
        // Priority just under .required: at .required (the default), this fights the system's
        // own auto-generated 'UIView-Encapsulated-Layout-Height' constraint on the same
        // property — confirmed via a real device console capture 2026-08-23: "Unable to
        // simultaneously satisfy constraints" logged on every single open, height visibly
        // thrashing (844 -> 428 -> 246) before settling. One point below .required lets the
        // system silently drop its own constraint instead of an emergency break-and-recover.
        let hc = self.view.heightAnchor.constraint(equalToConstant: keyboardHeight)
        hc.priority = .required - 1
        hc.isActive = true
        heightConstraint = hc
        nlog("SLKey viewDidLoad — extension process launched, view size=\(self.view.bounds.size) requestedHeight=\(keyboardHeight)")
        createPanel(layout: smallLetterLayout)
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        nlog("SLKey viewWillAppear view size=\(self.view.bounds.size) subviews=\(self.view.subviews.count)")
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        nlog("SLKey viewDidAppear view size=\(self.view.bounds.size) subviews=\(self.view.subviews.count)")
    }


    func removeAllPanelAndAddThe(panel: UIView) {
        if smallLetterLayout.isDescendant(of: self.view) { smallLetterLayout.removeFromSuperview() }
        if bigLetterLayout.isDescendant(of: self.view) { bigLetterLayout.removeFromSuperview() }
        if symbolLayout.isDescendant(of: self.view) { symbolLayout.removeFromSuperview() }
        dismissAlternatesPopup()
        createPanel(layout: panel)
    }


    func createPanel(layout: UIView) {
        let name = layout === smallLetterLayout ? "small" : layout === bigLetterLayout ? "big" : layout === symbolLayout ? "symbol" : "unknown"
        nlog("SLKey createPanel layout=\(name)")
        switch layout {
        case smallLetterLayout:
            createsLayoutKeyboard(inThe: layout, from: linesSmallButton, and: rowsSmallLetters)
        case bigLetterLayout:
            createsLayoutKeyboard(inThe: layout, from: linesBigButton, and: rowsBigLetters)
        case symbolLayout:
            createsLayoutKeyboard(inThe: layout, from: linesSymbolButton, and: rowsSymbolLetters)
        default:
            break
        }

        self.view.addSubview(layout)
        addConstraintOnthe(layout, inThe: self.view)
        heightConstraint.constant = layout === symbolLayout ? symbolKeyboardHeight : keyboardHeight
        nlog("SLKey createPanel done layout=\(name) layoutFrame=\(layout.frame) layoutSubviews=\(layout.subviews.count) requestedHeight=\(heightConstraint.constant)")
    }


    func createsLayoutKeyboard(inThe view: UIView, from linesKeyboard: [UIView], and linesRowKey: [[Key]]) {

        let alreadyBuilt = linesKeyboard[0].isDescendant(of: view)
        nlog("SLKey createsLayoutKeyboard alreadyBuilt=\(alreadyBuilt) rows=\(linesKeyboard.count)")
        if !alreadyBuilt {
        for item in 0...linesKeyboard.count - 1 {
            createsLineOf(buttons: linesRowKey[item], inThe: linesKeyboard[item])
            view.addSubview(linesKeyboard[item])
        }
        addConstraintsOnThe(lines: linesKeyboard, in: view, heightLine: rowHeight, space: rowSpacing)
        }
    }

    func createsLineOf(buttons:[Key], inThe view: UIView) {
        var keybuttonsInTheRow: [Key] = []
        for item in 0...buttons.count - 1 {
            let newKey = Key(type: .custom, buttons[item].letterName, image: buttons[item].image)
            newKey.alternates = buttons[item].alternates
            newKey.onLongPress = { [weak self] key in self?.showAlternatesPopup(for: key) }
            newKey.addTarget(self, action: #selector(didTapButton), for: .touchUpInside)
            keybuttonsInTheRow.append(newKey)
            view.addSubview(newKey)
        }
        addConstraintsOnTheKey(buttons: keybuttonsInTheRow, inThe: view, indentLeft: 5, indentRight: 5, space: 5)
        nlog("SLKey createsLineOf built \(keybuttonsInTheRow.count) keys in row")
    }

    // Shown on long-press of a key with alternates (currently just titlo → raised letters) —
    // a horizontally scrollable strip of full-size buttons above the pressed key, same idea as
    // the system keyboard's own accent popup. Tapping the original key still fires its normal
    // touchUpInside action as usual (e.g. titlo itself still gets typed on release) — this popup
    // is purely additive, for picking the letter that stacks on top of it.
    private func showAlternatesPopup(for key: Key) {
        dismissAlternatesPopup()
        guard !key.alternates.isEmpty else { return }
        alternatesPopupOwner = key

        let container = UIView()
        container.translatesAutoresizingMaskIntoConstraints = false
        container.backgroundColor = UIColor(white: 0.15, alpha: 1)
        container.layer.cornerRadius = 8
        container.layer.borderWidth = 1
        container.layer.borderColor = UIColor(white: 0.4, alpha: 1).cgColor
        self.view.addSubview(container)

        let scroll = UIScrollView()
        scroll.translatesAutoresizingMaskIntoConstraints = false
        scroll.showsHorizontalScrollIndicator = false
        container.addSubview(scroll)

        let stack = UIStackView()
        stack.translatesAutoresizingMaskIntoConstraints = false
        stack.axis = .horizontal
        stack.spacing = 3
        scroll.addSubview(stack)

        for alt in key.alternates {
            let btn = UIButton(type: .custom)
            // No dotted-circle placeholder here (unlike the keyboard's own keys) — user feedback
            // 2026-08-24: circle + tiny mark together read as illegible in this popup. Alone in
            // a big, dedicated picker button the mark is already self-explanatory as "a raised
            // letter" without needing a base-character hint the way it does crammed onto a
            // regular key alongside 8 others.
            btn.setTitle(alt, for: [])
            btn.titleLabel?.font = UIFont(name: "Ponomar-Regular", size: 34)
            btn.setTitleColor(.white, for: [])
            btn.backgroundColor = UIColor(white: 0.33, alpha: 1)
            btn.layer.cornerRadius = 6
            btn.translatesAutoresizingMaskIntoConstraints = false
            btn.widthAnchor.constraint(equalToConstant: 46).isActive = true
            btn.addAction(UIAction { [weak self] _ in self?.selectAlternate(alt) }, for: .touchUpInside)
            stack.addArrangedSubview(btn)
        }

        NSLayoutConstraint.activate([
            scroll.topAnchor.constraint(equalTo: container.topAnchor, constant: 4),
            scroll.bottomAnchor.constraint(equalTo: container.bottomAnchor, constant: -4),
            scroll.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 4),
            scroll.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -4),
            // Content pinned to contentLayoutGuide (the scrollable area, sized by the stack's own
            // intrinsic width) — pinning directly to the scroll view's own edges instead (the
            // frame, not the content) was the actual bug: it forced the stack to the VISIBLE
            // width instead of its real content width, an unsatisfiable fit for 29 fixed-46pt
            // buttons, which collapsed the whole popup to near-zero size — confirmed on a real
            // device 2026-08-23, it rendered as a hairline sliver instead of a visible panel.
            // Height pinned to frameLayoutGuide (the visible area) so it scrolls horizontally
            // only, never vertically.
            stack.topAnchor.constraint(equalTo: scroll.contentLayoutGuide.topAnchor),
            stack.bottomAnchor.constraint(equalTo: scroll.contentLayoutGuide.bottomAnchor),
            stack.leadingAnchor.constraint(equalTo: scroll.contentLayoutGuide.leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: scroll.contentLayoutGuide.trailingAnchor),
            stack.heightAnchor.constraint(equalTo: scroll.frameLayoutGuide.heightAnchor),
            container.heightAnchor.constraint(equalToConstant: 56),
            container.bottomAnchor.constraint(equalTo: key.topAnchor, constant: -4),
            // The actual remaining bug (confirmed via device log 2026-08-24: showAlternatesPopup
            // DOES run with count=29, so the gesture/closure wiring was never the problem) —
            // container previously had ONLY inequality constraints (<=/>= "don't exceed the
            // view"), nothing that pins an exact value. A plain UIView has no intrinsic content
            // size, and nothing else in the chain fixes one either (scroll's own frame is pinned
            // to container, not derived from the stack's intrinsic width — that only sizes the
            // SCROLLABLE content, not the visible frame) — so the width was fully undetermined
            // and Auto Layout collapsed it to ~0. An equality constraint actually resolves it.
            container.widthAnchor.constraint(equalTo: self.view.widthAnchor, constant: -16),
            container.centerXAnchor.constraint(equalTo: self.view.centerXAnchor),
        ])

        alternatesPopup = container
        nlog("SLKey showAlternatesPopup count=\(key.alternates.count)")
    }

    private func selectAlternate(_ alt: String) {
        nlog("SLKey selectAlternate=\(alt)")
        textDocumentProxy.insertText(alt)
        dismissAlternatesPopup()
    }

    private func dismissAlternatesPopup() {
        alternatesPopup?.removeFromSuperview()
        alternatesPopup = nil
        alternatesPopupOwner = nil
    }

    @objc func didTapButton(key: Key) {
        nlog("SLKey didTapButton letterValue=\(key.letterValue)")
        // Any tap other than on the key that just opened the popup dismisses it — lets typing
        // continue normally without the popup getting stuck open; the key that owns it is
        // deliberately exempt so releasing a long-press over its own key doesn't instantly
        // close the popup it just opened.
        if let owner = alternatesPopupOwner, owner !== key {
            dismissAlternatesPopup()
        }
        let proxy = textDocumentProxy
        switch key.letterValue {
        case "...":
            symbol = !symbol
            if symbol { removeAllPanelAndAddThe(panel: symbolLayout) }
            else { removeAllPanelAndAddThe(panel: smallLetterLayout) }
        case "BackSpace":
            proxy.deleteBackward()
        case "Return":
            proxy.insertText("\n")
        case "Space":
            proxy.insertText(" ")
        case "NextKB":
            self.advanceToNextInputMode()
        case "Shift":
            shift = !shift
            if shift { removeAllPanelAndAddThe(panel: bigLetterLayout) }
            else { removeAllPanelAndAddThe(panel: smallLetterLayout) }
        default :
            proxy.insertText(key.letterValue)
            if shift {
                shift = false
                removeAllPanelAndAddThe(panel: smallLetterLayout)
            }
        }
    }


}
