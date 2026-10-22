"""
Node/cell authentication — Schnorr ZKP on Edwards25519.

Protocol (4 messages, 2 round trips — same as old challenge-response):

  A → B: AUTH_COMMIT  { R_A, signing_pub_A, enc_pub_A }
  B → A: AUTH_COMMIT  { R_B, signing_pub_B, enc_pub_B }
  A → B: AUTH_RESPONSE { s_A }          s = r + c_self · x mod L
  B → A: AUTH_RESPONSE { s_B }

Challenge is computed from the transcript (Fiat-Shamir):
  c_self  = H("nevod-schnorr-v1" || R_self  || X_self  || R_peer || X_peer)
  c_peer  = H("nevod-schnorr-v1" || R_peer  || X_peer  || R_self || X_self)

Both sides independently derive the same two challenges from the same data.
Each side proves itself to the other with c_self; verifies the other with c_peer.

Works identically for node↔node and cell↔node.
"""

import hashlib
from typing import Optional

from .crypto import L, schnorr_commit, schnorr_prove, schnorr_verify
from .protocol import T, Packet, pack, unpack, encode_payload, decode_payload

_DOMAIN = b"nevod-schnorr-v1"


def _challenge(R_prover: bytes, X_prover: bytes,
               R_verifier: bytes, X_verifier: bytes) -> int:
    """Fiat-Shamir challenge: H(domain || R_prover || X_prover || R_verifier || X_verifier) mod L."""
    h = hashlib.sha256(_DOMAIN + R_prover + X_prover + R_verifier + X_verifier).digest()
    return int.from_bytes(h, 'little') % L


class AuthResult:
    def __init__(self, node_id: str, signing_pubkey: bytes, enc_pubkey: bytes):
        self.node_id = node_id
        self.signing_pubkey = signing_pubkey
        self.enc_pubkey = enc_pubkey


async def do_schnorr_auth(ws, identity,
                           expected_peer_id: Optional[str] = None) -> AuthResult:
    """
    Full Schnorr mutual auth handshake over a WebSocket (or any send/recv object).
    Works for both NodeIdentity and CellIdentity.
    Raises ValueError on auth failure.
    """
    our_id = getattr(identity, 'node_id', None) or getattr(identity, 'cell_id', None)
    signing_priv = identity.signing.private
    signing_pub  = identity.signing.public   # bytes
    enc_pub      = identity.encryption.public  # bytes

    # ── Phase 1: Exchange commitments ────────────────────────────────────────
    r_bytes, R_self = schnorr_commit(signing_priv)

    commit_pkt = Packet(
        type=T.AUTH_COMMIT,
        payload=encode_payload({
            "R":           R_self,
            "signing_pub": signing_pub,
            "enc_pub":     enc_pub,
        }),
        from_addr=our_id,
    )
    await ws.send(pack(commit_pkt))

    their_commit = unpack(await ws.recv())
    if their_commit.type != T.AUTH_COMMIT:
        raise ValueError(f"Schnorr: expected AUTH_COMMIT, got {their_commit.type!r}")

    d      = decode_payload(their_commit.payload)
    R_peer = bytes(d["R"])
    X_peer = bytes(d["signing_pub"])
    E_peer = bytes(d["enc_pub"])

    peer_id = X_peer.hex()
    if expected_peer_id and peer_id != expected_peer_id:
        raise ValueError(
            f"Schnorr: peer identity mismatch "
            f"(expected {expected_peer_id[:8]}… got {peer_id[:8]}…)"
        )

    # ── Phase 2: Compute challenges + exchange responses ─────────────────────
    c_self = _challenge(R_self, signing_pub, R_peer, X_peer)
    c_peer = _challenge(R_peer, X_peer, R_self, signing_pub)

    s_self = schnorr_prove(signing_priv, r_bytes, c_self)

    response_pkt = Packet(
        type=T.AUTH_RESPONSE,
        payload=encode_payload({"s": s_self}),
        from_addr=our_id,
    )
    await ws.send(pack(response_pkt))

    their_resp = unpack(await ws.recv())
    if their_resp.type != T.AUTH_RESPONSE:
        raise ValueError(f"Schnorr: expected AUTH_RESPONSE, got {their_resp.type!r}")

    s_peer = bytes(decode_payload(their_resp.payload)["s"])

    # Verify peer's Schnorr proof: s_peer·G == R_peer + c_peer·X_peer
    if not schnorr_verify(X_peer, R_peer, c_peer, s_peer):
        raise ValueError("Schnorr: peer proof verification failed")

    return AuthResult(
        node_id=peer_id,
        signing_pubkey=X_peer,
        enc_pubkey=E_peer,
    )
