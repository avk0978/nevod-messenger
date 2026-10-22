"""
Tests for the invite_mode="admin" registration channel — see
MD_Discuss/DISCUSS_REGISTRATION_CHANNEL.md for the full design.

Covers: JOIN_REQUEST after an invite_required NACK, admin notification via the
built-in registrar identity, and direct admission (no code) on approval.
"""

import asyncio
import pytest

from node.identity import NodeIdentity, CellIdentity
from node.node import Node
from node.client import CellClient
from node.protocol import (make_join_request, sign_packet, pack, decode_payload, T,
                           Packet, encode_payload)

BASE = 19400


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE + offset}"


async def make_admin_node(tmp_path, offset: int, admin_cell_ids=None) -> Node:
    address = addr(offset)
    id_path = str(tmp_path / f"n{offset}.json")
    db_path = str(tmp_path / f"n{offset}.db")
    idt = NodeIdentity.generate(address, invite_mode="admin",
                                 admin_cell_ids=admin_cell_ids or [])
    idt.save(id_path)
    return await Node.create(id_path, db_path)


async def connect_pending(node: Node) -> CellClient:
    """Connects a fresh identity — expected to get invite_required, connection
    stays open (CELL_REGISTER_NACK doesn't close the socket client-side)."""
    identity = CellIdentity.generate("Guest")
    client = CellClient(identity)
    await client.connect(addr_of(node), expected_fingerprint=node.identity.tls_fingerprint)
    await asyncio.sleep(0.1)
    return client


def addr_of(node: Node) -> str:
    return node.identity.address


class TestJoinRequestStorage:
    async def test_create_dedups(self, storage):
        first = await storage.create_join_request("cell1", "sign1", "enc1", "hi")
        second = await storage.create_join_request("cell1", "sign1", "enc1", "hi again")
        assert first is True
        assert second is False  # already pending, no duplicate row

    async def test_resolve_approved_admits_cell(self, storage):
        await storage.create_join_request("cell1", "sign1", "enc1", "")
        await storage.resolve_join_request("cell1", "approved", invited_by="admin")
        assert await storage.is_cell_allowed("cell1")
        pending = await storage.list_join_requests(status="pending")
        assert not any(r.cell_id == "cell1" for r in pending)

    async def test_resolve_denied_does_not_admit(self, storage):
        await storage.create_join_request("cell1", "sign1", "enc1", "")
        await storage.resolve_join_request("cell1", "denied")
        assert not await storage.is_cell_allowed("cell1")


class TestJoinRequestProtocol:
    async def test_join_request_stored_and_acked(self, tmp_path):
        node = await make_admin_node(tmp_path, 0)
        await node.start()
        try:
            client = await connect_pending(node)
            try:
                req = make_join_request(client.cell_id, node.identity.node_id, note="please")
                sign_packet(req, client.identity.signing)
                await client._ws.send(pack(req))
                await asyncio.sleep(0.15)

                pending = await node.storage.list_join_requests(status="pending")
                assert any(r.cell_id == client.cell_id and r.note == "please" for r in pending)
            finally:
                await client.disconnect()
        finally:
            await node.stop()

    async def test_display_name_stored_with_request(self, tmp_path):
        """The requester's chosen name rides along on JOIN_REQUEST itself (it never
        survives the earlier CELL_REGISTER NACK) — found 2026-09-13 that the admin
        panel/notification only ever showed a bare cell_id, no way to tell who was
        actually asking."""
        node = await make_admin_node(tmp_path, 2)
        await node.start()
        try:
            client = await connect_pending(node)
            try:
                req = make_join_request(client.cell_id, node.identity.node_id,
                                         note="hi", display_name="Anechka")
                sign_packet(req, client.identity.signing)
                await client._ws.send(pack(req))
                await asyncio.sleep(0.15)

                pending = await node.storage.list_join_requests(status="pending")
                match = next((r for r in pending if r.cell_id == client.cell_id), None)
                assert match is not None
                assert match.display_name == "Anechka"
            finally:
                await client.disconnect()
        finally:
            await node.stop()

    async def test_ensure_registrar_runs_on_live_mode_switch(self, tmp_path):
        """_ensure_registrar() only ever ran once, at node startup, gated on
        invite_mode=="admin" there. Flipping into "admin" LIVE via the admin panel
        (no restart in between — this is how the panel actually does it, see
        admin.py's _handle_set_invite_mode) used to leave _registrar_identity
        permanently None for the rest of that process's life, so _notify_admins
        silently no-op'd for every join request until the next restart. Found
        2026-09-13 tracing exactly that against a real node."""
        address = addr(20)
        id_path = str(tmp_path / "n20.json")
        db_path = str(tmp_path / "n20.db")
        idt = NodeIdentity.generate(address)  # starts as invite_mode="open"
        idt.save(id_path)
        node = await Node.create(id_path, db_path)
        await node.start()
        try:
            assert node._registrar_identity is None

            node.identity.invite_mode = "admin"
            await node._ensure_registrar()

            assert node._registrar_identity is not None
        finally:
            await node.stop()

    async def test_ignored_when_not_admin_mode(self, tmp_path):
        address = addr(10)
        id_path = str(tmp_path / "n10.json")
        db_path = str(tmp_path / "n10.db")
        idt = NodeIdentity.generate(address)  # default invite_mode="open"
        idt.save(id_path)
        node = await Node.create(id_path, db_path)
        await node.start()
        try:
            identity = CellIdentity.generate("Guest")
            client = CellClient(identity)
            await client.connect(address)
            await asyncio.sleep(0.1)
            try:
                req = make_join_request(client.cell_id, node.identity.node_id)
                sign_packet(req, client.identity.signing)
                await client._ws.send(pack(req))
                await asyncio.sleep(0.15)

                pending = await node.storage.list_join_requests(status="pending")
                assert pending == []  # open mode never needed a request in the first place
            finally:
                await client.disconnect()
        finally:
            await node.stop()

    async def test_approve_admits_and_reregister_succeeds(self, tmp_path):
        node = await make_admin_node(tmp_path, 1)
        await node.start()
        try:
            client = await connect_pending(node)
            try:
                req = make_join_request(client.cell_id, node.identity.node_id)
                sign_packet(req, client.identity.signing)
                await client._ws.send(pack(req))
                await asyncio.sleep(0.15)

                ok = await node.approve_join_request(client.cell_id)
                assert ok is True
                assert await node.storage.is_cell_allowed(client.cell_id)

                # A second registration attempt (no code) should now succeed outright.
                await client.disconnect()
                client2 = CellClient(client.identity)
                await client2.connect(addr_of(node))
                await asyncio.sleep(0.15)
                assert await node.storage.get_cell(client.cell_id) is not None
                await client2.disconnect()
            except Exception:
                await client.disconnect()
                raise
        finally:
            await node.stop()

    async def test_approve_unknown_cell_returns_false(self, tmp_path):
        node = await make_admin_node(tmp_path, 2)
        await node.start()
        try:
            assert await node.approve_join_request("nonexistent") is False
        finally:
            await node.stop()


class TestAdminNotification:
    async def test_admin_gets_notified_via_registrar(self, tmp_path):
        # Admin is itself a registered home cell on this node — realistic setup
        # (an operator running admin-only mode is presumably also a member).
        admin_identity = CellIdentity.generate("Admin")
        node = await make_admin_node(tmp_path, 3, admin_cell_ids=[admin_identity.cell_id])
        await node.start()
        try:
            received: list = []
            admin_client = CellClient(admin_identity,
                                       on_message=lambda f, m: received.append(m))
            # Admin registers normally — invite_mode="admin" means it needs a code too;
            # simplest path here is direct local admission (same as approve_join_request
            # would do), since what's under test is notification delivery, not admission.
            await node.storage._admit_cell(admin_identity.cell_id, "test")
            await admin_client.connect(addr_of(node))
            await asyncio.sleep(0.1)

            requester = await connect_pending(node)
            try:
                req = make_join_request(requester.cell_id, node.identity.node_id, note="hello")
                sign_packet(req, requester.identity.signing)
                await requester._ws.send(pack(req))
                await asyncio.sleep(0.2)
            finally:
                await requester.disconnect()

            assert len(received) == 1
            text = received[0].decode("utf-8")
            assert "hello" in text
            # The notification spells out the exact words this chat understands — an
            # admin has no way to guess "approve"/"deny" (not, say, "ok") otherwise.
            # See TestRegistrarChatCommands.test_approve_via_casual_synonym.
            assert "approve" in text and "deny" in text
            await admin_client.disconnect()
        finally:
            await node.stop()


class TestRegistrarNeverBuffersDeadLetters:
    """A synthetic identity like the registrar (_ensure_registrar) never has a live
    transport connection of its own, so anything routed to it besides a real chat
    command (see _maybe_handle_registrar_reply) would sit in message_buffer until
    its 72h TTL expires — nothing will ever "come online" to flush it. Found
    2026-09-18 on node1: 12 stuck rows, every one a delivered/read ACK the admin's
    client automatically sends back for a message the registrar sent."""

    async def test_ack_to_registrar_not_buffered(self, tmp_path):
        admin_identity = CellIdentity.generate("Admin")
        node = await make_admin_node(tmp_path, 50, admin_cell_ids=[admin_identity.cell_id])
        await node.start()
        try:
            admin_client = CellClient(admin_identity)
            await node.storage._admit_cell(admin_identity.cell_id, "test")
            await admin_client.connect(addr_of(node))
            await asyncio.sleep(0.1)

            await node.send_message(
                f"{admin_identity.cell_id}@{node.identity.node_id}",
                b"hello from registrar",
                from_cell_id=node._registrar_identity.cell_id,
            )
            await asyncio.sleep(0.2)  # let the client's automatic "delivered" ack round-trip

            buffered = await node.storage.get_buffered(node._registrar_identity.cell_id)
            assert buffered == []
            # The ACK's own bookkeeping (clearing the admin's inflight tracking) must
            # still run even though its destination gets dropped — only the trailing
            # route() is skipped, not the accounting that happens before it.
            assert admin_identity.cell_id not in node.router._inflight
            await admin_client.disconnect()
        finally:
            await node.stop()

    async def test_react_to_registrar_not_buffered(self, tmp_path):
        admin_identity = CellIdentity.generate("Admin")
        node = await make_admin_node(tmp_path, 51, admin_cell_ids=[admin_identity.cell_id])
        await node.start()
        try:
            await node.storage._admit_cell(admin_identity.cell_id, "test")
            admin_client = CellClient(admin_identity)
            await admin_client.connect(addr_of(node))
            await asyncio.sleep(0.1)

            react_pkt = Packet(
                type=T.REACT,
                payload=encode_payload({"message_id": "abc123", "emoji": "👍"}),
                from_addr=f"{admin_identity.cell_id}@{node.identity.node_id}",
                to_addr=f"{node._registrar_identity.cell_id}@{node.identity.node_id}",
            )
            sign_packet(react_pkt, admin_identity.signing)
            await admin_client._ws.send(pack(react_pkt))
            await asyncio.sleep(0.15)

            buffered = await node.storage.get_buffered(node._registrar_identity.cell_id)
            assert buffered == []
            await admin_client.disconnect()
        finally:
            await node.stop()

    async def test_offline_notice_for_registrars_own_send_not_buffered(self, tmp_path):
        """The other half of this dead-letter class, found 2026-09-19 on node1: a
        message the REGISTRAR sends to an admin who happens to be offline right now
        triggers router._notify_offline, which builds its own ACK{status:"offline"}
        and calls route() DIRECTLY — never through node.py's _dispatch, so the
        MSG-arrival-time guard in _maybe_handle_registrar_reply/_dispatch never even
        runs for it. That notice, addressed back to the registrar as the original
        sender, buffered forever the same way. 3 real stuck rows were exactly this."""
        admin_identity = CellIdentity.generate("Admin")
        node = await make_admin_node(tmp_path, 52, admin_cell_ids=[admin_identity.cell_id])
        await node.start()
        try:
            # Admitted, but never actually connects — presence lookup finds nothing,
            # which is what makes router.route() take the "buffer + _notify_offline"
            # path in the first place.
            await node.storage._admit_cell(admin_identity.cell_id, "test")
            await node.register_cell_locally(
                admin_identity.cell_id, admin_identity.signing.public,
                admin_identity.encryption.public, display_name="Admin",
            )

            await node.send_message(
                f"{admin_identity.cell_id}@{node.identity.node_id}",
                b"New join request from Someone",
                from_cell_id=node._registrar_identity.cell_id,
            )
            await asyncio.sleep(0.1)

            # The real message to the (offline) admin still buffers normally —
            # only the registrar-addressed "offline" notice about it should be dropped.
            admin_buffered = await node.storage.get_buffered(admin_identity.cell_id)
            assert len(admin_buffered) == 1
            registrar_buffered = await node.storage.get_buffered(node._registrar_identity.cell_id)
            assert registrar_buffered == []
        finally:
            await node.stop()


class TestJoinRequestResolvedSignal:
    """A request can realistically sit pending for days — approve_join_request's plain
    alert push and the client's own foreground retry cover the "applicant is offline by
    then" case, but if they happen to still be connected at the exact moment a decision
    is made, JOIN_REQUEST_RESOLVED reaches them immediately over that same connection
    instead of leaving them to find out later. See node.py's
    _notify_join_request_resolved."""

    async def test_approve_notifies_still_connected_applicant(self, tmp_path):
        node = await make_admin_node(tmp_path, 40)
        await node.start()
        try:
            resolved: list = []
            requester = CellIdentity.generate("Guest")
            client = CellClient(requester, on_join_request_resolved=lambda ok: resolved.append(ok))
            await client.connect(addr_of(node))
            await asyncio.sleep(0.1)

            req = make_join_request(client.cell_id, node.identity.node_id, display_name="Anechka")
            sign_packet(req, client.identity.signing)
            await client._ws.send(pack(req))
            await asyncio.sleep(0.15)

            ok = await node.approve_join_request(client.cell_id)
            await asyncio.sleep(0.15)

            assert ok
            assert resolved == [True]
        finally:
            await client.disconnect()
            await node.stop()

    async def test_deny_notifies_still_connected_applicant(self, tmp_path):
        node = await make_admin_node(tmp_path, 41)
        await node.start()
        try:
            resolved: list = []
            requester = CellIdentity.generate("Guest")
            client = CellClient(requester, on_join_request_resolved=lambda ok: resolved.append(ok))
            await client.connect(addr_of(node))
            await asyncio.sleep(0.1)

            req = make_join_request(client.cell_id, node.identity.node_id, display_name="Anechka")
            sign_packet(req, client.identity.signing)
            await client._ws.send(pack(req))
            await asyncio.sleep(0.15)

            ok = await node.deny_join_request(client.cell_id)
            await asyncio.sleep(0.15)

            assert ok
            assert resolved == [False]
        finally:
            await client.disconnect()
            await node.stop()

    async def test_approve_no_error_when_applicant_already_disconnected(self, tmp_path):
        """Best-effort only — must not raise or change behavior just because send_to()
        finds nobody connected (the realistic common case for a days-old request)."""
        node = await make_admin_node(tmp_path, 42)
        await node.start()
        try:
            client = await connect_pending(node)
            req = make_join_request(client.cell_id, node.identity.node_id)
            sign_packet(req, client.identity.signing)
            await client._ws.send(pack(req))
            await asyncio.sleep(0.15)
            await client.disconnect()
            await asyncio.sleep(0.1)

            ok = await node.approve_join_request(client.cell_id)

            assert ok
            assert await node.storage.is_cell_allowed(client.cell_id)
        finally:
            await node.stop()


class TestRegistrarChatCommands:
    """approve/deny typed directly in the "Node Registrar" chat — an alternative
    to the admin panel's Заявки на подключение page. Registrar has no live
    client of its own; node.py decrypts/replies in-process using the identity's
    own private key (_ensure_registrar) rather than routing/buffering these like
    an ordinary cell-to-cell message."""

    async def _setup(self, tmp_path, offset: int, n_admins: int = 1):
        admin_identity = CellIdentity.generate("Admin")
        node = await make_admin_node(tmp_path, offset, admin_cell_ids=[admin_identity.cell_id])
        await node.start()
        received: list = []
        admin_client = CellClient(admin_identity, on_message=lambda f, m: received.append(m))
        await node.storage._admit_cell(admin_identity.cell_id, "test")
        await admin_client.connect(addr_of(node))
        await asyncio.sleep(0.1)
        return node, admin_client, received

    async def _submit_request(self, node: Node, name: str, note: str = "") -> str:
        requester = await connect_pending(node)
        try:
            req = make_join_request(requester.cell_id, node.identity.node_id,
                                     note=note, display_name=name)
            sign_packet(req, requester.identity.signing)
            await requester._ws.send(pack(req))
            await asyncio.sleep(0.15)
        finally:
            await requester.disconnect()
        return requester.cell_id

    async def _send_to_registrar(self, admin_client: CellClient, node: Node, text: str):
        await admin_client.send(
            node._registrar_identity.cell_id, node.identity.node_id,
            node._registrar_identity.encryption.public, text.encode("utf-8"),
        )
        await asyncio.sleep(0.15)

    async def test_approve_via_chat_admits_and_replies(self, tmp_path):
        node, admin_client, received = await self._setup(tmp_path, 30)
        try:
            cell_id = await self._submit_request(node, "Anechka")
            received.clear()

            await self._send_to_registrar(admin_client, node, "approve")

            assert await node.storage.is_cell_allowed(cell_id)
            assert len(received) == 1
            assert "одобрена" in received[0].decode("utf-8")
        finally:
            await admin_client.disconnect()
            await node.stop()

    async def test_approve_via_casual_synonym(self, tmp_path):
        """A real admin typed "Ok" expecting it to work and it silently didn't (2026-09-18)
        — only the bare protocol word was recognized. The verb set is now deliberately
        generous; "ok" is the exact word that failed in the field."""
        node, admin_client, received = await self._setup(tmp_path, 35)
        try:
            cell_id = await self._submit_request(node, "Anechka")
            received.clear()

            await self._send_to_registrar(admin_client, node, "Ok")

            assert await node.storage.is_cell_allowed(cell_id)
            assert len(received) == 1
            assert "одобрена" in received[0].decode("utf-8")
        finally:
            await admin_client.disconnect()
            await node.stop()

    async def test_deny_via_chat_does_not_admit(self, tmp_path):
        node, admin_client, received = await self._setup(tmp_path, 31)
        try:
            cell_id = await self._submit_request(node, "Anechka")
            received.clear()

            await self._send_to_registrar(admin_client, node, "deny")

            assert not await node.storage.is_cell_allowed(cell_id)
            assert len(received) == 1
            assert "отклонена" in received[0].decode("utf-8")
        finally:
            await admin_client.disconnect()
            await node.stop()

    async def test_non_admin_reply_ignored(self, tmp_path):
        node = await make_admin_node(tmp_path, 32, admin_cell_ids=["someone_else"])
        await node.start()
        try:
            cell_id = await self._submit_request(node, "Anechka")

            stranger = await connect_pending(node)
            try:
                await stranger.send(
                    node._registrar_identity.cell_id, node.identity.node_id,
                    node._registrar_identity.encryption.public, b"approve",
                )
                await asyncio.sleep(0.15)
            finally:
                await stranger.disconnect()

            assert not await node.storage.is_cell_allowed(cell_id)
        finally:
            await node.stop()

    async def test_ambiguous_multiple_pending_lists_them_without_acting(self, tmp_path):
        node, admin_client, received = await self._setup(tmp_path, 33)
        try:
            cell1 = await self._submit_request(node, "Anechka")
            cell2 = await self._submit_request(node, "Boris")
            received.clear()

            await self._send_to_registrar(admin_client, node, "approve")

            assert not await node.storage.is_cell_allowed(cell1)
            assert not await node.storage.is_cell_allowed(cell2)
            assert len(received) == 1
            text = received[0].decode("utf-8")
            assert "Anechka" in text and "Boris" in text
        finally:
            await admin_client.disconnect()
            await node.stop()

    async def test_approve_with_prefix_disambiguates(self, tmp_path):
        node, admin_client, received = await self._setup(tmp_path, 34)
        try:
            cell1 = await self._submit_request(node, "Anechka")
            cell2 = await self._submit_request(node, "Boris")
            received.clear()

            await self._send_to_registrar(admin_client, node, f"approve {cell1[:8]}")

            assert await node.storage.is_cell_allowed(cell1)
            assert not await node.storage.is_cell_allowed(cell2)
        finally:
            await admin_client.disconnect()
            await node.stop()


class TestNackCarriesInviteMode:
    """The iOS client (Phase 2) needs to tell delegated from admin apart to decide
    whether offering "Request access" makes sense at all — both modes NACK
    identically otherwise. See DISCUSS_REGISTRATION_CHANNEL.md."""

    async def _capture_nack_payload(self, node: Node) -> dict:
        captured = {}
        orig_send_via = node.transport.send_via

        async def spy(conn, packet):
            if packet.type == T.CELL_REGISTER_NACK:
                captured["payload"] = decode_payload(packet.payload)
            await orig_send_via(conn, packet)

        node.transport.send_via = spy
        client = await connect_pending(node)
        await client.disconnect()
        return captured.get("payload", {})

    async def test_admin_mode_included_in_nack(self, tmp_path):
        node = await make_admin_node(tmp_path, 4)
        await node.start()
        try:
            payload = await self._capture_nack_payload(node)
            assert payload.get("reason") == "invite_required"
            assert payload.get("invite_mode") == "admin"
        finally:
            await node.stop()

    async def test_delegated_mode_included_in_nack(self, tmp_path):
        address = addr(5)
        id_path = str(tmp_path / "n5.json")
        db_path = str(tmp_path / "n5.db")
        idt = NodeIdentity.generate(address, invite_mode="delegated")
        idt.save(id_path)
        node = await Node.create(id_path, db_path)
        await node.start()
        try:
            payload = await self._capture_nack_payload(node)
            assert payload.get("invite_mode") == "delegated"
        finally:
            await node.stop()


class TestMemberAddedBroadcast:
    """A member already connected before someone else joins only ever re-fetched
    the node's member list on its OWN next reconnect (fetchNodeMembers() runs on
    that transition alone) — a just-admitted member could stay invisible to
    everyone already online for minutes, even though the new member's own client
    sees a fully populated list immediately. Confirmed on device 2026-09-23: a new member
    was admitted and saw everyone right away, but the admin (already connected)
    didn't see them until their first message happened to coincide with
    the admin's next periodic reconnect. Node._broadcast_member_added closes this by
    nudging already-connected home cells the moment a genuinely new cell registers."""

    async def test_new_member_registering_notifies_already_connected_members(self, tmp_path):
        admin_identity = CellIdentity.generate("Admin")
        node = await make_admin_node(tmp_path, 70, admin_cell_ids=[admin_identity.cell_id])
        await node.start()
        admin_client = newcomer_client = None
        try:
            await node.storage._admit_cell(admin_identity.cell_id, "test")
            received: list = []
            admin_client = CellClient(admin_identity, on_message=lambda f, m: received.append(m))
            await admin_client.connect(addr_of(node))
            await asyncio.sleep(0.1)

            newcomer_identity = CellIdentity.generate("Newcomer")
            await node.storage._admit_cell(newcomer_identity.cell_id, "test")
            newcomer_client = CellClient(newcomer_identity)
            await newcomer_client.connect(addr_of(node))
            await asyncio.sleep(0.15)

            assert len(received) == 1
            assert received[0].decode("utf-8") == f"member_added:{newcomer_identity.cell_id}"
        finally:
            if admin_client:
                await admin_client.disconnect()
            if newcomer_client:
                await newcomer_client.disconnect()
            await node.stop()

    async def test_reconnect_of_existing_member_does_not_notify(self, tmp_path):
        """register_cell is an upsert — a plain reconnect of someone already known
        must NOT re-announce them as new (would spam every reconnect cycle)."""
        admin_identity = CellIdentity.generate("Admin")
        node = await make_admin_node(tmp_path, 71, admin_cell_ids=[admin_identity.cell_id])
        await node.start()
        admin_client = other_client = None
        try:
            await node.storage._admit_cell(admin_identity.cell_id, "test")
            received: list = []
            admin_client = CellClient(admin_identity, on_message=lambda f, m: received.append(m))
            await admin_client.connect(addr_of(node))
            await asyncio.sleep(0.1)

            other_identity = CellIdentity.generate("Other")
            await node.storage._admit_cell(other_identity.cell_id, "test")
            other_client = CellClient(other_identity)
            await other_client.connect(addr_of(node))
            await asyncio.sleep(0.15)
            received.clear()

            await other_client.disconnect()
            await asyncio.sleep(0.1)
            other_client = CellClient(other_identity)
            await other_client.connect(addr_of(node))
            await asyncio.sleep(0.15)

            assert received == []
        finally:
            if admin_client:
                await admin_client.disconnect()
            if other_client:
                await other_client.disconnect()
            await node.stop()
