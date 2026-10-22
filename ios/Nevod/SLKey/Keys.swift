//
//  Keys.swift
//  SLEdit
//
//  Created by Andrey Kolpakov on 23.05.2018.
//  Copyright © 2018 Andrey Kolpakov. All rights reserved.
//

import Foundation
import UIKit

let smallLetterLayout: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), bigLetterLayout: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), symbolLayout: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}()
// ------------------------------------------------------------------------
let topLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), firstLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), secondLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), thirdLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), bottomLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}()

let bigTopLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), bigFirstLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), bigSecondLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), bigThirdLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), bigBottomLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}()

let symbolTopLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), symbolFirstLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}(), symbolSecondLine: UIView = {
    let value = UIView()
    value.translatesAutoresizingMaskIntoConstraints = false
    return value
}()
//-----------------------------------------------------------------

let nextKBImg: UIImage = { return UIImage(named: "NextKB")! }()
let backSpaceImg: UIImage = { return UIImage(named: "BS_w31xh22")! }()
let returnImg: UIImage = { return UIImage(named: "Enter")! }()
let shiftImg: UIImage = { return UIImage(named: "Shape")! }()



let smallLetterRowTop = [Key("а"), Key("б"), Key("в"), Key("г"), Key("д"), Key("е"), Key("ж"), Key("з"), Key("и"), Key("й"), Key("BackSpace", image: backSpaceImg)]
let smallLetterRow1 = [Key("к"), Key("л"), Key("м"), Key("н"), Key("о"), Key("п"), Key("р"), Key("с"), Key("т"), Key("у"), Key("Return", image: returnImg)]
let smallLetterRow2 = [Key("ф"), Key("х"), Key("ц"), Key("ч"), Key("ш"), Key("щ"), Key("ъ"), Key("ы"), Key("ь"), Key("э"), Key("Shift", image: shiftImg)]
// Row3/bottom used to fill their leftover slots with plain Latin letters purely as decorative
// stand-ins (Hirmos UCS, replaced this round, had no real historic glyphs to type at all — see
// the font-coverage audit). Ponomar Unicode actually has these, so they're real historic
// Cyrillic letters now: omega/yat/fita/izhitsa/psi/ot/little-yus/big-yus (row3), then
// iotified-e/iotified-little-yus/iotified-big-yus/uk/round-omega/koppa (bottom row).
// "ѯ" (ksi, U+046F) added — full re-audit of the historic Cyrillic block 2026-08-23 found it
// was the only real letter Ponomar supports that never made it onto the keyboard.
let smallLetterRow3 = [Key("ю"), Key("я"), Key("ѡ"), Key("ѣ"), Key("ѳ"), Key("ѵ"), Key("ѱ"), Key("ѿ"), Key("ѧ"), Key("ѫ"), Key("ѯ")]
// Last slot used to be " 7" — a leftover decorative filler from the original Hirmos layout,
// never actually replaced in the round-14 sweep. "і" (decimal i, U+0456) is a real, distinct
// Church Slavonic letter (е.g. "Іисусъ") — more essential than "ї" (which was already added),
// and Ponomar confirmed to have it via cmap.
let smallLetterRowBottom = [Key("ѥ"), Key("ѩ"), Key("ѭ"), Key("..."), Key("  "), Key("ѹ"), Key("ѻ"), Key("ҁ"), Key("ї"), Key("і")]


let bigLetterRowTop = [Key("А"), Key("Б"), Key("В"), Key("Г"), Key("Д"), Key("Е"), Key("Ж"), Key("З"), Key("И"), Key("Й"), Key("BackSpace", image: backSpaceImg)]
let bigLetterRow1 = [Key("К"), Key("Л"), Key("М"), Key("Н"), Key("О"), Key("П"), Key("Р"), Key("С"), Key("Т"), Key("У"), Key("Return", image: returnImg)]
let bigLetterRow2 = [Key("Ф"), Key("Х"), Key("Ц"), Key("Ч"), Key("Ш"), Key("Щ"), Key("Ъ"), Key("Ы"), Key("Ь"), Key("Э"), Key("Shift", image: shiftImg)]
let bigLetterRow3 = [Key("Ю"), Key("Я"), Key("Ѡ"), Key("Ѣ"), Key("Ѳ"), Key("Ѵ"), Key("Ѱ"), Key("Ѿ"), Key("Ѧ"), Key("Ѫ"), Key("Ѯ")]
let bigLetterRowBottom = [Key("Ѥ"), Key("Ѩ"), Key("Ѭ"), Key("..."), Key("  "), Key("Ѹ"), Key("Ѻ"), Key("Ҁ"), Key("Ї"), Key("І")]

// Shrunk from 5 rows to 3 (user request 2026-08-23): Church Slavonic text has no digits and
// no use for most ASCII symbols (they're used to typeset MODERN languages, not this one) — the
// original 0-9/!#$%&()*+<=>@ rows carried nothing actually needed for writing Church Slavonic.
// Kept only the handful still genuinely useful for punctuating a chat message.
// Row 1: the symbols actually worth keeping, plus BackSpace (was spread across all 3 old rows).
let symbolLetterRowTop = [Key(":"), Key(";"), Key(","), Key("."), Key("?"), Key("_"), Key("-"), Key("BackSpace", image: backSpaceImg)]
// Row 2: combining diacritics — real Church Slavonic writing needs these (titlo for
// abbreviated/sacred words, stress accents), which Ponomar Unicode actually has (confirmed via
// cmap: U+0483-0489 Cyrillic combining block + U+0300/0301/0311 general accents all present).
// Each is prefixed with "◌" (dotted circle) so the mark has a visible base to land on when shown
// alone on a key — KeyModel.swift strips that placeholder on insert, so only the real combining
// mark gets typed, landing on whatever letter precedes it. Plus Return (was on the removed row).
// Dropped the hundred-thousands/millions numeral marks (U+0488/0489) — user feedback 2026-08-23:
// too obscure/rarely useful for everyday writing, and the two nearly-identical-looking glyphs at
// the end of the row read as confusing rather than useful.
let symbolLetterRow1: [Key] = {
    let titlo = Key("◌\u{0483}")
    // "Выносные буквы" — a real Church Slavonic scribal convention: a letter omitted from an
    // abbreviated (titlo-marked) word is written raised above the line instead. Unicode has a
    // dedicated "Combining Cyrillic Letters" block for exactly this (U+2DE0-2DFF) — confirmed
    // via cmap that Ponomar supports 29 of its 32 letters (the 3 missing ones aren't in the font
    // at all, so left off here). First tried as a whole separate keyboard page — user feedback
    // 2026-08-23: the letters were too small to read there. A long-press popup on the titlo key
    // itself (same idea as the system keyboard's accent picker on "e"→é/è/ê) shows them at full
    // size on demand instead, and needs no extra page or switch key.
    titlo.alternates = ["\u{2DE0}","\u{2DE1}","\u{2DE2}","\u{2DE3}","\u{2DE4}","\u{2DE5}","\u{2DE6}","\u{2DE7}",
                         "\u{2DE8}","\u{2DE9}","\u{2DEA}","\u{2DEB}","\u{2DEC}","\u{2DED}","\u{2DEE}","\u{2DEF}",
                         "\u{2DF0}","\u{2DF1}","\u{2DF2}","\u{2DF3}","\u{2DF4}","\u{2DF5}","\u{2DF6}","\u{2DF7}",
                         "\u{2DF9}","\u{2DFA}","\u{2DFB}","\u{2DFC}","\u{2DFD}"]
    return [titlo, Key("◌\u{0301}"), Key("◌\u{0300}"), Key("◌\u{0311}"), Key("◌\u{0484}"), Key("◌\u{0485}"), Key("◌\u{0486}"), Key("◌\u{0487}"), Key("Return", image: returnImg)]
}()
// Row 3: punctuation genuinely missing before (no quotes at all) plus the long dash/ellipsis/
// guillemets standard in Russian-language typography, all confirmed present in Ponomar's cmap.
// "-" already lives on row 1, so not duplicated here. Plus Shift (was on the removed row).
let symbolLetterRow2 = [Key("\""), Key("'"), Key("..."), Key("  "), Key("—"), Key("…"), Key("«"), Key("»"), Key("Shift", image: shiftImg)]



















