"""AI bots run inside the node from the admin panel (node/ai_bots.py).

A bot created by the admin must come up as an ordinary cell of the node — over the node's
own port, so the user reaches it through the normal E2E path — answer on the user's key,
work on an invite-only node, and stop/vanish when the admin switches it off or deletes it.
The provider call is stubbed (no real API budget).
"""

import asyncio
import os

import pytest

from node.ai_bots import AIBotError, PRESETS
from node.bot import NevdBot, strip_prefixes, wrap_card
from node.client import CellClient
from node.identity import CellIdentity
from node.node import Node

BASE = 20500


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE + offset}"


@pytest.fixture
def fake_ai(monkeypatch):
    seen = []

    async def ask(self, cell_id, provider, key, text):
        seen.append((provider, key, text))
        return f"echo:{text}"
    monkeypatch.setattr(NevdBot, "_ask_ai", ask)
    return seen


class _User:
    def __init__(self, node: Node, offset: int):
        self.node, self.offset = node, offset
        self.identity = CellIdentity.generate(name="User")
        self.received = []
        self.client = CellClient(self.identity,
                                 on_message=lambda frm, pt: self.received.append(pt.decode()))

    async def say(self, bot_cell_id: str, bot_enc_pub: bytes, text: str):
        msg = wrap_card(self.identity.cell_id, addr(self.offset), self.node.identity.node_id,
                        self.identity.encryption.public, text)
        await self.client.send(bot_cell_id, self.node.identity.node_id, bot_enc_pub, msg.encode())

    async def wait(self, n=1):
        for _ in range(60):
            if len(self.received) >= n:
                return [strip_prefixes(t)[1] for t in self.received]
            await asyncio.sleep(0.1)
        raise AssertionError(f"got {len(self.received)} message(s), expected {n}")


async def _start(tmp_path, offset, invite_mode="open"):
    node = await Node.create_genesis(addr(offset), str(tmp_path / "n.json"),
                                     str(tmp_path / "n.db"), access="open")
    node.identity.invite_mode = invite_mode
    await node.start()
    return node


async def _wait_online(node, cell_id):
    for _ in range(60):
        if node.ai_bots.status(cell_id) == "online":
            return
        await asyncio.sleep(0.1)
    raise AssertionError(f"bot status {node.ai_bots.status(cell_id)}")


async def _bot_enc_pub(node, cell_id) -> bytes:
    cell = await node.storage.get_cell(cell_id)
    return bytes(cell.enc_pubkey)


async def test_no_bots_by_default(tmp_path):
    node = await _start(tmp_path, 0)
    try:
        assert await node.storage.list_ai_bots() == []
        assert await node.storage.get_published_cells() == []
    finally:
        await node.stop()


async def test_created_bot_answers_on_the_users_key(tmp_path, fake_ai, monkeypatch):
    monkeypatch.delenv("NEVOD_PUBLIC_CLIENT_ADDR", raising=False)
    node = await _start(tmp_path, 2)
    try:
        p = PRESETS["tolmach"]
        bot = await node.ai_bots.create(p["name"], p["description"], p["system_prompt"],
                                        ["gemini", "anthropic"])
        assert bot.providers == ["anthropic", "gemini"]          # canonical order
        assert os.path.exists(tmp_path / "ai_bots" / f"{bot.cell_id}.json")
        published = await node.storage.get_published_cells()
        assert [(c.cell_id, c.name, c.ai_providers) for c in published] == \
            [(bot.cell_id, "Толмач", ["anthropic", "gemini"])]
        await _wait_online(node, bot.cell_id)

        user = _User(node, 2)
        await user.client.connect(addr(2))
        await user.say(bot.cell_id, await _bot_enc_pub(node, bot.cell_id),
                       "ai-key:anthropic:sk-user\nhello")
        assert await user.wait() == ["echo:hello"]
        assert fake_ai == [("anthropic", "sk-user", "hello")]
        # The bot's card points the app at the node's client address, not at loopback.
        assert user.received[0].startswith(f"card:{bot.cell_id}@{node.identity.address}|")
        await user.client.disconnect()
    finally:
        await node.stop()


async def test_bot_connects_on_an_invite_only_node(tmp_path, fake_ai):
    node = await _start(tmp_path, 4, invite_mode="delegated")
    try:
        bot = await node.ai_bots.create("Helper", "", "be brief", ["openai"])
        await _wait_online(node, bot.cell_id)
    finally:
        await node.stop()


async def test_disable_enable_and_restart(tmp_path, fake_ai):
    node = await _start(tmp_path, 6)
    bot = await node.ai_bots.create("Helper", "d", "be brief", ["openai"])
    await _wait_online(node, bot.cell_id)
    await node.ai_bots.set_enabled(bot.cell_id, False)
    assert node.ai_bots.status(bot.cell_id) == "off"
    assert await node.storage.get_published_cells() == []
    assert await node.storage.get_cell(bot.cell_id) is not None     # the name stays its own
    await node.ai_bots.set_enabled(bot.cell_id, True)
    await _wait_online(node, bot.cell_id)
    await node.stop()

    # A restarted node brings its enabled bots back by itself.
    node = await Node.create(str(tmp_path / "n.json"), str(tmp_path / "n.db"))
    await node.start()
    try:
        await _wait_online(node, bot.cell_id)
    finally:
        await node.stop()


async def test_delete_removes_cell_keys_and_listing(tmp_path, fake_ai):
    node = await _start(tmp_path, 8)
    try:
        bot = await node.ai_bots.create("Helper", "", "be brief", ["openai"])
        await _wait_online(node, bot.cell_id)
        await node.ai_bots.delete(bot.cell_id)
        assert node.ai_bots.status(bot.cell_id) == "off"
        assert await node.storage.get_cell(bot.cell_id) is None
        assert await node.storage.list_ai_bots() == []
        assert await node.storage.get_published_cells() == []
        assert not os.path.exists(tmp_path / "ai_bots" / f"{bot.cell_id}.json")
        await asyncio.sleep(2.5)    # past the runner's first reconnect delay
        assert await node.storage.get_cell(bot.cell_id) is None
    finally:
        await node.stop()


async def test_update_restarts_with_new_prompt(tmp_path, fake_ai):
    node = await _start(tmp_path, 10)
    try:
        bot = await node.ai_bots.create("Helper", "", "old", ["openai"])
        await _wait_online(node, bot.cell_id)
        await node.ai_bots.update(bot.cell_id, "Helper 2", "new desc", "new", ["gemini"])
        b = await node.storage.get_ai_bot(bot.cell_id)
        assert (b.name, b.system_prompt, b.providers) == ("Helper 2", "new", ["gemini"])
        assert (await node.storage.get_cell(bot.cell_id)).display_name == "Helper 2"
        assert [c.name for c in await node.storage.get_published_cells()] == ["Helper 2"]
        await _wait_online(node, bot.cell_id)
    finally:
        await node.stop()


@pytest.mark.parametrize("name,prompt,providers,error", [
    ("", "p", ["openai"], "имя"),
    ("administrator", "p", ["openai"], "зарезервировано"),
    ("Bot", "", ["openai"], "инструкцию"),
    ("Bot", "p", [], "провайдера"),
    ("Bot", "p", ["mistral"], "провайдера"),
    ("Bot", "x" * 4001, ["openai"], "длиннее"),
])
async def test_validation(tmp_path, name, prompt, providers, error):
    node = await _start(tmp_path, 12)
    try:
        with pytest.raises(AIBotError, match=error):
            await node.ai_bots.create(name, "", prompt, providers)
        assert await node.storage.list_ai_bots() == []
    finally:
        await node.stop()


async def test_name_already_taken(tmp_path):
    node = await _start(tmp_path, 14)
    try:
        await node.register_cell_locally("ab" * 32, b"\x01" * 32, b"\x02" * 32, display_name="Bob")
        with pytest.raises(AIBotError, match="занято"):
            await node.ai_bots.create("Bob", "", "p", ["openai"])
    finally:
        await node.stop()


async def test_admin_api_round_trip(genesis_node, fake_ai):
    from tests.test_admin import _auth_header, _client
    client = await _client(genesis_node)
    try:
        h = _auth_header()
        r = await client.get("/nevod-admin/api/ai-bots", headers=h)
        data = await r.json()
        assert data["bots"] == [] and set(data["presets"]) == {"assistant", "tolmach"}

        p = data["presets"]["assistant"]
        r = await client.post("/nevod-admin/api/ai-bots", headers=h, json={
            "name": p["name"], "description": p["description"],
            "system_prompt": p["system_prompt"], "providers": ["anthropic"]})
        assert (await r.json()) == {"ok": True}
        r = await client.post("/nevod-admin/api/ai-bots", headers=h, json={
            "name": p["name"], "system_prompt": "x", "providers": ["anthropic"]})
        assert r.status == 400 and "занято" in (await r.json())["error"]

        bots = (await (await client.get("/nevod-admin/api/ai-bots", headers=h)).json())["bots"]
        assert [(b["name"], b["providers"], b["enabled"]) for b in bots] == \
            [("AI Assistant", ["anthropic"], True)]
        cid = bots[0]["cell_id"]
        await _wait_online(genesis_node, cid)

        r = await client.post(f"/nevod-admin/api/ai-bots/{cid}/enabled", headers=h,
                              json={"enabled": False})
        assert (await r.json())["ok"]
        bots = (await (await client.get("/nevod-admin/api/ai-bots", headers=h)).json())["bots"]
        assert (bots[0]["enabled"], bots[0]["status"]) == (False, "off")

        # Deleting it from the Cells page stops it too, instead of it re-registering.
        r = await client.delete(f"/nevod-admin/api/cells/{cid}", headers=h)
        assert r.status == 200
        assert await genesis_node.storage.list_ai_bots() == []
        assert await genesis_node.storage.get_cell(cid) is None
    finally:
        await client.close()
