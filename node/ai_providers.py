"""
node/ai_providers.py — the three AI providers a BYOK bot (node/bot.py) can talk to.

BYOK = the USER's own key (decision 2026-09-28: no operator-paid usage; 2026-10-16: the user
picks the provider, one key per provider for all bots). The key arrives inside the user's E2E
message with every request and is used for that one call only — never stored, never logged.
Exceptions raised here never carry the key either: it travels in headers, not URLs, and errors
are reduced to the codes below before they leave this module.

Error codes (the app shows them localized — keep in sync with AppStore.swift):
  invalid_key           provider rejected the key (401/403)
  no_credit             key is valid but the account has no money/quota left
  rate_limited          provider-side rate limit, try again later
  provider_unavailable  network error, timeout or provider 5xx
  no_model              key works but no usable chat model was found for it
  failed                anything else
"""

import re
from typing import List, Optional, Tuple

import httpx

ANTHROPIC = "anthropic"
OPENAI = "openai"
GEMINI = "gemini"
PROVIDERS = (ANTHROPIC, OPENAI, GEMINI)

# Preferred model per provider; if the provider's model list doesn't contain it, pick_model()
# falls back to the newest model of the same family, so a renamed/retired id doesn't break bots.
DEFAULT_MODELS = {
    ANTHROPIC: "claude-sonnet-5-5",
    OPENAI: "chat-latest",
    GEMINI: "gemini-flash-latest",
}

MAX_TOKENS = 1024
_ANTHROPIC_URL = "https://api.anthropic.com/v1"
_OPENAI_URL = "https://api.openai.com/v1"
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"


class AIError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _headers(provider: str, key: str) -> dict:
    if provider == ANTHROPIC:
        return {"x-api-key": key, "anthropic-version": "2023-06-01"}
    if provider == OPENAI:
        return {"Authorization": f"Bearer {key}"}
    return {"x-goog-api-key": key}


def _error_code(resp: httpx.Response) -> str:
    status = resp.status_code
    try:
        body = resp.text.lower()
    except Exception:
        body = ""
    if status in (401, 403):
        # Gemini answers an invalid key with 400 API_KEY_INVALID, handled below; a 403 there
        # can also mean "API not enabled for this project" — still a key/account problem.
        return "invalid_key"
    if "credit balance" in body or "insufficient_quota" in body or "billing" in body or status == 402:
        return "no_credit"
    if status == 400 and ("api_key_invalid" in body or "api key not valid" in body):
        return "invalid_key"
    if status == 429:
        return "rate_limited"
    if status >= 500:
        return "provider_unavailable"
    return "failed"


def _key_is_well_formed(key: str) -> bool:
    """Every provider's key is printable ASCII without spaces. Anything else (a stray Cyrillic
    letter or a smart quote from a paste) can't even go into an HTTP header — httpx raises
    UnicodeEncodeError, which once escaped up to the bot's receive loop and silenced it."""
    return bool(key) and key.isascii() and key.isprintable() and not any(c.isspace() for c in key)


async def _request(http: httpx.AsyncClient, method: str, url: str, provider: str, key: str,
                   json: Optional[dict] = None) -> dict:
    if not _key_is_well_formed(key):
        raise AIError("invalid_key")
    try:
        resp = await http.request(method, url, headers=_headers(provider, key), json=json)
    except httpx.HTTPError:
        raise AIError("provider_unavailable") from None
    if resp.status_code >= 400:
        raise AIError(_error_code(resp))
    try:
        return resp.json()
    except ValueError:
        raise AIError("failed") from None


async def list_models(http: httpx.AsyncClient, provider: str, key: str) -> List[str]:
    """The free "is this key good" call (decision 2026-09-28) — also tells us which models exist."""
    if provider == ANTHROPIC:
        data = await _request(http, "GET", f"{_ANTHROPIC_URL}/models?limit=100", provider, key)
        return [m.get("id", "") for m in data.get("data", [])]
    if provider == OPENAI:
        data = await _request(http, "GET", f"{_OPENAI_URL}/models", provider, key)
        return [m.get("id", "") for m in data.get("data", [])]
    if provider == GEMINI:
        data = await _request(http, "GET", f"{_GEMINI_URL}/models?pageSize=1000", provider, key)
        return [m.get("name", "").removeprefix("models/") for m in data.get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", ["generateContent"])]
    raise AIError("failed")


# Matched against whole name parts ("gpt-5.6-mini" → mini), not substrings — "gemini" contains "mini".
_EXCLUDE = re.compile(r"(?:^|[-.])(mini|nano|lite|audio|realtime|image|tts|transcribe|search|embed\w*|"
                      r"vision|live|preview|exp|instruct|haiku|opus|codex|moderation|dall|whisper)"
                      r"(?=$|[-.\d])")


_DATE = re.compile(r"-?(\d{4})-?(\d{2})-?(\d{2})$")


def _version_key(model_id: str) -> Tuple:
    """Version numbers first, snapshot date only as a tie-breaker — otherwise
    "gpt-5-2025-08-07" would outrank "gpt-5.6" on the date's digits."""
    m = _DATE.search(model_id)
    base = model_id[:m.start()] if m else model_id
    date = int("".join(m.groups())) if m else 99999999   # undated alias = newest of its version
    return tuple(int(n) for n in re.findall(r"\d+", base)), date


def pick_model(provider: str, available: List[str], preferred: Optional[str] = None) -> Optional[str]:
    want = preferred or DEFAULT_MODELS[provider]
    if want in available:
        return want
    family = {ANTHROPIC: r"^claude-sonnet", OPENAI: r"^gpt-", GEMINI: r"^gemini-.*flash"}[provider]
    candidates = [m for m in available if re.search(family, m) and not _EXCLUDE.search(m)]
    if not candidates:
        return None
    return max(candidates, key=_version_key)


async def check_key(http: httpx.AsyncClient, provider: str, key: str,
                    preferred: Optional[str] = None) -> str:
    """Returns the model to use with this key, or raises AIError."""
    model = pick_model(provider, await list_models(http, provider, key), preferred)
    if not model:
        raise AIError("no_model")
    return model


async def chat(http: httpx.AsyncClient, provider: str, key: str, model: str,
               system: str, history: List[dict]) -> str:
    """history: [{"role": "user"|"assistant", "content": str}], oldest first."""
    if provider == ANTHROPIC:
        data = await _request(http, "POST", f"{_ANTHROPIC_URL}/messages", provider, key, json={
            "model": model, "max_tokens": MAX_TOKENS, "system": system, "messages": history,
        })
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    elif provider == OPENAI:
        data = await _request(http, "POST", f"{_OPENAI_URL}/chat/completions", provider, key, json={
            "model": model, "max_completion_tokens": MAX_TOKENS,
            "messages": [{"role": "system", "content": system}] + history,
        })
        choices = data.get("choices") or [{}]
        text = (choices[0].get("message") or {}).get("content") or ""
    elif provider == GEMINI:
        data = await _request(http, "POST", f"{_GEMINI_URL}/models/{model}:generateContent",
                              provider, key, json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "model" if m["role"] == "assistant" else "user",
                          "parts": [{"text": m["content"]}]} for m in history],
            "generationConfig": {"maxOutputTokens": MAX_TOKENS},
        })
        candidates = data.get("candidates") or [{}]
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts)
    else:
        raise AIError("failed")
    return text.strip() or "…"
