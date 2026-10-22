//
//  KeyControler.swift
//  SLEdit
//
//  Created by Andrey Kolpakov on 23.05.2018.
//  Copyright © 2018 Andrey Kolpakov. All rights reserved.
//

import Foundation
import UIKit

protocol  SlavonicKeyboard {
    func addConstraintOnthe(_ layout: UIView, inThe supperView: UIView) -> Void
    func addConstraintsOnThe(lines: [UIView], in view: UIView, heightLine: CGFloat, space: CGFloat) -> Void
    func addConstraintsOnTheKey(buttons: [Key], inThe view: UIView, indentLeft: CGFloat, indentRight: CGFloat, space: CGFloat) -> Void
}

extension SlavonicKeyboard {
    
    func addConstraintOnthe(_ layout: UIView, inThe supperView: UIView) -> Void {
        layout.topAnchor.constraint(equalTo: supperView.topAnchor).isActive = true
        layout.bottomAnchor.constraint(equalTo: supperView.bottomAnchor).isActive = true
        layout.leftAnchor.constraint(equalTo: supperView.leftAnchor).isActive = true
        layout.rightAnchor.constraint(equalTo: supperView.rightAnchor).isActive = true
    }
    
    // Every row gets an explicit height + a top pinned either to the container (first row) or
    // to the previous row's bottom (every other row) — that alone fully determines every row's
    // frame, no row needs its bottom pinned too. Deliberately NOT also pinning the last row's
    // bottom to the container (the original 2018 code did, combined with an inert/never-
    // activated height constraint that made the redundancy harmless) — confirmed via a real
    // device test 2026-08-22 that activating the height constraint (a real bug, fixed) while
    // ALSO keeping the last row's bottom pin makes that row over-constrained (three competing
    // vertical constraints), and the resulting Auto Layout conflict left most keys untappable
    // (only Shift, on a middle row unaffected by the conflict, still worked).
    func addConstraintsOnThe(lines: [UIView], in view: UIView, heightLine: CGFloat, space: CGFloat) {
        for (index, line) in lines.enumerated(){
            line.leftAnchor.constraint(equalTo: view.leftAnchor).isActive = true
            line.rightAnchor.constraint(equalTo: view.rightAnchor).isActive = true
            line.heightAnchor.constraint(equalToConstant: heightLine).isActive = true
            if index == 0 {
                line.topAnchor.constraint(equalTo: view.topAnchor).isActive = true
            } else {
                line.topAnchor.constraint(equalTo: lines[index-1].bottomAnchor, constant: space).isActive = true
            }
        }
    }
    
    
    // Per-key width is computed from the ROW'S ACTUAL composition (weighted units summing to
    // 1.0 of the available width) rather than a hardcoded /12 divisor sized for an 11-key row —
    // the fixed divisor assumed every row had exactly the same key count, which silently left a
    // gap on rows with fewer keys (e.g. after removing the in-grid "next keyboard" key, since
    // iOS already shows its own switch affordance for any custom keyboard extension). The math
    // still guarantees the row exactly fills view.width: sum of all (fraction * width -
    // fraction * totalInsets) over a row whose fractions sum to 1 collapses to exactly
    // (view.width - totalInsets), matching what indentLeft/indentRight/space actually consume.
    func addConstraintsOnTheKey(buttons: [Key], inThe view: UIView, indentLeft: CGFloat, indentRight: CGFloat, space: CGFloat) -> Void {
        let idents = indentLeft + indentRight
        let totalSpacing = space * CGFloat(max(buttons.count - 1, 0))
        func weight(_ button: Key) -> CGFloat {
            switch button.letterValue {
            case " ": return 4
            case "BackSpace", "Return", "NextKB", "Shift": return 2
            default: return 1
            }
        }
        let totalWeight = buttons.reduce(0) { $0 + weight($1) }

        for (index, button) in buttons.enumerated() {
            button.topAnchor.constraint(equalTo: view.topAnchor, constant: 5).isActive = true
            button.bottomAnchor.constraint(equalTo: view.bottomAnchor, constant: -5).isActive = true
            let fraction = weight(button) / totalWeight
            button.widthAnchor.constraint(equalTo: view.widthAnchor, multiplier: fraction,
                                           constant: -(idents + totalSpacing) * fraction).isActive = true
            switch index {
            case 0:
                let nextButton = buttons[1]
                button.leftAnchor.constraint(equalTo: view.leftAnchor, constant: indentLeft).isActive = true
                button.rightAnchor.constraint(equalTo: nextButton.leftAnchor, constant: -space).isActive = true
            case buttons.count - 1:
                button.rightAnchor.constraint(equalTo: view.rightAnchor, constant: -indentRight).isActive = true
            default:
                let nextButton = buttons[index + 1]
                button.rightAnchor.constraint(equalTo: nextButton.leftAnchor, constant: -space).isActive = true
            }
        }
    }
    
}









