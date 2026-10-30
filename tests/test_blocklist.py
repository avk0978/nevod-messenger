"""
The curator-signed project node blocklist (node/blocklist.py, Node.apply_project_blocklist,
curator_sign sign-blocklist, panel "Общий список блокировки проекта Nevod").
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

import node.blocklist as blocklist
from node.crypto import gen_signing, sign, signing_priv_to_bytes
from node.identity import NodeIdentity
from node.node import Node
from node.storage import NodeEntry

BAD = "bb" * 32
WORSE = "cc" * 32
ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def curator(monkeypatch):
    kp = gen_signing()
    monkeypatch.setattr(blocklist, "CURATOR_PUBKEY_HEX", kp.public.hex())
    return kp


def signed(kp, version: int, nodes: dict) -> dict:
    return {"version": version,
            "nodes": [{"node_id": k, "reason": v} for k, v in nodes.items()],
            "sig": sign(blocklist.canonical_message(version, nodes), kp).hex()}


async def make_node(tmp_path) -> Node:
    id_path = str(tmp_path / "n.json")
    NodeIdentity.generate("127.0.0.1:19870").save(id_path)
    return await Node.create(id_path, str(tmp_path / "n.db"))


async def add(node: Node, node_id: str):
    now = int(time.time())
    await node.storage.upsert_node(NodeEntry(node_id=node_id, address="6.6.6.6:8765",
                                             last_seen=now, added_at=now))


def test_curator_key_matches_the_app():
    swift = (ROOT / "ios/Nevod/Nevod/NodeManifest.swift").read_text()
    key = re.search(r'curatorPublicKeyHex =\s*"([0-9a-f]{64})"', swift).group(1)
    assert key == blocklist.CURATOR_PUBKEY_HEX


def test_published_file_is_well_formed():
    doc = json.loads((ROOT / "manifests/blocked_nodes.json").read_text())
    assert blocklist.parse(doc) is not None


class TestVerify:
    def test_signed_accepted(self, curator):
        assert blocklist.verify_doc(signed(curator, 5, {BAD: "spam"})) == (5, {BAD: "spam"})

    def test_dropped_entry_or_changed_version_rejected(self, curator):
        doc = signed(curator, 5, {BAD: "spam", WORSE: "abuse"})
        assert blocklist.verify_doc({**doc, "nodes": doc["nodes"][:1]}) is None
        assert blocklist.verify_doc({**doc, "version": 6}) is None

    def test_other_key_or_malformed_rejected(self, curator):
        assert blocklist.verify_doc(signed(gen_signing(), 5, {BAD: "spam"})) is None
        assert blocklist.verify_doc({"version": 1, "nodes": [{"node_id": "xyz"}], "sig": "00"}) is None
        assert blocklist.verify_doc({"version": 1, "nodes": [], "sig": ""}) is None


class TestApply:
    async def test_newer_only_and_cut_off_when_on(self, tmp_path, curator):
        node = await make_node(tmp_path)
        await node.set_project_blocklist("on")
        await add(node, BAD)
        assert await node.apply_project_blocklist(signed(curator, 5, {BAD: "spam"}))
        assert node.is_node_blocked(BAD) and await node.storage.get_node(BAD) is None
        # replaying an older (or the same) version can't lift the block
        assert not await node.apply_project_blocklist(signed(curator, 4, {}))
        assert not await node.apply_project_blocklist(signed(curator, 5, {}))
        assert node.is_node_blocked(BAD)
        # a newer list without it does
        assert await node.apply_project_blocklist(signed(curator, 6, {}))
        assert not node.is_node_blocked(BAD)

    async def test_off_by_default_on_a_private_node(self, tmp_path, curator):
        node = await make_node(tmp_path)
        assert not node.project_blocklist_on()   # not a project node
        await add(node, BAD)
        await node.apply_project_blocklist(signed(curator, 5, {BAD: "spam"}))
        assert not node.is_node_blocked(BAD) and await node.storage.get_node(BAD) is not None
        # switching it on cuts the listed node off at once
        await node.set_project_blocklist("on")
        assert node.is_node_blocked(BAD) and await node.storage.get_node(BAD) is None

    async def test_project_node_default_on(self, tmp_path, monkeypatch):
        node = await make_node(tmp_path)
        monkeypatch.setattr("node.node.PROJECT_RELAY_NODE_IDS", frozenset({node.identity.node_id}))
        assert node.project_blocklist_on()
        await node.set_project_blocklist("off")
        assert not node.project_blocklist_on()

    async def test_own_node_never_cut_off(self, tmp_path, curator):
        node = await make_node(tmp_path)
        await node.set_project_blocklist("on")
        await node.apply_project_blocklist(signed(curator, 5, {node.identity.node_id: "x"}))
        assert not node.is_node_blocked(node.identity.node_id)

    async def test_kept_across_restart(self, tmp_path, curator):
        node = await make_node(tmp_path)
        await node.set_project_blocklist("on")
        await node.apply_project_blocklist(signed(curator, 5, {BAD: "spam"}))
        await node.storage.close()
        again = await Node.create(str(tmp_path / "n.json"), str(tmp_path / "n.db"))
        await again.start()
        try:
            assert again.project_blocklist_version == 5 and again.is_node_blocked(BAD)
        finally:
            await again.stop()


def test_curator_sign_blocklist_cli(tmp_path, monkeypatch):
    kp = gen_signing()
    key = tmp_path / "key.json"
    key.write_text(json.dumps({"private_key": signing_priv_to_bytes(kp.private).hex()}))
    lst = tmp_path / "blocked_nodes.json"
    lst.write_text(json.dumps({"version": 0, "nodes": [{"node_id": BAD.upper(), "reason": "spam"}],
                               "sig": ""}))
    subprocess.run([sys.executable, "-m", "node.curator_sign", "sign-blocklist",
                    "--privkey-file", str(key), "--list", str(lst)], check=True, cwd=ROOT,
                   capture_output=True)
    doc = json.loads(lst.read_text())
    v1 = doc["version"]
    assert blocklist.verify_doc(doc, kp.public.hex()) == (v1, {BAD: "spam"})
    subprocess.run([sys.executable, "-m", "node.curator_sign", "sign-blocklist",
                    "--privkey-file", str(key), "--list", str(lst)], check=True, cwd=ROOT,
                   capture_output=True)
    assert json.loads(lst.read_text())["version"] > v1   # always moves up


async def test_panel_toggle(genesis_node):
    import base64
    from aiohttp.test_utils import TestClient, TestServer
    from node.admin import AdminServer
    auth = {"Authorization": "Basic " + base64.b64encode(b":pw").decode()}
    client = TestClient(TestServer(AdminServer(genesis_node, password="pw")._make_app()))
    await client.start_server()
    try:
        r = await client.get("/nevod-admin/api/blocked-nodes", headers=auth)
        assert (await r.json())["project"] == {"applied": False, "version": 0, "nodes": []}
        r = await client.post("/nevod-admin/api/project-blocklist", headers=auth, json={"mode": "on"})
        assert r.status == 200 and genesis_node.project_blocklist_on()
        r = await client.post("/nevod-admin/api/project-blocklist", headers=auth, json={"mode": "x"})
        assert r.status == 400
    finally:
        await client.close()
