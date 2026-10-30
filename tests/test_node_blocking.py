"""
Blocking a node (admin panel "Узлы" → Заблокировать, node.py block_node): it leaves
node_table and presence, is never connected to or accepted (Transport.is_blocked), can't
come back through gossip, and nothing is routed from or to its cells (Router.route).
"""

import asyncio
import time
from types import SimpleNamespace

from node.identity import NodeIdentity
from node.node import Node
from node.protocol import Packet, T, make_gossip
from node.storage import NodeEntry

KNOWN = "aa" * 32    # an admitted node that gossips to us
BAD = "bb" * 32      # the node we block

BASE = 19820


async def make_node(tmp_path, name: str = "n", port: int = BASE) -> Node:
    id_path = str(tmp_path / f"{name}.json")
    NodeIdentity.generate(f"127.0.0.1:{port}").save(id_path)
    return await Node.create(id_path, str(tmp_path / f"{name}.db"))


async def add(node: Node, node_id: str, address: str, name: str = ""):
    now = int(time.time())
    await node.storage.upsert_node(NodeEntry(
        node_id=node_id, address=address, access="open", name=name,
        last_seen=now, added_at=now))


async def gossip(node: Node, sender: str, nodes: list, presence: list | None = None):
    await node.gossip.handle_gossip(make_gossip(sender, nodes, presence),
                                    SimpleNamespace(peer_node_id=sender))


def msg(from_addr: str, to_addr: str) -> Packet:
    return Packet(type=T.MSG, payload=b"", from_addr=from_addr, to_addr=to_addr)


class TestBlockNode:
    async def test_block_removes_node_and_presence_and_survives_restart(self, tmp_path):
        node = await make_node(tmp_path)
        await add(node, BAD, "6.6.6.6:8765", name="Spam")
        await node.storage.update_presence("c1" * 32, BAD)
        assert await node.block_node(BAD.upper(), reason="spam")
        assert node.is_node_blocked(BAD)
        assert await node.storage.get_node(BAD) is None
        assert await node.storage.get_presence("c1" * 32) is None
        [row] = await node.storage.list_blocked_nodes()
        assert (row["node_id"], row["name"], row["address"], row["reason"]) == \
            (BAD, "Spam", "6.6.6.6:8765", "spam")
        await node.storage.close()

        again = await make_node(tmp_path)
        assert not again.is_node_blocked(BAD)   # loaded in start()
        await again.start()
        try:
            assert again.is_node_blocked(BAD)
        finally:
            await again.stop()

    async def test_bad_ids_and_own_id_refused(self, tmp_path):
        node = await make_node(tmp_path)
        assert not await node.block_node("xyz")
        assert not await node.block_node("zz" * 32)
        assert not await node.block_node(node.identity.node_id)
        assert await node.storage.list_blocked_nodes() == []

    async def test_unblock(self, tmp_path):
        node = await make_node(tmp_path)
        await add(node, KNOWN, "10.0.0.1:8765")
        await node.block_node(BAD)
        assert await node.unblock_node(BAD)
        assert not node.is_node_blocked(BAD)
        assert await node.storage.list_blocked_nodes() == []
        # comes back like any node we didn't know
        await gossip(node, KNOWN, [{"node_id": BAD, "address": "6.6.6.6:8765"}])
        assert await node.storage.get_node(BAD) is not None


class TestGossip:
    async def test_blocked_node_not_reintroduced(self, tmp_path):
        node = await make_node(tmp_path)
        await add(node, KNOWN, "10.0.0.1:8765")
        await node.block_node(BAD)
        await gossip(node, KNOWN, [{"node_id": BAD, "address": "6.6.6.6:8765"}])
        assert await node.storage.get_node(BAD) is None


class TestTransport:
    async def test_blocked_node_refused_both_ways(self, tmp_path):
        a = await make_node(tmp_path, "a", BASE + 1)
        b = await make_node(tmp_path, "b", BASE + 2)
        await a.start()
        await b.start()
        try:
            await a.block_node(b.identity.node_id)
            # b dials a: auth completes, then a closes it and never registers it
            conn = await b.transport.connect(a.identity.address)
            await asyncio.sleep(0.2)
            assert await a.transport.connections.get(b.identity.node_id) is None
            assert conn.ws.close_code is not None
            # a never dials b
            try:
                await a.transport.connect_to_node(b.identity.node_id, b.identity.address)
                assert False, "connected to a blocked node"
            except ValueError:
                pass
            assert await a.transport.connections.get(b.identity.node_id) is None
        finally:
            await a.stop()
            await b.stop()

    async def test_live_connection_closed_on_block(self, tmp_path):
        a = await make_node(tmp_path, "a", BASE + 3)
        b = await make_node(tmp_path, "b", BASE + 4)
        await a.start()
        await b.start()
        try:
            await b.transport.connect(a.identity.address)
            await asyncio.sleep(0.2)
            assert await a.transport.connections.get(b.identity.node_id) is not None
            await a.block_node(b.identity.node_id)
            await asyncio.sleep(0.2)
            assert await a.transport.connections.get(b.identity.node_id) is None
        finally:
            await a.stop()
            await b.stop()


class TestRouting:
    async def _node_with_recorders(self, tmp_path):
        node = await make_node(tmp_path)
        sent = {"local": [], "node": [], "failed": []}

        async def deliver_local(pkt, seq=0):
            sent["local"].append(pkt.id)
            return True

        async def send_to_node(node_id, pkt, seq=0):
            sent["node"].append(node_id)
            return True

        async def undeliverable(pkt):
            sent["failed"].append(pkt.id)

        node.router._deliver_local = deliver_local
        node.router._send_to_node = send_to_node
        node.router._notify_undeliverable = undeliverable
        await node.storage.register_cell("11" * 32, b"s" * 32, b"e" * 32, True, "Alice")
        await node.block_node(BAD)
        return node, sent

    async def test_nothing_from_blocked_nodes_cells(self, tmp_path):
        node, sent = await self._node_with_recorders(tmp_path)
        await node.router.route(msg(f"{'22' * 32}@{BAD}", f"{'11' * 32}@{node.identity.node_id}"))
        assert sent == {"local": [], "node": [], "failed": []}

    async def test_nothing_to_blocked_nodes_cells(self, tmp_path):
        node, sent = await self._node_with_recorders(tmp_path)
        me = node.identity.node_id
        p = msg(f"{'11' * 32}@{me}", f"{'22' * 32}@{BAD}")
        await node.router.route(p)
        assert sent == {"local": [], "node": [], "failed": [p.id]}
        # nor through a presence that still points there (learned before the block)
        await node.storage.update_presence("33" * 32, BAD)
        q = msg(f"{'11' * 32}@{me}", f"{'33' * 32}@{KNOWN}")
        await node.router.route(q)
        assert sent["node"] == [] and sent["failed"] == [p.id, q.id]

    async def test_other_nodes_unaffected(self, tmp_path):
        node, sent = await self._node_with_recorders(tmp_path)
        me = node.identity.node_id
        await node.storage.update_presence("44" * 32, KNOWN)
        await node.router.route(msg(f"{'11' * 32}@{me}", f"{'44' * 32}@{KNOWN}"))
        await node.router.route(msg(f"{'44' * 32}@{KNOWN}", f"{'11' * 32}@{me}"))
        assert sent["node"] == [KNOWN] and len(sent["local"]) == 1 and sent["failed"] == []


class TestAdminPanel:
    async def test_block_list_unblock(self, genesis_node):
        import base64
        from aiohttp.test_utils import TestClient, TestServer
        from node.admin import AdminServer
        auth = {"Authorization": "Basic " + base64.b64encode(b":pw").decode()}
        client = TestClient(TestServer(AdminServer(genesis_node, password="pw")._make_app()))
        await client.start_server()
        try:
            r = await client.post("/nevod-admin/api/blocked-nodes", headers=auth,
                                  json={"node_id": BAD, "reason": "spam"})
            assert r.status == 200 and (await r.json())["ok"]
            r = await client.post("/nevod-admin/api/blocked-nodes", headers=auth,
                                  json={"node_id": genesis_node.identity.node_id})
            assert r.status == 400
            r = await client.get("/nevod-admin/api/blocked-nodes", headers=auth)
            assert [(n["node_id"], n["reason"]) for n in (await r.json())["nodes"]] == [(BAD, "spam")]
            r = await client.delete(f"/nevod-admin/api/blocked-nodes/{BAD}", headers=auth)
            assert (await r.json())["ok"] and not genesis_node.is_node_blocked(BAD)
        finally:
            await client.close()
