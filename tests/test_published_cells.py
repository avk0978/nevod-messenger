"""
Tests for the admin-curated "published cells" discovery feature (the cell/moon
list under a node's planet on the "Explore Network" screen) — see
PublishedCellEntry in storage.py and Node._handle_node_cells_request.

Deliberately separate from the private `cells` table (every registered cell,
including ordinary users) — these tests exist specifically to pin down the
cells_visibility access-control behavior (off/members/public), since that's
the actual privacy-sensitive part of this feature.
"""

import asyncio
import pytest

from node.identity import NodeIdentity
from node.node import Node
from node.client import CellClient
from node.storage import PublishedCellEntry


BASE = 19600


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE + offset}"


async def make_node(tmp_path, offset: int, cells_visibility: str = "members") -> Node:
    address = addr(offset)
    id_path = str(tmp_path / f"n{offset}.json")
    db_path = str(tmp_path / f"n{offset}.db")
    idt = NodeIdentity.generate(address, access="open", cells_visibility=cells_visibility)
    idt.save(id_path)
    return await Node.create(id_path, db_path)


class TestStorage:
    async def test_publish_and_list(self, tmp_path):
        node = await make_node(tmp_path, 0)
        try:
            await node.storage.publish_cell("aa" * 32, "Tolmach", "Translator", "bot")
            await node.storage.publish_cell("bb" * 32, "About", "info", "page", "# Hi")
            cells = await node.storage.get_published_cells()
            assert {c.cell_id for c in cells} == {"aa" * 32, "bb" * 32}
            page = next(c for c in cells if c.cell_id == "bb" * 32)
            assert page.kind == "page"
            assert page.landing_md == "# Hi"
        finally:
            await node.storage.close()

    async def test_republish_updates_in_place(self, tmp_path):
        node = await make_node(tmp_path, 1)
        try:
            await node.storage.publish_cell("aa" * 32, "Old Name", "old desc", "bot")
            await node.storage.publish_cell("aa" * 32, "New Name", "new desc", "bot")
            cells = await node.storage.get_published_cells()
            assert len(cells) == 1
            assert cells[0].name == "New Name"
        finally:
            await node.storage.close()

    async def test_unpublish_removes(self, tmp_path):
        node = await make_node(tmp_path, 2)
        try:
            await node.storage.publish_cell("aa" * 32, "Tolmach", "", "bot")
            await node.storage.unpublish_cell("aa" * 32)
            assert await node.storage.get_published_cells() == []
        finally:
            await node.storage.close()

    async def test_delete_cell_also_unpublishes(self, tmp_path):
        node = await make_node(tmp_path, 3)
        try:
            await node.storage.register_cell("aa" * 32, b"\x01" * 32, b"\x02" * 32)
            await node.storage.publish_cell("aa" * 32, "Tolmach", "", "bot")
            await node.storage.delete_cell("aa" * 32)
            assert await node.storage.get_published_cells() == []
        finally:
            await node.storage.close()


class TestWireVisibility:
    async def test_public_visibility_answers_anyone(self, tmp_path):
        node = await make_node(tmp_path, 10, cells_visibility="public")
        await node.start()
        stranger = None
        try:
            from node.crypto import gen_signing, gen_encryption
            bot_sign, bot_enc = gen_signing(), gen_encryption()
            bot_id = bot_sign.public.hex()
            await node.register_cell_locally(bot_id, bot_sign.public, bot_enc.public)
            await node.storage.publish_cell(bot_id, "Tolmach", "Translator", "bot")

            from node.identity import CellIdentity
            stranger = CellClient(CellIdentity.generate("Stranger"))
            await stranger.connect(addr(10))
            cells = await stranger.get_node_cells()

            assert len(cells) == 1
            assert cells[0]["cell_id"] == bot_id
            assert cells[0]["name"] == "Tolmach"
            assert cells[0]["enc_pubkey"] == bot_enc.public
        finally:
            if stranger:
                await stranger.disconnect()
            await node.stop()

    async def test_members_visibility_allows_registered_member(self, tmp_path):
        # CellClient.connect() always sends CELL_REGISTER as part of connecting, so
        # a real client that successfully connects to this node IS by definition a
        # member — this is the ordinary case (e.g. browsing your own home node).
        node = await make_node(tmp_path, 11, cells_visibility="members")
        await node.start()
        member = None
        try:
            from node.crypto import gen_signing, gen_encryption
            bot_sign, bot_enc = gen_signing(), gen_encryption()
            bot_id = bot_sign.public.hex()
            await node.register_cell_locally(bot_id, bot_sign.public, bot_enc.public)
            await node.storage.publish_cell(bot_id, "Tolmach", "", "bot")

            from node.identity import CellIdentity
            member = CellClient(CellIdentity.generate("Member"))
            await member.connect(addr(11))
            cells = await member.get_node_cells()
            assert len(cells) == 1
        finally:
            if member:
                await member.disconnect()
            await node.stop()

    async def test_members_visibility_denies_non_member(self, tmp_path):
        # A real non-member can't be produced through CellClient (connect() always
        # registers) — so this drives Node._handle_node_cells_request directly with
        # a request "from" a cell_id that was never registered on this node, the
        # same shape a relayed/forged request would have.
        node = await make_node(tmp_path, 12, cells_visibility="members")
        await node.start()
        try:
            from node.crypto import gen_signing, gen_encryption
            bot_sign, bot_enc = gen_signing(), gen_encryption()
            bot_id = bot_sign.public.hex()
            await node.register_cell_locally(bot_id, bot_sign.public, bot_enc.public)
            await node.storage.publish_cell(bot_id, "Tolmach", "", "bot")

            sent = []

            async def fake_send_via(conn, pkt):
                sent.append(pkt)

            node.transport.send_via = fake_send_via

            class FakeConn:
                peer_node_id = "ff" * 32  # never registered on this node

            from node.protocol import Packet, T
            outsider_id = "ff" * 32
            req = Packet(type=T.NODE_CELLS_REQUEST, payload=b"",
                        from_addr=f"{outsider_id}@{node.identity.node_id}",
                        to_addr=node.identity.node_id)
            await node._handle_node_cells_request(req, FakeConn())
            assert sent == [], "non-member must get no response at all when cells_visibility='members'"
        finally:
            await node.stop()

    async def test_off_visibility_denies_everyone(self, tmp_path):
        node = await make_node(tmp_path, 13, cells_visibility="off")
        await node.start()
        member = None
        try:
            from node.crypto import gen_signing, gen_encryption
            bot_sign, bot_enc = gen_signing(), gen_encryption()
            bot_id = bot_sign.public.hex()
            await node.register_cell_locally(bot_id, bot_sign.public, bot_enc.public)
            await node.storage.publish_cell(bot_id, "Tolmach", "", "bot")

            from node.identity import CellIdentity
            member = CellClient(CellIdentity.generate("Member"))
            await member.connect(addr(13))
            cells = await member.get_node_cells(timeout=1.0)
            assert cells == [], "cells_visibility='off' must withhold the list even from members"
        finally:
            if member:
                await member.disconnect()
            await node.stop()

    async def test_unregistered_cell_dropped_from_response(self, tmp_path):
        """A published cell that's no longer actually registered (deleted, or
        published before ever registering) is silently skipped, not sent with a
        missing/garbage enc_pubkey."""
        node = await make_node(tmp_path, 14, cells_visibility="public")
        await node.start()
        stranger = None
        try:
            await node.storage.publish_cell("aa" * 32, "Ghost Bot", "", "bot")
            from node.identity import CellIdentity
            stranger = CellClient(CellIdentity.generate("Stranger"))
            await stranger.connect(addr(14))
            cells = await stranger.get_node_cells(timeout=1.0)
            assert cells == []
        finally:
            if stranger:
                await stranger.disconnect()
            await node.stop()

    async def test_page_kind_carries_landing_md_not_enc_pubkey(self, tmp_path):
        node = await make_node(tmp_path, 15, cells_visibility="public")
        await node.start()
        stranger = None
        try:
            await node.storage.publish_cell("aa" * 32, "About", "info page",
                                            "page", "# Hello\nWelcome.")
            from node.identity import CellIdentity
            stranger = CellClient(CellIdentity.generate("Stranger"))
            await stranger.connect(addr(15))
            cells = await stranger.get_node_cells()
            assert len(cells) == 1
            assert cells[0]["kind"] == "page"
            assert cells[0]["landing_md"] == "# Hello\nWelcome."
            assert "enc_pubkey" not in cells[0]
        finally:
            if stranger:
                await stranger.disconnect()
            await node.stop()


class TestByokAiBot:
    """BYOK AI bots: the operator ticks which providers a bot accepts the USER's key for;
    the app reads that from the node's cell list to offer "add your key" in the chat."""

    async def test_ai_providers_reach_the_app(self, tmp_path):
        node = await make_node(tmp_path, 16, cells_visibility="public")
        await node.start()
        stranger = None
        try:
            from node.crypto import gen_signing, gen_encryption
            from node.identity import CellIdentity
            ai_sign, ai_enc = gen_signing(), gen_encryption()
            echo_sign, echo_enc = gen_signing(), gen_encryption()
            await node.register_cell_locally(ai_sign.public.hex(), ai_sign.public, ai_enc.public)
            await node.register_cell_locally(echo_sign.public.hex(), echo_sign.public, echo_enc.public)
            await node.storage.publish_cell(ai_sign.public.hex(), "Tolmach", "", "bot",
                                            ai_providers=["anthropic", "gemini"])
            await node.storage.publish_cell(echo_sign.public.hex(), "Mirror", "", "bot")
            stranger = CellClient(CellIdentity.generate("Stranger"))
            await stranger.connect(addr(16))
            cells = {c["name"]: c for c in await stranger.get_node_cells()}
            assert cells["Tolmach"]["ai_providers"] == ["anthropic", "gemini"]
            assert "ai_providers" not in cells["Mirror"]
        finally:
            if stranger:
                await stranger.disconnect()
            await node.stop()

    async def test_admin_validates_providers(self, genesis_node):
        from tests.test_admin import _auth_header, _client
        client = await _client(genesis_node)
        try:
            ok = await client.post("/nevod-admin/api/published-cells", headers=_auth_header(),
                                   json={"cell_id": "aa" * 32, "name": "T", "kind": "bot",
                                         "ai_providers": ["gemini", "anthropic", "gemini"]})
            assert (await ok.json())["ok"] is True
            listed = await (await client.get("/nevod-admin/api/published-cells",
                                             headers=_auth_header())).json()
            assert listed["cells"][0]["ai_providers"] == ["anthropic", "gemini"]
            for bad in ({"kind": "bot", "ai_providers": ["grok"]},
                        {"kind": "page", "ai_providers": ["openai"]},
                        {"kind": "bot", "ai_providers": "openai"}):
                r = await client.post("/nevod-admin/api/published-cells", headers=_auth_header(),
                                      json={"cell_id": "bb" * 32, "name": "X", **bad})
                assert r.status == 400, bad
        finally:
            await client.close()
