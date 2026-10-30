"""The project's shared node blocklist, signed by the curator (blocked_nodes.json).

A node's operator can always block a node for their own node (Node.block_node). This is
the network-wide part: the curator lists nodes that spam or carry forbidden content, signs
the whole list with the offline curator key (python -m node.curator_sign sign-blocklist),
and deploy_manifest.sh publishes it next to nodes.json. Project nodes apply it by default
— a listed node loses their push and TURN relays along with everything else a block
means; any other node applies it only if its operator switches it on (panel "Узлы").

The signature covers the whole list together with its version, so nobody can serve an
older list (to lift a block) or drop entries from the current one: a node only ever moves
to a higher version.
"""
import json
import logging
import os
from typing import Optional

from .crypto import verify

log = logging.getLogger(__name__)

# The curator's public key — the same trust anchor as the app's
# NodeManifest.curatorPublicKeyHex (tests/test_blocklist.py keeps the two in sync).
CURATOR_PUBKEY_HEX = "cdb8ac2df5d20663c1049df145615881ee93755a3daac9a412b267fb909cdab5"
DEFAULT_URL = "https://node1.nevod.network/blocked_nodes.json"
FETCH_INTERVAL = 3600  # seconds
MAX_REASON = 500


def _valid_node_id(node_id: str) -> bool:
    return len(node_id) == 64 and all(c in "0123456789abcdef" for c in node_id)


def canonical_message(version: int, nodes: dict) -> bytes:
    """Bytes the curator signs: the version, then one "node_id|reason" line per entry in
    node_id order. node_id is fixed-length hex and a reason has no newline, so the
    encoding is unambiguous."""
    lines = [f"blocked-nodes|{int(version)}"]
    lines += [f"{nid}|{nodes[nid]}" for nid in sorted(nodes)]
    return "\n".join(lines).encode("utf-8")


def parse(doc: dict) -> Optional[tuple]:
    """(version, {node_id: reason}) from a blocked_nodes.json document, or None if it is
    malformed. Does not check the signature."""
    try:
        version = int(doc["version"])
        nodes = {}
        for e in doc["nodes"]:
            nid = str(e["node_id"]).strip().lower()
            reason = str(e.get("reason", ""))
            if not _valid_node_id(nid) or "\n" in reason or len(reason) > MAX_REASON:
                return None
            nodes[nid] = reason
        return version, nodes
    except (KeyError, TypeError, ValueError):
        return None


def verify_doc(doc: dict, pubkey_hex: Optional[str] = None) -> Optional[tuple]:
    """(version, {node_id: reason}) if the document is well-formed and signed by the
    curator (or by pubkey_hex), else None."""
    pubkey_hex = pubkey_hex or CURATOR_PUBKEY_HEX
    parsed = parse(doc) if isinstance(doc, dict) else None
    if not parsed:
        return None
    try:
        sig = bytes.fromhex(str(doc.get("sig", "")))
    except ValueError:
        return None
    version, nodes = parsed
    if not sig or not verify(canonical_message(version, nodes), sig, bytes.fromhex(pubkey_hex)):
        return None
    return version, nodes


def load_saved(path: str) -> Optional[dict]:
    """The last accepted document, re-verified (a hand-edited file is ignored)."""
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return None
    return doc if verify_doc(doc) else None


def save(path: str, doc: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


async def fetch(url: str) -> Optional[dict]:
    """The published document, or None on any failure (offline, 404 before the first list
    is published, bad JSON) — the node then keeps what it has."""
    import aiohttp
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(url, headers={"Cache-Control": "no-cache"}) as r:
                if r.status != 200:
                    return None
                return json.loads(await r.text())
    except Exception as e:
        log.debug("blocklist fetch %s failed: %s", url, e)
        return None
