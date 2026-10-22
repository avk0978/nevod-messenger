"""
node/mirror_bot.py — trivial echo bot for testing the browse→bot-chat flow
end to end without spending an Anthropic API call or needing a key.

Same connector as node/bot.py (CellClient, card:/reply:/slavonic: prefix
handling) — only _on_message differs: instead of asking Claude, it echoes
the text straight back, prefixed so it's obviously the bot talking.

Usage: python -m node.mirror_bot --node localhost:8765
Registers (or reuses) its own cell on that node and prints its cell_id —
publish it via the node's admin panel ("Опубликованные ячейки", kind=bot,
name="Mirror") to make it reachable from NodesView.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Windows console defaults to the system codepage (cp1251 here), not UTF-8 — any
# em-dash/emoji/Cyrillic in a log line or print() crashes with UnicodeEncodeError
# even when stdout is redirected to a file. Force UTF-8 unconditionally.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .bot import card_string, strip_prefixes, wrap_card
from .client import CellClient
from .identity import CellIdentity

log = logging.getLogger("nevod.mirror_bot")


class MirrorBot:
    def __init__(self, identity: CellIdentity):
        self._known_pubkeys: dict[str, bytes] = {}
        self._node_addr = ""
        self.client = CellClient(identity, on_message=self._on_message)

    @property
    def card(self) -> str:
        return card_string(self.client.cell_id, self._node_addr, self.client.node_id,
                           self.client.identity.encryption.public)

    async def connect(self, address: str, expected_fingerprint: str | None = None):
        self._node_addr = address
        await self.client.connect(address, expected_fingerprint=expected_fingerprint)

    async def close(self):
        await self.client.disconnect()

    async def _on_message(self, from_addr: str, plaintext: bytes):
        cell_id, _, node_id = from_addr.partition("@")
        try:
            text = plaintext.decode("utf-8")
        except UnicodeDecodeError:
            log.warning("mirror: non-UTF8 message from %s, ignoring", cell_id[:8])
            return

        sender_pubkey, text = strip_prefixes(text)
        if sender_pubkey:
            self._known_pubkeys[cell_id] = sender_pubkey
        recipient_pubkey = self._known_pubkeys.get(cell_id)
        if not recipient_pubkey:
            log.warning("mirror: no enc_pubkey for %s, can't reply", cell_id[:8])
            return

        # Message text is never logged (same rule as node/bot.py and the app's nlog).
        log.info("mirror: echoing to %s len=%d", cell_id[:8], len(text))
        reply_text = f"🪞 {text}"
        wrapped = wrap_card(self.client.cell_id, self._node_addr, self.client.node_id,
                            self.client.identity.encryption.public, reply_text)
        await self.client.send(cell_id, node_id, recipient_pubkey, wrapped.encode("utf-8"))


async def _main():
    parser = argparse.ArgumentParser(description="Nevod echo bot for testing")
    parser.add_argument("--node", required=True, help="host:port of the node to connect to")
    parser.add_argument("--fingerprint", default=None)
    parser.add_argument("--identity", default="mirror_bot_identity.json")
    parser.add_argument("--name", default="Mirror")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    path = Path(args.identity)
    if path.exists():
        identity = CellIdentity.load(str(path))
    else:
        identity = CellIdentity.generate(name=args.name)
        identity.save(str(path))
        log.info("generated new mirror bot identity at %s", path)
    log.info("mirror bot cell_id=%s", identity.cell_id)

    bot = MirrorBot(identity)
    await bot.connect(args.node, expected_fingerprint=args.fingerprint)
    log.info("mirror bot connected and listening on %s - Ctrl+C to stop", args.node)
    print("\ncell_id to publish (admin panel -> Published cells -> kind=bot, name=Mirror):")
    print(f"  {bot.client.cell_id}\n")
    print("Card (paste into Contacts -> Add Contact to talk to it directly):")
    print(f"  {bot.card}\n")
    try:
        # Exit when the node connection ends (node redeployed, network drop) so Docker's
        # restart policy reconnects it — same as node/bot.py.
        await bot.client.wait_closed()
        log.warning("mirror: connection to the node ended - exiting so the supervisor restarts it")
    finally:
        await bot.close()
    sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass
