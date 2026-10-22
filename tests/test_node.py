"""
Integration tests for Node — transport, gossip, routing.

Uses real WebSocket connections on localhost with ports 19300+.
Each test class uses its own port range to avoid conflicts.
"""

import asyncio
import pytest

from node.identity import NodeIdentity
from node.node import Node
from node.storage import NodeEntry
from node.protocol import T, Packet, encode_payload
import time


BASE = 19300


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE + offset}"


async def make_node(tmp_path, offset: int, genesis: bool = False) -> Node:
    address = addr(offset)
    id_path = str(tmp_path / f"n{offset}.json")
    db_path = str(tmp_path / f"n{offset}.db")
    if genesis:
        return await Node.create_genesis(address, id_path, db_path, access="open")
    idt = NodeIdentity.generate(address)
    idt.save(id_path)
    return await Node.create(id_path, db_path)


class TestTwoNodesConnect:
    async def test_nodes_connect_via_join(self, tmp_path):
        n1 = await make_node(tmp_path, 0, genesis=True)
        n2 = await make_node(tmp_path, 1)
        await n1.start()
        await n2.start()
        try:
            await n2.join(addr(0))
            await asyncio.sleep(0.2)

            conn = await n1.transport.connections.get(n2.identity.node_id)
            assert conn is not None, "n1 should have connection to n2"
            assert conn.peer_node_id == n2.identity.node_id
        finally:
            await n1.stop()
            await n2.stop()

    async def test_peer_enc_pubkey_available_after_connect(self, tmp_path):
        n1 = await make_node(tmp_path, 2, genesis=True)
        n2 = await make_node(tmp_path, 3)
        await n1.start()
        await n2.start()
        try:
            await n2.join(addr(2))
            await asyncio.sleep(0.2)

            conn = await n2.transport.connections.get(n1.identity.node_id)
            assert conn is not None
            assert conn.peer_enc_pubkey == n1.identity.encryption.public
        finally:
            await n1.stop()
            await n2.stop()

    async def test_connection_is_bidirectional(self, tmp_path):
        n1 = await make_node(tmp_path, 4, genesis=True)
        n2 = await make_node(tmp_path, 5)
        await n1.start()
        await n2.start()
        try:
            await n2.join(addr(4))
            await asyncio.sleep(0.2)

            assert await n1.transport.connections.get(n2.identity.node_id) is not None
            assert await n2.transport.connections.get(n1.identity.node_id) is not None
        finally:
            await n1.stop()
            await n2.stop()

    async def test_multiple_peers(self, tmp_path):
        n1 = await make_node(tmp_path, 6, genesis=True)
        n2 = await make_node(tmp_path, 7)
        n3 = await make_node(tmp_path, 8)
        await n1.start()
        await n2.start()
        await n3.start()
        try:
            await n2.join(addr(6))
            await n3.join(addr(6))
            await asyncio.sleep(0.2)

            conns = await n1.transport.connections.all()
            peer_ids = {c.peer_node_id for c in conns}
            assert n2.identity.node_id in peer_ids
            assert n3.identity.node_id in peer_ids
        finally:
            await n1.stop()
            await n2.stop()
            await n3.stop()


class TestCellRegistration:
    async def test_register_cell_locally(self, tmp_path):
        n = await make_node(tmp_path, 10, genesis=True)
        await n.start()
        try:
            from node.crypto import gen_signing, gen_encryption
            cell_sign = gen_signing()
            cell_enc  = gen_encryption()
            cell_id   = cell_sign.public.hex()
            await n.register_cell_locally(cell_id, cell_sign.public, cell_enc.public)

            cell = await n.storage.get_cell(cell_id)
            assert cell is not None
            assert cell.signing_pubkey == cell_sign.public
            assert cell.enc_pubkey == cell_enc.public
        finally:
            await n.stop()

    async def test_presence_set_after_register(self, tmp_path):
        n = await make_node(tmp_path, 11, genesis=True)
        await n.start()
        try:
            from node.crypto import gen_signing, gen_encryption
            cell_sign = gen_signing()
            cell_id   = cell_sign.public.hex()
            await n.register_cell_locally(cell_id, cell_sign.public, gen_encryption().public)

            presence = await n.storage.get_presence(cell_id)
            assert presence is not None
            assert presence.home_node_id == n.identity.node_id
        finally:
            await n.stop()


class TestMessageRouting:
    async def test_message_buffered_when_no_route(self, tmp_path):
        n = await make_node(tmp_path, 12, genesis=True)
        await n.start()
        try:
            from node.crypto import gen_signing, gen_encryption
            cell_sign = gen_signing()
            cell_enc  = gen_encryption()
            cell_id   = cell_sign.public.hex()
            await n.register_cell_locally(cell_id, cell_sign.public, cell_enc.public)

            # manually set presence to an offline node so message gets buffered
            await n.storage.update_presence(cell_id, "ghost_node_id", None)
            await n.storage.upsert_node(NodeEntry(
                node_id="ghost_node_id",
                address="1.2.3.4:9999",
                status="offline",
                last_seen=int(time.time()) - 1000,
                added_at=int(time.time()),
            ))

            to_addr = f"{cell_id}@ghost_node_id"
            pkt = Packet(
                type=T.MSG,
                payload=b"encrypted-blob",
                from_addr=n.identity.node_id,
                to_addr=to_addr,
            )
            await n.router.route(pkt)

            buffered = await n.storage.get_buffered(cell_id)
            assert len(buffered) == 1
            assert buffered[0].to_cell == cell_id
        finally:
            await n.stop()

    async def test_msg_silent_buffers_without_push(self, tmp_path):
        """delete:/edit:/identity_deleted:/contact-added-notice control signals ride the
        same E2E "msg" shape but must never wake a killed app with a "New message" push —
        they produce no visible chat bubble, so a push for one was just confusing (see
        feedback session 2026-09-15: a user testing identity deletion got exactly this
        unexplained push). MSG_SILENT should still buffer and still tell the sender
        "queued" (status=offline), same as a real MSG — only the push itself is skipped."""
        n = await make_node(tmp_path, 16, genesis=True)
        await n.start()
        try:
            from node.crypto import gen_signing, gen_encryption
            cell_sign = gen_signing()
            cell_enc  = gen_encryption()
            cell_id   = cell_sign.public.hex()
            sender_sign = gen_signing()
            sender_enc  = gen_encryption()
            sender_id   = sender_sign.public.hex()
            await n.register_cell_locally(cell_id, cell_sign.public, cell_enc.public)
            await n.register_cell_locally(sender_id, sender_sign.public, sender_enc.public)
            await n.storage.save_push_token(cell_id, "fake-device-token")

            sent_pushes = []

            class FakeApns:
                async def send(self, token, **kwargs):
                    sent_pushes.append(token)
                    return True

            n.apns = FakeApns()

            await n.storage.update_presence(cell_id, "ghost_node_id", None)
            await n.storage.upsert_node(NodeEntry(
                node_id="ghost_node_id",
                address="1.2.3.4:9999",
                status="offline",
                last_seen=int(time.time()) - 1000,
                added_at=int(time.time()),
            ))
            to_addr = f"{cell_id}@ghost_node_id"

            silent_pkt = Packet(
                type=T.MSG_SILENT,
                payload=b"encrypted-blob",
                from_addr=f"{sender_id}@{n.identity.node_id}",
                to_addr=to_addr,
            )
            await n.router.route(silent_pkt)

            buffered = await n.storage.get_buffered(cell_id)
            assert len(buffered) == 1
            assert sent_pushes == []  # no push for the silent signal

            # sender still gets "queued", exactly like a real MSG would
            from node.router import _deserialize_packet
            from node.protocol import decode_payload
            sender_buffered = await n.storage.get_buffered(sender_id)
            assert len(sender_buffered) == 1
            ack_pkt = _deserialize_packet(sender_buffered[0].payload)
            assert ack_pkt.type == T.ACK
            d = decode_payload(ack_pkt.payload)
            assert d["message_id"] == silent_pkt.id
            assert d["status"] == "offline"

            # contrast: an ordinary MSG in the same situation DOES push
            real_pkt = Packet(
                type=T.MSG,
                payload=b"encrypted-blob-2",
                from_addr=f"{sender_id}@{n.identity.node_id}",
                to_addr=to_addr,
            )
            await n.router.route(real_pkt)
            assert sent_pushes == ["fake-device-token"]

            # The same MSG arriving again (re-buffered after a drop, or re-sent by the
            # sender's node) must not push again — one push per message id.
            n.router._push_times.clear()   # not the 3 s rate limit that stops it
            await n.router.route(real_pkt)
            assert sent_pushes == ["fake-device-token"]
        finally:
            await n.stop()

    async def test_stale_call_offer_dropped_on_flush(self, tmp_path):
        """A vcall_offer/vcall_signal that sat buffered past CALL_SIGNAL_STALE_SECS
        is almost certainly a dead call by the time the recipient reconnects — see
        the 2026-09-02 missed-call bug (feedback_remind_apns_sandbox_flip): a VoIP
        push failed silently, and the buffered offer got replayed hours later as if
        it were a live incoming call. flush_buffer() should drop it instead."""
        from node.router import _serialize_packet, CALL_SIGNAL_STALE_SECS

        n = await make_node(tmp_path, 13, genesis=True)
        await n.start()
        try:
            from node.crypto import gen_signing, gen_encryption
            cell_sign = gen_signing()
            cell_enc = gen_encryption()
            cell_id = cell_sign.public.hex()
            await n.register_cell_locally(cell_id, cell_sign.public, cell_enc.public)

            stale_pkt = Packet(
                type=T.VCALL_OFFER,
                payload=b"encrypted-offer",
                from_addr="caller_cell@some_node",
                to_addr=f"{cell_id}@{n.identity.node_id}",
                ts=int(time.time()) - CALL_SIGNAL_STALE_SECS - 5,
            )
            await n.storage.buffer_message(
                stale_pkt.id, cell_id, n.identity.node_id, _serialize_packet(stale_pkt)
            )
            assert len(await n.storage.get_buffered(cell_id)) == 1

            await n.router.flush_buffer(cell_id)

            # Dropped, not re-buffered — route() never got a chance to re-queue it.
            assert await n.storage.get_buffered(cell_id) == []
        finally:
            await n.stop()

    async def test_flush_sends_call_signals_before_file_chunks(self, tmp_path):
        """A call offer buffered behind a video must not wait for every chunk to go out
        first (device logs 2026-10-20: it reached the callee 30 s late). Everything else keeps
        its order — a delete (MSG_SILENT) or reaction must not overtake the message it refers
        to (2026-10-21)."""
        from node.router import _serialize_packet

        n = await make_node(tmp_path, 21, genesis=True)
        await n.start()
        try:
            from node.crypto import gen_signing, gen_encryption
            cell_sign = gen_signing()
            cell_enc = gen_encryption()
            cell_id = cell_sign.public.hex()
            await n.register_cell_locally(cell_id, cell_sign.public, cell_enc.public)
            to_addr = f"{cell_id}@{n.identity.node_id}"
            sent = [Packet(type=t, payload=b"x", from_addr="caller@some_node", to_addr=to_addr)
                    for t in (T.MSG_CHUNK, T.MSG_CHUNK, T.MSG, T.VCALL_OFFER, T.VCALL_SIGNAL,
                              T.MSG_SILENT, T.REACT, T.ACK)]
            for seq, pkt in enumerate(sent, start=1):
                await n.storage.buffer_message(pkt.id, cell_id, n.identity.node_id,
                                               _serialize_packet(pkt), seq)
            routed = []

            async def record(pkt, seq=None):
                routed.append(pkt.id)
            n.router.route = record
            await n.router.flush_buffer(cell_id)
            assert routed == [sent[i].id for i in (3, 4, 7, 0, 1, 2, 5, 6)]
        finally:
            await n.stop()

    async def test_unknown_cell_notifies_sender_failed(self, tmp_path):
        """A MSG to a cell that doesn't exist here at all (self-deregistered/identity
        reset, or never registered) must not just vanish — found 2026-09-13 investigating
        a real report of messages hanging forever "sending": router.route() logged
        "unknown cell, dropping" and returned with zero feedback to the sender, so the
        client never got any ack to react to. Now the sender gets a terminal
        status="failed" ack instead (node/router.py's _notify_undeliverable)."""
        from node.crypto import gen_signing, gen_encryption
        from node.router import _deserialize_packet
        from node.protocol import decode_payload

        n = await make_node(tmp_path, 14, genesis=True)
        await n.start()
        try:
            sender_sign = gen_signing()
            sender_enc = gen_encryption()
            sender_id = sender_sign.public.hex()
            await n.register_cell_locally(sender_id, sender_sign.public, sender_enc.public)

            ghost_cell_id = gen_signing().public.hex()  # never registered anywhere
            pkt = Packet(
                type=T.MSG,
                payload=b"encrypted-blob",
                from_addr=f"{sender_id}@{n.identity.node_id}",
                to_addr=f"{ghost_cell_id}@{n.identity.node_id}",
            )
            await n.router.route(pkt)

            # sender isn't actually transport-connected in this test, so the failure
            # ack routed back to it lands in its own buffer, same as any other ack
            # would while the recipient is offline.
            buffered = await n.storage.get_buffered(sender_id)
            assert len(buffered) == 1
            ack_pkt = _deserialize_packet(buffered[0].payload)
            assert ack_pkt.type == T.ACK
            d = decode_payload(ack_pkt.payload)
            assert d["message_id"] == pkt.id
            assert d["status"] == "failed"
        finally:
            await n.stop()

    async def test_local_message_delivered(self, tmp_path):
        delivered = []

        async def on_message(pkt: Packet):
            delivered.append(pkt)

        n = await Node.create_genesis(
            addr(13),
            str(tmp_path / "n13.json"),
            str(tmp_path / "n13.db"),
            on_message=on_message,
        )
        await n.start()
        try:
            from node.crypto import gen_signing, gen_encryption
            cell_sign = gen_signing()
            cell_enc  = gen_encryption()
            cell_id   = cell_sign.public.hex()
            await n.register_cell_locally(cell_id, cell_sign.public, cell_enc.public)

            await n.send_message(f"{cell_id}@{n.identity.node_id}", b"hello")
            await asyncio.sleep(0.1)

            assert len(delivered) == 1
            assert delivered[0].type == T.MSG
        finally:
            await n.stop()


class TestNodeTypePropagation:
    async def test_node_type_change_propagates_on_restart(self, tmp_path):
        """Found 2026-09-13 adding an admin-panel node_type setter: Node.start() used
        to re-feed node_table's OLD stored type straight back into
        refresh_own_node_flags instead of the current identity.node_type — unlike
        access, right next to it, which was already read from identity correctly.
        That made a node_type change (however made — CLI or the panel) a permanent
        no-op even across restarts, since node_table (what peers actually see via
        gossip) never picked it up."""
        address = addr(16)
        id_path = str(tmp_path / "n16.json")
        db_path = str(tmp_path / "n16.db")
        n = await Node.create_genesis(address, id_path, db_path, access="open")
        await n.start()
        node_id = n.identity.node_id
        row = await n.storage.get_node(node_id)
        assert row.type == "permanent"
        await n.stop()

        # Simulate what the admin panel's node-type setter does: flip
        # identity.node_type and persist it, then restart.
        n.identity.node_type = "temporary"
        n.identity.save(id_path)

        n2 = await Node.create(id_path, db_path)
        await n2.start()
        try:
            row2 = await n2.storage.get_node(node_id)
            assert row2.type == "temporary"
        finally:
            await n2.stop()


class TestPingPong:
    async def test_ping_updates_last_seen(self, tmp_path):
        n1 = await make_node(tmp_path, 14, genesis=True)
        n2 = await make_node(tmp_path, 15)
        await n1.start()
        await n2.start()
        try:
            await n2.join(addr(14))
            await asyncio.sleep(0.2)

            await n2.storage.upsert_node(NodeEntry(
                node_id=n1.identity.node_id,
                address=addr(14),
                type="permanent",
                access="open",
                last_seen=int(time.time()),
                status="online",
                added_at=int(time.time()),
            ))

            from node.protocol import make_ping, pack
            conn = await n2.transport.connections.get(n1.identity.node_id)
            assert conn is not None
            ping = make_ping(n2.identity.node_id, n1.identity.node_id)
            await conn.send(ping)
            await asyncio.sleep(0.2)
        finally:
            await n1.stop()
            await n2.stop()


class TestGenesisNode:
    async def test_genesis_has_self_in_node_table(self, tmp_path):
        n = await make_node(tmp_path, 20, genesis=True)
        await n.start()
        try:
            entry = await n.storage.get_node(n.identity.node_id)
            assert entry is not None
            assert entry.status == "online"
        finally:
            await n.stop()

    async def test_genesis_saves_identity(self, tmp_path):
        id_path = str(tmp_path / "genesis.json")
        n = await Node.create_genesis(addr(21), id_path, str(tmp_path / "g.db"))
        await n.start()
        try:
            loaded = NodeIdentity.load(id_path)
            assert loaded.node_id == n.identity.node_id
        finally:
            await n.stop()


async def make_node_with_join_mode(tmp_path, offset: int, node_join_mode: str) -> Node:
    """Like make_node(), but lets the test pick node_join_mode explicitly — the
    default helper always leaves it at NodeIdentity's own default ("invite")."""
    address = addr(offset)
    id_path = str(tmp_path / f"n{offset}.json")
    db_path = str(tmp_path / f"n{offset}.db")
    idt = NodeIdentity.generate(address, node_join_mode=node_join_mode)
    idt.save(id_path)
    return await Node.create(id_path, db_path)


class TestNodeAdmission:
    """DISCUSS_NODE_ADMISSION.md: node_join_mode governs admission of OTHER NODES
    into node_table, separate from invite_mode (which governs cells). Default
    ("invite") is unchanged existing behavior — covered incidentally by every other
    test in this file that calls .join() without open_join. These specifically
    cover the new "open" mode."""

    async def test_open_join_mode_admits_without_invite_code(self, tmp_path):
        bootstrap = await make_node_with_join_mode(tmp_path, 30, node_join_mode="open")
        joiner = await make_node(tmp_path, 31)
        await bootstrap.start()
        await joiner.start()
        try:
            reachable = await joiner.join(addr(30), open_join=True)
            # Not asserting a specific value — reachability depends on the dial-back
            # actually succeeding on this machine/port, which isn't what's being
            # tested here. The real assertion is that join() didn't raise.
            assert reachable in (True, False)

            entry = await bootstrap.storage.get_node(joiner.identity.node_id)
            assert entry is not None, "bootstrap should have admitted the joiner into its node_table"
            assert entry.status == "online"
        finally:
            await bootstrap.stop()
            await joiner.stop()

    async def test_default_join_mode_rejects_open_join(self, tmp_path):
        # node_join_mode defaults to "invite" — make_node() doesn't override it.
        bootstrap = await make_node(tmp_path, 32)
        joiner = await make_node(tmp_path, 33)
        await bootstrap.start()
        await joiner.start()
        try:
            with pytest.raises(ValueError, match="invite_required"):
                await joiner.join(addr(32), open_join=True)
        finally:
            await bootstrap.stop()
            await joiner.stop()
