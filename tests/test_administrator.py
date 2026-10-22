"""
Tests for every node's built-in "administrator" cell — in-app complaints/appeals that the
node operator reads and answers on the admin panel's Обращения page (node.py
_ensure_administrator / _maybe_handle_administrator_msg / reply_as_administrator).
"""

import asyncio

from node.identity import NodeIdentity, CellIdentity
from node.node import Node
from node.client import CellClient
from node.protocol import Packet, T, encode_payload, sign_packet, pack

BASE = 19600


def addr(offset: int) -> str:
    return f"127.0.0.1:{BASE + offset}"


async def make_node(tmp_path, offset: int) -> Node:
    id_path = str(tmp_path / f"n{offset}.json")
    idt = NodeIdentity.generate(addr(offset))
    idt.save(id_path)
    return await Node.create(id_path, str(tmp_path / f"n{offset}.db"))


async def connect(node: Node, name: str, received: list) -> CellClient:
    client = CellClient(CellIdentity.generate(name),
                        on_message=lambda f, m: received.append((f, m)))
    await client.connect(node.identity.address)
    await asyncio.sleep(0.1)
    return client


class TestAdministrator:
    async def test_identity_created_persisted_and_listed_as_member(self, tmp_path):
        node = await make_node(tmp_path, 0)
        await node.start()
        try:
            info = node.administrator_info()
            assert info and info["node_id"] == node.identity.node_id
            cell = await node.storage.get_cell(info["cell_id"])
            assert cell is not None and cell.display_name == "administrator"
            assert cell.enc_pubkey.hex() == info["enc_pub"]
            client = await connect(node, "Alice", [])
            try:
                # Listed like any member: the app resolves non-contact chat partners (and
                # opens a chat from a push tap) through the member list.
                members = await client.get_group_members()
                assert info["cell_id"] in {m["cell_id"] for m in members}
            finally:
                await client.disconnect()
        finally:
            await node.stop()
        # Same identity after a restart — the ✓ signature is bound to it.
        node2 = await Node.create(str(tmp_path / "n0.json"), str(tmp_path / "n0.db"))
        await node2.start()
        try:
            assert node2.administrator_info()["cell_id"] == info["cell_id"]
        finally:
            await node2.stop()

    async def test_appeal_stored_acked_and_answered(self, tmp_path):
        node = await make_node(tmp_path, 1)
        await node.start()
        try:
            info = node.administrator_info()
            received: list = []
            client = await connect(node, "Alice", received)
            try:
                msg_id = await client.send(info["cell_id"], node.identity.node_id,
                                           bytes.fromhex(info["enc_pub"]),
                                           "🚩 Жалоба\n\nспам".encode("utf-8"))
                await asyncio.sleep(0.2)
                assert client.get_status(msg_id) == "delivered"

                thread = await node.storage.get_appeal_thread(client.cell_id)
                assert [(m.direction, m.text) for m in thread] == [("in", "🚩 Жалоба\n\nспам")]
                # The name is whatever this node knows for the sender (the test CellClient
                # registers without one; the app sends its display name).
                sender = await node.storage.get_cell(client.cell_id)
                assert thread[0].display_name == sender.display_name
                threads = await node.storage.list_appeal_threads()
                assert threads[0]["cell_id"] == client.cell_id and threads[0]["unread"] == 1
                # Nothing left sitting in the dead-letter buffer for the service cell.
                assert await node.storage.get_buffered(info["cell_id"]) == []

                assert await node.reply_as_administrator(client.cell_id, "Разберёмся")
                await asyncio.sleep(0.2)
                assert received and received[-1][1] == "Разберёмся".encode("utf-8")
                assert received[-1][0].startswith(info["cell_id"] + "@")
                thread = await node.storage.get_appeal_thread(client.cell_id)
                assert [m.direction for m in thread] == ["in", "out"]
            finally:
                await client.disconnect()
        finally:
            await node.stop()

    async def test_non_text_to_administrator_not_buffered(self, tmp_path):
        """MSG_SILENT / REACT / VCALL_OFFER / ACK addressed to the administrator can never be
        delivered (no live connection) — they must be dropped, not buffered forever."""
        node = await make_node(tmp_path, 2)
        await node.start()
        try:
            info = node.administrator_info()
            client = await connect(node, "Bob", [])
            try:
                to_addr = f"{info['cell_id']}@{node.identity.node_id}"
                for t in (T.MSG_SILENT, T.REACT, T.VCALL_OFFER, T.ACK):
                    pkt = Packet(type=t, payload=encode_payload({"message_id": "x", "status": "read"}),
                                 from_addr=f"{client.cell_id}@{node.identity.node_id}",
                                 to_addr=to_addr)
                    sign_packet(pkt, client.identity.signing)
                    await client._ws.send(pack(pkt))
                await asyncio.sleep(0.2)
                assert await node.storage.get_buffered(info["cell_id"]) == []
                assert await node.storage.get_appeal_thread(client.cell_id) == []
            finally:
                await client.disconnect()
        finally:
            await node.stop()

    async def test_reply_without_known_key_fails_cleanly(self, tmp_path):
        node = await make_node(tmp_path, 3)
        await node.start()
        try:
            assert await node.reply_as_administrator("ab" * 32, "hello") is False
            assert await node.reply_as_administrator("ab" * 32, "   ") is False
        finally:
            await node.stop()

    async def test_diag_log_stored_and_announced_in_thread(self, tmp_path):
        import base64, re, zlib
        node = await make_node(tmp_path, 20)
        await node.start()
        try:
            info = node.administrator_info()
            client = await connect(node, "Alice", [])
            try:
                raw = ("[21:13:02] streamChunk 0/6\n" * 2000).encode()
                c = zlib.compressobj(wbits=-15)   # raw deflate, as NSData .zlib on iOS
                packed = c.compress(raw) + c.flush()
                msg_id = await client.send(info["cell_id"], node.identity.node_id,
                                           bytes.fromhex(info["enc_pub"]),
                                           b"nevod-log:" + base64.b64encode(packed))
                await asyncio.sleep(0.2)
                assert client.get_status(msg_id) == "delivered"
                thread = await node.storage.get_appeal_thread(client.cell_id)
                assert len(thread) == 1 and thread[0].text.startswith("📎 Журнал диагностики")
                log_id = int(re.search(r"\[log:(\d+)\]", thread[0].text).group(1))
                cell_id, _, stored = await node.storage.get_diag_log(log_id)
                assert cell_id == client.cell_id and zlib.decompress(stored, -15) == raw

                # Garbage is dropped, not shown as an appeal.
                await client.send(info["cell_id"], node.identity.node_id,
                                  bytes.fromhex(info["enc_pub"]), b"nevod-log:%%%not base64")
                await asyncio.sleep(0.2)
                assert len(await node.storage.get_appeal_thread(client.cell_id)) == 1
            finally:
                await client.disconnect()
        finally:
            await node.stop()
