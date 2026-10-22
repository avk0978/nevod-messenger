//
//  KeyModel.swift
//  SLEdit
//
//  Created by Andrey Kolpakov on 23.05.2018.
//  Copyright © 2018 Andrey Kolpakov. All rights reserved.
//

import Foundation
import UIKit

class Key: UIButton {
    var letterName: String
    var image: UIImage?
    
    var service: Bool {                                                                 // Служебная кнопка: ДА/НЕТ - ?
        if image != nil { return true }                                                 //Рисунок есть только у служебных кнопок
        else { return false }
    }
    
    var superscript: Bool {                                                             //Если название кнопки начинается с пробела то это "надстрочник"
        if letterName.first == " " { return true}
        else { return false }
    }

    // A combining diacritic (titlo, oxia, etc.) has no base character of its own — shown alone
    // on a button it would render invisibly or as a stray mark. "◌" (dotted circle, U+25CC) is
    // the standard placeholder virtual keyboards use so the mark has something to visibly land
    // on; Ponomar confirmed to include the glyph via cmap check. Only the PLACEHOLDER is
    // stripped on insert — the mark itself is what gets typed, landing on whatever real letter
    // precedes it in the text field.
    private static let combiningMarkPlaceholder: Unicode.Scalar = "◌"

    var letterValue: String {                                                           // Значение кнопки которое печатается
        if superscript {
            var value = letterName
            value.removeFirst()
            return value
        }
        // Character-level comparison/removeFirst() won't work here: Swift merges a base scalar
        // + a following combining mark into ONE grapheme cluster, so `letterName.first` is the
        // circle-plus-mark pair, never bare "◌" — confirmed on a real device 2026-08-23, the
        // circle printed straight into the message instead of being stripped. unicodeScalars
        // operates one scalar at a time regardless of how they cluster for display.
        guard letterName.unicodeScalars.first == Key.combiningMarkPlaceholder else { return letterName }
        var scalars = letterName.unicodeScalars
        scalars.removeFirst()
        return String(scalars)
    }

    // Long-press alternates (e.g. titlo → the 29 raised "выносные" letters written above it) —
    // user feedback 2026-08-23: a dedicated extra keyboard page made those letters too small to
    // read; a long-press popup (same idea as the system keyboard's accent picker on "e"→é/è/ê)
    // shows them at full size instead, and needs no extra page or switch key.
    var alternates: [String] = [] {
        didSet {
            guard !alternates.isEmpty, oldValue.isEmpty else { return }
            let lp = UILongPressGestureRecognizer(target: self, action: #selector(handleLongPress))
            lp.minimumPressDuration = 0.35
            addGestureRecognizer(lp)
        }
    }
    var onLongPress: ((Key) -> Void)?

    @objc private func handleLongPress(_ gr: UILongPressGestureRecognizer) {
        guard gr.state == .began else { return }
        onLongPress?(self)
    }

    // Matches the system keyboard's own dark-mode palette instead of the original stark
    // black-on-white 2018 design: lighter grey for letter keys, darker grey for service keys
    // (backspace/return/shift), same relationship real iOS dark keyboards use.
    private static let letterKeyColor = UIColor(white: 0.33, alpha: 1)
    private static let serviceKeyColor = UIColor(white: 0.15, alpha: 1)

    func initKey() {

        layer.cornerRadius = 6
        layer.shadowColor = UIColor.black.cgColor
        layer.shadowOffset = CGSize(width: 0, height: 1)
        layer.shadowOpacity = 0.5
        layer.shadowRadius = 1.0
        translatesAutoresizingMaskIntoConstraints = false

        if service && letterValue != " " {
            backgroundColor = Key.serviceKeyColor
            // Service icons (backspace/return/shift) are plain black-glyph PNGs designed for a
            // light key background — template rendering + tintColor recolors them white so
            // they stay visible against the now-dark key fill.
            setImage(image!.withRenderingMode(.alwaysTemplate), for: [])
            tintColor = .white
        } else {
            backgroundColor = Key.letterKeyColor
            setTitle(letterName, for: [])
            setTitleColor(.white, for: [])
            // Superscript/diacritic-only keys (the symbol layout's accent marks) previously
            // resized to 45pt — inside a 40-44pt-tall button that clipped/crowded the glyph,
            // which is exactly what made them hard to read. 26pt actually fits the key and
            // reads clearly; adjustsFontSizeToFitWidth is a safety net for any unusually wide
            // decorative glyph rather than a hard clip.
            titleLabel?.font = UIFont(name: "Ponomar-Regular", size: superscript ? 26 : 20)
            titleLabel?.adjustsFontSizeToFitWidth = true
            titleLabel?.minimumScaleFactor = 0.4
        }
    }
    
    init(_ letterName: String, image: UIImage?) {
        
        self.letterName = letterName
        self.image = image
        super.init(frame: .zero)
        initKey()
    }
    
    convenience init(_ letterName: String){
        
        self.init(letterName, image: nil)
    }
    
    convenience init(type: UIButton.ButtonType, _ letterName: String, image: UIImage?){
        
        self.init(letterName, image: image)
    }

//    convenience init(_ letter: String, _ capitalLetter: String?, image: UIImage?){
//
//        self.init(letter, capitalLetter, capitalize: false, image: image)
//    }

    
    required init?(coder aDecoder: NSCoder) {
        
        fatalError("init(coder:) has not been implemented")
    }
    
}

