"""
Tests for Schnorr ZKP authentication protocol (auth.py).

All tests use FakeWS (asyncio.Queue pairs) — no network, no TLS needed.
Integration tests (real WSS) are covered via test_tls.py / test_ack.py.

Block 1: Successful mutual auth (node↔node, cell↔node)
Block 2: Failure cases (mismatch, tampered proof, wrong packet type)
Block 3: Symmetry and repeatability
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import pytest

from node.auth import do_schnorr_auth
from node.identity import NodeIdentity, CellIdentity
from node.protocol import T, Packet, pack, unpack, encode_payload
from node.crypto import schnorr_commit


# ─── FakeWS helpers ───────────────────────────────────────────────────────────


class FakeWS:
    """Bidirectional asyncio.Queue pair simulating a WebSocket."""

    def __init__(self, send_q: asyncio.Queue, recv_q: asyncio.Queue):
        self._sq = send_q
        self._rq = recv_q

    async def send(self, data: bytes):
        await self._sq.put(data)

    async def recv(self) -> bytes:
        return await self._rq.get()


def make_pipe():
    """Return (ws_a, ws_b): what A sends, B receives and vice versa."""
    q_ab, q_ba = asyncio.Queue(), asyncio.Queue()
    return FakeWS(q_ab, q_ba), FakeWS(q_ba, q_ab)


def make_node() -> NodeIdentity:
    return NodeIdentity.generate("127.0.0.1:19600", access="open")


def make_cell() -> CellIdentity:
    return CellIdentity.generate()


async def _gather(*coros):
    """Run concurrently; return list (exceptions included, not re-raised)."""
    return await asyncio.gather(*coros, return_exceptions=True)


def _first_error(results: list):
    return next((r for r in results if isinstance(r, Exception)), None)


# ─── Block 1: Successful mutual auth ─────────────────────────────────────────


class TestSchnorrAuthSuccess:
    @pytest.mark.asyncio
    async def test_node_to_node_auth_succeeds(self):
        id_a, id_b = make_node(), make_node()
        ws_a, ws_b = make_pipe()
        r_a, r_b = await _gather(
            do_schnorr_auth(ws_a, id_a),
            do_schnorr_auth(ws_b, id_b),
        )
        assert not isinstance(r_a, Exception)
        assert not isinstance(r_b, Exception)

    @pytest.mark.asyncio
    async def test_auth_result_identifies_peer(self):
        """Each side learns the other's node_id."""
        id_a, id_b = make_node(), make_node()
        ws_a, ws_b = make_pipe()
        r_a, r_b = await _gather(
            do_schnorr_auth(ws_a, id_a),
            do_schnorr_auth(ws_b, id_b),
        )
        assert r_a.node_id == id_b.node_id
        assert r_b.node_id == id_a.node_id

    @pytest.mark.asyncio
    async def test_result_carries_correct_pubkeys(self):
        id_a, id_b = make_node(), make_node()
        ws_a, ws_b = make_pipe()
        r_a, r_b = await _gather(
            do_schnorr_auth(ws_a, id_a),
            do_schnorr_auth(ws_b, id_b),
        )
        assert r_a.signing_pubkey == id_b.signing.public
        assert r_a.enc_pubkey == id_b.encryption.public
        assert r_b.signing_pubkey == id_a.signing.public
        assert r_b.enc_pubkey == id_a.encryption.public

    @pytest.mark.asyncio
    async def test_node_id_is_signing_pubkey_hex(self):
        """AuthResult.node_id == signing_pubkey.hex() (same identity convention)."""
        id_a, id_b = make_node(), make_node()
        ws_a, ws_b = make_pipe()
        r_a, _ = await _gather(
            do_schnorr_auth(ws_a, id_a),
            do_schnorr_auth(ws_b, id_b),
        )
        assert r_a.node_id == id_b.signing.public.hex()

    @pytest.mark.asyncio
    async def test_expected_peer_id_match_passes(self):
        id_a, id_b = make_node(), make_node()
        ws_a, ws_b = make_pipe()
        r_a, _ = await _gather(
            do_schnorr_auth(ws_a, id_a, expected_peer_id=id_b.node_id),
            do_schnorr_auth(ws_b, id_b),
        )
        assert not isinstance(r_a, Exception)
        assert r_a.node_id == id_b.node_id

    @pytest.mark.asyncio
    async def test_cell_to_node_auth_succeeds(self):
        """CellIdentity (no TLS, no address) authenticates fine via Schnorr."""
        cell = make_cell()
        node = make_node()
        ws_cell, ws_node = make_pipe()
        r_cell, r_node = await _gather(
            do_schnorr_auth(ws_cell, cell),
            do_schnorr_auth(ws_node, node),
        )
        assert not isinstance(r_cell, Exception)
        assert r_cell.node_id == node.node_id
        assert r_node.node_id == cell.cell_id


# ─── Block 2: Failure cases ───────────────────────────────────────────────────


class TestSchnorrAuthFailures:
    @pytest.mark.asyncio
    async def test_wrong_expected_peer_id_rejected(self):
        """A expects id_c but gets id_b → mismatch → ValueError."""
        id_a, id_b, id_c = make_node(), make_node(), make_node()
        ws_a, ws_b = make_pipe()

        async def peer_sends_commit_and_exits():
            """Completes Phase 1 only; exits before Phase 2 so no hang."""
            r_bytes, R = schnorr_commit(id_b.signing.private)
            pkt = Packet(
                type=T.AUTH_COMMIT,
                payload=encode_payload({
                    "R": R,
                    "signing_pub": id_b.signing.public,
                    "enc_pub": id_b.encryption.public,
                }),
                from_addr=id_b.node_id,
            )
            await ws_b.send(pack(pkt))
            await ws_b.recv()   # consume A's commit (already in queue) then exit

        results = await _gather(
            do_schnorr_auth(ws_a, id_a, expected_peer_id=id_c.node_id),
            peer_sends_commit_and_exits(),
        )
        err = _first_error(results)
        assert err is not None, "Expected ValueError for peer id mismatch"
        assert "mismatch" in str(err).lower()

    @pytest.mark.asyncio
    async def test_tampered_proof_rejected(self):
        """If peer sends s=0 as its Schnorr response, verification must fail."""
        id_a, id_b = make_node(), make_node()
        q_ab, q_ba = asyncio.Queue(), asyncio.Queue()
        ws_a = FakeWS(q_ab, q_ba)
        ws_b_inner = FakeWS(q_ba, q_ab)

        class TamperedWS:
            """Intercepts B's outgoing AUTH_RESPONSE and replaces s with zeros."""
            async def send(self, data):
                pkt = unpack(data)
                if pkt.type == T.AUTH_RESPONSE:
                    bad = Packet(
                        type=T.AUTH_RESPONSE,
                        payload=encode_payload({"s": bytes(32)}),
                        from_addr=pkt.from_addr,
                    )
                    await ws_b_inner.send(pack(bad))
                else:
                    await ws_b_inner.send(data)

            async def recv(self):
                return await ws_b_inner.recv()

        results = await _gather(
            do_schnorr_auth(ws_a, id_a),
            do_schnorr_auth(TamperedWS(), id_b),
        )
        err = _first_error(results)
        assert err is not None, "Expected ValueError for tampered proof"
        assert "verification failed" in str(err).lower()

    @pytest.mark.asyncio
    async def test_wrong_packet_type_in_commit_phase(self):
        """Peer sends PING instead of AUTH_COMMIT → ValueError mentioning auth_commit."""
        id_a = make_node()
        ws_a, ws_b = make_pipe()

        async def send_ping_then_exit():
            pkt = Packet(type=T.PING, payload=b"", from_addr="bad")
            await ws_b.send(pack(pkt))
            await ws_b.recv()   # consume A's commit (already queued)

        results = await _gather(
            do_schnorr_auth(ws_a, id_a),
            send_ping_then_exit(),
        )
        err = _first_error(results)
        assert err is not None
        assert "auth_commit" in str(err).lower()

    @pytest.mark.asyncio
    async def test_wrong_packet_type_in_response_phase(self):
        """Peer sends PING instead of AUTH_RESPONSE → ValueError mentioning auth_response."""
        id_a, id_b = make_node(), make_node()
        q_ab, q_ba = asyncio.Queue(), asyncio.Queue()
        ws_a = FakeWS(q_ab, q_ba)
        ws_b_inner = FakeWS(q_ba, q_ab)

        class PingInsteadOfResponse:
            async def send(self, data):
                pkt = unpack(data)
                if pkt.type == T.AUTH_RESPONSE:
                    bad = Packet(type=T.PING, payload=b"", from_addr=pkt.from_addr)
                    await ws_b_inner.send(pack(bad))
                else:
                    await ws_b_inner.send(data)

            async def recv(self):
                return await ws_b_inner.recv()

        results = await _gather(
            do_schnorr_auth(ws_a, id_a),
            do_schnorr_auth(PingInsteadOfResponse(), id_b),
        )
        err = _first_error(results)
        assert err is not None
        assert "auth_response" in str(err).lower()


# ─── Block 3: Symmetry and repeatability ─────────────────────────────────────


class TestSchnorrAuthSymmetry:
    @pytest.mark.asyncio
    async def test_protocol_is_symmetric(self):
        """Swapping which side 'initiates' produces mirror results."""
        id_a, id_b = make_node(), make_node()
        ws1_a, ws1_b = make_pipe()
        ws2_a, ws2_b = make_pipe()

        r1_a, r1_b = await _gather(do_schnorr_auth(ws1_a, id_a), do_schnorr_auth(ws1_b, id_b))
        r2_a, r2_b = await _gather(do_schnorr_auth(ws2_a, id_b), do_schnorr_auth(ws2_b, id_a))

        assert not isinstance(r1_a, Exception)
        assert not isinstance(r2_a, Exception)
        assert r1_a.node_id == r2_b.node_id == id_b.node_id
        assert r1_b.node_id == r2_a.node_id == id_a.node_id

    @pytest.mark.asyncio
    async def test_repeated_auth_always_succeeds(self):
        """Same two identities can authenticate multiple times without issue."""
        id_a, id_b = make_node(), make_node()
        for _ in range(3):
            ws_a, ws_b = make_pipe()
            r_a, r_b = await _gather(
                do_schnorr_auth(ws_a, id_a),
                do_schnorr_auth(ws_b, id_b),
            )
            assert not isinstance(r_a, Exception)
            assert r_a.node_id == id_b.node_id
            assert r_b.node_id == id_a.node_id

    @pytest.mark.asyncio
    async def test_three_way_auth(self):
        """Three distinct identities can each auth with every other."""
        ids = [make_node() for _ in range(3)]
        for i, j in [(0, 1), (0, 2), (1, 2)]:
            ws_a, ws_b = make_pipe()
            r_a, r_b = await _gather(
                do_schnorr_auth(ws_a, ids[i]),
                do_schnorr_auth(ws_b, ids[j]),
            )
            assert not isinstance(r_a, Exception), f"auth failed between {i} and {j}"
            assert r_a.node_id == ids[j].node_id
