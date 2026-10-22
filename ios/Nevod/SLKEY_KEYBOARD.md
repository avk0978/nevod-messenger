# SLKey — Church Slavonic keyboard extension

`ios/Nevod/SLKey/` is a custom iOS keyboard extension (`com.apple.keyboard-service`)
embedded in the Nevod app for typing Church Slavonic text. It started life as
Andrey's 2018 personal project [OrtodoxKeyboard](https://github.com/avk0978/OrtodoxKeyboard)
(originally `SLEdit`/`SLKey`), reviewed, fixed, and embedded into Nevod in 2026,
then substantially redesigned (real Unicode font, historic letters, titlo +
raised-letter picker). The standalone OrtodoxKeyboard repo carries the same
final feature set, ported back after this work was confirmed on-device.

## Files

- `Keys.swift` — all layout data: the 4 `UIView` layout containers
  (`smallLetterLayout` / `bigLetterLayout` / `symbolLayout`, plus each layout's
  row-container views), and every row's `[Key]` array (`smallLetterRowTop`,
  `symbolLetterRow1`, etc). This is the only file you touch to add/remove/
  reorder keys.
- `KeyModel.swift` — the `Key: UIButton` class. Owns the dark key styling,
  the superscript/combining-mark stripping logic (`letterValue`), and the
  long-press-alternates mechanism (`alternates`, `onLongPress`).
- `KeyboardViewController.swift` — the `UIInputViewController` subclass.
  Builds/swaps the 3 layouts, computes the keyboard's requested height,
  handles every key tap, and owns the long-press alternates popup.
- `KeyControler.swift` — `SlavonicKeyboard` protocol extension: pure Auto
  Layout math (row stacking, per-key weighted widths). No state.
- `Ponomar-Regular.ttf` — the font (see below). Also copied into
  `ios/Nevod/Nevod/` so the main app's compose field and message bubbles can
  render the same font.
- `Info.plist` — `PrimaryLanguage` is `cu` (real ISO 639-2 code for Church
  Slavonic) and `UIAppFonts` registers the font for the extension process.

## Font: Ponomar Unicode, not Hirmos UCS

The original 2018 project used a font called "Hirmos UCS" that LOOKS like
Church Slavonic but isn't: its ~224 mapped code points are ordinary Latin/
Cyrillic ASCII positions redrawn with decorative glyphs — there is no real
Unicode Church Slavonic text underneath, so text typed with it isn't
actually interoperable Church Slavonic Unicode.

**Ponomar Unicode** (SIL OFL, `github.com/slavonic/Ponomar`) is the real
Unicode-encoded successor from the same design lineage (same original
designer, later re-encoded for Unicode by Aleksandr Andreev/Nikita Simmons).
It has 781 mapped code points, including full coverage of:
- the historic Cyrillic letters (U+0460–0481: omega, yat, fita, izhitsa,
  psi, ot, ksi, little/big yus, etc.)
- the Cyrillic combining marks (U+0483–0489: titlo, palatalization, dasia/
  psili pneumata, pokrytie, numeral marks)
- the "Combining Cyrillic Letters" block (U+2DE0–2DFF) — 29 of 32 present
- general combining accents (U+0300/0301/0311 — varia/oxia/kamora)

## Layouts

Three `UIView` layouts, swapped in/out of `self.view` by
`KeyboardViewController.createPanel(layout:)`:

1. **Letters** (`smallLetterLayout` / `bigLetterLayout`, 5 rows) — standard
   Cyrillic alphabet plus the historic letters that Hirmos UCS never had
   real glyphs for. Toggling Shift swaps between the two.
2. **Symbols** (`symbolLayout`, 3 rows) — deliberately NOT a full ASCII/
   digit keyboard. Church Slavonic text has no use for digits or most ASCII
   punctuation (that's for typesetting modern languages), so this layout
   only carries: the handful of symbols actually needed (`: ; , . ? _ -`),
   the 8 combining diacritics (titlo + 3 stress accents + 4 more marks),
   and punctuation that was missing before (quotes, em dash, ellipsis,
   guillemets).

The keyboard's requested height (`heightConstraint`) changes per layout
(letters = 5 rows, symbols = 3 rows) via `height(forRows:)`.

## Combining marks and the dotted-circle convention

A combining mark (titlo, a stress accent, a raised letter) has no base
character of its own — shown alone on a key it would render invisibly. Every
such key's `letterName` is `"◌" + <the mark>` (U+25CC dotted circle, the
standard placeholder virtual keyboards use). `Key.letterValue` strips that
placeholder before insertion, so only the real mark gets typed and lands on
whatever letter precedes it in the text field.

**Gotcha**: Swift merges a base scalar + a following combining mark into ONE
`Character` (extended grapheme cluster) — `letterName.first` is the
circle-plus-mark pair, never bare `"◌"`. The strip logic operates on
`letterName.unicodeScalars` instead, which sees them as separate scalars
regardless of how they cluster for display.

## Titlo + raised letters ("выносные буквы")

A real Church Slavonic scribal convention: when a word is abbreviated with a
titlo (a wavy line drawn over it), a letter omitted from the abbreviation is
written raised above the line, inside/near the titlo's arc. Unicode's
"Combining Cyrillic Letters" block (U+2DE0–2DFF) exists specifically for
this.

This is implemented as a **long-press popup** on the titlo key, not a
separate keyboard page (an earlier attempt at a dedicated 4th page made the
letters too small to read). `Key.alternates: [String]` holds the 29 raised-
letter marks; setting it non-empty attaches a `UILongPressGestureRecognizer`
(`didSet` observer). Long-pressing calls `KeyboardViewController.
showAlternatesPopup(for:)`, which builds a horizontally-scrollable
`UIScrollView`/`UIStackView` of large buttons above the key. Releasing the
long-press over the titlo key itself still fires the normal tap (types
titlo) — the popup is purely additive; picking a letter from it inserts just
that raised-letter mark on top.

**Gotcha (scroll content sizing)**: the popup's container `UIView` needs an
actual *equality* width constraint. Plain `UIView`s have no intrinsic
content size, and pinning the scroll view's content to its own frame anchors
(instead of `contentLayoutGuide`) doesn't help either — that only sizes the
frame from the container, not the other way around. Without an equality
width relationship somewhere in the chain, Auto Layout resolves the whole
popup to ~0×0. Fixed by giving the container `widthAnchor.constraint(equalTo:
view.widthAnchor, constant: -16)`.

## Two real Auto Layout bugs worth remembering

1. **Height constraint fighting the system's own one.** Setting
   `view.heightAnchor.constraint(equalToConstant:)` at `.required` priority
   (the default) directly conflicts with iOS's own auto-generated
   `UIView-Encapsulated-Layout-Height` constraint on the same property —
   "Unable to simultaneously satisfy constraints" logged on every single
   open, with visible height-thrashing before it settles. Fix: set the
   constraint's priority to `.required - 1` so the system silently drops its
   own constraint instead of an emergency break-and-recover.
2. **Over-constraining the last row.** Every row needs an explicit height +
   a top pinned to either the container (first row) or the previous row's
   bottom — that alone fully determines every row's frame. Also pinning the
   *last* row's bottom to the container over-constrains it (three competing
   vertical constraints) and silently breaks touch handling on most keys.

## App Group logging gotcha (debugging aid, not required for the extension to work)

The main Nevod app and the SLKey extension are separate OS processes that
can both be alive at once and both write to the same shared log file
(`NevLogger`, in `group.com.avk.Nevod`'s container). Each process's
`FileHandle` only seeks to end-of-file once, at open — if the *other*
process appends in between, the next write lands at a now-stale offset and
silently clobbers what the other process just wrote. `Logger.swift` reseeks
to EOF before every write to avoid this. There's also a redundant `os.Logger`
channel (visible live in Console.app / Xcode's Devices window, filtered to
process "SLKey") that doesn't depend on the file write succeeding at all —
this is what actually made diagnosing the two bugs above possible, since the
file channel was silently losing SLKey's lines to the race described above.

## Per-key width math

`KeyControler.addConstraintsOnTheKey` computes each key's width as a
weighted fraction of the row's total width (space bar = weight 4,
BackSpace/Return/Shift/NextKB = weight 2, everything else = weight 1) rather
than a hardcoded `/12` divisor — the fixed divisor assumed every row had
exactly the same key count, which silently left a gap on any row with fewer
keys.
