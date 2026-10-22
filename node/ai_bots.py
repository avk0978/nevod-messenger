"""BYOK AI bots the operator runs inside the node itself — the admin panel's "AI-боты" page.

Decision 2026-10-16: any planet can have AI bots, switched on from its admin panel, none by
default. Each bot is an ordinary cell of this node (its keys in ai_bots/<cell_id>.json next
to node.json, like the registrar and administrator) running the same NevdBot as the
standalone `python -m node.bot`: it dials this node's own port on loopback, so every message
takes the normal E2E path and nothing in routing knows bots exist. The node keeps it
connected (reconnect with backoff) for as long as it is enabled.

A bot never has a key of its own: it answers on the key each user sends with their message
(node/bot.py). Its operator — whoever runs this node — runs the code that decrypts what users
write to the bot; the privacy policy (§5) says so.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional

import httpx

from . import ai_providers as ai
from .bot import DEFAULT_SYSTEM_PROMPT, TOLMACH_SYSTEM_PROMPT, NevdBot
from .identity import CellIdentity
from .names import is_reserved_name
from .storage import AIBotEntry

log = logging.getLogger("nevod.ai_bots")

MAX_BOTS = 10
MAX_PROMPT_CHARS = 4000

# Ready-made bots for the admin page's "add" buttons — the admin can change everything after.
PRESETS: Dict[str, dict] = {
    "assistant": {
        "name": "AI Assistant",
        "description": "Answers questions on your own Claude, ChatGPT or Gemini key.",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
    },
    "tolmach": {
        "name": "Толмач",
        "description": "Translator: send any text, get it translated. Works on your own AI key.",
        "system_prompt": TOLMACH_SYSTEM_PROMPT,
    },
}


class AIBotError(Exception):
    """Shown to the admin as is (Russian, like the rest of the panel)."""


class AIBotManager:
    def __init__(self, node, data_dir: str):
        self._node = node
        self._dir = os.path.join(data_dir, "ai_bots")
        self._runners: Dict[str, asyncio.Task] = {}
        self._configs: Dict[str, tuple] = {}     # cell_id -> config the runner was started with
        self._online: Dict[str, bool] = {}
        self._http: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    # --- lifecycle (Node.start / Node.stop) ---

    async def start(self):
        await self.sync()

    async def stop(self):
        for task in self._runners.values():
            task.cancel()
        await asyncio.gather(*self._runners.values(), return_exceptions=True)
        self._runners.clear()
        self._configs.clear()
        if self._http:
            await self._http.aclose()
            self._http = None

    async def sync(self):
        """Make the running bots match the table: start enabled ones, stop disabled or
        deleted ones, restart a bot whose prompt/providers changed."""
        async with self._lock:
            wanted = {b.cell_id: b for b in await self._node.storage.list_ai_bots() if b.enabled}
            for cell_id in list(self._runners):
                b = wanted.get(cell_id)
                if b is None or _config(b) != self._configs.get(cell_id):
                    task = self._runners.pop(cell_id)
                    self._configs.pop(cell_id, None)
                    self._online.pop(cell_id, None)
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
            for cell_id, b in wanted.items():
                if cell_id not in self._runners:
                    identity = self._load_identity(cell_id)
                    if identity is None:
                        log.error("ai bot %s: identity file missing, not started", cell_id[:8])
                        continue
                    self._configs[cell_id] = _config(b)
                    self._runners[cell_id] = asyncio.create_task(
                        self._run(b, identity), name=f"ai-bot-{cell_id[:8]}")

    def status(self, cell_id: str) -> str:
        if cell_id not in self._runners:
            return "off"
        return "online" if self._online.get(cell_id) else "connecting"

    # --- admin actions ---

    async def create(self, name: str, description: str, system_prompt: str,
                     providers: List[str]) -> AIBotEntry:
        storage = self._node.storage
        if len(await storage.list_ai_bots()) >= MAX_BOTS:
            raise AIBotError(f"на ноде уже максимум ботов: {MAX_BOTS}")
        name, description, system_prompt, providers = await self._validate(
            None, name, description, system_prompt, providers)
        identity = CellIdentity.generate(name=name)
        os.makedirs(self._dir, exist_ok=True)
        identity.save(self._identity_path(identity.cell_id))
        await self._node.register_cell_locally(identity.cell_id, identity.signing.public,
                                               identity.encryption.public, display_name=name)
        # Admitted like any member, so it also connects to an invite-only node.
        await storage._admit_cell(identity.cell_id, "ai_bots")
        await storage.save_ai_bot(identity.cell_id, name, description, system_prompt,
                                  providers, enabled=True)
        await storage.publish_cell(identity.cell_id, name, description, kind="bot",
                                   ai_providers=providers)
        await self._node._broadcast_member_added(identity.cell_id)
        log.info("ai bot created: %s (%s)", identity.cell_id[:8], ",".join(providers))
        await self.sync()
        return await storage.get_ai_bot(identity.cell_id)

    async def update(self, cell_id: str, name: str, description: str, system_prompt: str,
                     providers: List[str]) -> AIBotEntry:
        storage = self._node.storage
        bot = await storage.get_ai_bot(cell_id)
        if bot is None:
            raise AIBotError("бот не найден")
        name, description, system_prompt, providers = await self._validate(
            cell_id, name, description, system_prompt, providers)
        await storage.save_ai_bot(cell_id, name, description, system_prompt, providers,
                                  enabled=bot.enabled)
        await storage.set_display_name(cell_id, name)
        if bot.enabled:
            await storage.publish_cell(cell_id, name, description, kind="bot",
                                       ai_providers=providers)
        await self.sync()
        return await storage.get_ai_bot(cell_id)

    async def set_enabled(self, cell_id: str, enabled: bool):
        """Off = stopped and taken off the planet's list; the cell and its name stay."""
        storage = self._node.storage
        bot = await storage.get_ai_bot(cell_id)
        if bot is None:
            raise AIBotError("бот не найден")
        await storage.save_ai_bot(cell_id, bot.name, bot.description, bot.system_prompt,
                                  bot.providers, enabled=enabled)
        if enabled:
            await storage.publish_cell(cell_id, bot.name, bot.description, kind="bot",
                                       ai_providers=bot.providers)
        else:
            await storage.unpublish_cell(cell_id)
        await self.sync()

    async def delete(self, cell_id: str):
        """Only the admin deletes (never automatic): the cell, its name and its keys go."""
        if await self._node.storage.get_ai_bot(cell_id) is None:
            raise AIBotError("бот не найден")
        await self._node.storage.delete_cell(cell_id)   # also drops ai_bots + published rows
        await self.sync()
        try:
            os.remove(self._identity_path(cell_id))
        except FileNotFoundError:
            pass
        log.info("ai bot deleted: %s", cell_id[:8])

    # --- internals ---

    async def _validate(self, cell_id: Optional[str], name: str, description: str,
                        system_prompt: str, providers: List[str]):
        name = (name or "").strip()[:64]
        description = (description or "").strip()[:280]
        system_prompt = (system_prompt or "").strip()
        providers = [p for p in ai.PROVIDERS if p in set(providers or [])]
        if not name:
            raise AIBotError("укажи имя бота")
        if is_reserved_name(name):
            raise AIBotError("это имя зарезервировано (administrator, nevod, …) — выбери другое")
        owner = await self._node.storage.get_cell_by_name(name)
        if owner and owner != cell_id:
            raise AIBotError("это имя уже занято на ноде")
        if not system_prompt:
            raise AIBotError("укажи инструкцию для бота")
        if len(system_prompt) > MAX_PROMPT_CHARS:
            raise AIBotError(f"инструкция слишком длинная, максимум символов: {MAX_PROMPT_CHARS}")
        if not providers:
            raise AIBotError("отметь хотя бы одного провайдера")
        return name, description, system_prompt, providers

    def _identity_path(self, cell_id: str) -> str:
        return os.path.join(self._dir, f"{cell_id}.json")

    def _load_identity(self, cell_id: str) -> Optional[CellIdentity]:
        try:
            return CellIdentity.load(self._identity_path(cell_id))
        except FileNotFoundError:
            return None

    def _local_endpoint(self):
        """Where the node itself listens, as seen from inside this process."""
        host, port = self._node.listen_endpoint
        if host in ("", "0.0.0.0", "::"):
            host = "127.0.0.1"
        scheme = "wss" if self._node.identity.tls_cert_pem else "ws"
        return f"{host}:{port}", scheme

    async def _run(self, entry: AIBotEntry, identity: CellIdentity):
        if self._http is None:
            self._http = httpx.AsyncClient(http2=True, timeout=60.0)
        address, scheme = self._local_endpoint()
        public_address = self._node._public_client_endpoint()[0]
        delay = 2
        while True:
            bot = NevdBot(identity, system_prompt=entry.system_prompt,
                          providers=tuple(entry.providers), http_client=self._http)
            try:
                await bot.connect(address, scheme=scheme, public_address=public_address,
                                  expected_node_id=self._node.identity.node_id)
                self._online[entry.cell_id] = True
                delay = 2
                await bot.client.wait_closed()
                log.warning("ai bot %s: connection to the node ended, reconnecting",
                            entry.cell_id[:8])
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("ai bot %s: connect failed: %s", entry.cell_id[:8], e)
            finally:
                self._online[entry.cell_id] = False
                await bot.close()   # shared http client is not closed (not owned by the bot)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)


def _config(b: AIBotEntry) -> tuple:
    return (b.system_prompt, tuple(b.providers))
