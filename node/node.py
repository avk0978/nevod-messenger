"""
Nevod Node — main orchestrator.

Lifecycle:
  node = await Node.create(identity_path, db_path)
  await node.start()
  ...
  await node.stop()

Genesis mode (first node in the network):
  node = await Node.create_genesis(address, identity_path, db_path)
"""

import asyncio
import base64
import hashlib
import hmac
import logging
import os
import random
import time
import uuid
from typing import Optional, Callable, Awaitable

from .identity import NodeIdentity
from .storage import Storage, NodeEntry, CARD_TTL_SECS
from .transport import Transport, PeerConnection
from .gossip import GossipEngine
from .router import Router, parse_addr
from .protocol import (Packet, T, pack, unpack, encode_payload, decode_payload,
                        make_turn_relay_request, make_turn_relay_response,
                        make_group_members_response, sign_packet,
                        make_node_register, make_node_cert, make_push_relay_request,
                        make_node_list_response, make_reachability_probe,
                        make_reachability_result, make_node_cells_response,
                        make_join_request_ack, make_join_request_resolved)
from . import push as _push
from .names import is_reserved_name, is_reserved_node_name, official_cell_ids
from .limits import new_cells_limiter, open_node_joins_limiter

log = logging.getLogger(__name__)

# Diagnostic logs sent to the administrator from the app — see Node._store_diag_log and
# DiagnosticReport.inAppPrefix on iOS (keep the prefix in sync).
DIAG_LOG_PREFIX = "nevod-log:"
DIAG_LOG_MAX_PACKED = 4 * 1024 * 1024
DIAG_LOG_MAX_RAW = 8 * 1024 * 1024
DIAG_LOGS_PER_DAY = 10

MessageCallback = Callable[[Packet], Awaitable[None]]


class Node:
    def __init__(
        self,
        identity: NodeIdentity,
        storage: Storage,
        on_message: Optional[MessageCallback] = None,
        identity_path: Optional[str] = None,
    ):
        self.identity = identity
        self.storage = storage
        self.on_message = on_message
        # Sibling-path base for the built-in registrar identity — see _ensure_registrar().
        # None only for a Node built directly (bypassing create()/create_genesis(), e.g.
        # some existing tests) — registrar setup is skipped in that case, harmlessly.
        self._identity_path = identity_path
        self._registrar_identity = None
        # Built-in "administrator" cell (every node) — see _ensure_administrator().
        self._administrator_identity = None
        # Per-IP brakes for a public open node — see node/limits.py (off by default).
        self._new_cells_limiter = new_cells_limiter()
        self._open_node_joins_limiter = open_node_joins_limiter()

        self.transport = Transport(identity, on_packet=self._dispatch)
        self.gossip = GossipEngine(self)
        self.router = Router(self)
        # AI bots the admin switched on (node/ai_bots.py) — none unless added in the panel.
        # Needs a data dir for their keys, so not for a Node built directly (tests).
        self.listen_endpoint = ("", 0)
        self.ai_bots = None
        if identity_path:
            from .ai_bots import AIBotManager
            self.ai_bots = AIBotManager(self, os.path.dirname(identity_path) or ".")
        self.transport.on_disconnect = self.router.on_connection_lost
        self.apns: _push.APNsSender | None = _push.from_env()
        # Platforms this node can relay push for on behalf of a node with no
        # credentials of its own — see storage.NodeEntry.push_relay_platforms
        # and _handle_push_relay_request. Only "apns" exists today; a future
        # FCM-capable node (once an Android client exists) would add "fcm" here.
        self.push_relay_platforms: list[str] = ["apns"] if self.apns is not None else []
        # Cached once at startup (not re-read per call) so the capability we
        # advertise (turn_relay) can never drift from what _generate_turn_creds
        # actually has available — presumes a coturn process is really
        # listening on it, not verified here. See storage.NodeEntry.turn_relay
        # / _request_turn_relay.
        self._turn_secret: str = os.environ.get("TURN_SECRET", "")
        self.turn_relay: bool = bool(self._turn_secret)
        # keyed by peer node_id — one in-flight join() per Node instance is all
        # that's ever needed, so no separate request-id correlation is required
        self._pending_node_cert: dict[str, asyncio.Future] = {}
        # push-relay abuse guard: (requesting node_id) → monotonic time of last
        # relay we performed for them. Mirrors router.py's own push rate-limit.
        self._relay_times: dict[str, float] = {}
        # same idea for TURN relay requests we serve for other nodes
        self._turn_relay_times: dict[str, float] = {}
        # request_id → Future, for our own outstanding TURN_RELAY_REQUESTs
        self._pending_turn_futures: dict[str, asyncio.Future] = {}
        # peer_node_id → Future, for our own outstanding REACHABILITY_PROBEs — one
        # in-flight probe per peer is all self-diagnostics ever needs at once
        self._pending_reachability: dict[str, asyncio.Future] = {}

    @classmethod
    async def create(cls, identity_path: str, db_path: str,
                     on_message: Optional[MessageCallback] = None) -> "Node":
        identity = NodeIdentity.load(identity_path)
        storage = Storage(db_path)
        await storage.open()
        return cls(identity, storage, on_message, identity_path=identity_path)

    @classmethod
    async def create_genesis(cls, address: str, identity_path: str, db_path: str,
                              access: str = "open",
                              node_type: str = "permanent",
                              parent_node_id: str = "",
                              name: str = "",
                              on_message: Optional[MessageCallback] = None) -> "Node":
        """Create and persist the first node in the network."""
        identity = NodeIdentity.generate(
            address, node_type=node_type, access=access,
            parent_node_id=parent_node_id, name=name,
        )
        identity.save(identity_path)

        storage = Storage(db_path)
        await storage.open()

        node = cls(identity, storage, on_message, identity_path=identity_path)

        # register self in node_table
        await storage.upsert_node(NodeEntry(
            node_id=identity.node_id,
            address=address,
            type=node_type,
            access=access,
            tls_fingerprint=identity.tls_fingerprint,
            name=identity.name,
            push_relay_platforms=",".join(node.push_relay_platforms),
            turn_relay=node.turn_relay,
            last_seen=int(time.time()),
            status="online",
            added_at=int(time.time()),
        ))

        log.info("genesis node created: %s at %s", identity.node_id[:16], address)
        return node

    async def start(self):
        import os
        host, port = _split_address(self.identity.address)
        bind_host = os.environ.get("NEVOD_BIND", host)
        await self.transport.start(bind_host, port)
        self.listen_endpoint = (bind_host, port)
        self.gossip.start()
        # Refresh our own node_table row every start — a genesis node inserts
        # itself once at creation and otherwise never updates that row again, so
        # capability flags (push_relay_platforms) or a changed address would
        # otherwise go stale until someone re-joins. Cheap no-op elsewhere.
        existing = await self.storage.get_node(self.identity.node_id)
        await self.storage.upsert_node(NodeEntry(
            node_id=self.identity.node_id,
            address=self.identity.address,
            type=existing.type if existing else "permanent",
            access=self.identity.access,
            tls_fingerprint=self.identity.tls_fingerprint,
            name=self.identity.name,
            push_relay_platforms=",".join(self.push_relay_platforms),
            turn_relay=self.turn_relay,
            last_seen=int(time.time()),
            status="online",
            added_at=existing.added_at if existing else int(time.time()),
        ))
        # upsert_node above never actually updates access/type for an existing row (see
        # Storage.refresh_own_node_flags' own doc comment for why that's deliberate) — this
        # is what actually picks up a changed self.identity.access (e.g. via
        # `nevod.py set-access`) or self.identity.node_type on restart. Only ever
        # touches our own row.
        #
        # Bug found 2026-09-13 adding an admin-panel node_type setter: this used to pass
        # `existing.type if existing else "permanent"` — re-feeding the OLD node_table
        # value straight back in, instead of the current identity.node_type. That made
        # a node_type change a permanent no-op even across restarts (unlike access,
        # right above, which correctly reads self.identity.access) — identity.json's
        # type never propagated into the row peers actually see via gossip.
        await self.storage.refresh_own_node_flags(
            self.identity.node_id, self.identity.access, self.identity.node_type,
        )
        await self._ensure_registrar()
        await self._ensure_administrator()
        if self.ai_bots:
            await self.ai_bots.start()
        log.info("node %s started on %s:%d", self.identity.node_id[:16], bind_host, port)

    async def _ensure_registrar(self):
        """The invite_mode="admin" registration channel needs a real, ordinary cell to
        send notifications FROM — not a new "system message" concept the client has to
        learn (see MD_Discuss/DISCUSS_REGISTRATION_CHANNEL.md). Generates (once, persisted)
        and self-registers a CellIdentity for this, the same way any other cell would
        register, just called in-process instead of over a socket. Idempotent — safe on
        every startup (register_cell_locally's register_cell() is an upsert). Only
        actually runs for invite_mode="admin" — every other node (including every test
        fixture, none of which opt into this mode) should see no behavior change
        whatsoever, in particular no extra "member" showing up in group_members_request
        results (this bit a real test — see git history if this comment predates one)."""
        if self.identity.invite_mode != "admin":
            return
        if not self._identity_path:
            return  # Node built directly, bypassing create()/create_genesis() — e.g. tests
        from .identity import CellIdentity
        registrar_path = os.path.join(os.path.dirname(self._identity_path) or ".",
                                       "registrar_identity.json")
        if os.path.exists(registrar_path):
            registrar = CellIdentity.load(registrar_path)
        else:
            registrar = CellIdentity.generate(name="Node Registrar")
            registrar.save(registrar_path)
            log.info("generated registrar identity: %s", registrar.cell_id[:16])
        self._registrar_identity = registrar
        await self.register_cell_locally(
            registrar.cell_id, registrar.signing.public, registrar.encryption.public,
            display_name="Node Registrar",
        )

    async def stop(self):
        if self.ai_bots:
            await self.ai_bots.stop()
        self.gossip.stop()
        await self.transport.stop()
        await self.storage.close()
        log.info("node %s stopped", self.identity.node_id[:16])

    async def join(self, bootstrap_address: str,
                   expected_fingerprint: Optional[str] = None,
                   invite_code: Optional[str] = None,
                   open_join: bool = False):
        """
        Connect to an existing node.

        Without invite_code and open_join=False (default): unchanged simplified v1
        behavior — the bootstrap node acts as recommender with no approval
        round-trip, just registered directly. Kept exactly as-is since a lot of
        existing tests (test_node.py, test_presence_gossip.py, etc.) depend on this
        not requiring the bootstrap's admission.

        With invite_code, OR open_join=True: sends NODE_REGISTER and waits for the
        bootstrap to admit us (NODE_CERT) — with invite_code if given, or empty if
        not (only actually succeeds against a bootstrap whose own
        `node_join_mode == "open"`; see DISCUSS_NODE_ADMISSION.md). On approval, the
        full node_table snapshot the bootstrap sends back is pulled in — existing
        gossip.py then propagates us to the rest of the network over subsequent
        rounds. open_join is a separate explicit flag rather than just "invite_code
        passed as '' instead of None" so the caller's intent (attempt a real,
        possibly-rejected admission) is unambiguous at the call site.
        """
        conn = await self.transport.connect(bootstrap_address,
                                            expected_fingerprint=expected_fingerprint)
        log.info("joined via %s (peer: %s)", bootstrap_address, conn.peer_node_id[:8])

        if invite_code or open_join:
            loop = asyncio.get_event_loop()
            fut: asyncio.Future = loop.create_future()
            self._pending_node_cert[conn.peer_node_id] = fut
            pkt = make_node_register(
                self.identity.node_id, conn.peer_node_id, invite_code or "",
                self.identity.address, self.identity.tls_fingerprint,
                self.identity.name, ",".join(self.push_relay_platforms),
                self.turn_relay,
            )
            await self.transport.send_via(conn, pkt)
            try:
                result = await asyncio.wait_for(fut, timeout=15)
            except asyncio.TimeoutError:
                self._pending_node_cert.pop(conn.peer_node_id, None)
                raise TimeoutError("no response from recommender node (timed out)")
            if not result.get("ok"):
                raise ValueError(f"join rejected: {result.get('reason', 'unknown')}")
            for n in result.get("node_table", []):
                node_id = n.get("node_id", "")
                address = n.get("address", "")
                if not node_id or not address or node_id == self.identity.node_id:
                    continue
                await self.storage.upsert_node(NodeEntry(
                    node_id=node_id,
                    address=address,
                    type=n.get("type", "permanent"),
                    access=n.get("access", "closed"),
                    tls_fingerprint=n.get("tls_fingerprint", ""),
                    name=n.get("name", ""),
                    push_relay_platforms=n.get("push_relay_platforms", ""),
                    turn_relay=bool(n.get("turn_relay", False)),
                    last_seen=int(time.time()),
                    status="online",
                    added_at=int(time.time()),
                ))
            log.info("admitted (%s) — pulled %d node_table entries",
                     "invite" if invite_code else "open", len(result.get("node_table", [])))
            return result.get("reachable")

        # register bootstrap peer in our node_table
        await self.storage.upsert_node(NodeEntry(
            node_id=conn.peer_node_id,
            address=bootstrap_address,
            type="permanent",
            access="open",
            tls_fingerprint=expected_fingerprint or "",
            last_seen=int(time.time()),
            status="online",
            added_at=int(time.time()),
        ))

    async def send_message(self, to_cell_at_node: str, plaintext: bytes,
                           from_cell_id: Optional[str] = None, msg_type: str = None):
        """
        Send an E2E encrypted message.
        to_cell_at_node: "cell_id@node_id"
        plaintext: raw message bytes
        msg_type: defaults to T.MSG (a real chat message); pass T.MSG_SILENT for a
        control signal that must not surface as a visible bubble or "New message" push.
        """
        from .crypto import encrypt
        from .protocol import Packet

        cell_id, _ = to_cell_at_node.split("@", 1)
        cell = await self.storage.get_cell(cell_id)
        if cell is None:
            raise ValueError(f"unknown cell {cell_id[:8]} — no enc_pubkey")

        encrypted = encrypt(plaintext, cell.enc_pubkey)
        payload = encode_payload({
            "ephemeral_pubkey": encrypted["ephemeral_pubkey"],
            "nonce":            encrypted["nonce"],
            "ciphertext":       encrypted["ciphertext"],
        })

        from_addr = (
            f"{from_cell_id}@{self.identity.node_id}"
            if from_cell_id
            else self.identity.node_id
        )
        pkt = Packet(
            type=msg_type or T.MSG,
            payload=payload,
            from_addr=from_addr,
            to_addr=to_cell_at_node,
        )
        await self.router.route(pkt)

    # --- packet dispatcher ---

    async def _dispatch(self, pkt: Packet, conn: PeerConnection):
        t = pkt.type

        if t == T.PING:
            await self.gossip.handle_ping(pkt, conn)

        elif t == T.PONG:
            await self.gossip.handle_pong(pkt)

        elif t == T.GOSSIP:
            await self.gossip.handle_gossip(pkt)

        elif t == T.MSG or t == T.MSG_CHUNK or t == T.MSG_SILENT:
            if await self._maybe_handle_registrar_reply(pkt):
                return
            # MSG_CHUNK/MSG_SILENT never go through _maybe_handle_registrar_reply
            # (it only ever consumes T.MSG) — drop rather than route/buffer forever
            # if somehow addressed to the registrar anyway (see _is_registrar_address).
            if await self._maybe_handle_administrator_msg(pkt):
                return
            if t != T.MSG and self._is_service_address(pkt.to_addr):
                return
            await self.router.route(pkt)

        elif t == T.VCALL_OFFER:
            # Nobody can ever answer a call to a server-side service cell.
            if not self._is_service_address(pkt.to_addr):
                await self.router.route(pkt)

        elif t == T.VCALL_SIGNAL:
            await self.router.route(pkt)

        elif t == T.ACK:
            # Confirm delivery — remove from inflight tracking. This bookkeeping must
            # run regardless of where the ACK is headed (it's about the SENDER's own
            # inflight state, not the recipient) — only the trailing route() is
            # conditional, see _is_registrar_address.
            d = decode_payload(pkt.payload)
            msg_id = d.get('message_id', '')
            from_cell = pkt.from_addr.split('@')[0] if '@' in pkt.from_addr else None
            confirmed = None
            if from_cell and msg_id:
                confirmed = self.router.on_ack_received(from_cell, msg_id)
            # A file-chunk ack exists only for the in-flight tracking above: the sender
            # stores no message for a fragment's id, so routing it on would just be a wasted
            # packet per chunk (and a "NO MATCHING MESSAGE" on the sender's side).
            if confirmed is not None and confirmed.type == T.MSG_CHUNK:
                return
            if not self._is_service_address(pkt.to_addr):
                await self.router.route(pkt)

        elif t == T.REACT:
            # No inflight-tracking hook needed (unlike ACK) — a reaction isn't correlated
            # against a pending send, it's just routed straight through like anything else.
            if not self._is_service_address(pkt.to_addr):
                await self.router.route(pkt)

        elif t == T.CHILD_PRESENCE_UPDATE:
            await self._handle_child_presence_update(pkt)

        elif t == T.GROUP_MEMBERS_REQUEST:
            await self._handle_group_members_request(pkt, conn)

        elif t == T.NODE_REMOVE:
            await self._handle_node_remove(pkt)

        elif t == T.NODE_LEAVING:
            await self._handle_node_leaving(pkt)

        elif t == T.NODE_REGISTER:
            await self._handle_node_register(pkt, conn)

        elif t == T.NODE_CERT:
            await self._handle_node_cert(pkt, conn)

        elif t == T.PRESENCE_QUERY:
            await self._handle_presence_query(pkt, conn)

        elif t == T.PRESENCE_RESPONSE:
            pass  # handled by callers that await specific replies

        elif t == T.CELL_REGISTER:
            await self._handle_cell_register(pkt, conn)

        elif t == T.JOIN_REQUEST:
            await self._handle_join_request(pkt, conn)

        elif t == T.INVITE_CREATE:
            await self._handle_invite_create(pkt, conn)

        elif t == T.CARD_CREATE:
            await self._handle_card_create(pkt, conn)

        elif t == T.PUSH_REGISTER:
            await self._handle_push_register(pkt, conn)

        elif t == T.CHAT_PREFS:
            await self._handle_chat_prefs(pkt, conn)

        elif t == T.NODE_LIST_REQUEST:
            await self._handle_node_list_request(pkt, conn)

        elif t == T.NODE_CELLS_REQUEST:
            await self._handle_node_cells_request(pkt, conn)

        elif t == T.CELL_DEREGISTER:
            cell_id = conn.peer_node_id
            await self.storage.delete_cell(cell_id)
            log.info("cell self-deregistered: %s", cell_id[:8])

        elif t == T.PUSH_RELAY_REQUEST:
            await self._handle_push_relay_request(pkt, conn)

        elif t == T.TURN_RELAY_REQUEST:
            await self._handle_turn_relay_request(pkt, conn)

        elif t == T.TURN_RELAY_RESPONSE:
            await self._handle_turn_relay_response(pkt)

        elif t == T.REACHABILITY_PROBE:
            await self._handle_reachability_probe(pkt, conn)

        elif t == T.REACHABILITY_RESULT:
            await self._handle_reachability_result(pkt)

        else:
            log.debug("unhandled packet type: %s from %s", t, pkt.from_addr[:16])

    async def _handle_node_remove(self, pkt: Packet):
        try:
            data = decode_payload(pkt.payload)
            node_id = data["node_id"]
        except Exception:
            return
        await self.storage.remove_node(node_id)
        log.info("removed node %s (network broadcast)", node_id[:8])

    async def _handle_node_leaving(self, pkt: Packet):
        node_id = pkt.from_addr
        await self.storage.remove_node(node_id)
        await self.transport.connections.remove(node_id)
        log.info("node %s left gracefully", node_id[:8])

    async def _handle_node_register(self, pkt: Packet, conn: PeerConnection):
        try:
            data = decode_payload(pkt.payload)
            invite_code     = str(data.get("invite_code", ""))
            address         = str(data.get("address", ""))
            tls_fingerprint = str(data.get("tls_fingerprint", ""))
            name            = str(data.get("name", "")).strip()[:64]
            push_relay      = str(data.get("push_relay_platforms", ""))
            turn_relay      = bool(data.get("turn_relay", False))
        except Exception:
            return

        # Trust only the identity Schnorr auth already proved for this connection —
        # never a self-claimed node_id in the payload (mirrors _handle_cell_register).
        node_id = conn.peer_node_id

        if not invite_code:
            # node_join_mode="open" (opt-in, default is "invite" — see
            # DISCUSS_NODE_ADMISSION.md) admits any node with no invite at all. Mere
            # node_table presence grants no power over any cell's data — the actual
            # trust decision is which node a CELL registers on (invite_mode, a
            # separate existing field), unaffected by this.
            if self.identity.node_join_mode != "open":
                log.info("NODE_REGISTER nack (invite required): %s", node_id[:8])
                await self._send_node_cert(conn, ok=False, reason="invite_required")
                return
            # Nobody vouched for this node, so it may not borrow the project's names
            # (node/names.py), and one address may not flood the node table.
            if is_reserved_node_name(name):
                log.info("NODE_REGISTER nack (reserved name): %s name=%s", node_id[:8], name)
                await self._send_node_cert(conn, ok=False, reason="name_reserved")
                return
            known = await self.storage.get_node(node_id)
            if known is None and not self._open_node_joins_limiter.allow(getattr(conn, "remote_ip", "")):
                log.info("NODE_REGISTER nack (rate limited): %s ip=%s", node_id[:8], getattr(conn, "remote_ip", ""))
                await self._send_node_cert(conn, ok=False, reason="rate_limited")
                return
            log.info("node registering via open node_join_mode (no invite): %s", node_id[:8])
        else:
            ok = await self.storage.use_node_invite(invite_code.strip().upper(), node_id)
            if not ok:
                log.warning("NODE_REGISTER nack (bad invite): %s code=%s", node_id[:8], invite_code)
                await self._send_node_cert(conn, ok=False, reason="invite_invalid")
                return

        await self.storage.upsert_node(NodeEntry(
            node_id=node_id,
            address=address,
            type="permanent",
            access="open",
            tls_fingerprint=tls_fingerprint,
            name=name,
            push_relay_platforms=push_relay,
            turn_relay=turn_relay,
            last_seen=int(time.time()),
            status="online",
            added_at=int(time.time()),
        ))
        log.info("node admitted (%s): %s (%s)", "open" if not invite_code else "invite",
                 node_id[:8], name or "no name")

        reachable = await self._test_reachability(node_id, address, tls_fingerprint)

        all_nodes = await self.storage.get_all_nodes()
        await self._send_node_cert(conn, ok=True, node_table=[n.to_dict() for n in all_nodes],
                                   reachable=reachable)

    async def _test_reachability(self, node_id: str, address: str,
                                 tls_fingerprint: str, timeout: float = 8.0) -> bool:
        """Dials the address the joining node just registered, from here —
        the same path any other peer would use to reach it later. Cheaper
        and more honest than trusting the address at face value: catches
        the exact class of problem this was built for (NAT/port-forward not
        set up, or a VPN silently rerouting the node's own outbound
        traffic) at registration time instead of leaving the operator to
        discover it only when someone else's connection attempt fails."""
        try:
            conn = await asyncio.wait_for(
                self.transport.connect_to_node(node_id, address,
                                               expected_fingerprint=tls_fingerprint or None),
                timeout=timeout,
            )
            await conn.close()
            return True
        except Exception as e:
            log.info("reachability test failed for %s at %s: %s", node_id[:8], address, e)
            return False

    async def probe_reachability_via(self, peer_node_id: str, timeout: float = 10.0) -> Optional[bool]:
        """Self-diagnostics entry point: ask an already-known peer to dial OUR OWN
        advertised address and report whether it worked. Returns None (not False) if
        the peer itself couldn't be reached or never answered — that's "inconclusive",
        distinct from "peer answered: no, your address doesn't work"."""
        conn = await self.transport.connections.get(peer_node_id)
        if not conn:
            entry = await self.storage.get_node(peer_node_id)
            if not entry:
                return None
            try:
                conn = await asyncio.wait_for(
                    self.transport.connect_to_node(
                        peer_node_id, entry.address,
                        expected_fingerprint=entry.tls_fingerprint or None,
                    ),
                    timeout=timeout,
                )
            except Exception:
                return None
        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending_reachability[peer_node_id] = fut
        try:
            await self.transport.send_via(
                conn, make_reachability_probe(self.identity.node_id, peer_node_id, self.identity.address)
            )
            return await asyncio.wait_for(fut, timeout=timeout)
        except Exception:
            return None
        finally:
            self._pending_reachability.pop(peer_node_id, None)

    async def _handle_reachability_probe(self, pkt: Packet, conn: PeerConnection):
        """A peer is asking "can you reach me at my advertised address" — reuses the
        same dial-back check NODE_REGISTER admission uses (_test_reachability), just
        on-demand for self-diagnostics instead of only at join time.

        Prefers the address already on file for this peer (locally-verified data over
        a self-report); falls back to the address in the payload if we don't have them
        yet (e.g. right after a fresh join, before the first gossip round). Either way
        this can't be turned into an open relay for probing arbitrary third parties:
        the node_id being tested is always conn.peer_node_id (authenticated by the
        connection itself, never taken from the payload), and _test_reachability only
        reports "reachable" if whoever answers at that address proves that exact
        identity — an attacker can make us dial anywhere, but the result reveals
        nothing beyond "does a Nevod node with this specific pubkey run there"."""
        entry = await self.storage.get_node(conn.peer_node_id)
        address = entry.address if entry else ""
        tls_fingerprint = entry.tls_fingerprint if entry else ""
        if not address:
            try:
                data = decode_payload(pkt.payload)
                address = str(data.get("address", ""))
            except Exception:
                address = ""
        if not address:
            return
        reachable = await self._test_reachability(conn.peer_node_id, address, tls_fingerprint)
        resp = make_reachability_result(self.identity.node_id, pkt.from_addr, reachable)
        await self.transport.send_via(conn, resp)

    async def _handle_reachability_result(self, pkt: Packet):
        fut = self._pending_reachability.get(pkt.from_addr)
        if not fut or fut.done():
            return
        try:
            data = decode_payload(pkt.payload)
            fut.set_result(bool(data.get("reachable", False)))
        except Exception:
            fut.set_result(False)

    async def _send_node_cert(self, conn: PeerConnection, ok: bool,
                              node_table: list = None, reason: str = "",
                              reachable: bool = None):
        pkt = make_node_cert(self.identity.node_id, conn.peer_node_id, ok, node_table, reason,
                             reachable)
        sign_packet(pkt, self.identity.signing)
        await self.transport.send_via(conn, pkt)

    async def _handle_node_cert(self, pkt: Packet, conn: PeerConnection):
        """Resolves the future join() is awaiting. Unsolicited NODE_CERT (no
        pending join for this peer) is silently ignored."""
        fut = self._pending_node_cert.pop(conn.peer_node_id, None)
        if not fut or fut.done():
            return
        try:
            fut.set_result(decode_payload(pkt.payload))
        except Exception as e:
            fut.set_exception(e)

    async def _handle_presence_query(self, pkt: Packet, conn: PeerConnection):
        try:
            data = decode_payload(pkt.payload)
            cell_id = data["cell_id"]
        except Exception:
            return
        presence = await self.storage.get_presence(cell_id)
        response_payload = encode_payload({
            "cell_id": cell_id,
            "home_node_id": presence.home_node_id if presence else None,
            "visiting_node_id": presence.visiting_node_id if presence else None,
        })
        response = Packet(
            type=T.PRESENCE_RESPONSE,
            payload=response_payload,
            from_addr=self.identity.node_id,
            to_addr=pkt.from_addr,
        )
        await self.transport.send_via(conn, response)

    async def _handle_cell_register(self, pkt: Packet, conn: PeerConnection):
        try:
            data = decode_payload(pkt.payload)
            cell_id      = data["cell_id"]
            signing_pub  = bytes(data["signing_pubkey"])
            enc_pub      = bytes(data["enc_pubkey"])
            is_home      = bool(data.get("is_home", True))
            invite_code  = data.get("invite_code", "")
            display_name = str(data.get("display_name", "")).strip()[:64]
        except Exception:
            return

        # Claimed identity must match the key proven during auth handshake
        if signing_pub != conn.peer_signing_pubkey:
            log.warning("CELL_REGISTER rejected: signing_pubkey mismatch from %s",
                        conn.peer_node_id[:8])
            return
        if cell_id != conn.peer_node_id:
            log.warning("CELL_REGISTER rejected: cell_id/peer_node_id mismatch")
            return

        # Invite-mode access control
        mode = self.identity.invite_mode
        if mode != "open":
            already_allowed = await self.storage.is_cell_allowed(cell_id)
            if not already_allowed:
                if not invite_code:
                    log.info("CELL_REGISTER nack (invite required): %s", cell_id[:8])
                    # invite_mode rides along so the client knows whether a JOIN_REQUEST
                    # (invite_mode="admin" only, see _handle_join_request) is even worth
                    # offering — both "admin" and "delegated" NACK identically otherwise,
                    # and a JOIN_REQUEST sent to a "delegated" node is just silently ignored.
                    await self._send_nack(conn, "invite_required", extra={"invite_mode": mode})
                    return
                ok = await self.storage.use_invite(invite_code.strip().upper(), cell_id)
                if not ok:
                    log.warning("CELL_REGISTER nack (bad invite): %s code=%s",
                                cell_id[:8], invite_code)
                    await self._send_nack(conn, "invite_invalid")
                    return
                log.info("invite used: code=%s cell=%s", invite_code, cell_id[:8])

        # Reserved names (administrator, admin, support, …) are for this node's own official
        # cells only — see node/names.py. Answered with the existing "name_taken" NACK so every
        # client version, old ones included, already shows "name taken, choose another".
        # Only NEW names are checked: every client re-sends cell_register with its current
        # name on every reconnect, so a cell already registered under this exact name (from
        # before this check existed) must keep reconnecting — otherwise it'd be NACK'd on
        # every connect and locked out. The iOS app separately flags look-alike names from
        # non-official cells, which covers those grandfathered ones.
        if display_name and is_reserved_name(display_name) and cell_id.lower() not in official_cell_ids():
            existing = await self.storage.get_cell(cell_id)
            if not (existing and existing.display_name == display_name):
                log.info("CELL_REGISTER nack (reserved name): %s name=%s", cell_id[:8], display_name)
                await self._send_nack(conn, "name_taken")
                return

        if display_name:
            existing_name_cell = await self.storage.get_cell_by_name(display_name)
            if existing_name_cell and existing_name_cell != cell_id:
                log.info("CELL_REGISTER nack (name taken): %s name=%s", cell_id[:8], display_name)
                await self._send_nack(conn, "name_taken")
                return

        # A brand-new cell only (a reconnect never counts) — see node/limits.py.
        if (await self.storage.get_cell(cell_id) is None
                and not self._new_cells_limiter.allow(getattr(conn, "remote_ip", ""))):
            log.info("CELL_REGISTER nack (rate limited): %s ip=%s", cell_id[:8], getattr(conn, "remote_ip", ""))
            await self._send_nack(conn, "rate_limited")
            return

        is_new = await self.storage.register_cell(
            cell_id, signing_pub, enc_pub, is_home, display_name)
        await self.storage.update_presence(
            cell_id,
            home_node_id=self.identity.node_id,
            visiting_node_id=None,
        )
        log.info("cell registered: %s (home=%s new=%s)", cell_id[:8], is_home, is_new)

        if is_new and is_home:
            await self._broadcast_member_added(cell_id)

        # Child node: tell parent that this cell is now visiting here
        if (self.identity.node_type == "temporary"
                and self.identity.parent_node_id):
            await self._notify_parent_presence(cell_id)

        # Send TURN credentials so the client can make calls through this node
        await self._send_turn_creds(cell_id, conn)

        # Deliver any buffered messages that arrived while cell was offline
        await self.router.flush_buffer(cell_id)

    async def _handle_join_request(self, pkt: Packet, conn: PeerConnection):
        """invite_mode="admin" registration channel — sent by a not-yet-admitted cell
        after CELL_REGISTER_NACK{reason:"invite_required"}, on the same already-
        authenticated connection (so identity comes entirely from `conn`, no claim to
        re-verify, unlike _handle_cell_register). See NodeIdentity.admin_cell_ids and
        MD_Discuss/DISCUSS_REGISTRATION_CHANNEL.md."""
        if self.identity.invite_mode != "admin":
            ack = make_join_request_ack(
                self.identity.node_id, conn.peer_node_id, ok=False, reason="not_applicable")
            sign_packet(ack, self.identity.signing)
            await self.transport.send_via(conn, ack)
            return
        try:
            payload = decode_payload(pkt.payload)
            note = str(payload.get("note", "")).strip()[:500]
            # The name the requester chose at setup, sent alongside the join request
            # since it never made it past the earlier CELL_REGISTER NACK — without it
            # the admin only ever saw a bare cell_id in the panel/notification, no way
            # to tell who's actually asking. See NevdClient.sendJoinRequest.
            display_name = str(payload.get("display_name", "")).strip()[:64]
        except Exception:
            note = ""
            display_name = ""
        cell_id = conn.peer_node_id
        created = await self.storage.create_join_request(
            cell_id, conn.peer_signing_pubkey.hex(), conn.peer_enc_pubkey.hex(), note,
            display_name)
        ack = make_join_request_ack(self.identity.node_id, cell_id, ok=True)
        sign_packet(ack, self.identity.signing)
        await self.transport.send_via(conn, ack)
        if created:
            log.info("join request from %s (name=%r note=%r)", cell_id[:8], display_name, note[:40])
            who = display_name if display_name else f"{cell_id[:8]}…"
            body = f"New join request from {who}"
            if note:
                body += f" — {note[:120]}"
            # Spell out the exact words this chat understands right in the notification —
            # found 2026-09-18 that an admin typed "Ok" expecting it to work and it didn't
            # (only "approve"/"deny" and their Russian/yes-no synonyms are recognized, see
            # _handle_registrar_command), with no way to guess the vocabulary without
            # already knowing it.
            body += ' — ответьте "approve" или "deny" в этом чате, либо решите в админке.'
            await self._notify_admins(body)
        else:
            log.info("join request from %s — already pending/resolved, no re-notify", cell_id[:8])

    async def _notify_admins(self, text: str):
        """Sends `text` to every NodeIdentity.admin_cell_ids entry, from the built-in
        registrar identity (_ensure_registrar) — an ordinary encrypted MSG via the
        normal router, not a new client-side concept. Silently skips an admin_cell_id
        that isn't itself a registered cell here (nothing to encrypt to)."""
        if not self._registrar_identity or not self.identity.admin_cell_ids:
            return
        for admin_id in self.identity.admin_cell_ids:
            try:
                await self.send_message(
                    f"{admin_id}@{self.identity.node_id}", text.encode("utf-8"),
                    from_cell_id=self._registrar_identity.cell_id,
                )
            except ValueError:
                log.warning("registrar: admin_cell_id %s has no enc_pubkey here, skipping",
                            admin_id[:8])

    async def _broadcast_member_added(self, new_cell_id: str):
        """A brand-new home cell just registered — nudge every OTHER currently-
        connected home cell to refresh its member list. Without this, an already-
        connected client only re-fetches members on its own next reconnect
        (AppStore.fetchNodeMembers runs solely on that "connected" transition), so a
        just-admitted member could sit invisible to everyone already online for
        minutes. Confirmed on device 2026-09-23: a new member was admitted and could see
        the whole node right away (their own connect refreshed fully populated data),
        but the admin (already connected) didn't see them until their first
        message happened to coincide with the admin's next periodic reconnect.

        Routed through the registrar identity (same as _notify_admins) so a sender
        exists at all and delivery ACKs land on the already-solved dead-letter path
        (_is_registrar_address) instead of buffering forever — best-effort, silently
        skipped on nodes without a registrar (invite_mode != "admin"; not reported
        there yet, not worth a second sender identity for an unconfirmed gap)."""
        if not self._registrar_identity:
            return
        for conn in await self.transport.connections.all():
            if conn.peer_node_id == new_cell_id:
                continue
            cell = await self.storage.get_cell(conn.peer_node_id)
            if not cell or not cell.is_home:
                continue
            try:
                await self.send_message(
                    f"{conn.peer_node_id}@{self.identity.node_id}",
                    f"member_added:{new_cell_id}".encode("utf-8"),
                    from_cell_id=self._registrar_identity.cell_id,
                    msg_type=T.MSG_SILENT,
                )
            except ValueError:
                pass

    # --- built-in administrator (appeals / complaints) ---

    async def _ensure_administrator(self):
        """Every node gets its own "administrator" cell: users send complaints/appeals to
        it from the app (Report -> in-app), the node operator reads and answers them on the
        admin panel's Обращения page. Like the registrar, its keys live here in the node
        process (administrator_identity.json next to the node identity) — deliberately:
        an appeal is addressed to the operator, so the operator's own server decrypting it
        is the intended recipient reading it, not a leak of anyone's private chats. The ✓
        badge is separate: a curator signs {cell_id, enc_pub, node_id} into official.json
        (see node/curator_sign.py sign-official, role administrator)."""
        if not self._identity_path:
            return  # Node built directly, bypassing create() — e.g. unit tests
        from .identity import CellIdentity
        path = os.path.join(os.path.dirname(self._identity_path) or ".",
                            "administrator_identity.json")
        if os.path.exists(path):
            admin = CellIdentity.load(path)
        else:
            admin = CellIdentity.generate(name="administrator")
            admin.save(path)
            log.info("generated administrator identity: %s", admin.cell_id[:16])
        self._administrator_identity = admin
        await self.register_cell_locally(
            admin.cell_id, admin.signing.public, admin.encryption.public,
            display_name="administrator",
        )

    def administrator_info(self) -> Optional[dict]:
        """What a curator needs to sign this node's administrator into official.json."""
        a = self._administrator_identity
        if not a:
            return None
        return {"cell_id": a.cell_id, "enc_pub": a.encryption.public.hex(),
                "node_id": self.identity.node_id}

    def _is_administrator_address(self, addr: str) -> bool:
        if not self._administrator_identity:
            return False
        cell_id, node_id = parse_addr(addr)
        return cell_id == self._administrator_identity.cell_id and node_id == self.identity.node_id

    def _is_service_address(self, addr: str) -> bool:
        """Server-side cells with no live connection (registrar, administrator) — anything
        routed to them that isn't consumed in-process would sit in message_buffer forever
        (see _is_registrar_address)."""
        return self._is_registrar_address(addr) or self._is_administrator_address(addr)

    async def _maybe_handle_administrator_msg(self, pkt: Packet) -> bool:
        """An appeal to this node's administrator: decrypted in-process, stored for the
        admin panel, acked "delivered" so the sender's bubble doesn't sit queued. Only
        T.MSG carries text; MSG_CHUNK (media) / MSG_SILENT addressed here are dropped by
        the caller's _is_service_address guard. Returns True if consumed."""
        if pkt.type != T.MSG or not self._is_administrator_address(pkt.to_addr):
            return False
        sender_id, sender_node = parse_addr(pkt.from_addr)
        if not sender_id:
            return True
        try:
            d = decode_payload(pkt.payload)
            from .crypto import decrypt
            plaintext = decrypt(bytes(d["ciphertext"]), bytes(d["nonce"]),
                                bytes(d["ephemeral_pubkey"]),
                                self._administrator_identity.encryption)
        except Exception:
            log.warning("administrator: failed to decrypt message from %s", sender_id[:8])
            return True
        ack = Packet(type=T.ACK,
                     payload=encode_payload({"message_id": pkt.id, "status": "delivered"}),
                     from_addr=pkt.to_addr, to_addr=pkt.from_addr)
        await self.router.route(ack)
        from .bot import strip_prefixes
        card_pub, text = strip_prefixes(plaintext.decode("utf-8", errors="replace"))
        cell = await self.storage.get_cell(sender_id)
        enc_pub = card_pub.hex() if card_pub else (cell.enc_pubkey.hex() if cell else "")
        name = cell.display_name if cell else ""
        if text.startswith(DIAG_LOG_PREFIX):
            await self._store_diag_log(sender_id, sender_node, name, enc_pub,
                                       text[len(DIAG_LOG_PREFIX):])
            return True
        await self.storage.add_appeal(sender_id, sender_node or self.identity.node_id,
                                      name, enc_pub, "in", text.strip())
        log.info("administrator: appeal from %s (%d chars)", sender_id[:8], len(text))
        if self._registrar_identity and self.identity.admin_cell_ids:
            who = name or f"{sender_id[:8]}…"
            await self._notify_admins(f"Новое обращение от {who} — админка → Обращения.")
        return True

    async def _store_diag_log(self, sender_id: str, sender_node: str, name: str, enc_pub: str,
                              body: str):
        """The app's diagnostic log (DiagnosticsView, sent when the phone has no Mail account):
        base64 of raw-deflate text. Bounded both ways — packed and unpacked size, and per
        sender per day — since anyone can message the administrator."""
        import binascii
        import zlib
        try:
            packed = base64.b64decode(body, validate=True)
        except (binascii.Error, ValueError):
            log.warning("administrator: diag log from %s is not base64", sender_id[:8])
            return
        if len(packed) > DIAG_LOG_MAX_PACKED:
            log.warning("administrator: diag log from %s too big (%d bytes packed)",
                        sender_id[:8], len(packed))
            return
        try:
            inflater = zlib.decompressobj(-15)
            raw = inflater.decompress(packed, DIAG_LOG_MAX_RAW)
        except zlib.error:
            log.warning("administrator: diag log from %s does not inflate", sender_id[:8])
            return
        if inflater.unconsumed_tail:
            log.warning("administrator: diag log from %s over %d bytes unpacked",
                        sender_id[:8], DIAG_LOG_MAX_RAW)
            return
        if await self.storage.count_diag_logs_since(sender_id, int(time.time()) - 86400) >= DIAG_LOGS_PER_DAY:
            log.warning("administrator: diag log from %s dropped — daily limit", sender_id[:8])
            return
        log_id = await self.storage.add_diag_log(sender_id, packed, len(raw))
        await self.storage.add_appeal(sender_id, sender_node or self.identity.node_id, name, enc_pub,
                                      "in", f"📎 Журнал диагностики [log:{log_id}] ({len(raw) // 1024} KB)")
        log.info("administrator: diag log %d from %s (%d bytes)", log_id, sender_id[:8], len(raw))
        if self._registrar_identity and self.identity.admin_cell_ids:
            who = name or f"{sender_id[:8]}…"
            await self._notify_admins(f"Журнал диагностики от {who} — админка → Обращения.")

    async def reply_as_administrator(self, cell_id: str, text: str) -> bool:
        """Admin panel reply: an ordinary E2E-encrypted MSG from the administrator cell.
        The recipient's key comes from this node's cell table, or — for a sender homed on
        another node — from the card: prefix their appeal carried (kept with the appeal)."""
        text = text.strip()
        if not self._administrator_identity or not text:
            return False
        thread = await self.storage.get_appeal_thread(cell_id)
        cell = await self.storage.get_cell(cell_id)
        enc_pub = cell.enc_pubkey if cell else None
        node_id = self.identity.node_id
        incoming = [m for m in thread if m.direction == "in"]
        if incoming:
            node_id = incoming[-1].node_id or node_id
            if enc_pub is None and incoming[-1].enc_pub:
                enc_pub = bytes.fromhex(incoming[-1].enc_pub)
        if enc_pub is None:
            return False
        from .crypto import encrypt
        encrypted = encrypt(text.encode("utf-8"), enc_pub)
        pkt = Packet(
            type=T.MSG,
            payload=encode_payload({
                "ephemeral_pubkey": encrypted["ephemeral_pubkey"],
                "nonce": encrypted["nonce"],
                "ciphertext": encrypted["ciphertext"],
            }),
            from_addr=f"{self._administrator_identity.cell_id}@{self.identity.node_id}",
            to_addr=f"{cell_id}@{node_id}",
        )
        await self.router.route(pkt)
        await self.storage.add_appeal(cell_id, node_id, cell.display_name if cell else "",
                                      "", "out", text)
        return True

    def _is_registrar_address(self, addr: str) -> bool:
        """True if `addr` ("cell_id@node_id") names the built-in registrar cell on
        THIS node. Guards both _maybe_handle_registrar_reply (below) and the
        message_buffer dead-letter cases in _dispatch — a synthetic, server-only
        identity with no live transport connection can never come online to flush a
        buffered delivery, so anything routed to it that isn't handled specially here
        would sit in message_buffer until its TTL expires (see 2026-09-18 finding:
        12 stuck rows on node1, every one a delivered/read ACK the admin's client
        automatically sent back for a registrar message)."""
        if not self._registrar_identity:
            return False
        cell_id, node_id = parse_addr(addr)
        return cell_id == self._registrar_identity.cell_id and node_id == self.identity.node_id

    async def _maybe_handle_registrar_reply(self, pkt: Packet) -> bool:
        """Lets an admin approve/deny a join request by replying in the "Node
        Registrar" chat, instead of only via the admin panel's Заявки на подключение
        page. Registrar has no live client connection to route/buffer a reply to —
        its private key was generated and lives entirely here in the node process
        (_ensure_registrar), so a message addressed to it is decrypted and acted on
        in-process rather than treated like an ordinary cell-to-cell MSG. Returns
        True if this packet was consumed (whether or not it made sense as a
        command) — callers must not also route() it, since nothing will ever come
        online to receive it. Non-admin senders and anything not addressed to
        registrar fall straight back to normal routing."""
        if pkt.type != T.MSG or self.identity.invite_mode != "admin":
            return False
        if not self._is_registrar_address(pkt.to_addr):
            return False
        sender_id, _ = parse_addr(pkt.from_addr)
        # Same posture as bot.py's allowed_cells gate: a non-admin gets no reply at
        # all, rather than confirming this address does something.
        if not sender_id or sender_id not in self.identity.admin_cell_ids:
            return True
        try:
            d = decode_payload(pkt.payload)
            from .crypto import decrypt
            plaintext = decrypt(bytes(d["ciphertext"]), bytes(d["nonce"]),
                                bytes(d["ephemeral_pubkey"]), self._registrar_identity.encryption)
        except Exception:
            log.warning("registrar: failed to decrypt reply from admin %s", sender_id[:8])
            return True
        # Ack immediately so the admin's own chat doesn't show this stuck "queued"
        # forever — a live client would send exactly this on successful receipt.
        ack = Packet(type=T.ACK,
                     payload=encode_payload({"message_id": pkt.id, "status": "delivered"}),
                     from_addr=pkt.to_addr, to_addr=pkt.from_addr)
        await self.router.route(ack)
        from .bot import strip_prefixes
        _, text = strip_prefixes(plaintext.decode("utf-8", errors="replace"))
        await self._handle_registrar_command(sender_id, text.strip())
        return True

    async def _reply_from_registrar(self, admin_id: str, text: str):
        await self.send_message(f"{admin_id}@{self.identity.node_id}", text.encode("utf-8"),
                                from_cell_id=self._registrar_identity.cell_id)

    async def _handle_registrar_command(self, admin_id: str, text: str):
        """approve/deny [cell_id prefix] — the prefix is only required when more
        than one request is pending (matches the short id shown in the admin
        panel's Заявки на подключение table and in the push/notify text)."""
        parts = text.split(maxsplit=1)
        if not parts:
            return
        verb = parts[0].strip().lower().rstrip(".,!?")
        # Deliberately generous — found 2026-09-18 that a real admin typed "Ok" expecting
        # it to work and it silently didn't (only the bare protocol words were recognized).
        # Anything a human would plausibly type to mean "yes, let them in" should work,
        # not just the one exact word from the notification text.
        approve_verbs = {"approve", "approved", "allow", "admit", "ok", "okay",
                         "одобрить", "одобряю", "одобрено", "принять", "да", "ага", "yes", "+"}
        deny_verbs = {"deny", "denied", "reject", "rejected", "decline",
                      "отклонить", "отклоняю", "отклонено", "отказать", "нет", "no", "-"}
        if verb not in approve_verbs and verb not in deny_verbs:
            await self._reply_from_registrar(
                admin_id,
                "Не понял команду. Ответьте «approve» или «deny» "
                "(добавьте начало cell_id, если заявок несколько).",
            )
            return
        pending = await self.storage.list_join_requests(status="pending")
        if not pending:
            await self._reply_from_registrar(admin_id, "Нет ожидающих заявок.")
            return
        target = parts[1].strip().lower() if len(parts) > 1 else ""
        if target:
            matches = [r for r in pending if r.cell_id.lower().startswith(target)]
        else:
            matches = pending
        if len(matches) == 0:
            await self._reply_from_registrar(admin_id, f"Не найдена заявка «{target}».")
            return
        if len(matches) > 1:
            listing = "\n".join(
                f"• {r.display_name or r.cell_id[:8]} — {r.cell_id[:8]}" for r in matches
            )
            await self._reply_from_registrar(
                admin_id,
                f"Заявок несколько, уточните cell_id:\n{listing}",
            )
            return
        match = matches[0]
        who = match.display_name or match.cell_id[:8]
        if verb in approve_verbs:
            ok = await self.approve_join_request(match.cell_id)
            reply = f"✅ Заявка от {who} одобрена." if ok else "Не удалось одобрить — уже обработана?"
        else:
            ok = await self.deny_join_request(match.cell_id)
            reply = f"🚫 Заявка от {who} отклонена." if ok else "Не удалось отклонить — уже обработана?"
        await self._reply_from_registrar(admin_id, reply)

    async def approve_join_request(self, cell_id: str) -> bool:
        """Called from admin.py (panel button) or the registrar chat (see
        _handle_registrar_command) — admits `cell_id` directly into allowed_cells (no
        code — the requester is already the exact cryptographic identity that asked,
        see resolve_join_request's doc comment) and wakes them two ways. Returns False
        if there was no pending request for this cell_id."""
        pending = await self.storage.list_join_requests(status="pending")
        if not any(r.cell_id == cell_id for r in pending):
            return False
        await self.storage.resolve_join_request(cell_id, "approved",
                                                  invited_by=self.identity.node_id)
        log.info("join request approved: %s", cell_id[:8])
        await self._notify_join_request_resolved(cell_id, approved=True)
        result = await self.storage.get_push_token(cell_id)
        if result and self.apns is not None:
            token, platform = result
            if platform == "apns":
                await self.apns.send(token, title="Nevod",
                                      body="Заявка одобрена — откройте Nevod")
        return True

    async def deny_join_request(self, cell_id: str) -> bool:
        pending = await self.storage.list_join_requests(status="pending")
        if not any(r.cell_id == cell_id for r in pending):
            return False
        await self.storage.resolve_join_request(cell_id, "denied")
        log.info("join request denied: %s", cell_id[:8])
        await self._notify_join_request_resolved(cell_id, approved=False)
        return True

    async def _notify_join_request_resolved(self, cell_id: str, approved: bool):
        """Best-effort real-time nudge: a JOIN_REQUEST_RESOLVED packet straight over
        this cell's still-open connection, if it happens to still be connected right
        now (transport tracks peer_node_id from the auth handshake, well before any
        admission check — see protocol.py's JOIN_REQUEST_RESOLVED doc comment). A
        request can sit pending for days, so this is genuinely just best-effort for
        whoever happens to be online at the exact moment of the decision — the plain
        alert push (approve_join_request, above) and the client's own foreground/
        "Check again" retry are what cover everyone else. No-ops silently if nobody's
        connected right now; nothing to clean up either way."""
        pkt = make_join_request_resolved(self.identity.node_id, cell_id, approved)
        await self.transport.send_to(cell_id, pkt)

    def _generate_turn_creds(self, cell_id: str) -> Optional[dict]:
        """Time-limited HMAC credential (coturn use-auth-secret format) for our
        own coturn. None if we have no TURN_SECRET — the caller decides what
        to do (fall back to relay, or refuse a relay request)."""
        if not self._turn_secret:
            return None
        expiry = int(time.time()) + 3600  # valid 1 hour
        username = f"{expiry}:{cell_id}"
        password = base64.b64encode(
            hmac.new(self._turn_secret.encode(), username.encode(), hashlib.sha1).digest()
        ).decode()
        host = self.identity.address.split(":")[0]
        return {"url": f"turn:{host}:3478", "username": username, "credential": password}

    async def _send_turn_creds(self, cell_id: str, conn: PeerConnection):
        creds = self._generate_turn_creds(cell_id)
        if creds is None:
            # No coturn of our own — ask a peer node that has one instead of
            # leaving the cell with no TURN at all (relay-only calls need it).
            await self._request_turn_relay(cell_id, conn)
            return
        pkt = Packet(
            type=T.TURN_CREDS,
            payload=encode_payload(creds),
            from_addr=self.identity.node_id,
            to_addr=cell_id,
        )
        sign_packet(pkt, self.identity.signing)
        await self.transport.send_via(conn, pkt)
        log.debug("turn_creds sent to %s", cell_id[:8])

    async def _request_turn_relay(self, cell_id: str, conn: PeerConnection):
        """We have no TURN_SECRET — ask a randomly chosen known node that
        advertised turn_relay to generate credentials for this cell. TURN
        relay carries real call media (unlike push relay's cheap API call),
        so spreading requests across all capable nodes instead of always the
        same one matters here."""
        candidates = [n for n in await self.storage.get_turn_relay_nodes()
                     if n.node_id != self.identity.node_id]
        if not candidates:
            log.info("turn-relay: no turn-relay node known, cell %s gets no TURN", cell_id[:8])
            return
        relay = random.choice(candidates)
        request_id = uuid.uuid4().hex
        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending_turn_futures[request_id] = fut
        req = make_turn_relay_request(self.identity.node_id, relay.node_id, request_id, cell_id)
        sign_packet(req, self.identity.signing)
        sent = await self.router._send_to_node(relay.node_id, req)
        if not sent:
            self._pending_turn_futures.pop(request_id, None)
            log.info("turn-relay: could not reach relay node %s", relay.node_id[:8])
            return
        try:
            creds = await asyncio.wait_for(fut, timeout=5.0)
        except asyncio.TimeoutError:
            self._pending_turn_futures.pop(request_id, None)
            log.info("turn-relay: relay node %s did not respond in time", relay.node_id[:8])
            return
        if creds is None:
            log.info("turn-relay: relay node %s declined", relay.node_id[:8])
            return
        pkt = Packet(
            type=T.TURN_CREDS,
            payload=encode_payload(creds),
            from_addr=self.identity.node_id,
            to_addr=cell_id,
        )
        sign_packet(pkt, self.identity.signing)
        await self.transport.send_via(conn, pkt)
        log.info("turn-relay: relayed TURN creds for cell %s via %s", cell_id[:8], relay.node_id[:8])

    async def _handle_turn_relay_request(self, pkt: Packet, conn: PeerConnection):
        """Another node has no TURN_SECRET of its own and is asking us to
        generate credentials for one of its cells. Same trust/abuse-guard
        shape as _handle_push_relay_request."""
        requester_id = conn.peer_node_id
        request_id = ""
        try:
            d = decode_payload(pkt.payload)
            request_id = str(d.get("request_id", ""))
            cell_id = str(d.get("cell_id", ""))
        except Exception:
            return
        if not request_id:
            return

        async def reply(creds: Optional[dict]):
            resp = make_turn_relay_response(self.identity.node_id, requester_id, request_id, creds)
            sign_packet(resp, self.identity.signing)
            await self.router._send_to_node(requester_id, resp)

        known = await self.storage.get_node(requester_id)
        if known is None:
            log.info("turn-relay: refusing request from unknown node %s", requester_id[:8])
            await reply(None)
            return
        now = time.time()
        last = self._turn_relay_times.get(requester_id, 0.0)
        if now - last < 10.0:
            log.info("turn-relay: rate-limited request from %s (%.1fs since last)",
                     requester_id[:8], now - last)
            await reply(None)
            return
        self._turn_relay_times[requester_id] = now
        creds = self._generate_turn_creds(cell_id)
        if creds is None:
            log.info("turn-relay: asked for TURN by %s but we have none ourselves",
                     requester_id[:8])
        await reply(creds)

    async def _handle_turn_relay_response(self, pkt: Packet):
        try:
            d = decode_payload(pkt.payload)
            request_id = str(d.get("request_id", ""))
            ok = bool(d.get("ok", False))
        except Exception:
            return
        fut = self._pending_turn_futures.pop(request_id, None)
        if fut is None or fut.done():
            return
        if not ok:
            fut.set_result(None)
            return
        fut.set_result({"url": d.get("url", ""), "username": d.get("username", ""),
                        "credential": d.get("credential", "")})

    async def _send_nack(self, conn: PeerConnection, reason: str, extra: Optional[dict] = None):
        payload = {"reason": reason}
        if extra:
            payload.update(extra)
        nack = Packet(
            type=T.CELL_REGISTER_NACK,
            payload=encode_payload(payload),
            from_addr=self.identity.node_id,
        )
        sign_packet(nack, self.identity.signing)
        await self.transport.send_via(conn, nack)

    def _public_client_endpoint(self) -> tuple[str, str]:
        """Address + TLS fingerprint to hand to a *cell* (app user) in an invite
        token — not necessarily the same as identity.address, which is what
        other NODES dial for P2P join/gossip and must stay the node's own
        self-signed raw port. A deployment fronted by a reverse proxy with a
        real CA cert (e.g. prod's nginx) can set NEVOD_PUBLIC_CLIENT_ADDR to
        that friendlier address; clients then need no TLS pinning at all, so
        the fingerprint is left empty (the iOS/PWA clients treat an empty
        fingerprint as "use normal system trust", not "no address given").
        Falls back to identity.address + identity.tls_fingerprint (self-signed
        pinning) when unset — the original behavior, for home nodes with no
        reverse proxy in front of them.
        """
        public_addr = os.environ.get("NEVOD_PUBLIC_CLIENT_ADDR", "").strip()
        if public_addr:
            return public_addr, ""
        return self.identity.address, self.identity.tls_fingerprint

    async def _handle_invite_create(self, pkt: Packet, conn: PeerConnection):
        """Cell asks to create an invite code (for delegated mode)."""
        cell_id = conn.peer_node_id
        mode = self.identity.invite_mode
        allowed = False
        if mode == "open":
            allowed = True
        elif mode == "delegated":
            allowed = await self.storage.can_cell_invite(cell_id)
        # mode == "admin": only admin panel can create codes — always deny here

        resp_payload: dict
        if allowed:
            code = await self.storage.create_invite(created_by=cell_id)
            address, fingerprint = self._public_client_endpoint()
            resp_payload = {
                "ok": True,
                "code": code,
                "address": address,
                "tls_fingerprint": fingerprint,
            }
            log.info("invite created by cell %s: %s", cell_id[:8], code)
        else:
            resp_payload = {"ok": False, "reason": "not_allowed"}

        resp = Packet(
            type=T.INVITE_RESPONSE,
            payload=encode_payload(resp_payload),
            from_addr=self.identity.node_id,
            to_addr=cell_id,
        )
        sign_packet(resp, self.identity.signing)
        await self.transport.send_via(conn, resp)

    async def _handle_push_register(self, pkt: Packet, conn: PeerConnection):
        """Cell registers its APNs device token — regular alert token or, separately,
        its VoIP token (a cell needs both at once, so these are never the same slot)."""
        try:
            d = decode_payload(pkt.payload)
            token    = str(d.get("token", "")).strip()
            platform = str(d.get("platform", "apns"))
        except Exception:
            return
        if not token:
            return
        cell_id = conn.peer_node_id
        if platform == "voip":
            await self.storage.save_voip_push_token(cell_id, token)
            log.info("voip push token registered for cell %s", cell_id[:8])
        else:
            await self.storage.save_push_token(cell_id, token, platform)
            log.info("push token registered for cell %s (%s)", cell_id[:8], platform)

    async def _handle_node_list_request(self, pkt: Packet, conn):
        """Public directory — any connected cell can ask for the list of "open" (publicly
        joinable) nodes this node knows about via gossip. Unlike _handle_group_members_request,
        deliberately NOT gated behind admission: "open" access is the whole point of these
        nodes advertising themselves, so there's nothing to protect by hiding the list."""
        all_nodes = await self.storage.get_all_nodes()
        nodes = [
            {"node_id": n.node_id, "name": n.name, "address": n.address}
            for n in all_nodes if n.access == "open"
        ]
        resp = make_node_list_response(
            from_node=self.identity.node_id,
            to_addr=pkt.from_addr,
            nodes=nodes,
        )
        await self.transport.send_via(conn, resp)

    async def _handle_node_cells_request(self, pkt: Packet, conn):
        """Public-facing (admin-curated) cell/moon list for this node's "Explore
        Network" entry — see PublishedCellEntry in storage.py. Gated by
        cells_visibility; only ever reveals what the operator explicitly opted to
        publish, never the raw `cells` table (which includes every ordinary
        registered user, not just published ones)."""
        visibility = self.identity.cells_visibility
        log.info("node_cells_request from=%s visibility=%s", conn.peer_node_id[:8], visibility)
        if visibility == "off":
            log.info("node_cells_request %s — withheld (visibility=off)", conn.peer_node_id[:8])
            return
        if visibility == "members":
            is_member = await self.storage.get_cell(conn.peer_node_id) is not None
            if not is_member:
                log.info("node_cells_request %s — withheld (not a registered member)",
                         conn.peer_node_id[:8])
                return  # not a member — silently withhold, same as group members

        published = await self.storage.get_published_cells()
        cells = []
        for p in published:
            entry = {"cell_id": p.cell_id, "name": p.name, "description": p.description,
                     "kind": p.kind}
            if p.kind == "bot":
                cell = await self.storage.get_cell(p.cell_id)
                if not cell:
                    continue  # published but not currently a registered cell — skip
                entry["enc_pubkey"] = cell.enc_pubkey
                if p.ai_providers:
                    entry["ai_providers"] = p.ai_providers
            elif p.kind == "page":
                entry["landing_md"] = p.landing_md
            cells.append(entry)
        log.info("node_cells_request %s — replying with %d cell(s) (published total=%d)",
                 conn.peer_node_id[:8], len(cells), len(published))

        resp = make_node_cells_response(
            from_node=self.identity.node_id,
            to_addr=pkt.from_addr,
            cells=cells,
        )
        await self.transport.send_via(conn, resp)

    async def _handle_chat_prefs(self, pkt: Packet, conn: PeerConnection):
        """Owner sets a per-sender push preference (currently just sound on/off) — owner
        comes from the authenticated connection (conn.peer_node_id), never trusted from the
        payload, same as _handle_push_register above."""
        try:
            d = decode_payload(pkt.payload)
            peer_cell_id  = str(d.get("peer_cell_id", "")).strip()
        except Exception:
            return
        if not peer_cell_id:
            return
        owner_cell_id = conn.peer_node_id
        # Each field is applied only if present — a block-only update must not silently
        # reset the sound preference to its default (and vice versa).
        if "sound_enabled" in d:
            sound_enabled = bool(d["sound_enabled"])
            await self.storage.set_sound_enabled(owner_cell_id, peer_cell_id, sound_enabled)
            log.info("chat prefs: owner=%s peer=%s sound_enabled=%s",
                     owner_cell_id[:8], peer_cell_id[:8], sound_enabled)
        if "blocked" in d:
            blocked = bool(d["blocked"])
            await self.storage.set_blocked(owner_cell_id, peer_cell_id, blocked)
            log.info("chat prefs: owner=%s peer=%s blocked=%s",
                     owner_cell_id[:8], peer_cell_id[:8], blocked)

    async def _handle_push_relay_request(self, pkt: Packet, conn: PeerConnection):
        """Another node has no push credentials for this platform and is asking
        us to send on its behalf — see router.py's _send_push / _relay_voip_push.
        We only help nodes we already know (admitted to the network at some
        point, either directly or via gossip), and rate-limit per requester so
        one node can't burn through our push quota. VoIP (kind="voip") is
        exempt from the rate limit — same reasoning as the direct-send path in
        router.py: a call offer is a one-off event, not part of a flood, and
        delaying it means a missed call."""
        requester_id = conn.peer_node_id
        if self.apns is None:
            return
        known = await self.storage.get_node(requester_id)
        if known is None:
            log.info("push-relay: refusing request from unknown node %s", requester_id[:8])
            return
        try:
            d = decode_payload(pkt.payload)
            platform  = str(d.get("platform", ""))
            token     = str(d.get("push_token", "")).strip()
            title     = str(d.get("title", "Nevod"))[:64]
            body      = str(d.get("body", "New message"))[:120]
            kind      = str(d.get("kind", "alert"))
            caller_id = str(d.get("caller_id", ""))
        except Exception:
            return
        if not token or platform != "apns":
            log.info("push-relay: unsupported platform=%r from %s", platform, requester_id[:8])
            return

        if kind == "voip":
            ok = await self.apns.send_voip(token, caller_id=caller_id, caller_name=title)
            log.info("push-relay: relayed VOIP push for node %s to %s… result=%s",
                     requester_id[:8], token[:8], ok)
            return

        now = time.time()
        last = self._relay_times.get(requester_id, 0.0)
        if now - last < 60.0:
            log.info("push-relay: rate-limited request from %s (%.1fs since last)",
                     requester_id[:8], now - last)
            return
        self._relay_times[requester_id] = now
        ok = await self.apns.send(token, title=title, body=body, sender_cell_id=caller_id)
        log.info("push-relay: relayed push for node %s to %s… result=%s",
                 requester_id[:8], token[:8], ok)

    async def _handle_card_create(self, pkt: Packet, conn: PeerConnection):
        """Cell asks to generate a short contact card code (7-day TTL)."""
        cell_id = conn.peer_node_id
        cell = await self.storage.get_cell(cell_id)
        if not cell:
            return
        code = await self.storage.create_contact_card(cell_id, cell.enc_pubkey.hex())
        expires_at = int(time.time()) + CARD_TTL_SECS
        resp = Packet(
            type=T.CARD_RESPONSE,
            payload=encode_payload({"ok": True, "code": code, "expires_at": expires_at}),
            from_addr=self.identity.node_id,
            to_addr=cell_id,
        )
        sign_packet(resp, self.identity.signing)
        await self.transport.send_via(conn, resp)
        log.info("contact card created for cell %s: %s", cell_id[:8], code)

    async def _notify_parent_presence(self, cell_id: str):
        """Child node → send CHILD_PRESENCE_UPDATE to parent."""
        from .protocol import make_child_presence_update
        parent_id = self.identity.parent_node_id
        parent_entry = await self.storage.get_node(parent_id)
        if not parent_entry:
            log.debug("child: parent %s not in node_table, can't notify", parent_id[:8])
            return
        try:
            conn = await self.transport.connections.get(parent_id)
            if not conn:
                conn = await self.transport.connect_to_node(
                    parent_id, parent_entry.address,
                    expected_fingerprint=parent_entry.tls_fingerprint or None,
                )
            pkt = make_child_presence_update(
                from_node=self.identity.node_id,
                to_node=parent_id,
                cell_id=cell_id,
                child_node_id=self.identity.node_id,
                child_address=self.identity.address,
                child_tls_fingerprint=self.identity.tls_fingerprint,
            )
            await self.transport.send_via(conn, pkt)
            log.info("child: notified parent %s of cell %s", parent_id[:8], cell_id[:8])
        except Exception as e:
            log.debug("child: failed to notify parent %s: %s", parent_id[:8], e)

    async def _handle_child_presence_update(self, pkt: Packet):
        """Parent receives CHILD_PRESENCE_UPDATE — cell is visiting a child node."""
        try:
            data = decode_payload(pkt.payload)
            cell_id               = data["cell_id"]
            child_node_id         = data["child_node_id"]
            child_address         = data["child_address"]
            child_tls_fingerprint = data.get("child_tls_fingerprint", "")
        except Exception:
            return

        # Register child node so router can connect to it
        await self.storage.upsert_node(NodeEntry(
            node_id=child_node_id,
            address=child_address,
            type="temporary",
            access="closed",
            tls_fingerprint=child_tls_fingerprint,
            last_seen=int(time.time()),
            status="online",
            added_at=int(time.time()),
        ))

        # Update presence: this cell is now visiting the child node
        existing = await self.storage.get_presence(cell_id)
        home = existing.home_node_id if existing else self.identity.node_id
        await self.storage.update_presence(
            cell_id,
            home_node_id=home,
            visiting_node_id=child_node_id,
        )
        log.info("parent: cell %s now visiting child %s", cell_id[:8], child_node_id[:8])

        # Flush buffered messages — the cell is now reachable via child_node
        await self.router.flush_buffer(cell_id)

    async def _handle_group_members_request(self, pkt: Packet, conn):
        """Return all home-cells registered on this node (group member list)."""
        if self.identity.invite_mode != "open":
            if not await self.storage.is_cell_allowed(conn.peer_node_id):
                return  # not admitted — don't reveal members
        cells = await self.storage.list_cells(home_only=True)
        if self.identity.members_visibility == "service":
            visible = await self._service_cell_ids()
            visible.add(conn.peer_node_id)   # the requester itself
            cells = [c for c in cells if c.cell_id.lower() in visible]
        # The built-in administrator stays IN this list on purpose: the app resolves every
        # non-contact chat partner (chat list, push-tap deep link, "identity gone" checks)
        # through node members — hiding it made administrator's replies arrive but never show
        # up as a chat (found on device 2026-09-29).
        members = [
            {"cell_id": c.cell_id, "enc_pubkey": c.enc_pubkey, "display_name": c.display_name}
            for c in cells
        ]
        resp = make_group_members_response(
            from_node=self.identity.node_id,
            to_addr=pkt.from_addr,
            members=members,
        )
        await self.transport.send_via(conn, resp)

    async def _service_cell_ids(self) -> set:
        """Cells listed even with members_visibility="service": administrator, registrar,
        published cells (bots/channels the operator chose to show) and official cells."""
        ids = set(official_cell_ids())
        for svc in (self._administrator_identity, self._registrar_identity):
            if svc:
                ids.add(svc.cell_id.lower())
        ids.update(p.cell_id.lower() for p in await self.storage.get_published_cells())
        return ids

    async def destroy(self, identity_path: Optional[str] = None):
        """
        Destroy this node: notify peers, stop, wipe all stored data.
        Used for group deletion (nevod temp destroy).
        """
        leaving = Packet(type=T.NODE_LEAVING, payload=b"",
                         from_addr=self.identity.node_id)
        for conn in await self.transport.connections.all():
            try:
                await self.transport.send_via(conn, leaving)
            except Exception:
                pass

        await self.storage.wipe_all()
        await self.stop()

        if identity_path:
            import os
            try:
                os.remove(identity_path)
            except FileNotFoundError:
                pass

        log.info("node %s destroyed", self.identity.node_id[:16])

    # --- convenience ---

    async def register_cell_locally(self, cell_id: str,
                                     signing_pubkey: bytes, enc_pubkey: bytes,
                                     display_name: str = ""):
        """Register a local cell on this node. register_cell() is upsert-safe and
        keeps the existing name when display_name is empty, so this is safe to call
        on every startup (see _ensure_registrar's use for the built-in registrar
        identity)."""
        await self.storage.register_cell(cell_id, signing_pubkey, enc_pubkey,
                                          is_home=True, display_name=display_name)
        await self.storage.update_presence(
            cell_id,
            home_node_id=self.identity.node_id,
        )


def _split_address(address: str):
    host, port = address.rsplit(":", 1)
    return host, int(port)
