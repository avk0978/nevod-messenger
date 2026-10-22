"""Smoke tests for the admin panel's HTTP surface — mainly guards against the
2026-09-13 six-page split (node/admin.py's _HTML monolith → _shell()/_NAV) ever
regressing into a page that 500s or drops a route, since nothing exercised the
admin HTTP layer at all before this.
"""

import base64

from aiohttp.test_utils import TestClient, TestServer

from node.admin import AdminServer, _hash_password, _verify_password

PASSWORD = "test-password"


def _auth_header():
    token = base64.b64encode(f":{PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def _client(genesis_node):
    server = AdminServer(genesis_node, password=PASSWORD)
    client = TestClient(TestServer(server._make_app()))
    await client.start_server()
    return client


class TestAdminPages:
    async def test_pages_require_auth(self, genesis_node):
        client = await _client(genesis_node)
        try:
            r = await client.get("/nevod-admin/")
            assert r.status == 401
        finally:
            await client.close()

    async def test_every_nav_page_renders(self, genesis_node):
        client = await _client(genesis_node)
        try:
            for path in ("/nevod-admin/", "/nevod-admin/settings",
                         "/nevod-admin/join-requests", "/nevod-admin/invites",
                         "/nevod-admin/nodes", "/nevod-admin/published",
                         "/nevod-admin/security", "/nevod-admin/diagnostics"):
                r = await client.get(path, headers=_auth_header())
                assert r.status == 200, path
                assert "text/html" in r.headers["Content-Type"]
                body = await r.text()
                assert "<title>Nevod Admin</title>" in body
                # Every page carries the full nav bar so the admin can jump
                # between sections without going back to the overview first.
                assert 'href="/nevod-admin/join-requests"' in body
        finally:
            await client.close()

    async def test_bare_nevod_admin_also_works(self, genesis_node):
        """No trailing slash — the original single-page route."""
        client = await _client(genesis_node)
        try:
            r = await client.get("/nevod-admin", headers=_auth_header())
            assert r.status == 200
        finally:
            await client.close()


class TestNodeType:
    async def test_set_node_type_persists_to_identity(self, genesis_node, tmp_path):
        assert genesis_node.identity.node_type == "permanent"
        client = await _client(genesis_node)
        try:
            r = await client.post("/nevod-admin/api/node-type", headers=_auth_header(),
                                  json={"node_type": "temporary"})
            assert r.status == 200
            data = await r.json()
            assert data["ok"] is True and data["restart_required"] is True
            assert genesis_node.identity.node_type == "temporary"
        finally:
            await client.close()

    async def test_set_node_type_rejects_bad_value(self, genesis_node):
        client = await _client(genesis_node)
        try:
            r = await client.post("/nevod-admin/api/node-type", headers=_auth_header(),
                                  json={"node_type": "nonsense"})
            assert r.status == 400
        finally:
            await client.close()


class TestNodeName:
    async def test_set_name_reflected_immediately(self, genesis_node):
        """Found 2026-09-13: there was no way to set this at all — a node with
        `name` unset showed its raw node_id everywhere, including on node1 which
        the user knows as "Dev Planet" but the panel never actually said so."""
        assert genesis_node.identity.name == ""
        client = await _client(genesis_node)
        try:
            r = await client.post("/nevod-admin/api/name", headers=_auth_header(),
                                  json={"name": "Dev Planet"})
            assert r.status == 200
            assert genesis_node.identity.name == "Dev Planet"

            r2 = await client.get("/nevod-admin/api/cells", headers=_auth_header())
            data = await r2.json()
            assert data["node_name"] == "Dev Planet"
        finally:
            await client.close()


class TestPasswordHashing:
    def test_hash_roundtrips_and_uses_a_real_salt(self):
        h1 = _hash_password("correct horse battery staple")
        h2 = _hash_password("correct horse battery staple")
        assert h1 != h2  # different random salt each time, even for the same password
        assert _verify_password("correct horse battery staple", h1)
        assert _verify_password("correct horse battery staple", h2)
        assert not _verify_password("wrong password", h1)
        assert h1.startswith("pbkdf2_sha256$")


class TestAdminUsers:
    async def test_add_list_login_with_new_admin_and_delete(self, genesis_node):
        client = await _client(genesis_node)
        try:
            r = await client.post("/nevod-admin/api/admins", headers=_auth_header(),
                                  json={"username": "anechka", "password": "verysecretpw"})
            assert r.status == 200

            # The new login actually works, unauthenticated with the ORIGINAL
            # password — this is the whole point of a per-admin account.
            new_auth = {"Authorization": "Basic " + base64.b64encode(
                b"anechka:verysecretpw").decode()}
            r2 = await client.get("/nevod-admin/api/admins", headers=new_auth)
            assert r2.status == 200
            data = await r2.json()
            usernames = [a["username"] for a in data["admins"]]
            assert "anechka" in usernames

            # Never leaks a hash or plaintext back out.
            body_text = await r2.text()
            assert "verysecretpw" not in body_text
            assert "pbkdf2_sha256" not in body_text

            r3 = await client.delete("/nevod-admin/api/admins/anechka", headers=_auth_header())
            assert r3.status == 200
            r4 = await client.get("/nevod-admin/api/admins", headers=_auth_header())
            data4 = await r4.json()
            assert "anechka" not in [a["username"] for a in data4["admins"]]

            # Deleted login no longer works.
            r5 = await client.get("/nevod-admin/api/admins", headers=new_auth)
            assert r5.status == 401
        finally:
            await client.close()

    async def test_rejects_short_password(self, genesis_node):
        client = await _client(genesis_node)
        try:
            r = await client.post("/nevod-admin/api/admins", headers=_auth_header(),
                                  json={"username": "x", "password": "short"})
            assert r.status == 400
        finally:
            await client.close()

    async def test_legacy_password_still_works_even_with_admins_list_populated(self, genesis_node):
        """The env/installer credential is a permanent break-glass login — adding
        per-admin accounts must never be able to lock it out."""
        client = await _client(genesis_node)
        try:
            await client.post("/nevod-admin/api/admins", headers=_auth_header(),
                              json={"username": "someone", "password": "anotherpassword1"})
            r = await client.get("/nevod-admin/api/cells", headers=_auth_header())
            assert r.status == 200
        finally:
            await client.close()


class TestParentNodeId:
    async def test_set_parent_node_id_persists_and_can_be_cleared(self, genesis_node):
        assert genesis_node.identity.parent_node_id == ""
        client = await _client(genesis_node)
        try:
            r = await client.post("/nevod-admin/api/parent-node-id", headers=_auth_header(),
                                  json={"parent_node_id": "deadbeef" * 8})
            assert r.status == 200
            assert genesis_node.identity.parent_node_id == "deadbeef" * 8

            r2 = await client.get("/nevod-admin/api/cells", headers=_auth_header())
            data = await r2.json()
            assert data["parent_node_id"] == "deadbeef" * 8

            # Empty string clears it back to "no parent".
            r3 = await client.post("/nevod-admin/api/parent-node-id", headers=_auth_header(),
                                   json={"parent_node_id": ""})
            assert r3.status == 200
            assert genesis_node.identity.parent_node_id == ""
        finally:
            await client.close()


class TestJoinRequestsPageData:
    async def test_join_requests_api_includes_display_name(self, genesis_node):
        """The 2026-09-13 fix: the admin previously had no way to see who was
        actually asking to join, only a bare cell_id — see node.py's
        _handle_join_request."""
        genesis_node.identity.invite_mode = "admin"
        await genesis_node.storage.create_join_request(
            "somecell", "sign", "enc", note="hi", display_name="Anechka")

        client = await _client(genesis_node)
        try:
            r = await client.get("/nevod-admin/api/join-requests", headers=_auth_header())
            assert r.status == 200
            data = await r.json()
            assert any(req["display_name"] == "Anechka" for req in data["requests"])
        finally:
            await client.close()
