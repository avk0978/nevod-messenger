"""Blocking (chat_blocks / Router.route drop) and reserved display names (node/names.py) —
App Store Guideline 1.2 prep, 2026-09-28."""

import time

import pytest

from node.names import is_reserved_name
from node.protocol import Packet, T, encode_payload
from node.storage import NodeEntry
from tests.test_node import make_node


class TestReservedNames:
    @pytest.mark.parametrize("name", [
        "administrator", "Administrator", "ADMIN", "Ad.Min", "adm1n", "admln",
        "Аdmin",            # Cyrillic А
        "аdміn",            # mixed Cyrillic а/і
        "администратор", "Админ", "адмін", "модератор", "Поддержка", "підтримка",
        "Nevod Support", "nevod", "Невод", "Node Registrar", "official", "𝐚𝐝𝐦𝐢𝐧",
        "Официальный", "офіційний", "Реєстратор",
    ])
    def test_reserved(self, name):
        assert is_reserved_name(name)

    @pytest.mark.parametrize("name", [
        "Andrey", "Anna", "Котик 💥❤️", "Солнышко", "Oleg", "Maria", "", "   ", "😀",
    ])
    def test_not_reserved(self, name):
        assert not is_reserved_name(name)


class TestBlockStorage:
    async def test_set_and_clear(self, storage):
        assert not await storage.is_blocked("owner", "sender")
        await storage.set_blocked("owner", "sender", True)
        assert await storage.is_blocked("owner", "sender")
        # direction matters: owner blocking sender doesn't block the reverse
        assert not await storage.is_blocked("sender", "owner")
        await storage.set_blocked("owner", "sender", False)
        assert not await storage.is_blocked("owner", "sender")

    async def test_block_does_not_touch_sound_pref(self, storage):
        await storage.set_sound_enabled("owner", "sender", False)
        await storage.set_blocked("owner", "sender", True)
        await storage.set_blocked("owner", "sender", False)
        assert not await storage.get_sound_enabled("owner", "sender")


async def _two_cells(n):
    from node.crypto import gen_signing, gen_encryption
    rs, re_ = gen_signing(), gen_encryption()
    ss, se = gen_signing(), gen_encryption()
    recipient, sender = rs.public.hex(), ss.public.hex()
    await n.register_cell_locally(recipient, rs.public, re_.public)
    await n.register_cell_locally(sender, ss.public, se.public)
    # recipient offline on an unreachable node → an unblocked packet gets buffered + pushed
    await n.storage.update_presence(recipient, "ghost_node_id", None)
    await n.storage.upsert_node(NodeEntry(
        node_id="ghost_node_id", address="1.2.3.4:9999", status="offline",
        last_seen=int(time.time()) - 1000, added_at=int(time.time()),
    ))
    await n.storage.save_push_token(recipient, "fake-device-token")
    return recipient, sender


class TestRouterDropsBlocked:
    async def test_blocked_sender_dropped_no_buffer_no_push(self, tmp_path):
        n = await make_node(tmp_path, 61, genesis=True)
        await n.start()
        try:
            recipient, sender = await _two_cells(n)
            pushes = []

            class FakeApns:
                async def send(self, token, **kwargs):
                    pushes.append(token)
                    return True

                async def send_voip(self, token, **kwargs):
                    pushes.append(("voip", token))
                    return True

            n.apns = FakeApns()
            await n.storage.set_blocked(recipient, sender, True)

            for t in (T.MSG, T.MSG_SILENT, T.REACT, T.VCALL_OFFER, T.VCALL_SIGNAL):
                await n.router.route(Packet(type=t, payload=b"blob",
                                            from_addr=f"{sender}@{n.identity.node_id}",
                                            to_addr=f"{recipient}@ghost_node_id"))
            assert await n.storage.get_buffered(recipient) == []
            assert pushes == []
            # the sender got a generic "failed" ack for each message-type packet (not calls)
            from node.router import _deserialize_packet
            from node.protocol import decode_payload
            acks = [decode_payload(_deserialize_packet(b.payload).payload)["status"]
                    for b in await n.storage.get_buffered(sender)]
            assert acks == ["failed", "failed"]  # MSG and MSG_SILENT

            # unblock → the same message goes through normally again
            await n.storage.set_blocked(recipient, sender, False)
            await n.router.route(Packet(type=T.MSG, payload=b"blob",
                                        from_addr=f"{sender}@{n.identity.node_id}",
                                        to_addr=f"{recipient}@ghost_node_id"))
            assert len(await n.storage.get_buffered(recipient)) == 1
            assert pushes == ["fake-device-token"]
        finally:
            await n.stop()

    async def test_chat_prefs_block_only_keeps_sound(self, tmp_path):
        """A {"blocked": ...} update must not reset the sound pref (the old handler defaulted
        sound_enabled=True whenever the key was missing)."""
        n = await make_node(tmp_path, 62, genesis=True)
        await n.start()
        try:
            class FakeConn:
                peer_node_id = "aa" * 32

            def prefs(d):
                return Packet(type=T.CHAT_PREFS, payload=encode_payload(d),
                              from_addr=f"{'aa' * 32}@{n.identity.node_id}",
                              to_addr=n.identity.node_id)

            await n._handle_chat_prefs(prefs({"peer_cell_id": "bb" * 32, "sound_enabled": False}), FakeConn())
            await n._handle_chat_prefs(prefs({"peer_cell_id": "bb" * 32, "blocked": True}), FakeConn())
            assert await n.storage.is_blocked("aa" * 32, "bb" * 32)
            assert not await n.storage.get_sound_enabled("aa" * 32, "bb" * 32)
        finally:
            await n.stop()


class TestReservedNameRegistration:
    async def _register(self, n, sign, enc, name, nacks):
        class FakeConn:
            peer_signing_pubkey = sign.public
            peer_node_id = sign.public.hex()

        pkt = Packet(type=T.CELL_REGISTER, payload=encode_payload({
            "cell_id": sign.public.hex(), "signing_pubkey": sign.public,
            "enc_pubkey": enc.public, "is_home": True, "display_name": name,
        }), from_addr=sign.public.hex(), to_addr=n.identity.node_id)
        await n._handle_cell_register(pkt, FakeConn())

    async def test_new_reserved_name_rejected_but_official_and_existing_allowed(self, tmp_path, monkeypatch):
        from node.crypto import gen_signing, gen_encryption
        n = await make_node(tmp_path, 63, genesis=True)
        await n.start()
        try:
            nacks = []

            async def fake_nack(conn, reason, extra=None):
                nacks.append(reason)

            n._send_nack = fake_nack

            # 1. ordinary user asking for "administrator" → name_taken, not registered
            impostor, impostor_enc = gen_signing(), gen_encryption()
            await self._register(n, impostor, impostor_enc, "Administrator", nacks)
            assert nacks == ["name_taken"]
            assert await n.storage.get_cell(impostor.public.hex()) is None

            # 2. the official cell (NEVOD_OFFICIAL_CELL_IDS) may use a reserved name — not
            #    "administrator" itself any more: every node's built-in administrator cell
            #    (_ensure_administrator) already holds that one.
            official, official_enc = gen_signing(), gen_encryption()
            monkeypatch.setenv("NEVOD_OFFICIAL_CELL_IDS", official.public.hex())
            await self._register(n, official, official_enc, "support", nacks)
            assert nacks == ["name_taken"]
            cell = await n.storage.get_cell(official.public.hex())
            assert cell is not None and cell.display_name == "support"

            # 3. a cell already registered under a reserved-looking name (before this check
            #    existed) keeps reconnecting with it — no lockout
            legacy, legacy_enc = gen_signing(), gen_encryption()
            await n.register_cell_locally(legacy.public.hex(), legacy.public, legacy_enc.public,
                                          display_name="nevod_mirror_bot")
            await self._register(n, legacy, legacy_enc, "nevod_mirror_bot", nacks)
            assert nacks == ["name_taken"]
            # …but can't rename itself to a different reserved name
            await self._register(n, legacy, legacy_enc, "admin", nacks)
            assert nacks == ["name_taken", "name_taken"]
        finally:
            await n.stop()


class TestOfficialSignature:
    def test_sign_verify_and_domain_separation(self):
        from node.crypto import gen_signing, signing_priv_to_bytes
        from node.curator_sign import sign_official, verify_official, sign_entry, verify_entry
        kp = gen_signing()
        priv, pub = signing_priv_to_bytes(kp.private).hex(), kp.public.hex()
        cell = "ab" * 32
        sig = sign_official(cell, "administrator", priv)
        assert verify_official(cell, "administrator", sig, pub)
        assert not verify_official("cd" * 32, "administrator", sig, pub)
        # a node-entry signature must never pass as an official-account one
        node_sig = sign_entry(cell, "administrator", "", "informational", priv)
        assert not verify_official(cell, "administrator", node_sig, pub)
        # enc_pub/node_id are covered by the signature — swapping the key must fail
        sig2 = sign_official(cell, "administrator", priv, "ee" * 32, "ff" * 32)
        assert verify_official(cell, "administrator", sig2, pub, "ee" * 32, "ff" * 32)
        assert not verify_official(cell, "administrator", sig2, pub, "dd" * 32, "ff" * 32)
