"""Which nodes this node may hand push tokens and TURN requests to.

A node without its own APNs key or TURN_SECRET borrows them from another node that
advertises push_relay_platforms / turn_relay in the node table. Those flags arrive via
gossip and are only a node's own claim, while the relay gets real things: device push
tokens, sender display names and timing, and the TURN server the node's users call
through. So a claim alone is not enough — only nodes on a fixed list are ever chosen as
relays.

By default the list is the project's nodes, the same node_ids the curator signs into
the app's bootstrap manifest (ios/Nevod/Nevod/nodes.json; tests/test_relays.py keeps
the two in sync). A network outside the project that runs relays of its own sets
NEVOD_TRUSTED_RELAYS to a comma-separated list of their node_ids instead.
"""
import os

PROJECT_RELAY_NODE_IDS = frozenset({
    "0c69eee506cc5f897b65f231df37f0214130e9c3f461393983a6794a99f4f2cd",  # Dev Planet
    "63a79b460f5922d341ccf324b3fb5b9b9b33d4c7887150545f01414b3f8e15b8",  # Nevod Home
    "2050f850823921b135e467fe27d59b7701327d3fdb3b4685f4bba9441de64504",  # Nevod Open
    "1156066c50b9bc2a08c4a2f7c710c6d848c98c45a235f1d5cad5c272935671d8",  # Kitaevo
    "431546eec7def694df899e796019a23874d0bab2b71f70771cf9da4baa434f95",  # avk
})


def trusted_relay_ids() -> frozenset:
    raw = os.environ.get("NEVOD_TRUSTED_RELAYS", "").strip()
    if raw:
        return frozenset(x.strip() for x in raw.split(",") if x.strip())
    return PROJECT_RELAY_NODE_IDS
