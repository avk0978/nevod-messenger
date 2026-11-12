"""The "accepted" ack (node.py _ack_accepted): the sending phone learns the node holds its
message. Device test 2026-11-04: a video's last chunks were lost in the phone's own TCP
buffer when iOS suspended the app, and the message waited on "sent" forever."""

import pytest

from node.crypto import gen_signing, gen_encryption
from node.protocol import T, Packet, decode_payload
from tests.test_node import make_node


class FakeConn:
    def __init__(self, peer_node_id):
        self.peer_node_id = peer_node_id


async def _setup(tmp_path, offset):
    n = await make_node(tmp_path, offset, genesis=True)
    sent = []

    async def send_via(conn, pkt):
        sent.append((conn, pkt))

    n.transport.send_via = send_via
    a_sign, a_enc = gen_signing(), gen_encryption()
    b_sign, b_enc = gen_signing(), gen_encryption()
    a, b = a_sign.public.hex(), b_sign.public.hex()
    await n.register_cell_locally(a, a_sign.public, a_enc.public)
    await n.register_cell_locally(b, b_sign.public, b_enc.public)
    return n, sent, a, b


def _pkt(n, a, b, type_=T.MSG, id_=None):
    p = Packet(type=type_, payload=b"blob",
               from_addr=f"{a}@{n.identity.node_id}", to_addr=f"{b}@{n.identity.node_id}")
    if id_:
        p.id = id_
    return p


def _accepted(sent):
    out = []
    for _, p in sent:
        if p.type == T.ACK:
            d = decode_payload(p.payload)
            if d.get("status") == "accepted":
                out.append(d["message_id"])
    return out


@pytest.mark.asyncio
async def test_msg_from_own_connection_gets_accepted(tmp_path):
    n, sent, a, b = await _setup(tmp_path, 60)
    conn = FakeConn(a)
    pkt = _pkt(n, a, b, id_="7C1D0A2B-0000-0000-0000-000000000001")
    await n._dispatch(pkt, conn)
    assert _accepted(sent) == [pkt.id]
    ack = [p for c, p in sent if p.type == T.ACK][0]
    assert ack.to_addr == pkt.from_addr
    assert [c for c, p in sent if p.type == T.ACK][0] is conn


@pytest.mark.asyncio
async def test_no_accepted_for_chunks_untracked_ids_or_relayed(tmp_path):
    n, sent, a, b = await _setup(tmp_path, 61)
    # a middle chunk of a file
    await n._dispatch(_pkt(n, a, b, type_=T.MSG_CHUNK, id_="u-ABC"), FakeConn(a))
    # a T.MSG with an untracked id
    await n._dispatch(_pkt(n, a, b, id_="u-DEF"), FakeConn(a))
    # relayed by another node: the connection isn't the sender's own
    await n._dispatch(_pkt(n, a, b, id_="REAL-ID"), FakeConn("some-other-node-id"))
    # a silent signal
    await n._dispatch(_pkt(n, a, b, type_=T.MSG_SILENT, id_="SILENT-ID"), FakeConn(a))
    assert _accepted(sent) == []


@pytest.mark.asyncio
async def test_resumable_chunk_gets_accepted(tmp_path):
    """1.3 (263): a chunk with a fixed id "u-r-<transfer>-<index>" is acked, so the phone
    can resume after a drop instead of re-sending the whole file."""
    n, sent, a, b = await _setup(tmp_path, 62)
    cid = "u-r-7C1D0A2B-0000-0000-0000-000000000001-5"
    await n._dispatch(_pkt(n, a, b, type_=T.MSG_CHUNK, id_=cid), FakeConn(a))
    # relayed from another node: not acked
    await n._dispatch(_pkt(n, a, b, type_=T.MSG_CHUNK, id_=cid + "0"), FakeConn("other-node"))
    assert _accepted(sent) == [cid]


@pytest.mark.asyncio
async def test_resent_resumable_chunk_buffered_once(tmp_path):
    """The recipient is offline: the same chunk sent twice (two attempts) is buffered once
    — before fixed ids every attempt was stored and replayed (977 chunks for a 283-chunk
    video, device test 2026-11-06)."""
    n, sent, a, b = await _setup(tmp_path, 63)
    cid = "u-r-7C1D0A2B-0000-0000-0000-000000000002-1"
    for _ in range(2):
        await n._dispatch(_pkt(n, a, b, type_=T.MSG_CHUNK, id_=cid), FakeConn(a))
    buffered = await n.storage.get_buffered(b)
    assert [m.message_id for m in buffered] == [cid]
    assert _accepted(sent) == [cid, cid]
