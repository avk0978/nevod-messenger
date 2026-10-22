"""
File chunks (MSG_CHUNK) and the node's in-flight tracking.

A chunk written to a recipient's socket isn't necessarily received: on a mobile link that
has just dropped it can sit in the TCP buffer and vanish. The node keeps every unacked
chunk and re-buffers it when the connection goes away — in its ORIGINAL place in line,
because the receiver rebuilds the file strictly in arrival order. Chunk acks are for the
node only and must not be routed on to the sender.
"""

import asyncio

from node.client import CellClient
from node.identity import CellIdentity
from node.node import Node
from node.protocol import T, Packet, encode_payload, pack, sign_packet
from node.router import _deserialize_packet, _serialize_packet

BASE = 20100


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE + offset}"


async def make_node(tmp_path, offset: int) -> Node:
    return await Node.create_genesis(
        addr(offset),
        str(tmp_path / f"n{offset}.json"),
        str(tmp_path / f"n{offset}.db"),
        access="open",
    )


def chunk(from_addr: str, to_addr: str, msg_type: str = T.MSG_CHUNK) -> Packet:
    return Packet(type=msg_type, payload=encode_payload({"blob": b"x"}),
                  from_addr=from_addr, to_addr=to_addr)


class TestDisconnectHook:
    async def test_client_disconnect_reaches_router(self, tmp_path):
        """Regression: from 9307822 (2026-09-19) until 2026-10-13 _recv_loop removed the
        registry entry itself, so _handle_incoming's own remove() always returned False and
        on_disconnect never ran — nothing in flight was ever re-buffered."""
        node = await make_node(tmp_path, 7)
        await node.start()
        called = []
        orig = node.transport.on_disconnect

        async def spy(peer_id):
            called.append(peer_id)
            await orig(peer_id)

        node.transport.on_disconnect = spy
        alice = CellIdentity.generate("Alice")
        cell = CellClient(alice)
        try:
            await cell.connect(addr(7))
            await asyncio.sleep(0.05)
            await cell.disconnect()
            await asyncio.sleep(0.3)
            assert called == [alice.cell_id]
        finally:
            await node.stop()


class TestRecentAcksResent:
    """An ACK written into a connection that is already dying is lost — nobody acks an ack,
    so the node re-queues the ones it sent in the last ACK_RESEND_WINDOW_SECS when the
    connection drops."""

    async def test_ack_sent_just_before_disconnect_is_redelivered(self, tmp_path):
        node = await make_node(tmp_path, 5)
        await node.start()
        idt_a, idt_b = CellIdentity.generate("Alice"), CellIdentity.generate("Bob")
        acks = []

        async def on_ack(mid, st):
            acks.append((mid, st))

        cell_a = CellClient(idt_a, on_ack=on_ack)
        try:
            await cell_a.connect(addr(5))
            await asyncio.sleep(0.05)
            node_id = node.identity.node_id
            from node.protocol import make_ack
            ack = make_ack(f"{idt_b.cell_id}@{node_id}", f"{idt_a.cell_id}@{node_id}",
                           "msg-1", "delivered")
            await node.router.route(ack)
            await asyncio.sleep(0.1)
            assert ("msg-1", "delivered") in acks

            # The connection dies; the node can't know whether that ack made it.
            await cell_a.disconnect()
            await asyncio.sleep(0.2)
            buffered = await node.storage.get_buffered(idt_a.cell_id)
            assert [_deserialize_packet(m.payload).id for m in buffered] == [ack.id]

            acks.clear()
            cell_a2 = CellClient(idt_a, on_ack=on_ack)
            await cell_a2.connect(addr(5))
            await asyncio.sleep(0.2)
            assert ("msg-1", "delivered") in acks
            await cell_a2.disconnect()
        finally:
            await node.stop()

    async def test_ack_resent_at_most_max_times(self, tmp_path):
        """A client dropping its connection again and again within the window doesn't get
        the same ACK forever."""
        import time
        from node.router import ACK_MAX_RESENDS
        node = await make_node(tmp_path, 8)
        alice = CellIdentity.generate("Alice")
        try:
            await node.register_cell_locally(alice.cell_id, alice.signing.public, alice.encryption.public)
            ack = chunk("bob@x", f"{alice.cell_id}@{node.identity.node_id}", T.ACK)
            resent = 0
            for _ in range(ACK_MAX_RESENDS + 2):
                node.router._recent_acks[alice.cell_id] = [(time.monotonic(), ack, 1)]
                await node.router.on_connection_lost(alice.cell_id)
                if await node.storage.get_buffered(alice.cell_id):
                    resent += 1
                    await node.storage.delete_buffered(ack.id)   # as flush_buffer would
            assert resent == ACK_MAX_RESENDS
        finally:
            await node.stop()

    async def test_old_acks_not_resent(self, tmp_path):
        import time
        from node.router import ACK_RESEND_WINDOW_SECS
        node = await make_node(tmp_path, 6)
        alice = CellIdentity.generate("Alice")
        try:
            await node.register_cell_locally(alice.cell_id, alice.signing.public, alice.encryption.public)
            old = chunk("bob@x", f"{alice.cell_id}@{node.identity.node_id}", T.ACK)
            node.router._recent_acks[alice.cell_id] = [
                (time.monotonic() - ACK_RESEND_WINDOW_SECS - 1, old, 1)]
            await node.router.on_connection_lost(alice.cell_id)
            assert await node.storage.get_buffered(alice.cell_id) == []
            assert alice.cell_id not in node.router._recent_acks
        finally:
            await node.stop()


class TestBufferOrder:
    async def test_get_buffered_orders_by_seq_not_insertion(self, tmp_path):
        node = await make_node(tmp_path, 0)
        try:
            await node.storage.buffer_message("late", "cell", "n", b"p2", seq=200)
            await node.storage.buffer_message("early", "cell", "n", b"p1", seq=100)
            ids = [m.message_id for m in await node.storage.get_buffered("cell")]
            assert ids == ["early", "late"]
        finally:
            await node.stop()

    async def test_rows_without_seq_come_first_in_insertion_order(self, tmp_path):
        """Rows buffered before the seq column existed are all 0 — older than anything since."""
        node = await make_node(tmp_path, 1)
        try:
            await node.storage.buffer_message("new", "cell", "n", b"p", seq=5)
            await node.storage.buffer_message("old1", "cell", "n", b"p")
            await node.storage.buffer_message("old2", "cell", "n", b"p")
            ids = [m.message_id for m in await node.storage.get_buffered("cell")]
            assert ids == ["old1", "old2", "new"]
        finally:
            await node.stop()


class TestInflightChunks:
    async def test_unacked_chunk_rebuffered_ahead_of_later_ones(self, tmp_path):
        """Chunk 1 was written to the socket (in flight) when the connection died; chunk 2
        was routed after the drop and buffered first. Chunk 1 must still come out first."""
        node = await make_node(tmp_path, 2)
        bob = CellIdentity.generate("Bob")
        try:
            await node.register_cell_locally(bob.cell_id, bob.signing.public, bob.encryption.public)
            to = f"{bob.cell_id}@{node.identity.node_id}"
            c1, c2 = chunk("alice@x", to), chunk("alice@x", to)
            seq1 = node.router._next_seq()
            node.router._inflight[bob.cell_id] = {c1.id: (c1, seq1)}
            seq2 = node.router._next_seq()
            await node.storage.buffer_message(c2.id, bob.cell_id, node.identity.node_id,
                                              _serialize_packet(c2), seq2)

            await node.router.on_connection_lost(bob.cell_id)

            ids = [m.message_id for m in await node.storage.get_buffered(bob.cell_id)]
            assert ids == [c1.id, c2.id]
            assert bob.cell_id not in node.router._inflight
        finally:
            await node.stop()

    async def test_chunk_tracked_then_cleared_by_ack_which_is_not_forwarded(self, tmp_path):
        node = await make_node(tmp_path, 3)
        await node.start()
        idt_a, idt_b = CellIdentity.generate("Alice"), CellIdentity.generate("Bob")
        acks_at_sender = []

        async def on_ack(mid, st):
            acks_at_sender.append((mid, st))

        cell_a = CellClient(idt_a, on_ack=on_ack)
        cell_b = CellClient(idt_b)
        try:
            await cell_a.connect(addr(3))
            await cell_b.connect(addr(3))
            await asyncio.sleep(0.05)

            node_id = node.identity.node_id
            c = chunk(f"{idt_a.cell_id}@{node_id}", f"{idt_b.cell_id}@{node_id}")
            sign_packet(c, idt_a.signing)
            await cell_a._ws.send(pack(c))
            # A real message after it, to show acks do still flow to the sender.
            msg_id = await cell_a.send(idt_b.cell_id, node_id, idt_b.encryption.public, b"hi")
            await asyncio.sleep(0.3)

            assert idt_b.cell_id not in node.router._inflight      # chunk acked by Bob
            assert (msg_id, "delivered") in acks_at_sender
            assert all(mid != c.id for mid, _ in acks_at_sender)    # chunk ack stayed at node
        finally:
            await cell_a.disconnect()
            await cell_b.disconnect()
            await node.stop()

    async def test_flush_keeps_original_order_when_rebuffered(self, tmp_path):
        """A packet bounced back into the buffer mid-flush keeps its seq — it doesn't jump
        behind the rest of the queue."""
        node = await make_node(tmp_path, 4)
        bob = CellIdentity.generate("Bob")
        try:
            await node.register_cell_locally(bob.cell_id, bob.signing.public, bob.encryption.public)
            to = f"{bob.cell_id}@{node.identity.node_id}"
            pkts = [chunk("alice@x", to) for _ in range(3)]
            for p in pkts:
                await node.storage.buffer_message(p.id, bob.cell_id, node.identity.node_id,
                                                  _serialize_packet(p), node.router._next_seq())

            # Bob isn't actually connected, so every route() during flush bounces back into
            # the buffer — the worst case of "disconnected again mid-flush".
            await node.router.flush_buffer(bob.cell_id)

            got = [_deserialize_packet(m.payload).id for m in await node.storage.get_buffered(bob.cell_id)]
            assert got == [p.id for p in pkts]
        finally:
            await node.stop()


class TestChunkWindow:
    async def test_at_most_window_chunks_unacked_and_signals_go_first(self, tmp_path):
        """Chunks beyond CHUNK_WINDOW wait in the node until earlier ones are acked, while a
        call signal is written at once (device logs 2026-10-20: a hangup queued behind a
        video in the socket reached the callee after she had hung up herself)."""
        from node.router import CHUNK_WINDOW
        from node.protocol import Packet, T
        node = await make_node(tmp_path, 40)
        try:
            written = []

            async def send_to(cell_id, pkt):
                written.append(pkt.id)
                return True

            async def get(cell_id):
                return object()
            node.transport.send_to = send_to
            node.transport.connections.get = get
            to = "c" * 64 + "@" + node.identity.node_id
            chunks = [Packet(type=T.MSG_CHUNK, payload=b"x", from_addr="a@b", to_addr=to)
                      for _ in range(5)]
            for p in chunks:
                assert await node.router._deliver_local(p)
            await asyncio.sleep(0.2)
            assert written == [p.id for p in chunks[:CHUNK_WINDOW]]

            signal = Packet(type=T.VCALL_SIGNAL, payload=b"h", from_addr="a@b", to_addr=to)
            assert await node.router._deliver_local(signal)
            assert written[-1] == signal.id

            node.router.on_ack_received("c" * 64, chunks[0].id)
            await asyncio.sleep(0.2)
            assert chunks[CHUNK_WINDOW].id in written

            # A drop buffers the queued ones too (they count as in flight).
            await node.router.on_connection_lost("c" * 64)
            assert node.router._chunk_queue.get("c" * 64) is None
        finally:
            await node.stop()
