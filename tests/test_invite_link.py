"""Cell invite codes: 24 h default lifetime, admin-selectable lifetime, https link form.

Device test 2026-10-16: a code that lived 10 minutes was useless for inviting a person, and
the admin QR held a bare "ADDRESS|FP|CODE" token the phone's own camera could do nothing with.
"""

import time
from urllib.parse import unquote

from node.protocol import (CELL_INVITE_LINK_BASE, make_cell_invite_link,
                           make_cell_invite_token, parse_cell_invite_token)
from node.storage import CELL_INVITE_TTL_SECS

from tests.test_admin import _auth_header, _client


class TestInviteLink:
    def test_link_round_trips_token(self):
        token = make_cell_invite_token("kitaevo.nevod.network/nevod-ws", "", "AB12-CD34")
        link = make_cell_invite_link(token)
        assert link.startswith(CELL_INVITE_LINK_BASE)
        assert "|" not in link
        assert parse_cell_invite_token(unquote(link[len(CELL_INVITE_LINK_BASE):])) == (
            "kitaevo.nevod.network/nevod-ws", "", "AB12-CD34")


class TestInviteTtl:
    async def test_default_ttl_is_24h(self, storage):
        await storage.create_invite(created_by="admin")
        [inv] = await storage.list_invites()
        assert inv.expires_at - inv.created_at == CELL_INVITE_TTL_SECS == 24 * 3600

    async def test_admin_creates_with_chosen_ttl_and_link(self, genesis_node):
        client = await _client(genesis_node)
        try:
            r = await client.post("/nevod-admin/api/invites", json={"ttl_secs": 7 * 24 * 3600},
                                  headers=_auth_header())
            data = await r.json()
            assert data["ok"] is True
            assert data["link"].startswith(CELL_INVITE_LINK_BASE)
            assert abs(data["expires_at"] - (time.time() + 7 * 24 * 3600)) < 5
            r = await client.get("/nevod-admin/api/invites", headers=_auth_header())
            [inv] = (await r.json())["invites"]
            assert inv["code"] == data["code"]
            assert inv["link"] == data["link"]
            assert inv["expires_at"] - inv["created_at"] == 7 * 24 * 3600
        finally:
            await client.close()

    async def test_admin_without_body_uses_default(self, genesis_node):
        client = await _client(genesis_node)
        try:
            r = await client.post("/nevod-admin/api/invites", headers=_auth_header())
            data = await r.json()
            assert data["ok"] is True
            assert abs(data["expires_at"] - (time.time() + CELL_INVITE_TTL_SECS)) < 5
        finally:
            await client.close()

    async def test_admin_rejects_unlisted_ttl(self, genesis_node):
        client = await _client(genesis_node)
        try:
            r = await client.post("/nevod-admin/api/invites", json={"ttl_secs": 10 ** 9},
                                  headers=_auth_header())
            assert r.status == 400
        finally:
            await client.close()
