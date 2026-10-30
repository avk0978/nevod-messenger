"""
NODE_LIST_REQUEST ("Explore Network"): open nodes only, each with the fingerprint of its
own certificate, so the app can pin a node that isn't in the curator's nodes.json (VPS test
2026-10-30: without it the app couldn't open a private operator's planet).
"""

import time
from types import SimpleNamespace

from node.identity import NodeIdentity
from node.node import Node
from node.protocol import Packet, T, decode_payload
from node.storage import NodeEntry


async def test_open_nodes_with_fingerprint(tmp_path):
    id_path = str(tmp_path / "n.json")
    NodeIdentity.generate("127.0.0.1:19840").save(id_path)
    node = await Node.create(id_path, str(tmp_path / "n.db"))
    now = int(time.time())
    for nid, access, fp in (("aa" * 32, "open", "f1" * 32), ("bb" * 32, "closed", "f2" * 32)):
        await node.storage.upsert_node(NodeEntry(
            node_id=nid, address=f"{nid[:2]}.example:8765", access=access, name=nid[:2],
            tls_fingerprint=fp, last_seen=now, added_at=now))
    sent = []

    async def send_via(conn, pkt):
        sent.append(pkt)

    node.transport.send_via = send_via
    req = Packet(type=T.NODE_LIST_REQUEST, payload=b"", from_addr="cc" * 32, to_addr=node.identity.node_id)
    await node._handle_node_list_request(req, SimpleNamespace(peer_node_id="cc" * 32))
    [resp] = sent
    assert resp.type == T.NODE_LIST_RESPONSE
    nodes = decode_payload(resp.payload)["nodes"]
    assert [(n["node_id"], n["tls_fingerprint"]) for n in nodes] == [("aa" * 32, "f1" * 32)]
