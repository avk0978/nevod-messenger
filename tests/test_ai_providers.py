"""node/ai_providers.py against a fake HTTP transport — request shapes, model choice, error codes.

No real provider is called. The point is the plumbing the BYOK bot relies on: the user's key
goes in the right header (never the URL), answers are parsed per provider, and every failure
is reduced to a code the app can localize — never to an exception text carrying the key.
"""

import json

import httpx
import pytest

from node import ai_providers as ai

KEY = "secret-user-key-123"


def client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class TestPickModel:
    def test_preferred_when_available(self):
        assert ai.pick_model(ai.ANTHROPIC, ["claude-haiku-5", "claude-sonnet-5-5"]) == "claude-sonnet-5-5"

    def test_falls_back_to_newest_of_family(self):
        ids = ["gpt-5-2025-08-07", "gpt-5.6", "gpt-5.6-mini", "gpt-realtime", "text-embedding-3"]
        assert ai.pick_model(ai.OPENAI, ids) == "gpt-5.6"

    def test_gemini_skips_lite_and_preview(self):
        ids = ["gemini-3.6-flash", "gemini-3.7-flash-preview", "gemini-3.5-flash-lite", "gemini-3-pro"]
        assert ai.pick_model(ai.GEMINI, ids) == "gemini-3.6-flash"

    def test_none_when_nothing_fits(self):
        assert ai.pick_model(ai.OPENAI, ["whisper-1"]) is None

    def test_operator_override(self):
        assert ai.pick_model(ai.OPENAI, ["gpt-x", "gpt-5.6"], preferred="gpt-x") == "gpt-x"


class TestRequests:
    async def test_anthropic_check_and_chat(self):
        seen = []

        def handler(req: httpx.Request):
            seen.append(req)
            assert req.headers["x-api-key"] == KEY
            if req.url.path == "/v1/models":
                return httpx.Response(200, json={"data": [{"id": "claude-sonnet-5-5"}]})
            body = json.loads(req.content)
            assert body["model"] == "claude-sonnet-5-5"
            assert body["system"] == "sys"
            assert body["messages"] == [{"role": "user", "content": "hi"}]
            return httpx.Response(200, json={"content": [{"type": "text", "text": " hello "}]})

        async with client(handler) as http:
            model = await ai.check_key(http, ai.ANTHROPIC, KEY)
            assert await ai.chat(http, ai.ANTHROPIC, KEY, model, "sys",
                                 [{"role": "user", "content": "hi"}]) == "hello"
        assert all(KEY not in str(r.url) for r in seen)

    async def test_openai_chat_puts_system_first(self):
        def handler(req: httpx.Request):
            assert req.headers["authorization"] == f"Bearer {KEY}"
            body = json.loads(req.content)
            assert body["messages"][0] == {"role": "system", "content": "sys"}
            assert body["messages"][1:] == [{"role": "user", "content": "q"},
                                            {"role": "assistant", "content": "a"},
                                            {"role": "user", "content": "q2"}]
            return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

        async with client(handler) as http:
            history = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"},
                       {"role": "user", "content": "q2"}]
            assert await ai.chat(http, ai.OPENAI, KEY, "chat-latest", "sys", history) == "ok"

    async def test_gemini_roles_and_model_list(self):
        def handler(req: httpx.Request):
            assert req.headers["x-goog-api-key"] == KEY
            assert KEY not in str(req.url)
            if req.method == "GET":
                return httpx.Response(200, json={"models": [
                    {"name": "models/gemini-3.6-flash", "supportedGenerationMethods": ["generateContent"]},
                    {"name": "models/text-embedding-004", "supportedGenerationMethods": ["embedContent"]},
                ]})
            assert req.url.path == "/v1beta/models/gemini-3.6-flash:generateContent"
            body = json.loads(req.content)
            assert body["systemInstruction"] == {"parts": [{"text": "sys"}]}
            assert [c["role"] for c in body["contents"]] == ["user", "model", "user"]
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "ciao"}]}}]})

        async with client(handler) as http:
            model = await ai.check_key(http, ai.GEMINI, KEY)
            assert model == "gemini-3.6-flash"
            history = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"},
                       {"role": "user", "content": "c"}]
            assert await ai.chat(http, ai.GEMINI, KEY, model, "sys", history) == "ciao"


class TestErrors:
    @pytest.mark.parametrize("status,body,code", [
        (401, {"error": "bad key"}, "invalid_key"),
        (403, {}, "invalid_key"),
        (400, {"error": {"status": "INVALID_ARGUMENT", "details": [{"reason": "API_KEY_INVALID"}]}}, "invalid_key"),
        (400, {"error": {"message": "Your credit balance is too low"}}, "no_credit"),
        (429, {"error": {"code": "insufficient_quota"}}, "no_credit"),
        (429, {"error": "slow down"}, "rate_limited"),
        (529, {}, "provider_unavailable"),
        (404, {}, "failed"),
    ])
    async def test_status_to_code(self, status, body, code):
        async with client(lambda req: httpx.Response(status, json=body)) as http:
            with pytest.raises(ai.AIError) as e:
                await ai.list_models(http, ai.OPENAI, KEY)
        assert e.value.code == code
        assert KEY not in str(e.value) and e.value.__cause__ is None

    @pytest.mark.parametrize("bad", ["sk-proj-ключпользователя", "sk-“quoted”", "sk key", "sk-key\n", ""])
    async def test_malformed_key_never_reaches_http(self, bad):
        # 2026-10-16 on device: a pasted OpenAI key with non-ASCII letters made httpx raise
        # UnicodeEncodeError, which escaped and silenced the bot's receive loop.
        def handler(req):
            raise AssertionError("no request may be sent with a malformed key")

        async with client(handler) as http:
            with pytest.raises(ai.AIError) as e:
                await ai.check_key(http, ai.OPENAI, bad)
        assert e.value.code == "invalid_key"

    async def test_network_error(self):
        def handler(req):
            raise httpx.ConnectError(f"boom {req.headers}")

        async with client(handler) as http:
            with pytest.raises(ai.AIError) as e:
                await ai.chat(http, ai.ANTHROPIC, KEY, "m", "s", [{"role": "user", "content": "x"}])
        assert e.value.code == "provider_unavailable"
        assert KEY not in str(e.value) and e.value.__cause__ is None

    async def test_no_usable_model(self):
        async with client(lambda req: httpx.Response(200, json={"data": [{"id": "whisper-1"}]})) as http:
            with pytest.raises(ai.AIError) as e:
                await ai.check_key(http, ai.OPENAI, KEY)
        assert e.value.code == "no_model"
