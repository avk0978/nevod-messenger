"""
Presence Gossip tests.

Блок 1: Открытый узел — presence в gossip
Блок 2: Закрытый узел — presence НЕ в gossip
Блок 3: Дочерний узел — P2P + CHILD_PRESENCE_UPDATE к родителю
Блок 4: Переход между узлами
"""

import asyncio
import time

import pytest

from node.client import CellClient
from node.identity import CellIdentity, NodeIdentity
from node.node import Node
from node.storage import NodeEntry

BASE_PORT = 19700


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE_PORT + offset}"


async def bidirectional_gossip(n_from, n_to):
    """
    Trigger gossip exchange in both directions so each node knows the other
    in its own node_table (required for _exchange() to find a storage entry).
    n_from→n_to first (n_to learns n_from), then n_to→n_from (n_from learns presence).
    """
    # n_from sends to n_to: n_to learns about n_from in its node_table
    entry_in_nto = await n_from.storage.get_node(n_to.identity.node_id)
    if not entry_in_nto:
        # n_to connected to n_from first, so n_from's table doesn't have n_to yet
        # Send gossip from n_to→n_from so n_from learns about n_to
        entry_nfrom_in_nto = await n_to.storage.get_node(n_from.identity.node_id)
        if entry_nfrom_in_nto:
            await n_to.gossip._exchange(entry_nfrom_in_nto)
            await asyncio.sleep(0.05)

    # n_from now has n_to in its table — send presence gossip n_from→n_to
    entry_nto = await n_from.storage.get_node(n_to.identity.node_id)
    if entry_nto:
        await n_from.gossip._exchange(entry_nto)
        await asyncio.sleep(0.1)


async def make_node(tmp_path, offset: int,
                    access: str = "open",
                    node_type: str = "permanent",
                    parent_node_id: str = "") -> Node:
    return await Node.create_genesis(
        addr(offset),
        str(tmp_path / f"n{offset}.json"),
        str(tmp_path / f"n{offset}.db"),
        access=access,
        node_type=node_type,
        parent_node_id=parent_node_id,
    )


# ─── Блок 1: Открытый узел — gossip presence ─────────────────────────────────

class TestOpenNodeGossip:
    async def test_open_node_presence_in_gossip(self, tmp_path):
        """
        cell регистрируется на open-узле n1 →
        n1 делает gossip exchange с n2 →
        n2.storage содержит presence(cell_id, home=n1)
        """
        n1 = await make_node(tmp_path, 0, access="open")
        n2 = await make_node(tmp_path, 1, access="open")
        await n1.start()
        await n2.start()

        idt = CellIdentity.generate("Alice")
        cell = CellClient(idt)
        try:
            await n2.join(addr(0), expected_fingerprint=n1.identity.tls_fingerprint)
            await asyncio.sleep(0.05)

            await cell.connect(addr(0))
            await asyncio.sleep(0.05)  # cell registers on n1

            # Trigger gossip: n1 sends its presence to n2
            await bidirectional_gossip(n1, n2)

            presence = await n2.storage.get_presence(idt.cell_id)
            assert presence is not None
            assert presence.home_node_id == n1.identity.node_id
        finally:
            await cell.disconnect()
            await n1.stop()
            await n2.stop()

    async def test_open_node_cell_reachable_via_gossip_presence(self, tmp_path):
        """
        n3 не знал о cell заранее →
        получил gossip presence от n1 →
        внешняя cell может отправить MSG через n3 → n1 → cell
        """
        n1 = await make_node(tmp_path, 2, access="open")
        n2 = await make_node(tmp_path, 3, access="open")
        await n1.start()
        await n2.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        received = []

        async def on_b(from_addr, plaintext):
            received.append(plaintext)

        cell_a = CellClient(idt_a)
        cell_b = CellClient(idt_b, on_message=on_b)
        try:
            await n2.join(addr(2), expected_fingerprint=n1.identity.tls_fingerprint)
            await asyncio.sleep(0.05)

            # cell_b on n1, cell_a on n2
            await cell_b.connect(addr(2))
            await cell_a.connect(addr(3))
            await asyncio.sleep(0.05)

            # Propagate n1's presence (with cell_b) to n2 via gossip
            await bidirectional_gossip(n1, n2)

            # n2 should now know cell_b is on n1 — cell_a can send from n2
            await cell_a.send(
                idt_b.cell_id, n1.identity.node_id,
                idt_b.encryption.public, b"via gossip",
            )
            await asyncio.sleep(0.3)

            assert received == [b"via gossip"]
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await n1.stop()
            await n2.stop()

    async def test_open_node_gossip_includes_presence_field(self, tmp_path):
        """Gossip payload from open node contains 'presence' key after cell registers."""
        n1 = await make_node(tmp_path, 4, access="open")
        n2 = await make_node(tmp_path, 5, access="open")
        await n1.start()
        await n2.start()

        idt = CellIdentity.generate("Alice")
        cell = CellClient(idt)
        captured = []

        original_handle = n2.gossip.handle_gossip

        async def intercept(pkt):
            from node.protocol import decode_payload
            try:
                data = decode_payload(pkt.payload)
                captured.append(data)
            except Exception:
                pass
            await original_handle(pkt)

        n2.gossip.handle_gossip = intercept

        try:
            await n2.join(addr(4), expected_fingerprint=n1.identity.tls_fingerprint)
            await cell.connect(addr(4))
            await asyncio.sleep(0.05)

            await bidirectional_gossip(n1, n2)

            assert any("presence" in d for d in captured)
        finally:
            n2.gossip.handle_gossip = original_handle
            await cell.disconnect()
            await n1.stop()
            await n2.stop()


# ─── Блок 2: Закрытый узел — presence НЕ в gossip ────────────────────────────

class TestClosedNodeGossip:
    async def test_closed_node_presence_not_in_gossip(self, tmp_path):
        """
        cell регистрируется на closed-узле n1 →
        n1 делает gossip exchange с n2 →
        n2.storage НЕ содержит presence этой cell
        """
        n1 = await make_node(tmp_path, 10, access="closed")
        n2 = await make_node(tmp_path, 11, access="open")
        await n1.start()
        await n2.start()

        idt = CellIdentity.generate("Bob")
        cell = CellClient(idt)
        try:
            await n2.join(addr(10), expected_fingerprint=n1.identity.tls_fingerprint)
            await asyncio.sleep(0.05)

            await cell.connect(addr(10))
            await asyncio.sleep(0.05)

            # Trigger gossip from closed n1 to n2
            await bidirectional_gossip(n1, n2)

            # n2 must NOT know about this cell's presence
            presence = await n2.storage.get_presence(idt.cell_id)
            assert presence is None
        finally:
            await cell.disconnect()
            await n1.stop()
            await n2.stop()

    async def test_closed_node_cell_reachable_by_explicit_address(self, tmp_path):
        """
        Отправитель знает cell_id@closed_node_id явно →
        MSG доставляется без gossip lookup
        """
        closed = await make_node(tmp_path, 12, access="closed")
        open_n = await make_node(tmp_path, 13, access="open")
        await closed.start()
        await open_n.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        received = []

        async def on_b(from_addr, plaintext):
            received.append(plaintext)

        cell_a = CellClient(idt_a)
        cell_b = CellClient(idt_b, on_message=on_b)
        try:
            # n2 joins closed node so routing can connect
            await open_n.join(addr(12),
                              expected_fingerprint=closed.identity.tls_fingerprint)
            await asyncio.sleep(0.05)

            await cell_b.connect(addr(12))  # Bob on closed node
            await cell_a.connect(addr(13))  # Alice on open node
            await asyncio.sleep(0.05)

            # Alice knows Bob's exact address — no gossip needed
            await cell_a.send(
                idt_b.cell_id, closed.identity.node_id,
                idt_b.encryption.public, b"direct to closed",
            )
            await asyncio.sleep(0.3)

            assert received == [b"direct to closed"]
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await closed.stop()
            await open_n.stop()

    async def test_closed_node_gossip_payload_has_no_presence(self, tmp_path):
        """Gossip payload from closed node must NOT contain 'presence'."""
        n1 = await make_node(tmp_path, 14, access="closed")
        n2 = await make_node(tmp_path, 15, access="open")
        await n1.start()
        await n2.start()

        idt = CellIdentity.generate("Carol")
        cell = CellClient(idt)
        captured = []

        original_handle = n2.gossip.handle_gossip

        async def intercept(pkt):
            from node.protocol import decode_payload
            try:
                captured.append(decode_payload(pkt.payload))
            except Exception:
                pass
            await original_handle(pkt)

        n2.gossip.handle_gossip = intercept

        try:
            await n2.join(addr(14), expected_fingerprint=n1.identity.tls_fingerprint)
            await cell.connect(addr(14))
            await asyncio.sleep(0.05)

            await bidirectional_gossip(n1, n2)

            # Closed node gossip must not leak presence
            assert not any("presence" in d for d in captured)
        finally:
            n2.gossip.handle_gossip = original_handle
            await cell.disconnect()
            await n1.stop()
            await n2.stop()


# ─── Блок 3: Дочерний узел ────────────────────────────────────────────────────

class TestChildNode:
    async def test_child_node_p2p_delivery(self, tmp_path):
        """Alice и Bob оба на child_node — MSG доставляется внутри child_node."""
        parent = await make_node(tmp_path, 20, access="closed")
        child  = await make_node(tmp_path, 21, access="closed",
                                 node_type="temporary",
                                 parent_node_id=parent.identity.node_id)
        await parent.start()
        await child.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        received = []

        async def on_b(from_addr, plaintext):
            received.append(plaintext)

        cell_a = CellClient(idt_a)
        cell_b = CellClient(idt_b, on_message=on_b)
        try:
            await cell_a.connect(addr(21))
            await cell_b.connect(addr(21))
            await asyncio.sleep(0.05)

            await cell_a.send(
                idt_b.cell_id, child.identity.node_id,
                idt_b.encryption.public, b"hello from child",
            )
            await asyncio.sleep(0.2)

            assert received == [b"hello from child"]
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await child.stop()
            await parent.stop()

    async def test_child_node_notifies_parent(self, tmp_path):
        """
        Bob подключается к child_node →
        child_node отправляет CHILD_PRESENCE_UPDATE родителю →
        родитель знает: Bob сейчас на child_node (visiting_node_id)
        """
        parent = await make_node(tmp_path, 22, access="closed")
        child  = await make_node(tmp_path, 23, access="closed",
                                 node_type="temporary",
                                 parent_node_id=parent.identity.node_id)
        await parent.start()
        await child.start()

        # Child joins parent so it has parent in its node_table
        await child.join(addr(22),
                         expected_fingerprint=parent.identity.tls_fingerprint)
        await asyncio.sleep(0.05)

        idt_b = CellIdentity.generate("Bob")
        cell_b = CellClient(idt_b)
        try:
            # Bob is normally registered on parent
            await parent.register_cell_locally(
                idt_b.cell_id,
                idt_b.signing.public,
                idt_b.encryption.public,
            )

            # Bob connects to child_node
            await cell_b.connect(addr(23))
            await asyncio.sleep(0.2)  # time for CHILD_PRESENCE_UPDATE to arrive

            # Parent should now know Bob is visiting child
            presence = await parent.storage.get_presence(idt_b.cell_id)
            assert presence is not None
            assert presence.visiting_node_id == child.identity.node_id
        finally:
            await cell_b.disconnect()
            await child.stop()
            await parent.stop()

    async def test_external_message_forwarded_via_parent(self, tmp_path):
        """
        Внешняя cell пишет на bob@Node_Bob →
        Node_Bob форвардит на child_node →
        Bob получает сообщение
        """
        parent = await make_node(tmp_path, 24, access="closed")
        child  = await make_node(tmp_path, 25, access="closed",
                                 node_type="temporary",
                                 parent_node_id=parent.identity.node_id)
        ext_n  = await make_node(tmp_path, 26, access="open")
        await parent.start()
        await child.start()
        await ext_n.start()

        # Child joins parent
        await child.join(addr(24),
                         expected_fingerprint=parent.identity.tls_fingerprint)
        # External node joins parent
        await ext_n.join(addr(24),
                         expected_fingerprint=parent.identity.tls_fingerprint)
        await asyncio.sleep(0.05)

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        received = []

        async def on_b(from_addr, plaintext):
            received.append(plaintext)

        cell_a = CellClient(idt_a)
        cell_b = CellClient(idt_b, on_message=on_b)
        try:
            # Bob registered on parent (home), Alice on external node
            await parent.register_cell_locally(
                idt_b.cell_id,
                idt_b.signing.public,
                idt_b.encryption.public,
            )
            await cell_a.connect(addr(26))
            await asyncio.sleep(0.05)

            # Bob goes to child_node
            await cell_b.connect(addr(25))
            await asyncio.sleep(0.3)  # wait for CHILD_PRESENCE_UPDATE

            # Alice writes to bob@parent — parent forwards to child_node
            await cell_a.send(
                idt_b.cell_id, parent.identity.node_id,
                idt_b.encryption.public, b"forwarded via parent",
            )
            await asyncio.sleep(0.4)

            assert received == [b"forwarded via parent"]
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await ext_n.stop()
            await child.stop()
            await parent.stop()

    async def test_child_node_always_closed_no_gossip(self, tmp_path):
        """Child node never includes presence in gossip even if nodes know about it."""
        parent = await make_node(tmp_path, 27, access="closed")
        child  = await make_node(tmp_path, 28, access="closed",
                                 node_type="temporary",
                                 parent_node_id=parent.identity.node_id)
        other  = await make_node(tmp_path, 29, access="open")
        await parent.start()
        await child.start()
        await other.start()

        idt = CellIdentity.generate("Alice")
        cell = CellClient(idt)
        captured = []

        original_handle = other.gossip.handle_gossip

        async def intercept(pkt):
            from node.protocol import decode_payload
            try:
                captured.append(decode_payload(pkt.payload))
            except Exception:
                pass
            await original_handle(pkt)

        other.gossip.handle_gossip = intercept

        try:
            await other.join(addr(28),
                             expected_fingerprint=child.identity.tls_fingerprint)
            await cell.connect(addr(28))
            await asyncio.sleep(0.05)

            await bidirectional_gossip(child, other)

            # Child (temporary/closed) must NOT leak presence to other nodes
            assert not any("presence" in d for d in captured)
        finally:
            other.gossip.handle_gossip = original_handle
            await cell.disconnect()
            await child.stop()
            await parent.stop()
            await other.stop()


# ─── Блок 4: Переход между узлами ────────────────────────────────────────────

class TestNodeTransition:
    async def test_cell_moves_to_child_node_parent_updates(self, tmp_path):
        """
        Bob был на parent (closed) → переключился на child_node →
        parent обновил visiting_node_id
        """
        parent = await make_node(tmp_path, 30, access="closed")
        child  = await make_node(tmp_path, 31, access="closed",
                                 node_type="temporary",
                                 parent_node_id=parent.identity.node_id)
        await parent.start()
        await child.start()

        await child.join(addr(30),
                         expected_fingerprint=parent.identity.tls_fingerprint)
        await asyncio.sleep(0.05)

        idt_b = CellIdentity.generate("Bob")
        cell_on_parent = CellClient(idt_b)
        cell_on_child  = CellClient(idt_b)
        try:
            # Bob registers on parent
            await cell_on_parent.connect(addr(30))
            await asyncio.sleep(0.1)

            presence_before = await parent.storage.get_presence(idt_b.cell_id)
            assert presence_before is not None
            assert presence_before.visiting_node_id is None

            # Bob disconnects from parent, connects to child
            await cell_on_parent.disconnect()
            await asyncio.sleep(0.05)

            await cell_on_child.connect(addr(31))
            await asyncio.sleep(0.3)  # wait for CHILD_PRESENCE_UPDATE

            presence_after = await parent.storage.get_presence(idt_b.cell_id)
            assert presence_after is not None
            assert presence_after.visiting_node_id == child.identity.node_id
        finally:
            await cell_on_child.disconnect()
            await child.stop()
            await parent.stop()

    async def test_messages_buffered_during_transition_delivered_after(self, tmp_path):
        """
        В момент перехода Bob офлайн → MSG буферизуется →
        Bob подключается к child_node → flush буфера → доставка
        """
        parent = await make_node(tmp_path, 32, access="closed")
        child  = await make_node(tmp_path, 33, access="closed",
                                 node_type="temporary",
                                 parent_node_id=parent.identity.node_id)
        await parent.start()
        await child.start()

        await child.join(addr(32),
                         expected_fingerprint=parent.identity.tls_fingerprint)
        await asyncio.sleep(0.05)

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        received = []

        async def on_b(from_addr, plaintext):
            received.append(plaintext)

        cell_a = CellClient(idt_a)
        try:
            # Register Bob on parent so Alice can send to bob@parent
            await parent.register_cell_locally(
                idt_b.cell_id,
                idt_b.signing.public,
                idt_b.encryption.public,
            )
            await cell_a.connect(addr(32))  # Alice on parent
            await asyncio.sleep(0.05)

            # Bob is offline — message gets buffered
            await cell_a.send(
                idt_b.cell_id, parent.identity.node_id,
                idt_b.encryption.public, b"buffered during transition",
            )
            await asyncio.sleep(0.1)

            # Bob comes online on child_node
            cell_b = CellClient(idt_b, on_message=on_b)
            await cell_b.connect(addr(33))
            await asyncio.sleep(0.4)  # flush buffer + CHILD_PRESENCE_UPDATE

            # The buffered message should be delivered after registration
            assert received == [b"buffered during transition"]
            await cell_b.disconnect()
        finally:
            await cell_a.disconnect()
            await child.stop()
            await parent.stop()
