"""
Who may change a node's node_table (gossip.handle_gossip, node.py _handle_node_remove /
_handle_node_leaving) and which nodes are ever chosen as push / TURN relays
(node/relays.py, storage.get_push_relay_nodes / get_turn_relay_nodes).
"""

import json
import time
from pathlib import Path
from types import SimpleNamespace

from node.identity import NodeIdentity
from node.node import Node
from node.protocol import Packet, T, encode_payload, make_gossip
from node.relays import PROJECT_RELAY_NODE_IDS
from node.storage import NodeEntry

KNOWN = "aa" * 32       # a node admitted earlier — in our node_table
STRANGER = "bb" * 32    # never admitted
NEW = "cc" * 32         # introduced through gossip
OPEN = "2050f850823921b135e467fe27d59b7701327d3fdb3b4685f4bba9441de64504"  # a project relay


async def make_node(tmp_path) -> Node:
    id_path = str(tmp_path / "n.json")
    NodeIdentity.generate("127.0.0.1:19790").save(id_path)
    node = await Node.create(id_path, str(tmp_path / "n.db"))
    await add(node, KNOWN, "10.0.0.1:8765")
    return node


async def add(node: Node, node_id: str, address: str, push: str = "", turn: bool = False):
    now = int(time.time())
    await node.storage.upsert_node(NodeEntry(
        node_id=node_id, address=address, access="open", tls_fingerprint="f" * 64,
        push_relay_platforms=push, turn_relay=turn, last_seen=now, added_at=now))


def entry(node_id: str, address: str, push: str = "", turn: bool = False) -> dict:
    return {"node_id": node_id, "address": address, "tls_fingerprint": "e" * 64,
            "push_relay_platforms": push, "turn_relay": turn}


async def gossip(node: Node, sender: str, nodes: list, presence: list | None = None):
    pkt = make_gossip(sender, nodes, presence)
    await node.gossip.handle_gossip(pkt, SimpleNamespace(peer_node_id=sender))


class TestGossipSender:
    async def test_unknown_sender_ignored(self, tmp_path):
        node = await make_node(tmp_path)
        await gossip(node, STRANGER, [entry(NEW, "6.6.6.6:8765")])
        assert await node.storage.get_node(NEW) is None

    async def test_unknown_sender_cannot_add_itself(self, tmp_path):
        """A node that was never admitted can't get in by gossiping its own entry —
        otherwise node_join_mode="invite" could be bypassed."""
        node = await make_node(tmp_path)
        await gossip(node, STRANGER, [entry(STRANGER, "6.6.6.6:8765")])
        assert await node.storage.get_node(STRANGER) is None

    async def test_known_sender_introduces_new_node(self, tmp_path):
        node = await make_node(tmp_path)
        await gossip(node, KNOWN, [entry(NEW, "5.5.5.5:8765")])
        assert (await node.storage.get_node(NEW)).address == "5.5.5.5:8765"

    async def test_third_party_cannot_rewrite_known_node(self, tmp_path):
        node = await make_node(tmp_path)
        await add(node, NEW, "5.5.5.5:8765")
        await gossip(node, KNOWN, [entry(NEW, "6.6.6.6:8765", push="apns", turn=True)])
        n = await node.storage.get_node(NEW)
        assert n.address == "5.5.5.5:8765" and n.tls_fingerprint == "f" * 64
        assert not n.turn_relay and n.push_relay_platforms_list() == []

    async def test_node_updates_its_own_entry(self, tmp_path):
        node = await make_node(tmp_path)
        await gossip(node, KNOWN, [entry(KNOWN, "10.0.0.2:8765")])
        assert (await node.storage.get_node(KNOWN)).address == "10.0.0.2:8765"


class TestGossipPresence:
    async def test_sender_announces_its_own_cells(self, tmp_path):
        node = await make_node(tmp_path)
        await gossip(node, KNOWN, [], [{"cell_id": "11" * 32, "home_node_id": KNOWN}])
        assert (await node.storage.get_presence("11" * 32)).home_node_id == KNOWN

    async def test_sender_cannot_claim_cells_of_another_node(self, tmp_path):
        node = await make_node(tmp_path)
        await gossip(node, KNOWN, [], [{"cell_id": "11" * 32, "home_node_id": NEW}])
        assert await node.storage.get_presence("11" * 32) is None


class TestNodeRemoveAndLeaving:
    async def test_remove_of_another_node_ignored(self, tmp_path):
        node = await make_node(tmp_path)
        await add(node, NEW, "5.5.5.5:8765")
        pkt = Packet(type=T.NODE_REMOVE, payload=encode_payload({"node_id": NEW}), from_addr=KNOWN)
        await node._handle_node_remove(pkt, SimpleNamespace(peer_node_id=KNOWN))
        assert await node.storage.get_node(NEW) is not None

    async def test_leaving_uses_authenticated_sender(self, tmp_path):
        node = await make_node(tmp_path)
        await add(node, NEW, "5.5.5.5:8765")
        # from_addr names NEW, but the connection belongs to STRANGER
        pkt = Packet(type=T.NODE_LEAVING, payload=b"", from_addr=NEW)
        await node._handle_node_leaving(pkt, SimpleNamespace(peer_node_id=STRANGER))
        assert await node.storage.get_node(NEW) is not None

    async def test_node_leaves_by_itself(self, tmp_path):
        node = await make_node(tmp_path)
        pkt = Packet(type=T.NODE_LEAVING, payload=b"", from_addr=KNOWN)
        await node._handle_node_leaving(pkt, SimpleNamespace(peer_node_id=KNOWN))
        assert await node.storage.get_node(KNOWN) is None


class TestTrustedRelays:
    async def test_only_trusted_nodes_are_relays(self, tmp_path, monkeypatch):
        monkeypatch.delenv("NEVOD_TRUSTED_RELAYS", raising=False)
        node = await make_node(tmp_path)
        await add(node, NEW, "5.5.5.5:8765", push="apns", turn=True)
        await add(node, OPEN, "203.0.113.10:8775", push="apns", turn=True)
        assert [n.node_id for n in await node.storage.get_push_relay_nodes("apns")] == [OPEN]
        assert [n.node_id for n in await node.storage.get_turn_relay_nodes()] == [OPEN]

    async def test_env_replaces_project_list(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NEVOD_TRUSTED_RELAYS", f" {NEW} , ")
        node = await make_node(tmp_path)
        await add(node, NEW, "5.5.5.5:8765", push="apns", turn=True)
        await add(node, OPEN, "203.0.113.10:8775", push="apns", turn=True)
        assert [n.node_id for n in await node.storage.get_push_relay_nodes("apns")] == [NEW]
        assert [n.node_id for n in await node.storage.get_turn_relay_nodes()] == [NEW]

    def test_project_list_matches_signed_manifest(self):
        """The default relay list is the curator-signed nodes.json the app ships."""
        manifest = Path(__file__).resolve().parent.parent / "ios/Nevod/Nevod/nodes.json"
        data = json.loads(manifest.read_text())
        nodes = data if isinstance(data, list) else data.get("nodes", data)
        assert {n["node_id"] for n in nodes} == set(PROJECT_RELAY_NODE_IDS)
