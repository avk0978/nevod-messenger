"""
Nevod wire protocol.

Transport: WebSocket over TLS
Serialization: MessagePack

Packet format:
  v       — protocol version (int)
  id      — UUID v4 (str)
  type    — message type (str)
  from    — "cell_id@node_id" or "node_id" (str)
  to      — "cell_id@node_id" or "node_id" (str)
  payload — content (bytes, encrypted or plaintext depending on type)
  sig     — Ed25519 signature over (id+type+from+to+payload+ts) (bytes)
  ts      — unix timestamp (int)
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import Optional

import msgpack


PROTO_VERSION = 1


class T:
    """Message types."""
    MSG                    = "msg"
    MSG_CHUNK              = "msg_chunk"  # same E2E payload shape as MSG — a non-final
                                           # fragment of a chunked file transfer. Routed/
                                           # buffered exactly like MSG, but never triggers a
                                           # push: the node can't see chunk index/total (E2E-
                                           # encrypted), but the sender already knows which
                                           # chunk is last and sends that one as plain MSG —
                                           # see AppStore.sendChunkedStream. Without this, a
                                           # 45-chunk transfer would fire 45 separate pushes.
    MSG_SILENT             = "msg_silent"  # same E2E payload shape as MSG — a control signal
                                           # (delete:/edit:/identity_deleted:/contact-added
                                           # notice) that never becomes a visible chat bubble
                                           # on the recipient's side. Routed/buffered exactly
                                           # like MSG (delivery ACKs, offline/undeliverable
                                           # notices to the sender all still apply), but never
                                           # push-eligible — the node can't see the plaintext
                                           # prefix (E2E-encrypted) to tell it apart from real
                                           # content, so without its own wire type these were
                                           # paging recipients with a "New message" push for
                                           # something that produces no message in the chat.
    ACK                    = "ack"
    REACT                  = "react"  # single emoji reaction to a message — routed/buffered
                                       # generically exactly like ACK (no push, no special
                                       # router branch needed: only MSG/VCALL_OFFER trigger
                                       # pushes, everything else falls through to the plain
                                       # deliver-or-buffer path)
    PING                   = "ping"
    PONG                   = "pong"
    GOSSIP                 = "gossip"
    NODE_REGISTER          = "node_register"
    NODE_VOTE              = "node_vote"
    NODE_CERT              = "node_cert"
    NODE_REMOVE            = "node_remove"
    NODE_LEAVING           = "node_leaving"
    PRESENCE_QUERY         = "presence_query"
    PRESENCE_RESPONSE      = "presence_response"
    CELL_REGISTER          = "cell_register"
    CELL_REGISTER_NACK     = "cell_register_nack"
    # invite_mode="admin" registration channel — sent by a not-yet-admitted cell after
    # a CELL_REGISTER_NACK{reason:"invite_required"}, on the same already-authenticated
    # connection. No code/email involved — see NodeIdentity.admin_cell_ids's doc comment
    # and MD_Discuss/DISCUSS_REGISTRATION_CHANNEL.md for the full design.
    JOIN_REQUEST           = "join_request"
    JOIN_REQUEST_ACK       = "join_request_ack"
    JOIN_REQUEST_RESOLVED  = "join_request_resolved"  # server-initiated, sent the moment an
                                                       # admin approves/denies — best-effort
                                                       # over the SAME still-open connection a
                                                       # pending applicant's client kept alive
                                                       # after its invite_required nack (see
                                                       # transport.py: peer_node_id is tracked
                                                       # from auth, before any admission check,
                                                       # so send_to() reaches them even while
                                                       # never admitted). Lets a waiting client
                                                       # react the instant a decision is made
                                                       # instead of only finding out on its next
                                                       # reconnect/foreground/push — a request
                                                       # can sit pending for days, so inferring
                                                       # the outcome from a connection-status
                                                       # flicker alone isn't enough.
    CELL_INVITE            = "cell_invite"
    INVITE_CREATE          = "invite_create"
    INVITE_RESPONSE        = "invite_response"
    CHILD_PRESENCE_UPDATE  = "child_presence_update"
    AUTH_COMMIT              = "auth_commit"
    AUTH_CHALLENGE           = "auth_challenge"
    AUTH_RESPONSE            = "auth_response"
    GROUP_MEMBERS_REQUEST    = "group_members_request"
    GROUP_MEMBERS_RESPONSE   = "group_members_response"
    TURN_CREDS               = "turn_creds"
    CARD_CREATE              = "card_create"
    CARD_RESPONSE            = "card_response"
    PUSH_REGISTER            = "push_register"
    CHAT_PREFS               = "chat_prefs"
    NODE_LIST_REQUEST        = "node_list_request"
    NODE_LIST_RESPONSE       = "node_list_response"
    CELL_DEREGISTER          = "cell_deregister"
    CELL_REMOVED             = "cell_removed"
    VCALL_OFFER              = "vcall_offer"  # same E2E payload shape as MSG; separate type
                                               # lets the router trigger a VoIP push without
                                               # ever needing to decrypt the (opaque) content
    VCALL_SIGNAL              = "vcall_signal"  # ring/answer/ice/reject/hangup/busy — same
                                                 # payload shape too, but never wakes the app
                                                 # (only the initial offer should) and never
                                                 # deserves a "New message" alert push either
    PUSH_RELAY_REQUEST        = "push_relay_request"  # node-to-node: "please send this push,
                                                        # I have no credentials for this platform"
    TURN_RELAY_REQUEST        = "turn_relay_request"  # node-to-node: "generate TURN creds for
                                                        # my cell, I have no TURN_SECRET/coturn"
    TURN_RELAY_RESPONSE       = "turn_relay_response"  # reply carrying the generated creds
    REACHABILITY_PROBE        = "reachability_probe"  # node-to-node: "dial my advertised
                                                        # address back and tell me if it worked"
                                                        # — self-diagnostics, see diagnostics.py
    REACHABILITY_RESULT       = "reachability_result"  # reply carrying the boolean
    NODE_CELLS_REQUEST        = "node_cells_request"  # "what cells has this node's admin
                                                        # published for discovery?" — gated by
                                                        # NodeIdentity.cells_visibility, see
                                                        # node.py's _handle_node_cells_request.
                                                        # Distinct from the private `cells` table
                                                        # (every registered cell, not just the
                                                        # ones an admin chose to list publicly).
    NODE_CELLS_RESPONSE       = "node_cells_response"


@dataclass
class Packet:
    type: str
    payload: bytes
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_addr: str = ""
    to_addr: str = ""
    sig: bytes = b""
    ts: int = field(default_factory=lambda: int(time.time()))
    v: int = PROTO_VERSION
    # Cleartext (not E2E-encrypted) display name of the sending cell — only ever
    # set on vcall_offer, by the calling client itself (same value it already puts
    # in the encrypted JSON offer, just duplicated here in the open). Needed for
    # VoIP push: a node must show a real caller name without decrypting the
    # offer, and the *receiving* node generally has no local record of a caller
    # registered on a different node (storage.get_cell only sees its own home
    # cells) — so this can't be resolved locally the way a same-node call's
    # caller name could be.
    caller_name: str = ""

    def sign_data(self) -> bytes:
        """Canonical bytes to sign: id + type + from + to + payload + ts + caller_name."""
        return (
            self.id.encode()
            + self.type.encode()
            + self.from_addr.encode()
            + self.to_addr.encode()
            + self.payload
            + str(self.ts).encode()
            + self.caller_name.encode()
        )


def pack(packet: Packet) -> bytes:
    return msgpack.packb(
        {
            "v": packet.v,
            "id": packet.id,
            "type": packet.type,
            "from": packet.from_addr,
            "to": packet.to_addr,
            "payload": packet.payload,
            "sig": packet.sig,
            "ts": packet.ts,
            "caller_name": packet.caller_name,
        },
        use_bin_type=True,
    )


def unpack(data: bytes) -> Packet:
    d = msgpack.unpackb(data, raw=False)
    return Packet(
        v=d.get("v", PROTO_VERSION),
        id=d.get("id", ""),
        type=d.get("type", ""),
        from_addr=d.get("from", ""),
        to_addr=d.get("to", ""),
        payload=d.get("payload", b"") or b"",
        sig=d.get("sig", b"") or b"",
        ts=d.get("ts", 0),
        caller_name=d.get("caller_name", "") or "",
    )


# --- Signing ---

def sign_packet(packet: Packet, signing_kp) -> Packet:
    """Sign packet in-place (sets sig field) and return it."""
    from .crypto import sign
    packet.sig = sign(packet.sign_data(), signing_kp)
    return packet


def verify_packet(packet: Packet, signing_pubkey: bytes) -> bool:
    """Verify packet signature. Returns False if sig is missing or invalid."""
    if not packet.sig:
        return False
    from .crypto import verify
    return verify(packet.sign_data(), packet.sig, signing_pubkey)


# --- Payload helpers (msgpack encode/decode dicts into payload bytes) ---

def encode_payload(data: dict) -> bytes:
    return msgpack.packb(data, use_bin_type=True)


def decode_payload(payload: bytes) -> dict:
    return msgpack.unpackb(payload, raw=False)


# --- Specific packet constructors ---

def make_ping(from_node: str, to_node: str) -> Packet:
    return Packet(type=T.PING, payload=b"", from_addr=from_node, to_addr=to_node)


def make_pong(from_node: str, to_node: str, ping_id: str) -> Packet:
    return Packet(
        type=T.PONG,
        payload=encode_payload({"ping_id": ping_id}),
        from_addr=from_node,
        to_addr=to_node,
    )


def make_gossip(from_node: str, node_table_entries: list,
                presence_entries: list = None) -> Packet:
    payload: dict = {"nodes": node_table_entries}
    if presence_entries:
        payload["presence"] = presence_entries
    return Packet(
        type=T.GOSSIP,
        payload=encode_payload(payload),
        from_addr=from_node,
    )


def make_child_presence_update(from_node: str, to_node: str,
                                cell_id: str, child_node_id: str,
                                child_address: str,
                                child_tls_fingerprint: str = "") -> Packet:
    return Packet(
        type=T.CHILD_PRESENCE_UPDATE,
        payload=encode_payload({
            "cell_id":               cell_id,
            "child_node_id":         child_node_id,
            "child_address":         child_address,
            "child_tls_fingerprint": child_tls_fingerprint,
        }),
        from_addr=from_node,
        to_addr=to_node,
    )


def make_auth_challenge(from_node: str, to_node: str, nonce: bytes) -> Packet:
    return Packet(
        type=T.AUTH_CHALLENGE,
        payload=encode_payload({"nonce": nonce}),
        from_addr=from_node,
        to_addr=to_node,
    )


def make_ack(from_addr: str, to_addr: str,
             message_id: str, status: str) -> Packet:
    return Packet(
        type=T.ACK,
        payload=encode_payload({"message_id": message_id, "status": status}),
        from_addr=from_addr,
        to_addr=to_addr,
    )


def make_group_members_request(from_addr: str, to_node: str) -> Packet:
    return Packet(
        type=T.GROUP_MEMBERS_REQUEST,
        payload=b"",
        from_addr=from_addr,
        to_addr=to_node,
    )


def make_group_members_response(from_node: str, to_addr: str, members: list) -> Packet:
    """members: list of {"cell_id": str, "enc_pubkey": bytes}"""
    return Packet(
        type=T.GROUP_MEMBERS_RESPONSE,
        payload=encode_payload({"members": members}),
        from_addr=from_node,
        to_addr=to_addr,
    )


def make_join_request(from_addr: str, to_node: str, note: str = "",
                       display_name: str = "") -> Packet:
    """Sent by a not-yet-admitted cell after CELL_REGISTER_NACK{reason:"invite_required"}
    on a node with invite_mode="admin" — see JOIN_REQUEST's own comment in T."""
    return Packet(
        type=T.JOIN_REQUEST,
        payload=encode_payload({"note": note, "display_name": display_name}),
        from_addr=from_addr,
        to_addr=to_node,
    )


def make_join_request_ack(from_node: str, to_addr: str, ok: bool, reason: str = "") -> Packet:
    payload = {"ok": ok}
    if reason:
        payload["reason"] = reason
    return Packet(
        type=T.JOIN_REQUEST_ACK,
        payload=encode_payload(payload),
        from_addr=from_node,
        to_addr=to_addr,
    )


def make_join_request_resolved(from_node: str, to_addr: str, approved: bool) -> Packet:
    return Packet(
        type=T.JOIN_REQUEST_RESOLVED,
        payload=encode_payload({"approved": approved}),
        from_addr=from_node,
        to_addr=to_addr,
    )


def make_node_list_request(from_addr: str, to_node: str) -> Packet:
    return Packet(
        type=T.NODE_LIST_REQUEST,
        payload=b"",
        from_addr=from_addr,
        to_addr=to_node,
    )


def make_node_list_response(from_node: str, to_addr: str, nodes: list) -> Packet:
    """nodes: list of {"node_id": str, "name": str, "address": str}"""
    return Packet(
        type=T.NODE_LIST_RESPONSE,
        payload=encode_payload({"nodes": nodes}),
        from_addr=from_node,
        to_addr=to_addr,
    )


def make_node_cells_request(from_addr: str, to_node: str) -> Packet:
    return Packet(
        type=T.NODE_CELLS_REQUEST,
        payload=b"",
        from_addr=from_addr,
        to_addr=to_node,
    )


def make_node_cells_response(from_node: str, to_addr: str, cells: list) -> Packet:
    """cells: list of {"cell_id", "name", "description", "kind", "enc_pubkey" (bytes,
    only for kind="bot"), "ai_providers" (BYOK AI bots only), "landing_md" (only for
    kind="page")}"""
    return Packet(
        type=T.NODE_CELLS_RESPONSE,
        payload=encode_payload({"cells": cells}),
        from_addr=from_node,
        to_addr=to_addr,
    )


def make_reachability_probe(from_node: str, to_node: str, address: str) -> Packet:
    """`address` is the asker's own claimed reachable address — used only as a fallback
    when the responder doesn't already have this peer in its node_table (e.g. right
    after a fresh join, before the first gossip round). Not a trust concern: whoever
    answers there still has to authenticate as `from_node`'s exact identity for the
    probe to come back "reachable" (see node.py's _test_reachability)."""
    return Packet(
        type=T.REACHABILITY_PROBE,
        payload=encode_payload({"address": address}),
        from_addr=from_node,
        to_addr=to_node,
    )


def make_reachability_result(from_node: str, to_node: str, reachable: bool) -> Packet:
    return Packet(
        type=T.REACHABILITY_RESULT,
        payload=encode_payload({"reachable": reachable}),
        from_addr=from_node,
        to_addr=to_node,
    )


def make_node_register(from_node: str, to_node: str, invite_code: str,
                       address: str, tls_fingerprint: str, name: str = "",
                       push_relay_platforms: str = "", turn_relay: bool = False) -> Packet:
    return Packet(
        type=T.NODE_REGISTER,
        payload=encode_payload({
            "invite_code":          invite_code,
            "address":              address,
            "tls_fingerprint":      tls_fingerprint,
            "name":                 name,
            "push_relay_platforms": push_relay_platforms,
            "turn_relay":           turn_relay,
        }),
        from_addr=from_node,
        to_addr=to_node,
    )


def make_push_relay_request(from_node: str, to_node: str, platform: str,
                            push_token: str, title: str, body: str,
                            kind: str = "alert", caller_id: str = "") -> Packet:
    """Node-to-node: "I have no push credentials for `platform` — please send
    this push on my behalf." Sent when this node's own _send_push (or
    _send_voip_push) would otherwise be a silent no-op. See router.py's
    _send_push/_relay_voip_push / node.py's _handle_push_relay_request.

    kind="alert" (default) is a regular "New message" notification (title/body
    used as-is; caller_id doubles as the sender's cell id here, for the iOS
    Notification Service Extension's local-alias rewrite and tap-to-deep-link —
    see node/push.py's sender_cell_id). kind="voip" is a call-offer wakeup —
    title carries the caller's display name and caller_id their cell id,
    matching APNsSender.send_voip's signature; body is unused for voip."""
    return Packet(
        type=T.PUSH_RELAY_REQUEST,
        payload=encode_payload({
            "platform":   platform,
            "push_token": push_token,
            "title":      title,
            "body":       body,
            "kind":       kind,
            "caller_id":  caller_id,
        }),
        from_addr=from_node,
        to_addr=to_node,
    )


def make_turn_relay_request(from_node: str, to_node: str, request_id: str, cell_id: str) -> Packet:
    """Node-to-node: "I have no TURN_SECRET/coturn — please generate TURN
    credentials for my cell." See node.py's _request_turn_relay /
    _handle_turn_relay_request."""
    return Packet(
        type=T.TURN_RELAY_REQUEST,
        payload=encode_payload({"request_id": request_id, "cell_id": cell_id}),
        from_addr=from_node,
        to_addr=to_node,
    )


def make_turn_relay_response(from_node: str, to_node: str, request_id: str,
                             creds: Optional[dict]) -> Packet:
    """Reply to TURN_RELAY_REQUEST — `creds` is None if the request was
    rejected (unknown requester, rate-limited, or we turned out to have no
    TURN_SECRET either)."""
    payload = {"request_id": request_id, "ok": creds is not None}
    if creds is not None:
        payload.update(creds)
    return Packet(
        type=T.TURN_RELAY_RESPONSE,
        payload=encode_payload(payload),
        from_addr=from_node,
        to_addr=to_node,
    )


def make_node_cert(from_node: str, to_node: str, ok: bool,
                   node_table: list = None, reason: str = "",
                   reachable: bool = None) -> Packet:
    payload: dict = {"ok": ok}
    if ok:
        payload["node_table"] = node_table or []
        if reachable is not None:
            # Did the recommender manage to dial the address we just
            # registered? Lets the joining side know immediately whether
            # port-forwarding/NAT/VPN is actually working, instead of
            # discovering it only when some future peer can't connect.
            payload["reachable"] = reachable
    else:
        payload["reason"] = reason
    return Packet(
        type=T.NODE_CERT,
        payload=encode_payload(payload),
        from_addr=from_node,
        to_addr=to_node,
    )


# --- Node-invite token: "ADDRESS|TLS_FINGERPRINT|CODE" ---
# A brand-new node doesn't yet know any node's address, unlike a cell invite
# (which is entered into an app already pointed at a specific node) — so the
# token has to bundle the bootstrap address + fingerprint alongside the code.

def make_node_invite_token(address: str, tls_fingerprint: str, code: str) -> str:
    return f"{address}|{tls_fingerprint}|{code}"


def parse_node_invite_token(token: str) -> tuple[str, str, str]:
    parts = token.strip().split("|")
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"malformed node invite token: {token!r}")
    address, tls_fingerprint, code = parts
    return address, tls_fingerprint, code


# --- Cell-invite token: "ADDRESS|TLS_FINGERPRINT|CODE" ---
# Same idea as the node-invite token above, but for onboarding a new *cell*
# (app user) who isn't pointed at any node yet — e.g. scanning a friend's QR
# code cold. A bare short code (the existing "XXXX-XXXX" format) only works
# once the app already knows which node to talk to; this bundles that in.
# tls_fingerprint may be empty — that means "no pinning needed, use normal
# system CA trust" (a deployment fronted by a reverse proxy with a real
# certificate, e.g. prod's nginx; see Node._public_client_endpoint).

def make_cell_invite_token(address: str, tls_fingerprint: str, code: str) -> str:
    return f"{address}|{tls_fingerprint}|{code}"


CELL_INVITE_LINK_BASE = "https://nevod.network/join/#t="


def make_cell_invite_link(token: str) -> str:
    """QR/share form of a cell invite token: an https link the phone's own camera can open
    (a bare token only works from the scanner inside Nevod — device test 2026-10-16). The
    token rides in the #fragment, so the web server never receives it; nevod.network/join/
    hands it to the app via nevod://join?t=…, and the app's scanner accepts the link too."""
    from urllib.parse import quote
    return CELL_INVITE_LINK_BASE + quote(token, safe="")


def parse_cell_invite_token(token: str) -> tuple[str, str, str]:
    parts = token.strip().split("|")
    if len(parts) != 3 or not parts[0] or not parts[2]:
        raise ValueError(f"malformed cell invite token: {token!r}")
    address, tls_fingerprint, code = parts
    return address, tls_fingerprint, code


def make_auth_response(from_node: str, to_node: str,
                       nonce: bytes, signature: bytes,
                       signing_pubkey: bytes, enc_pubkey: bytes) -> Packet:
    return Packet(
        type=T.AUTH_RESPONSE,
        payload=encode_payload({
            "nonce": nonce,
            "sig": signature,
            "signing_pubkey": signing_pubkey,
            "enc_pubkey": enc_pubkey,
        }),
        from_addr=from_node,
        to_addr=to_node,
    )
