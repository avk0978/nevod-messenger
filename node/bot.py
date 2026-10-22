"""
node/bot.py — generic AI-agent cell connector (Cluster Б: "AI-агент на открытой ноде").

Connects any AI agent to a Nevod node as an ordinary cell — see node/client.py's
CellClient, already built for exactly this ("connects a cell (user or AI
agent) to a Nevod node"). A bot is just another cell talking the normal
protocol, not special node infrastructure; runs as its own process,
independent of node.py.

This file is persona-agnostic: --name/--system-prompt(-file) configure WHICH
agent a given run is. "Толмач" (a translator) was the first agent built on
this connector — see the default prompt below for its exact wording — but
any other persona (FAQ bot, assistant for a specific community, etc.) is
just a different invocation of the same script, not a fork of it.

Scope, per the agreed design (MD_Discuss/DISCUSS_NODE_ADMISSION.md and Cluster
Б planning): an agent built on this connector ONLY replies with text — no
tool/function-calling access, no remote execution on anyone's device, no
built-in payment/metering ("оплата вне протокола" — if a bot charges, that
happens entirely outside Nevod). BYOK: the bot has no API key of its own —
every request carries the user's own key for the provider THEY chose (Claude,
ChatGPT or Gemini), used for that one call and never stored or logged (user
decisions 2026-09-28 and 2026-10-16; wire format below). An optional --allowed-cells
whitelist restricts who may talk to a given instance at all (default: open
to everyone who finds it).

First-contact reachability turned out to already be solved, just under a
different name than we first assumed: NevdClient.swift's send() already
prepends a "card:cellId@nodeAddr|nodeId|encPubKeyHex\n" line to EVERY
outgoing message (see its `cardLine`/`formatCard`/`parseCard` in
Models.swift) — not just first contact, always. AppStore.swift's incoming
handler already auto-offers to add an unknown sender as a contact from that
same line (`pendingCard`/AddContactBanner). So instead of inventing a new
"pubkey:" prefix (an earlier draft of this file did exactly that — redundant
with something that already existed), this bot reuses the real "card:"
convention: parses it from incoming messages the same way the iOS client
does, and prepends its own in every reply. A human's ContactsView "Add
Contact" screen also accepts a raw card string pasted directly (no QR, no
node round-trip) — so a bot's card, printed at startup, can be pasted
straight in to start a real conversation with it today, without waiting on
the (separately discussed, not yet built) "tap a planet to start chatting"
UI. Reaches only whoever the sender already chose to message — the card line
lives inside the E2E-encrypted payload, same trust boundary as the message
content itself, never visible to routing nodes.
"""

import argparse
import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import httpx

from . import ai_providers as ai
from .identity import CellIdentity
from .client import CellClient

log = logging.getLogger("nevod.bot")

DEFAULT_NAME = "Nevod Bot"
MAX_HISTORY_MESSAGES = 6  # per-sender, short-term only — not persisted across restarts

DEFAULT_SYSTEM_PROMPT = (
    "You are an assistant reachable on the Nevod messaging network. Keep "
    "replies short — this is a chat, not an essay. You have no ability to "
    "run code, access files, browse the web, or take any action outside "
    "this conversation; if asked to do something like that, say plainly "
    "that you can't."
)

# The first agent built on this connector — "Толмач" ("Tolmach", Russian for
# "interpreter"), a translator. Not used unless a run explicitly asks for it
# (--system-prompt-file pointed at a file with this text, or --system-prompt
# passed directly) — kept here only as the canonical example wording.
TOLMACH_SYSTEM_PROMPT = (
    'You are "Толмач" ("Tolmach" — Russian for "interpreter"), a translation '
    "assistant reachable on the Nevod messaging network. Translate whatever "
    "text the user sends, or answer direct questions about a translation. "
    "Keep replies short — this is a chat, not an essay. You have no ability "
    "to run code, access files, browse the web, or take any action outside "
    "this conversation; if asked to do something like that, say plainly "
    "that you can't and that you only translate."
)


# ─── wire-level "card:" prefix — see module docstring; must match
#     Models.swift's formatCard()/parseCard() byte-for-byte ────────────────

_CARD_RE = re.compile(r"^card:([0-9a-f]{64})@([^|]+)\|([^|]+)\|([0-9a-f]{64})\n",
                      re.IGNORECASE)


def wrap_card(cell_id: str, node_addr: str, node_id: str, enc_pubkey: bytes, text: str) -> str:
    return f"card:{cell_id}@{node_addr}|{node_id}|{enc_pubkey.hex()}\n{text}"


def card_string(cell_id: str, node_addr: str, node_id: str, enc_pubkey: bytes) -> str:
    """The bare card (no leading 'card:', no message body) — this is what a
    human pastes into ContactsView's "Add Contact" text field."""
    return f"{cell_id}@{node_addr}|{node_id}|{enc_pubkey.hex()}"


def strip_prefixes(text: str) -> Tuple[Optional[bytes], str]:
    """Mirrors NevdClient.swift's prefix-chain convention (card: outermost,
    then reply:, then slavonic:) — strips whatever's present. Returns the
    sender's embedded enc_pubkey (None if absent) and the underlying text."""
    sender_pubkey = None
    m = _CARD_RE.match(text)
    if m:
        sender_pubkey = bytes.fromhex(m.group(4))
        text = text[m.end():]
    if text.startswith("reply:"):
        nl = text.find("\n")
        if nl != -1:
            text = text[nl + 1:]
    if text.startswith("slavonic:\n"):
        text = text[len("slavonic:\n"):]
    return sender_pubkey, text


# ─── BYOK wire lines (inside the E2E payload, right after the card: line) ───
#     Must match AppStore.swift byte-for-byte. The key never appears in the sender's
#     own stored message — the app adds the line only to what goes on the wire.
#
#   user → bot, ordinary message:  "ai-key:<provider>:<key>\n" + [reply:/slavonic:] + text
#   user → bot, key check (silent): "ai-check:<provider>:<key>"
#   bot → user (silent):            "ai-check-result:<provider>:ok"
#                                   "ai-check-result:<provider>:<error code>"
#                                   "ai-error:<error code>:<provider>"  (no_key: provider empty)
#   Error codes: node/ai_providers.py.

AI_KEY_PREFIX = "ai-key:"
AI_CHECK_PREFIX = "ai-check:"
# Silent control signals the app sends to every chat partner — no answer expected.
_CONTROL_PREFIXES = ("delete:", "edit:", "identity_deleted:", "notify:")


def parse_ai_line(text: str, prefix: str) -> Tuple[Optional[str], Optional[str], str]:
    """(provider, key, rest) if `text` starts with `prefix`, else (None, None, text)."""
    if not text.startswith(prefix):
        return None, None, text
    line, sep, rest = text[len(prefix):].partition("\n")
    provider, _, key = line.partition(":")
    return provider.strip(), key.strip(), rest if sep else ""


# ─── bot ─────────────────────────────────────────────────────────────────

class NevdBot:
    def __init__(self, identity: CellIdentity,
                 system_prompt: str = DEFAULT_SYSTEM_PROMPT,
                 providers: Tuple[str, ...] = ai.PROVIDERS,
                 models: Optional[Dict[str, str]] = None,
                 allowed_cells: Optional[Set[str]] = None,
                 http_client: Optional[httpx.AsyncClient] = None):
        self._system_prompt = system_prompt
        self._providers = tuple(providers)
        self._preferred = dict(models or {})
        # Model actually chosen per provider, learned from a successful key check (list
        # models) — shared by all users. Keys themselves are never kept.
        self._models: Dict[str, str] = {}
        # None = open to everyone (default). A non-None set restricts replies
        # to only those cell_ids — anyone else is silently ignored, no reply
        # at all (avoids confirming to a stranger that this bot exists/is
        # reachable, rather than politely declining).
        self._allowed_cells = allowed_cells
        self._http = http_client or httpx.AsyncClient(http2=True, timeout=60.0)
        self._owns_http = http_client is None
        self._known_pubkeys: Dict[str, bytes] = {}   # cell_id -> enc_pubkey
        self._history: Dict[str, List[dict]] = {}    # cell_id -> [{"role", "content"}], RAM only
        self._node_addr: str = ""
        self._tasks: Set[asyncio.Task] = set()
        self._sender_locks: Dict[str, asyncio.Lock] = {}
        self.client = CellClient(identity, on_message=self._on_message)

    @property
    def card(self) -> str:
        """This bot's own card — paste-ready for ContactsView's "Add Contact"
        screen. Only valid after connect()."""
        return card_string(self.client.cell_id, self._node_addr, self.client.node_id,
                           self.client.identity.encryption.public)

    async def connect(self, address: str, expected_fingerprint: Optional[str] = None, *,
                      scheme: str = "wss", public_address: Optional[str] = None,
                      expected_node_id: Optional[str] = None):
        """public_address: what goes into the bot's card for the app, when the bot itself
        dials another address (a node's in-process bot uses its loopback port)."""
        self._node_addr = public_address or address
        await self.client.connect(address, expected_node_id=expected_node_id,
                                  expected_fingerprint=expected_fingerprint, scheme=scheme)

    async def close(self):
        for t in list(self._tasks):
            t.cancel()
        await self.client.disconnect()
        if self._owns_http:
            await self._http.aclose()

    async def _reply(self, cell_id: str, node_id: str, text: str, silent: bool = False):
        wrapped = wrap_card(self.client.cell_id, self._node_addr, self.client.node_id,
                            self.client.identity.encryption.public, text)
        await self.client.send(cell_id, node_id, self._known_pubkeys[cell_id],
                               wrapped.encode("utf-8"), silent=silent)

    async def _on_message(self, from_addr: str, plaintext: bytes):
        # Answered in the background: the receive loop awaits this callback, and one slow
        # AI call (seconds) must not hold up everyone else's messages. A per-sender lock
        # keeps one user's turns in order, so their short history stays paired.
        task = asyncio.create_task(self._handle_in_order(from_addr, plaintext))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _handle_in_order(self, from_addr: str, plaintext: bytes):
        lock = self._sender_locks.setdefault(from_addr.partition("@")[0], asyncio.Lock())
        async with lock:
            try:
                await self._handle(from_addr, plaintext)
            except Exception:
                log.exception("bot: failed to handle a message from %s", from_addr[:8])

    async def _handle(self, from_addr: str, plaintext: bytes):
        cell_id, _, node_id = from_addr.partition("@")
        if self._allowed_cells is not None and cell_id not in self._allowed_cells:
            log.info("bot: message from %s ignored (not on allow-list)", cell_id[:8])
            return
        try:
            text = plaintext.decode("utf-8")
        except UnicodeDecodeError:
            log.warning("bot: non-UTF8 message from %s, ignoring", cell_id[:8])
            return

        m = _CARD_RE.match(text)
        if m:
            self._known_pubkeys[cell_id] = bytes.fromhex(m.group(4))
            text = text[m.end():]
        if cell_id not in self._known_pubkeys:
            log.warning("bot: no enc_pubkey for %s (no card: prefix, no prior "
                        "contact) — can't reply", cell_id[:8])
            return

        provider, key, _ = parse_ai_line(text, AI_CHECK_PREFIX)
        if provider is not None:
            code = await self._check(provider, key)
            log.info("bot: key check from %s provider=%s -> %s", cell_id[:8], provider, code)
            await self._reply(cell_id, node_id, f"ai-check-result:{provider}:{code}", silent=True)
            return

        provider, key, text = parse_ai_line(text, AI_KEY_PREFIX)
        _, text = strip_prefixes(text)   # reply:/slavonic: — the bot answers the bare text
        if not provider or not key:
            if not text.startswith(_CONTROL_PREFIXES):
                await self._reply(cell_id, node_id, "ai-error:no_key:", silent=True)
            return

        # Message text is never logged (same rule as the app's nlog) — only its length.
        log.info("bot: message from %s provider=%s len=%d", cell_id[:8], provider, len(text))
        try:
            reply_text = await self._ask_ai(cell_id, provider, key, text)
        except ai.AIError as e:
            log.info("bot: %s call for %s failed: %s", provider, cell_id[:8], e.code)
            await self._reply(cell_id, node_id, f"ai-error:{e.code}:{provider}", silent=True)
            return
        await self._reply(cell_id, node_id, reply_text)

    async def _check(self, provider: str, key: str) -> str:
        if provider not in self._providers:
            return "unsupported_provider"
        if not key:
            return "invalid_key"
        try:
            self._models[provider] = await ai.check_key(self._http, provider, key,
                                                        self._preferred.get(provider))
        except ai.AIError as e:
            return e.code
        return "ok"

    async def _ask_ai(self, cell_id: str, provider: str, key: str, text: str) -> str:
        """Split out from _on_message so tests can stub this one call without
        spending real API budget or needing a live key."""
        if provider not in self._providers:
            raise ai.AIError("unsupported_provider")
        model = self._models.get(provider)
        if not model:   # e.g. the bot restarted since the user's key check
            model = await ai.check_key(self._http, provider, key, self._preferred.get(provider))
            self._models[provider] = model
        history = self._history.setdefault(cell_id, [])
        history.append({"role": "user", "content": text})
        del history[:-MAX_HISTORY_MESSAGES]
        try:
            reply = await ai.chat(self._http, provider, key, model, self._system_prompt, history)
        except ai.AIError:
            history.pop()   # keep user/assistant turns paired for the next attempt
            raise
        history.append({"role": "assistant", "content": reply})
        del history[:-MAX_HISTORY_MESSAGES]
        return reply


# ─── entrypoint ─────────────────────────────────────────────────────────

def _load_or_create_identity(path: Path, name: str) -> CellIdentity:
    if path.exists():
        return CellIdentity.load(str(path))
    identity = CellIdentity.generate(name=name)
    identity.save(str(path))
    log.info("generated new bot identity at %s", path)
    return identity


def _load_allowed_cells(inline: Optional[str], file_path: Optional[str]) -> Optional[Set[str]]:
    """None (the default, if neither flag is given) means open to everyone."""
    if not inline and not file_path:
        return None
    cells: Set[str] = set()
    if inline:
        cells.update(c.strip().lower() for c in inline.split(",") if c.strip())
    if file_path:
        with open(file_path, encoding="utf-8") as f:
            cells.update(line.strip().lower() for line in f if line.strip())
    return cells


def _resolve_system_prompt(inline: Optional[str], file_path: Optional[str]) -> str:
    if inline:
        return inline
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    return DEFAULT_SYSTEM_PROMPT


async def _main():
    parser = argparse.ArgumentParser(
        description="Nevod AI-agent connector (Cluster Б) — generic, persona set via flags")
    parser.add_argument("--node", required=True, help="host:port of the node to connect to")
    parser.add_argument("--fingerprint", default=None, help="expected TLS fingerprint (optional)")
    parser.add_argument("--identity", default="bot_identity.json",
                        help="path to this bot's cell identity file (created on first run)")
    parser.add_argument("--name", default=DEFAULT_NAME,
                        help="display name for this bot's identity (only used on first run)")
    parser.add_argument("--providers", default=",".join(ai.PROVIDERS),
                        help="comma-separated providers this bot accepts user keys for "
                             "(default: all three) - must match the providers ticked "
                             "when publishing it in the admin panel")
    for p in ai.PROVIDERS:
        parser.add_argument(f"--{p}-model", default=None,
                            help=f"preferred {p} model (default {ai.DEFAULT_MODELS[p]}; if the "
                                 "user's key can't see it, the newest model of that family)")
    parser.add_argument("--system-prompt", default=None,
                        help="inline system prompt text (overrides --system-prompt-file)")
    parser.add_argument("--system-prompt-file", default=None,
                        help="path to a text file containing the system prompt "
                             "(default: a generic no-tools assistant prompt)")
    parser.add_argument("--allowed-cells", default=None,
                        help="comma-separated hex cell_ids allowed to message this bot "
                             "(default: open to everyone)")
    parser.add_argument("--allowed-cells-file", default=None,
                        help="path to a file with one allowed cell_id per line "
                             "(combines with --allowed-cells)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    providers = tuple(p.strip() for p in args.providers.split(",") if p.strip())
    unknown = [p for p in providers if p not in ai.PROVIDERS]
    if unknown or not providers:
        parser.error(f"--providers: unknown {unknown}, choose from {', '.join(ai.PROVIDERS)}")
    models = {p: getattr(args, f"{p}_model") for p in ai.PROVIDERS if getattr(args, f"{p}_model")}

    system_prompt = _resolve_system_prompt(args.system_prompt, args.system_prompt_file)
    allowed_cells = _load_allowed_cells(args.allowed_cells, args.allowed_cells_file)
    log.info("bot allow-list: %s", "open to everyone" if allowed_cells is None
             else f"{len(allowed_cells)} cell(s)")

    identity = _load_or_create_identity(Path(args.identity), args.name)
    log.info("bot cell_id=%s enc_pubkey=%s", identity.cell_id, identity.encryption.public.hex())

    bot = NevdBot(identity, system_prompt=system_prompt, providers=providers, models=models,
                  allowed_cells=allowed_cells)
    await bot.connect(args.node, expected_fingerprint=args.fingerprint)
    log.info("bot connected and listening on %s (user keys: %s) - Ctrl+C to stop",
             args.node, ", ".join(providers))
    print("\nPaste this into Nevod → Contacts → Add Contact → text field to chat with the bot:")
    print(f"  {bot.card}\n")
    try:
        # Exit when the node connection ends (node redeployed, network drop): the bot has no
        # reconnect loop of its own, and Docker's restart policy brings it back connected.
        await bot.client.wait_closed()
        log.warning("bot: connection to the node ended - exiting so the supervisor restarts it")
    finally:
        await bot.close()
    sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass


# Billing: BYOK (decision 2026-09-28) - every call runs on the requesting user's own
# provider key, so the operator pays nothing and needs no budget cap. The bot can't be
# used as a free relay for the same reason: no key, no call.
