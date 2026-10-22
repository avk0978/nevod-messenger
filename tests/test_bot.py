"""
Tests for node/bot.py's wire-level "card:" prefix handling (the SAME
convention NevdClient.swift/Models.swift already use — see that module's
docstring), the BYOK ai-key:/ai-check: lines, and the message round-trip
through a real node. The provider call (_ask_ai / check_key) is stubbed: this suite verifies
the crypto/wire path (real infrastructure this project owns), not a
third-party LLM API's behavior, and avoids spending real API budget in test
runs.
"""

import asyncio
import pytest

from node.identity import CellIdentity
from node.node import Node
from node.client import CellClient
from node import ai_providers
from node.bot import (
    NevdBot, wrap_card, card_string, strip_prefixes, parse_ai_line,
    _load_allowed_cells, _resolve_system_prompt, DEFAULT_SYSTEM_PROMPT,
)


BASE = 19500


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE + offset}"


async def make_node(tmp_path, offset: int) -> Node:
    address = addr(offset)
    id_path = str(tmp_path / f"n{offset}.json")
    db_path = str(tmp_path / f"n{offset}.db")
    return await Node.create_genesis(address, id_path, db_path, access="open")


class TestCardPrefix:
    def test_wrap_and_strip_roundtrip(self):
        pk = bytes(range(32))
        wrapped = wrap_card("aa" * 32, "127.0.0.1:9999", "bb" * 32, pk, "hello there")
        sender_pk, text = strip_prefixes(wrapped)
        assert sender_pk == pk
        assert text == "hello there"

    def test_strip_without_prefix_returns_none(self):
        sender_pk, text = strip_prefixes("just plain text")
        assert sender_pk is None
        assert text == "just plain text"

    def test_strip_handles_reply_and_slavonic_chain(self):
        # mirrors NevdClient.swift's own nesting order: card outermost, then
        # reply:, then slavonic:
        pk = bytes(range(32))
        wrapped = wrap_card("aa" * 32, "127.0.0.1:9999", "bb" * 32, pk,
                            "reply:abc123\nslavonic:\nПривет")
        sender_pk, text = strip_prefixes(wrapped)
        assert sender_pk == pk
        assert text == "Привет"

    def test_card_string_matches_wrap_card_body(self):
        pk = bytes(range(32))
        bare = card_string("aa" * 32, "127.0.0.1:9999", "bb" * 32, pk)
        wrapped = wrap_card("aa" * 32, "127.0.0.1:9999", "bb" * 32, pk, "x")
        assert wrapped == f"card:{bare}\nx"


class TestCliHelpers:
    def test_no_allow_list_flags_means_open(self):
        assert _load_allowed_cells(None, None) is None

    def test_inline_allow_list_parsed_lowercased(self):
        cells = _load_allowed_cells("AA11, bb22 ,cc33", None)
        assert cells == {"aa11", "bb22", "cc33"}

    def test_allow_list_file_merges_with_inline(self, tmp_path):
        f = tmp_path / "allowed.txt"
        f.write_text("dd44\nee55\n", encoding="utf-8")
        cells = _load_allowed_cells("aa11", str(f))
        assert cells == {"aa11", "dd44", "ee55"}

    def test_default_system_prompt_used_when_nothing_given(self):
        assert _resolve_system_prompt(None, None) == DEFAULT_SYSTEM_PROMPT

    def test_inline_system_prompt_wins_over_file(self, tmp_path):
        f = tmp_path / "prompt.txt"
        f.write_text("from file", encoding="utf-8")
        assert _resolve_system_prompt("from flag", str(f)) == "from flag"

    def test_system_prompt_file_used_when_no_inline(self, tmp_path):
        f = tmp_path / "prompt.txt"
        f.write_text("  from file  \n", encoding="utf-8")
        assert _resolve_system_prompt(None, str(f)) == "from file"


class _Harness:
    """A real node + the bot + one user cell. The provider call (_ask_ai / _check's HTTP)
    is stubbed: this verifies the wire path, not a third-party API."""

    def __init__(self, tmp_path, offset, **bot_kwargs):
        self.tmp_path, self.offset, self.bot_kwargs = tmp_path, offset, bot_kwargs
        self.received = []

    async def __aenter__(self):
        self.node = await make_node(self.tmp_path, self.offset)
        await self.node.start()
        self.bot_identity = CellIdentity.generate(name="Tolmach")
        self.bot = NevdBot(self.bot_identity, **self.bot_kwargs)
        self.sent = []   # (text, silent) of everything the bot sent
        real_send = self.bot.client.send

        async def spy(to_cell, to_node, pub, plaintext, silent=False):
            self.sent.append((strip_prefixes(plaintext.decode())[1], silent))
            return await real_send(to_cell, to_node, pub, plaintext, silent=silent)
        self.bot.client.send = spy
        await self.bot.connect(addr(self.offset))
        self.user_identity = CellIdentity.generate(name="User")
        self.user = CellClient(self.user_identity,
                               on_message=lambda frm, pt: self.received.append(pt.decode()))
        await self.user.connect(addr(self.offset))
        return self

    async def say(self, text):
        msg = wrap_card(self.user.cell_id, addr(self.offset), self.user.node_id,
                        self.user_identity.encryption.public, text)
        await self.user.send(self.bot.client.cell_id, self.node.identity.node_id,
                             self.bot_identity.encryption.public, msg.encode())

    async def wait_reply(self, n=1):
        for _ in range(50):
            if len(self.sent) >= n:
                return
            await asyncio.sleep(0.1)
        raise AssertionError(f"bot sent {len(self.sent)} message(s), expected {n}")

    async def __aexit__(self, *exc):
        await self.bot.close()
        await self.user.disconnect()
        await self.node.stop()


class TestByokBot:
    async def test_message_with_key_gets_answer_on_that_key(self, tmp_path, monkeypatch):
        async with _Harness(tmp_path, 0) as h:
            calls = []

            async def fake_ask(cell_id, provider, key, text):
                calls.append((provider, key, text))
                return f"echo: {text}"
            monkeypatch.setattr(h.bot, "_ask_ai", fake_ask)
            await h.say("ai-key:anthropic:sk-ant-123\nreply:abc\nhello, translate this")
            await h.wait_reply()
            assert calls == [("anthropic", "sk-ant-123", "hello, translate this")]
            assert h.sent == [("echo: hello, translate this", False)]
            for _ in range(30):
                if h.received:
                    break
                await asyncio.sleep(0.1)
            sender_pk, text = strip_prefixes(h.received[0])
            assert sender_pk == h.bot_identity.encryption.public
            assert text == "echo: hello, translate this"

    async def test_message_without_key_gets_silent_no_key(self, tmp_path):
        async with _Harness(tmp_path, 5) as h:
            await h.say("hello")
            await h.wait_reply()
            assert h.sent == [("ai-error:no_key:", True)]

    async def test_control_signal_without_key_gets_no_answer(self, tmp_path):
        async with _Harness(tmp_path, 7) as h:
            await h.say("delete:abc123")
            await asyncio.sleep(0.5)
            assert h.sent == []

    async def test_key_check_answers_silently(self, tmp_path, monkeypatch):
        async with _Harness(tmp_path, 20, providers=("anthropic", "gemini")) as h:
            async def fake_check_key(http, provider, key, preferred=None):
                if key != "good":
                    raise ai_providers.AIError("invalid_key")
                return "model-x"
            monkeypatch.setattr(ai_providers, "check_key", fake_check_key)
            await h.say("ai-check:gemini:good")
            await h.say("ai-check:anthropic:bad")
            await h.say("ai-check:openai:good")
            await h.wait_reply(3)
            assert sorted(h.sent) == sorted([("ai-check-result:gemini:ok", True),
                                             ("ai-check-result:anthropic:invalid_key", True),
                                             ("ai-check-result:openai:unsupported_provider", True)])
            assert h.bot._models == {"gemini": "model-x"}

    async def test_provider_error_becomes_silent_code(self, tmp_path, monkeypatch):
        async with _Harness(tmp_path, 25) as h:
            async def failing(cell_id, provider, key, text):
                raise ai_providers.AIError("no_credit")
            monkeypatch.setattr(h.bot, "_ask_ai", failing)
            await h.say("ai-key:openai:sk-1\nhi")
            await h.wait_reply()
            assert h.sent == [("ai-error:no_credit:openai", True)]

    async def test_failing_message_does_not_silence_the_bot(self, tmp_path, monkeypatch):
        # 2026-10-16 on device: one malformed key raised out of the handler, ended the
        # receive loop, and AI Assistant stopped answering everyone.
        async with _Harness(tmp_path, 27) as h:
            calls = []

            async def flaky_check(provider, key):
                calls.append(key)
                if len(calls) == 1:
                    raise UnicodeEncodeError("ascii", key, 0, 1, "boom")
                return "ok"
            monkeypatch.setattr(h.bot, "_check", flaky_check)
            await h.say("ai-check:anthropic:first")
            await h.say("ai-check:anthropic:second")
            await h.wait_reply()
            assert h.sent == [("ai-check-result:anthropic:ok", True)]
            assert calls == ["first", "second"]


class TestAllowList:
    async def test_disallowed_sender_gets_no_reply(self, tmp_path):
        async with _Harness(tmp_path, 10, allowed_cells={"aa" * 32}) as h:
            await h.say("ai-key:anthropic:k\nhi")
            await asyncio.sleep(0.5)
            assert h.sent == []

    async def test_allowed_sender_gets_a_reply(self, tmp_path, monkeypatch):
        async with _Harness(tmp_path, 15) as h:
            h.bot._allowed_cells = {h.user.cell_id}
            monkeypatch.setattr(h.bot, "_ask_ai",
                                lambda c, p, k, t: asyncio.sleep(0, result="ok"))
            await h.say("ai-key:anthropic:k\nhi")
            await h.wait_reply()
            assert h.sent == [("ok", False)]


class TestParseAiLine:
    def test_key_line(self):
        assert parse_ai_line("ai-key:openai:sk-a:b\nrest\nmore", "ai-key:") == \
            ("openai", "sk-a:b", "rest\nmore")

    def test_check_without_newline(self):
        assert parse_ai_line("ai-check:gemini:AIza1", "ai-check:") == ("gemini", "AIza1", "")

    def test_other_text(self):
        assert parse_ai_line("hello", "ai-key:") == (None, None, "hello")
