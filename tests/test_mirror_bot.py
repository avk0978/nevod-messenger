"""node/mirror_bot.py — the echo bot App Review talks to on Nevod Open (no second device).

It must echo text back to the sender through a real node, and never write the text to its log.
"""

import asyncio
import logging

from node.bot import strip_prefixes, wrap_card
from node.client import CellClient
from node.identity import CellIdentity
from node.mirror_bot import MirrorBot
from node.node import Node

ADDR = "127.0.0.1:20700"


async def test_echoes_text_without_logging_it(tmp_path, caplog):
    node = await Node.create_genesis(ADDR, str(tmp_path / "n.json"), str(tmp_path / "n.db"),
                                     access="open")
    await node.start()
    bot_id = CellIdentity.generate(name="Echo")
    bot = MirrorBot(bot_id)
    received = []
    user_id = CellIdentity.generate(name="User")
    user = CellClient(user_id, on_message=lambda frm, pt: received.append(pt.decode()))
    try:
        await bot.connect(ADDR)
        await user.connect(ADDR)
        secret = "very private words"
        msg = wrap_card(user.cell_id, ADDR, node.identity.node_id,
                        user_id.encryption.public, secret)
        with caplog.at_level(logging.INFO):
            await user.send(bot.client.cell_id, node.identity.node_id,
                            bot_id.encryption.public, msg.encode())
            for _ in range(50):
                if received:
                    break
                await asyncio.sleep(0.1)
        assert [strip_prefixes(t)[1] for t in received] == [f"🪞 {secret}"]
        assert secret not in caplog.text
    finally:
        await user.disconnect()
        await bot.close()
        await node.stop()
