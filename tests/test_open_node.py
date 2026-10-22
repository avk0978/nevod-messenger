"""
A public open node (Nevod Open): strangers register freely, so they must not see a directory
of each other (members_visibility="service"), a node joining without an invite may not take
the project's names, and one address can't script a flood of registrations.
"""

import asyncio

from node.client import CellClient
from node.identity import NodeIdentity, CellIdentity
from node.limits import RateLimiter
from node.names import is_reserved_node_name
from node.node import Node
from node.transport import _client_ip

BASE = 20300


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE + offset}"


async def make_node(tmp_path, offset: int, **identity_kwargs) -> Node:
    id_path = str(tmp_path / f"n{offset}.json")
    idt = NodeIdentity.generate(addr(offset), **identity_kwargs)
    idt.save(id_path)
    return await Node.create(id_path, str(tmp_path / f"n{offset}.db"))


async def connect(node: Node, name: str) -> CellClient:
    client = CellClient(CellIdentity.generate(name))
    await client.connect(node.identity.address)
    await asyncio.sleep(0.1)
    return client


class TestMembersVisibility:
    async def test_service_mode_lists_only_service_cells_and_self(self, tmp_path):
        node = await make_node(tmp_path, 0)
        node.identity.members_visibility = "service"
        await node.start()
        alice = bob = None
        try:
            alice = await connect(node, "Alice")
            bob = await connect(node, "Bob")
            await node.storage.publish_cell(bob.cell_id, "Bob the bot")   # published = service
            carol = await connect(node, "Carol")
            ids = {m["cell_id"] for m in await carol.get_group_members()}
            assert node.administrator_info()["cell_id"] in ids
            assert bob.cell_id in ids
            assert carol.cell_id in ids          # itself
            assert alice.cell_id not in ids      # an ordinary stranger
            await carol.disconnect()
        finally:
            for c in (alice, bob):
                if c:
                    await c.disconnect()
            await node.stop()

    async def test_default_lists_everyone(self, tmp_path):
        node = await make_node(tmp_path, 1)
        await node.start()
        try:
            alice = await connect(node, "Alice")
            bob = await connect(node, "Bob")
            ids = {m["cell_id"] for m in await bob.get_group_members()}
            assert alice.cell_id in ids
            await alice.disconnect()
            await bob.disconnect()
        finally:
            await node.stop()

    def test_setting_persisted(self, tmp_path):
        idt = NodeIdentity.generate(addr(2))
        idt.members_visibility = "service"
        idt.save(str(tmp_path / "n.json"))
        assert NodeIdentity.load(str(tmp_path / "n.json")).members_visibility == "service"


class TestReservedNodeNames:
    def test_reserved(self):
        for name in ("Nevod", "Nevod Open", "nevod-official", "Dev Planet", "DEVPLANET",
                     "Kitaevo", "avk", "Офіційний вузол", "N3vod", "Admin's node"):
            assert is_reserved_node_name(name), name

    def test_ordinary(self):
        for name in ("", "Моя семья", "Family", "Ape Planet", "Havkat", "Kyiv node"):
            assert not is_reserved_node_name(name), name


class TestRateLimiter:
    def test_limit_per_key(self):
        rl = RateLimiter(2, 3600)
        assert rl.allow("1.2.3.4") and rl.allow("1.2.3.4")
        assert not rl.allow("1.2.3.4")
        assert rl.allow("5.6.7.8")

    def test_disabled(self):
        rl = RateLimiter(0, 3600)
        assert all(rl.allow("1.2.3.4") for _ in range(100))

    async def test_new_cell_limited_reconnect_not(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NEVOD_NEW_CELLS_PER_IP_PER_HOUR", "1")
        node = await make_node(tmp_path, 3)
        await node.start()
        try:
            idt = CellIdentity.generate("Alice")
            first = CellClient(idt)
            await first.connect(node.identity.address)
            await asyncio.sleep(0.1)
            await first.disconnect()
            assert await node.storage.get_cell(idt.cell_id) is not None

            again = CellClient(idt)                       # reconnect: not counted
            await again.connect(node.identity.address)
            await asyncio.sleep(0.1)
            await again.disconnect()

            other = CellIdentity.generate("Bob")          # a second new cell, same IP
            c = CellClient(other)
            try:
                await c.connect(node.identity.address)
            except Exception:
                pass
            await asyncio.sleep(0.1)
            assert await node.storage.get_cell(other.cell_id) is None
            await c.disconnect()
        finally:
            await node.stop()


class TestClientIp:
    class _Ws:
        def __init__(self, remote, headers):
            self.remote_address = (remote, 1234)
            self.request = type("R", (), {"headers": headers})()

    def test_proxy_header_trusted_from_private(self):
        assert _client_ip(self._Ws("172.18.0.5", {"X-Real-IP": "203.0.113.7"})) == "203.0.113.7"

    def test_header_ignored_from_public(self):
        # A real public address — the RFC 5737 documentation ranges count as "private" in ipaddress.
        assert _client_ip(self._Ws("8.8.8.8", {"X-Real-IP": "203.0.113.7"})) == "8.8.8.8"

    def test_no_header(self):
        assert _client_ip(self._Ws("127.0.0.1", {})) == "127.0.0.1"
