"""
Cell client — connects a cell (user or AI agent) to a Nevod node.

Flow:
  1. WebSocket connect to node
  2. Mutual challenge-response auth (same as node-to-node)
  3. Send CELL_REGISTER (cell_id + signing_pubkey + enc_pubkey)
  4. Ready: send E2E encrypted messages, receive and decrypt incoming

Usage:
    cell = CellClient(identity, on_message=handler)
    await cell.connect("127.0.0.1:8765")
    await cell.send(to_cell_id, to_node_id, recipient_enc_pubkey, b"hello")
    ...
    await cell.disconnect()
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Awaitable

import websockets
from websockets.protocol import State as _WSState
from websockets.exceptions import ConnectionClosed

from .identity import CellIdentity
from .protocol import (
    Packet, T, pack, unpack,
    sign_packet, verify_packet,
    encode_payload, decode_payload, make_ack,
    make_group_members_request, make_node_cells_request,
)
from .auth import do_schnorr_auth
from .crypto import encrypt, decrypt

log = logging.getLogger(__name__)

ACK_TTL = 72 * 3600  # seconds — matches node buffer TTL

# on_message(from_addr: str, plaintext: bytes)
MessageCallback = Callable[[str, bytes], Awaitable[None]]
# on_ack(message_id: str, status: str)
AckCallback = Callable[[str, str], Awaitable[None]]
# on_join_request_resolved(approved: bool) — see node.py's _notify_join_request_resolved
JoinRequestResolvedCallback = Callable[[bool], Awaitable[None]]


class CellClient:
    def __init__(self, identity: CellIdentity,
                 on_message: Optional[MessageCallback] = None,
                 on_ack: Optional[AckCallback] = None,
                 on_join_request_resolved: Optional[JoinRequestResolvedCallback] = None):
        self.identity = identity
        self.on_message = on_message
        self.on_ack = on_ack
        self.on_join_request_resolved = on_join_request_resolved
        self._ws = None
        self._node_id: str = ""
        self._node_signing_pubkey: bytes = b""
        self._recv_task: Optional[asyncio.Task] = None
        self._sent: dict = {}           # message_id → sent_at (int timestamp)
        self._ack_status: dict = {}     # message_id → latest ACK status string
        self._incoming_from: dict = {}  # received msg_id → original from_addr
        self._pending_members: Optional[asyncio.Future] = None
        self._pending_cells: Optional[asyncio.Future] = None

    @property
    def cell_id(self) -> str:
        return self.identity.cell_id

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def connected(self) -> bool:
        return self._ws is not None and self._ws.state == _WSState.OPEN

    async def connect(self, address: str,
                      expected_node_id: Optional[str] = None,
                      expected_fingerprint: Optional[str] = None,
                      scheme: str = "wss"):
        """Connect to node via WSS, authenticate, register cell. scheme="ws" only for a
        node's own in-process cells dialing its loopback port when it runs without TLS."""
        from .transport import _build_client_ssl_ctx, _tls_fingerprint
        ssl_ctx = _build_client_ssl_ctx() if scheme == "wss" else None
        ws = await websockets.connect(f"{scheme}://{address}", ssl=ssl_ctx)
        if expected_fingerprint and ssl_ctx:
            actual = _tls_fingerprint(ws)
            if actual != expected_fingerprint:
                await ws.close()
                raise ValueError(
                    f"TLS fingerprint mismatch for {address}: "
                    f"expected {expected_fingerprint[:16]}… got {actual[:16]}…"
                )

        node_signing_pub, _node_enc_pub = await _do_auth(
            ws, self.identity, expected_node_id
        )
        self._node_id             = node_signing_pub.hex()
        self._node_signing_pubkey = node_signing_pub
        self._ws = ws

        # Register this cell on the node
        reg = Packet(
            type=T.CELL_REGISTER,
            payload=encode_payload({
                "cell_id":        self.cell_id,
                "signing_pubkey": self.identity.signing.public,
                "enc_pubkey":     self.identity.encryption.public,
                "is_home":        True,
            }),
            from_addr=self.cell_id,
            to_addr=self._node_id,
        )
        sign_packet(reg, self.identity.signing)
        await ws.send(pack(reg))

        self._recv_task = asyncio.create_task(
            self._recv_loop(), name=f"cell-recv-{self.cell_id[:8]}"
        )
        log.info("cell %s registered on node %s", self.cell_id[:8], self._node_id[:8])

    async def wait_closed(self):
        """Returns when the connection to the node has ended (closed by the node or a network
        error). A long-running process awaits this and exits, so its supervisor restarts it."""
        if self._recv_task:
            # asyncio.wait, not `await task`: the receive task ending (even cancelled by
            # disconnect) is a normal return here, while a cancel of the CALLER still
            # propagates — swallowing that kept a node's in-process bot alive on stop.
            await asyncio.wait({self._recv_task})

    async def disconnect(self):
        ws = self._ws  # save before recv_task.cancel() clears it
        if self._recv_task:
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                pass
            self._recv_task = None
        if ws:
            try:
                await ws.close()
            except Exception:
                pass
        self._ws = None

    async def send(self, to_cell_id: str, to_node_id: str,
                   recipient_enc_pubkey: bytes, plaintext: bytes, silent: bool = False) -> str:
        """E2E encrypt plaintext and send to recipient cell. Returns message_id.
        silent=True sends MSG_SILENT: a control signal with no chat bubble, never pushed."""
        if not self.connected:
            raise RuntimeError("CellClient: not connected")

        enc = encrypt(plaintext, recipient_enc_pubkey)
        pkt = Packet(
            type=T.MSG_SILENT if silent else T.MSG,
            payload=encode_payload({
                "ephemeral_pubkey": enc["ephemeral_pubkey"],
                "nonce":            enc["nonce"],
                "ciphertext":       enc["ciphertext"],
            }),
            from_addr=f"{self.cell_id}@{self._node_id}",
            to_addr=f"{to_cell_id}@{to_node_id}",
        )
        self._sent[pkt.id] = int(time.time())
        sign_packet(pkt, self.identity.signing)
        await self._ws.send(pack(pkt))
        return pkt.id

    def get_status(self, message_id: str) -> str:
        """Return status of a sent message: in_transit / delivered / read / failed / unknown."""
        if message_id in self._ack_status:
            return self._ack_status[message_id]
        sent_at = self._sent.get(message_id)
        if sent_at is None:
            return "unknown"
        if int(time.time()) - sent_at >= ACK_TTL:
            return "failed"
        return "in_transit"

    async def get_group_members(self) -> list:
        """Request member list from the connected group node. Returns [{cell_id, enc_pubkey}]."""
        if not self.connected:
            raise RuntimeError("CellClient: not connected")
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending_members = fut
        req = make_group_members_request(
            from_addr=f"{self.cell_id}@{self._node_id}",
            to_node=self._node_id,
        )
        sign_packet(req, self.identity.signing)
        await self._ws.send(pack(req))
        return await asyncio.wait_for(fut, timeout=5.0)

    async def get_node_cells(self, timeout: float = 5.0) -> list:
        """Request the connected node's admin-published cell/moon list (see
        node.py's _handle_node_cells_request). The node sends NO response at
        all (not even an empty one) when cells_visibility="off", or ="members"
        and this cell isn't registered there — same silent-withhold precedent
        as group members — so that case surfaces here as a timeout, caught and
        turned into [] rather than distinguishing it from "genuinely nothing
        published"; that ambiguity is deliberate, see the handler."""
        if not self.connected:
            raise RuntimeError("CellClient: not connected")
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending_cells = fut
        req = make_node_cells_request(
            from_addr=f"{self.cell_id}@{self._node_id}",
            to_node=self._node_id,
        )
        sign_packet(req, self.identity.signing)
        await self._ws.send(pack(req))
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending_cells = None
            return []

    async def send_to_group(self, members: list, plaintext: bytes) -> list:
        """E2E encrypt plaintext and send to every group member (except self). Returns message_ids."""
        ids = []
        for m in members:
            cell_id = m["cell_id"]
            enc_pub = bytes(m["enc_pubkey"])
            if cell_id == self.cell_id:
                continue
            mid = await self.send(cell_id, self._node_id, enc_pub, plaintext)
            ids.append(mid)
        return ids

    async def mark_read(self, message_id: str):
        """Send 'read' ACK for a received message (call after displaying to user)."""
        from_addr = self._incoming_from.get(message_id)
        if not from_addr:
            return
        await self._send_ack(message_id, "read", from_addr)

    # --- internal ---

    async def _recv_loop(self):
        try:
            async for raw in self._ws:
                pkt = unpack(raw)
                if not verify_packet(pkt, self._node_signing_pubkey):
                    log.warning("cell: dropped packet with invalid sig from node %s",
                                self._node_id[:8])
                    continue
                await self._dispatch(pkt)
        except ConnectionClosed:
            log.info("cell %s: connection to node closed", self.cell_id[:8])
        except Exception as e:
            log.error("cell %s recv loop error: %s", self.cell_id[:8], e)
        finally:
            self._ws = None

    async def _dispatch(self, pkt: Packet):
        if pkt.type == T.MSG or pkt.type == T.MSG_SILENT:
            await self._handle_msg(pkt)
        elif pkt.type == T.MSG_CHUNK:
            # File fragments aren't assembled here, but must still be acked: the node keeps
            # every unacked chunk in memory (Router._inflight) and re-buffers it for redelivery
            # whenever this connection drops.
            await self._send_ack(pkt.id, "delivered", pkt.from_addr)
        elif pkt.type == T.ACK:
            await self._handle_ack(pkt)  # ACK never generates another ACK
        elif pkt.type == T.GROUP_MEMBERS_RESPONSE:
            await self._handle_group_members_response(pkt)
        elif pkt.type == T.NODE_CELLS_RESPONSE:
            await self._handle_node_cells_response(pkt)
        elif pkt.type == T.JOIN_REQUEST_RESOLVED:
            await self._handle_join_request_resolved(pkt)
        else:
            log.debug("cell: unhandled packet type %s", pkt.type)

    async def _handle_msg(self, pkt: Packet):
        try:
            data = decode_payload(pkt.payload)
            plaintext = decrypt(
                bytes(data["ciphertext"]),
                bytes(data["nonce"]),
                bytes(data["ephemeral_pubkey"]),
                self.identity.encryption,
            )
        except Exception as e:
            log.warning("cell: failed to decrypt message from %s: %s",
                        pkt.from_addr[:16], e)
            return

        self._incoming_from[pkt.id] = pkt.from_addr
        await self._send_ack(pkt.id, "delivered", pkt.from_addr)

        if self.on_message:
            # A bug in one message's handler must not end the receive loop — the cell would
            # stay "connected" on the node yet never read another packet.
            try:
                result = self.on_message(pkt.from_addr, plaintext)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                log.exception("cell %s: on_message failed for a message from %s",
                              self.cell_id[:8], pkt.from_addr[:16])

    async def _handle_ack(self, pkt: Packet):
        try:
            data = decode_payload(pkt.payload)
            message_id = data["message_id"]
            status = data["status"]
        except Exception:
            return
        if status not in ("delivered", "read"):
            log.debug("cell: ignoring unknown ACK status %r", status)
            return
        self._ack_status[message_id] = status
        log.debug("cell: ACK %s → %s", message_id[:8], status)
        if self.on_ack:
            await self.on_ack(message_id, status)

    async def _handle_join_request_resolved(self, pkt: Packet):
        try:
            data = decode_payload(pkt.payload)
            approved = bool(data.get("approved", False))
        except Exception:
            return
        log.info("cell: join request resolved approved=%s", approved)
        if self.on_join_request_resolved:
            result = self.on_join_request_resolved(approved)
            if asyncio.iscoroutine(result):
                await result

    async def _handle_group_members_response(self, pkt: Packet):
        data = decode_payload(pkt.payload)
        members = [
            {"cell_id": m["cell_id"], "enc_pubkey": bytes(m["enc_pubkey"])}
            for m in data.get("members", [])
        ]
        if self._pending_members and not self._pending_members.done():
            self._pending_members.set_result(members)
        self._pending_members = None

    async def _handle_node_cells_response(self, pkt: Packet):
        data = decode_payload(pkt.payload)
        cells = []
        for c in data.get("cells", []):
            entry = {"cell_id": c["cell_id"], "name": c.get("name", ""),
                     "description": c.get("description", ""), "kind": c.get("kind", "bot")}
            if "enc_pubkey" in c:
                entry["enc_pubkey"] = bytes(c["enc_pubkey"])
            if "landing_md" in c:
                entry["landing_md"] = c["landing_md"]
            if "ai_providers" in c:
                entry["ai_providers"] = list(c["ai_providers"])
            cells.append(entry)
        if self._pending_cells and not self._pending_cells.done():
            self._pending_cells.set_result(cells)
        self._pending_cells = None

    async def _send_ack(self, message_id: str, status: str, to_addr: str):
        """Send ACK packet. Only called from _handle_msg — ACK never generates ACK."""
        if not self.connected:
            return
        pkt = make_ack(
            from_addr=f"{self.cell_id}@{self._node_id}",
            to_addr=to_addr,
            message_id=message_id,
            status=status,
        )
        sign_packet(pkt, self.identity.signing)
        try:
            await self._ws.send(pack(pkt))
        except Exception as e:
            log.debug("cell: failed to send ACK: %s", e)


# ─── shared auth helper ───────────────────────────────────────────────────────

async def _do_auth(ws, identity, expected_peer_id: Optional[str]):
    """Schnorr ZKP mutual auth. Returns (peer_signing_pubkey, peer_enc_pubkey)."""
    result = await do_schnorr_auth(ws, identity, expected_peer_id=expected_peer_id)
    return result.signing_pubkey, result.enc_pubkey
