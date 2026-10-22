"""
ACK tests.

Блок 1: Протокол (сериализация, статусы)
Блок 2: Delivered ACK (один узел, два узла)
Блок 3: Read ACK
Блок 4: Fire-and-forget + TTL
Блок 5: ACK через буфер
"""

import asyncio
import time

import pytest

from node.client import CellClient, ACK_TTL
from node.identity import CellIdentity
from node.node import Node
from node.protocol import make_ack, T, encode_payload, decode_payload, pack, unpack

BASE_PORT = 19800


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE_PORT + offset}"


async def make_node(tmp_path, offset: int, access: str = "open") -> Node:
    return await Node.create_genesis(
        addr(offset),
        str(tmp_path / f"n{offset}.json"),
        str(tmp_path / f"n{offset}.db"),
        access=access,
    )


# ─── Блок 1: Протокол ─────────────────────────────────────────────────────────

class TestACKProtocol:
    def test_make_ack_packet(self):
        pkt = make_ack("cell_b@node_b", "cell_a@node_a", "msg-001", "delivered")
        assert pkt.type == T.ACK
        assert pkt.from_addr == "cell_b@node_b"
        assert pkt.to_addr   == "cell_a@node_a"
        data = decode_payload(pkt.payload)
        assert data["message_id"] == "msg-001"
        assert data["status"]     == "delivered"

    def test_ack_pack_unpack_roundtrip(self):
        original = make_ack("cell_b@node_b", "cell_a@node_a", "msg-abc", "read")
        restored = unpack(pack(original))
        assert restored.type == T.ACK
        data = decode_payload(restored.payload)
        assert data["message_id"] == "msg-abc"
        assert data["status"]     == "read"

    def test_ack_valid_statuses(self):
        for status in ("delivered", "read"):
            pkt = make_ack("a", "b", "id", status)
            data = decode_payload(pkt.payload)
            assert data["status"] == status

    async def test_unknown_ack_status_ignored(self, tmp_path):
        """ACK with unknown status must not crash the client."""
        node = await make_node(tmp_path, 0)
        await node.start()
        cell = CellClient(CellIdentity.generate("Alice"))
        try:
            await cell.connect(addr(0))
            # Simulate receiving ACK with bad status directly
            from node.protocol import Packet, sign_packet
            bad_pkt = Packet(
                type=T.ACK,
                payload=encode_payload({"message_id": "x", "status": "unknown_bad"}),
                from_addr=f"cell@{node.identity.node_id}",
                to_addr=cell.cell_id,
            )
            sign_packet(bad_pkt, node.identity.signing)
            # Dispatch directly — should not raise
            await cell._handle_ack(bad_pkt)
            assert cell._ack_status.get("x") is None
        finally:
            await cell.disconnect()
            await node.stop()


# ─── Блок 2: Delivered ACK ────────────────────────────────────────────────────

class TestDeliveredACK:
    async def test_cell_sends_delivered_ack_on_receive(self, tmp_path):
        """cell_b receives MSG → cell_a.on_ack is called with 'delivered'."""
        node = await make_node(tmp_path, 10)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        acks_received = []

        async def on_ack(message_id, status):
            acks_received.append((message_id, status))

        cell_a = CellClient(idt_a, on_ack=on_ack)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(10))
            await cell_b.connect(addr(10))
            await asyncio.sleep(0.05)

            msg_id = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"hello",
            )
            await asyncio.sleep(0.2)

            assert any(mid == msg_id and st == "delivered"
                       for mid, st in acks_received)
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()

    async def test_on_ack_callback_signature(self, tmp_path):
        """on_ack(message_id: str, status: str) — types correct."""
        node = await make_node(tmp_path, 11)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        ack_args = []

        async def on_ack(message_id, status):
            ack_args.append((message_id, status))

        cell_a = CellClient(idt_a, on_ack=on_ack)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(11))
            await cell_b.connect(addr(11))
            await asyncio.sleep(0.05)

            msg_id = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"test",
            )
            await asyncio.sleep(0.2)

            assert ack_args
            mid, st = ack_args[0]
            assert isinstance(mid, str)
            assert isinstance(st, str)
            assert mid == msg_id
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()

    async def test_get_status_delivered(self, tmp_path):
        """cell_a.get_status(msg_id) == 'delivered' after ACK received."""
        node = await make_node(tmp_path, 12)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")

        cell_a = CellClient(idt_a)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(12))
            await cell_b.connect(addr(12))
            await asyncio.sleep(0.05)

            msg_id = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"status check",
            )
            assert cell_a.get_status(msg_id) == "in_transit"
            await asyncio.sleep(0.2)
            assert cell_a.get_status(msg_id) == "delivered"
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()

    async def test_delivered_ack_cross_node(self, tmp_path):
        """cell_a on node1, cell_b on node2 — ACK routes back cross-node."""
        n1 = await make_node(tmp_path, 20)
        n2 = await make_node(tmp_path, 21)
        await n1.start()
        await n2.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        acks = []

        async def on_ack(mid, st):
            acks.append((mid, st))

        cell_a = CellClient(idt_a, on_ack=on_ack)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(20))
            await cell_b.connect(addr(21))
            await asyncio.sleep(0.05)

            # n1 must know about n2 (and vice versa) for routing to work
            await n2.join(addr(20), expected_fingerprint=n1.identity.tls_fingerprint)
            await asyncio.sleep(0.1)

            msg_id = await cell_a.send(
                idt_b.cell_id, n2.identity.node_id,
                idt_b.encryption.public, b"cross node",
            )
            await asyncio.sleep(0.4)

            assert any(mid == msg_id and st == "delivered" for mid, st in acks)
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await n1.stop()
            await n2.stop()


# ─── Блок 3: Read ACK ─────────────────────────────────────────────────────────

class TestReadACK:
    async def test_mark_read_sends_read_ack(self, tmp_path):
        """cell_b.mark_read(msg_id) → cell_a.on_ack called with 'read'."""
        node = await make_node(tmp_path, 30)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        acks = []

        async def on_ack(mid, st):
            acks.append((mid, st))

        received_ids = []

        async def on_b_message(from_addr, plaintext):
            # simulate: message received but not yet "read"
            pass

        cell_a = CellClient(idt_a, on_ack=on_ack)
        cell_b = CellClient(idt_b, on_message=on_b_message)
        try:
            await cell_a.connect(addr(30))
            await cell_b.connect(addr(30))
            await asyncio.sleep(0.05)

            msg_id = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"read me",
            )
            await asyncio.sleep(0.2)

            # cell_b marks the message as read
            await cell_b.mark_read(msg_id)
            await asyncio.sleep(0.2)

            statuses = [st for mid, st in acks if mid == msg_id]
            assert "read" in statuses
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()

    async def test_get_status_read(self, tmp_path):
        """cell_a.get_status(msg_id) == 'read' after read ACK received."""
        node = await make_node(tmp_path, 31)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")

        cell_a = CellClient(idt_a)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(31))
            await cell_b.connect(addr(31))
            await asyncio.sleep(0.05)

            msg_id = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"mark me read",
            )
            await asyncio.sleep(0.2)
            assert cell_a.get_status(msg_id) == "delivered"

            await cell_b.mark_read(msg_id)
            await asyncio.sleep(0.2)
            assert cell_a.get_status(msg_id) == "read"
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()

    async def test_delivered_before_read(self, tmp_path):
        """Status sequence: in_transit → delivered → read (never reversed)."""
        node = await make_node(tmp_path, 32)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        ack_sequence = []

        async def on_ack(mid, st):
            ack_sequence.append(st)

        cell_a = CellClient(idt_a, on_ack=on_ack)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(32))
            await cell_b.connect(addr(32))
            await asyncio.sleep(0.05)

            msg_id = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"sequence",
            )
            await asyncio.sleep(0.15)
            await cell_b.mark_read(msg_id)
            await asyncio.sleep(0.2)

            assert "delivered" in ack_sequence
            assert "read" in ack_sequence
            # delivered must come before read
            assert ack_sequence.index("delivered") < ack_sequence.index("read")
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()


# ─── Блок 4: Fire-and-forget + TTL ───────────────────────────────────────────

class TestFireAndForget:
    async def test_send_returns_message_id(self, tmp_path):
        node = await make_node(tmp_path, 40)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        cell_a = CellClient(idt_a)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(40))
            await cell_b.connect(addr(40))
            await asyncio.sleep(0.05)

            msg_id = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"id check",
            )
            assert isinstance(msg_id, str) and len(msg_id) > 0
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()

    async def test_message_timestamp_stored_on_send(self, tmp_path):
        node = await make_node(tmp_path, 41)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        cell_a = CellClient(idt_a)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(41))
            await cell_b.connect(addr(41))
            await asyncio.sleep(0.05)

            before = int(time.time())
            msg_id = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"timestamp",
            )
            after = int(time.time())

            assert msg_id in cell_a._sent
            assert before <= cell_a._sent[msg_id] <= after
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()

    async def test_two_sends_produce_different_message_ids(self, tmp_path):
        node = await make_node(tmp_path, 42)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        cell_a = CellClient(idt_a)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(42))
            await cell_b.connect(addr(42))
            await asyncio.sleep(0.05)

            id1 = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"first",
            )
            id2 = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"second",
            )
            assert id1 != id2
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()

    def test_no_ack_within_ttl_is_in_transit(self):
        cell = CellClient(CellIdentity.generate("Test"))
        fake_id = "fake-msg-id"
        cell._sent[fake_id] = int(time.time())
        assert cell.get_status(fake_id) == "in_transit"

    def test_72h_ttl_gives_failed_status(self):
        cell = CellClient(CellIdentity.generate("Test"))
        fake_id = "old-msg-id"
        cell._sent[fake_id] = int(time.time()) - ACK_TTL - 1
        assert cell.get_status(fake_id) == "failed"

    def test_unknown_message_id_returns_unknown(self):
        cell = CellClient(CellIdentity.generate("Test"))
        assert cell.get_status("nonexistent") == "unknown"

    async def test_no_auto_retransmit(self, tmp_path):
        """Cell makes no automatic retry — only one message in _sent after one send."""
        node = await make_node(tmp_path, 43)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        cell_a = CellClient(idt_a)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(43))
            await cell_b.connect(addr(43))
            await asyncio.sleep(0.05)

            await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"once",
            )
            await asyncio.sleep(0.3)
            # Only one entry in _sent — no auto-retransmit
            assert len(cell_a._sent) == 1
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()


# ─── Блок 5: ACK через буфер ─────────────────────────────────────────────────

class TestACKThroughBuffer:
    async def test_ack_delivered_after_buffer_flush(self, tmp_path):
        """
        cell_b офлайн → MSG буферизован на ноде →
        cell_b подключается → получает из буфера →
        отправляет ACK(delivered) → cell_a получает ACK
        """
        node = await make_node(tmp_path, 50)
        await node.start()

        idt_a = CellIdentity.generate("Alice")
        idt_b = CellIdentity.generate("Bob")
        acks = []

        async def on_ack(mid, st):
            acks.append((mid, st))

        cell_a = CellClient(idt_a, on_ack=on_ack)
        try:
            # cell_a connects and registers cell_b's enc_pub via pre-registration
            await cell_a.connect(addr(50))

            # register cell_b on node so routing knows enc_pub
            await node.register_cell_locally(
                idt_b.cell_id,
                idt_b.signing.public,
                idt_b.encryption.public,
            )
            await asyncio.sleep(0.05)

            # send while cell_b is offline → gets buffered
            msg_id = await cell_a.send(
                idt_b.cell_id, node.identity.node_id,
                idt_b.encryption.public, b"buffered hello",
            )
            await asyncio.sleep(0.1)

            # cell_b comes online → buffer flush
            cell_b = CellClient(idt_b)
            await cell_b.connect(addr(50))
            await asyncio.sleep(0.3)

            assert any(mid == msg_id and st == "delivered" for mid, st in acks)

            await cell_b.disconnect()
        finally:
            await cell_a.disconnect()
            await node.stop()
