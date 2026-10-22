"""
Tests for group messaging (group = child/temporary node).

Architecture (from DISCUSS_GROUPS.md):
  - A group IS a child node (type="temporary", parent_node_id set).
  - Messages are individual E2E-encrypted MSGs, one per member.
  - Member list is discovered via GROUP_MEMBERS_REQUEST/RESPONSE.
  - Group destruction wipes all data and disconnects all members.

Block 1: Group node creation and member connection
Block 2: Group member list (GROUP_MEMBERS_REQUEST/RESPONSE)
Block 3: Group message delivery
Block 4: Group destruction
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import tempfile
import pytest

from node.node import Node
from node.client import CellClient
from node.identity import NodeIdentity, CellIdentity
from node.storage import NodeEntry
import time

BASE_PORT = 19500


# ─── Helpers ──────────────────────────────────────────────────────────────────


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE_PORT + offset}"


async def start_group_node(port_offset: int, parent_node_id: str = "") -> Node:
    """Start a group node (temporary/closed child node)."""
    td = tempfile.mkdtemp()
    node = await Node.create_genesis(
        address=addr(port_offset),
        identity_path=os.path.join(td, "id.json"),
        db_path=os.path.join(td, "db.sqlite"),
        access="closed",
        node_type="temporary",
        parent_node_id=parent_node_id,
    )
    await node.start()
    return node


async def start_home_node(port_offset: int) -> Node:
    """Start a permanent home node."""
    td = tempfile.mkdtemp()
    node = await Node.create_genesis(
        address=addr(port_offset),
        identity_path=os.path.join(td, "id.json"),
        db_path=os.path.join(td, "db.sqlite"),
        access="open",
        node_type="permanent",
    )
    await node.start()
    return node


async def connect_cell(cell: CellIdentity, node: Node,
                        on_message=None) -> CellClient:
    client = CellClient(cell, on_message=on_message)
    await client.connect(node.identity.address,
                         expected_fingerprint=node.identity.tls_fingerprint)
    return client


# ─── Block 1: Group creation and member connection ────────────────────────────


class TestGroupCreation:
    @pytest.mark.asyncio
    async def test_group_is_child_node(self):
        """Group node is a temporary child node with parent_node_id."""
        home = await start_home_node(0)
        group = await start_group_node(1, parent_node_id=home.identity.node_id)
        try:
            assert group.identity.node_type == "temporary"
            assert group.identity.parent_node_id == home.identity.node_id
            assert group.identity.access == "closed"
        finally:
            await group.stop()
            await home.stop()

    @pytest.mark.asyncio
    async def test_members_connect_to_group_node(self):
        """Three cells can connect to the group node simultaneously."""
        group = await start_group_node(2)
        cells = [CellIdentity.generate() for _ in range(3)]
        clients = []
        try:
            for c in cells:
                cl = await connect_cell(c, group)
                clients.append(cl)
            assert len(clients) == 3
            assert all(cl.connected for cl in clients)
        finally:
            for cl in clients:
                await cl.disconnect()
            await group.stop()

    @pytest.mark.asyncio
    async def test_group_node_cells_registered_as_home(self):
        """Cells connecting to the group node are registered with is_home=True."""
        group = await start_group_node(3)
        cells = [CellIdentity.generate() for _ in range(2)]
        clients = []
        try:
            for c in cells:
                clients.append(await connect_cell(c, group))
            await asyncio.sleep(0.05)

            registered = await group.storage.list_cells(home_only=True)
            registered_ids = {c.cell_id for c in registered}
            assert cells[0].cell_id in registered_ids
            assert cells[1].cell_id in registered_ids
        finally:
            for cl in clients:
                await cl.disconnect()
            await group.stop()

    @pytest.mark.asyncio
    async def test_group_node_not_gossiped(self):
        """Closed group node does not gossip its presence — can't be discovered."""
        home = await start_home_node(4)
        group = await start_group_node(5, parent_node_id=home.identity.node_id)
        try:
            # A third node joins home — should NOT learn group node via gossip
            observer = await start_home_node(6)
            try:
                await observer.join(home.identity.address,
                                    expected_fingerprint=home.identity.tls_fingerprint)
                await asyncio.sleep(0.15)

                # group node is closed → not gossiped → observer doesn't know it
                group_entry = await observer.storage.get_node(group.identity.node_id)
                assert group_entry is None
            finally:
                await observer.stop()
        finally:
            await group.stop()
            await home.stop()


# ─── Block 2: Group member list ───────────────────────────────────────────────


class TestGroupMemberList:
    @pytest.mark.asyncio
    async def test_get_group_members_returns_all_members(self):
        """GROUP_MEMBERS_REQUEST returns all registered cells with enc_pubkeys."""
        group = await start_group_node(10)
        cells = [CellIdentity.generate() for _ in range(3)]
        clients = []
        try:
            for c in cells:
                clients.append(await connect_cell(c, group))
            await asyncio.sleep(0.05)

            members = await clients[0].get_group_members()
            member_ids = {m["cell_id"] for m in members}
            for c in cells:
                assert c.cell_id in member_ids

        finally:
            for cl in clients:
                await cl.disconnect()
            await group.stop()

    @pytest.mark.asyncio
    async def test_get_group_members_includes_enc_pubkeys(self):
        """Each member entry includes enc_pubkey as bytes."""
        group = await start_group_node(11)
        cell_a = CellIdentity.generate()
        cell_b = CellIdentity.generate()
        cl_a, cl_b = None, None
        try:
            cl_a = await connect_cell(cell_a, group)
            cl_b = await connect_cell(cell_b, group)
            await asyncio.sleep(0.05)

            members = await cl_a.get_group_members()
            by_id = {m["cell_id"]: m for m in members}

            assert cell_b.cell_id in by_id
            assert bytes(by_id[cell_b.cell_id]["enc_pubkey"]) == cell_b.encryption.public
        finally:
            if cl_a: await cl_a.disconnect()
            if cl_b: await cl_b.disconnect()
            await group.stop()

    @pytest.mark.asyncio
    async def test_member_list_grows_after_new_join(self):
        """Member list grows after a new cell joins the group."""
        group = await start_group_node(12)
        cell_a = CellIdentity.generate()
        cell_b = CellIdentity.generate()
        cl_a, cl_b = None, None
        try:
            cl_a = await connect_cell(cell_a, group)
            await asyncio.sleep(0.05)

            members_before = await cl_a.get_group_members()
            ids_before = {m["cell_id"] for m in members_before}
            assert cell_b.cell_id not in ids_before

            cl_b = await connect_cell(cell_b, group)
            await asyncio.sleep(0.05)

            members_after = await cl_a.get_group_members()
            ids_after = {m["cell_id"] for m in members_after}
            assert cell_b.cell_id in ids_after
        finally:
            if cl_a: await cl_a.disconnect()
            if cl_b: await cl_b.disconnect()
            await group.stop()


# ─── Block 3: Group message delivery ─────────────────────────────────────────


class TestGroupMessageDelivery:
    @pytest.mark.asyncio
    async def test_message_reaches_all_online_members(self):
        """Alice sends to group → Bob and Carol both receive it."""
        group = await start_group_node(20)
        alice_id = CellIdentity.generate()
        bob_id   = CellIdentity.generate()
        carol_id = CellIdentity.generate()

        bob_received:   asyncio.Queue = asyncio.Queue()
        carol_received: asyncio.Queue = asyncio.Queue()

        try:
            cl_alice = await connect_cell(alice_id, group)
            cl_bob   = await connect_cell(bob_id,   group,
                            on_message=lambda f, m: bob_received.put_nowait(m))
            cl_carol = await connect_cell(carol_id, group,
                            on_message=lambda f, m: carol_received.put_nowait(m))
            await asyncio.sleep(0.05)

            members = await cl_alice.get_group_members()
            await cl_alice.send_to_group(members, b"hello group")

            bob_msg   = await asyncio.wait_for(bob_received.get(), timeout=3.0)
            carol_msg = await asyncio.wait_for(carol_received.get(), timeout=3.0)

            assert bob_msg   == b"hello group"
            assert carol_msg == b"hello group"
        finally:
            for cl in [cl_alice, cl_bob, cl_carol]:
                try: await cl.disconnect()
                except Exception: pass
            await group.stop()

    @pytest.mark.asyncio
    async def test_send_to_group_skips_self(self):
        """send_to_group does not send a message to the sender itself."""
        group = await start_group_node(21)
        alice_id = CellIdentity.generate()
        cl_alice = None
        try:
            self_received: asyncio.Queue = asyncio.Queue()
            cl_alice = await connect_cell(
                alice_id, group,
                on_message=lambda f, m: self_received.put_nowait(m),
            )
            await asyncio.sleep(0.05)

            members = await cl_alice.get_group_members()
            # Every node also lists its built-in administrator cell — not part of this test.
            admin = group.administrator_info()
            members = [m for m in members if not admin or m["cell_id"] != admin["cell_id"]]
            ids = await cl_alice.send_to_group(members, b"test")

            # No message sent to self → queue stays empty
            await asyncio.sleep(0.1)
            assert self_received.empty()
            assert not any(i for i in ids)  # empty list (only self in group)
        finally:
            if cl_alice: await cl_alice.disconnect()
            await group.stop()

    @pytest.mark.asyncio
    async def test_message_buffered_for_offline_member(self):
        """Message to offline group member is buffered; delivered on reconnect."""
        group = await start_group_node(22)
        alice_id = CellIdentity.generate()
        dave_id  = CellIdentity.generate()

        dave_received: asyncio.Queue = asyncio.Queue()

        cl_alice = await connect_cell(alice_id, group)
        cl_dave  = await connect_cell(dave_id,  group)
        await asyncio.sleep(0.05)

        try:
            # Dave goes offline
            await cl_dave.disconnect()
            await asyncio.sleep(0.05)

            # Alice sends to group (Dave is offline)
            members = await cl_alice.get_group_members()
            await cl_alice.send_to_group(members, b"buffered for dave")

            # Dave reconnects
            cl_dave2 = await connect_cell(
                dave_id, group,
                on_message=lambda f, m: dave_received.put_nowait(m),
            )
            try:
                msg = await asyncio.wait_for(dave_received.get(), timeout=3.0)
                assert msg == b"buffered for dave"
            finally:
                await cl_dave2.disconnect()
        finally:
            try: await cl_alice.disconnect()
            except Exception: pass
            await group.stop()


# ─── Block 4: Group destruction ───────────────────────────────────────────────


class TestGroupDestruction:
    @pytest.mark.asyncio
    async def test_destroy_wipes_all_storage(self):
        """After destroy(), all tables are empty."""
        from node.storage import Storage
        group = await start_group_node(30)
        db_path = group.storage.db_path  # save before destroy closes the DB
        cell = CellIdentity.generate()
        cl = await connect_cell(cell, group)
        await asyncio.sleep(0.05)

        # Verify data exists
        assert await group.storage.list_cells(home_only=True)

        await group.destroy()  # wipes tables then closes DB

        # Re-open DB to verify wipe (storage is closed after destroy)
        s2 = Storage(db_path)
        await s2.open()
        try:
            cells = await s2.list_cells()
            nodes = await s2.get_all_nodes()
            assert cells == []
            assert nodes == []
        finally:
            await s2.close()

    @pytest.mark.asyncio
    async def test_destroy_disconnects_all_members(self):
        """After destroy(), all connected cell clients are disconnected."""
        group = await start_group_node(31)
        cells = [CellIdentity.generate() for _ in range(3)]
        clients = []
        try:
            for c in cells:
                clients.append(await connect_cell(c, group))
            await asyncio.sleep(0.05)
            assert all(cl.connected for cl in clients)

            await group.destroy()
            await asyncio.sleep(0.15)

            assert all(not cl.connected for cl in clients)
        finally:
            for cl in clients:
                try: await cl.disconnect()
                except Exception: pass

    @pytest.mark.asyncio
    async def test_destroy_removes_identity_file(self):
        """destroy(identity_path=...) deletes the identity file."""
        td = tempfile.mkdtemp()
        identity_path = os.path.join(td, "id.json")
        db_path = os.path.join(td, "db.sqlite")

        node = await Node.create_genesis(
            address=addr(32),
            identity_path=identity_path,
            db_path=db_path,
            access="closed",
            node_type="temporary",
        )
        await node.start()
        assert os.path.exists(identity_path)

        await node.destroy(identity_path=identity_path)

        assert not os.path.exists(identity_path)
