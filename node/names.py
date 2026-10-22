"""Reserved display names — anti-impersonation for official Nevod accounts.

Nevod's rule (2026-09-28): the network administration answers every abuse@/support@/
privacy@ email ONLY inside the Nevod app, from the official "administrator" account, never
by email. That rule only protects users if nobody else can call themselves "administrator"
— display names are otherwise freely chosen. So a node refuses to register a name that
normalizes to one of the reserved words below, unless the cell is one of this node's own
official cells (NEVOD_OFFICIAL_CELL_IDS).

Normalization is deliberately aggressive (case, separators, digits-for-letters, and
Cyrillic/Greek look-alikes all fold together) — "Аdmin" with a Cyrillic А, "adm1n",
"Ad.Min" and "администратор" must all be caught. The iOS app mirrors this exact list and
folding (ios/Nevod/Nevod/Storage/ReservedNames.swift) to warn about look-alikes coming
from nodes that don't run this check; keep the two in sync.
"""
import os
import unicodedata

# Folded forms (see _fold) — compared as substrings, so "nevodadmin" or "supportteam" match too.
RESERVED_STEMS = (
    "administrator", "admin", "moderator", "support", "nevod", "registrar", "official",
    "security", "abuse",
)

# Look-alikes → Latin. Cyrillic and Greek letters that render identically (or nearly) to
# Latin ones, plus transliteration of the Russian/Ukrainian words for the reserved roles
# is handled by listing those stems explicitly in RESERVED_NATIVE below.
_CONFUSABLES = str.maketrans({
    "а": "a", "в": "b", "е": "e", "ё": "e", "к": "k", "м": "m", "н": "h", "о": "o",
    "р": "p", "с": "c", "т": "t", "у": "y", "х": "x", "і": "i", "ї": "i", "ј": "j",
    "ѕ": "s", "ԁ": "d", "ɡ": "g", "ո": "n",
    "α": "a", "β": "b", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p",
    "τ": "t", "υ": "u", "χ": "x",
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "@": "a", "$": "s",
    "!": "i", "|": "i", "l": "i",
})

# Native-language forms of the same roles. Folded with the exact same _fold() as names
# (not just the confusables table) — otherwise e.g. "й" in "официальный" survives in the stem
# but decomposes to "и" in the name, and the two never match.
RESERVED_NATIVE = (
    "администратор", "админ", "адмін", "модератор", "поддержка", "підтримка", "невод",
    "регистратор", "реєстратор", "официальный", "офіційний", "безопасность",
)


def _fold(name: str) -> str:
    # NFKC collapses full-width / styled Unicode letters (𝐚𝐝𝐦𝐢𝐧) to plain ones first.
    s = unicodedata.normalize("NFKC", name).lower().translate(_CONFUSABLES)
    # Strip combining marks (accents) and everything that isn't a letter.
    s = "".join(ch for ch in unicodedata.normalize("NFD", s)
                if unicodedata.category(ch) != "Mn")
    return "".join(ch for ch in s if ch.isalpha())


def is_reserved_name(name: str) -> bool:
    folded = _fold(name)
    if not folded:
        return False
    return any(stem in folded for stem in _FOLDED_STEMS)


_FOLDED_STEMS = tuple(_fold(stem) for stem in RESERVED_STEMS + RESERVED_NATIVE)


# Node names that would pass a stranger's node off as one of the project's own. Only
# checked for nodes joining WITHOUT an invite (node_join_mode="open", i.e. Nevod Open) —
# a node admitted by invite was vouched for by whoever issued it. The ring of a verified
# node in the app comes from the curator-signed nodes.json, not from the name, but a
# look-alike name next to it would still mislead.
RESERVED_NODE_STEMS = RESERVED_STEMS + ("devplanet", "nevodopen", "kitaevo", "avk")


def is_reserved_node_name(name: str) -> bool:
    folded = _fold(name)
    if not folded:
        return False
    if folded in _FOLDED_SHORT_NODE_STEMS:
        return True
    return any(stem in folded for stem in _FOLDED_NODE_STEMS)


# Stems this short ("avk") would match inside ordinary words as substrings — whole name only.
_FOLDED_SHORT_NODE_STEMS = tuple(_fold(s) for s in RESERVED_NODE_STEMS if len(_fold(s)) <= 3)
_FOLDED_NODE_STEMS = tuple(
    _fold(s) for s in RESERVED_NODE_STEMS + RESERVED_NATIVE if len(_fold(s)) > 3
)


def official_cell_ids() -> set:
    """This node's own official cells, allowed to use reserved names — comma-separated
    NEVOD_OFFICIAL_CELL_IDS (full hex cell ids). Read per call: cheap, and lets an operator
    change it with a plain container restart."""
    raw = os.environ.get("NEVOD_OFFICIAL_CELL_IDS", "")
    return {c.strip().lower() for c in raw.split(",") if c.strip()}
