"""
WebSocket transport layer.

- Server: accepts incoming connections from other nodes / cells
- Client: initiates outgoing connections to other nodes
- Each connection: mutual auth (auth.py) → then message exchange
- After auth: connection registered in ConnectionRegistry
"""

import asyncio
import hashlib
import logging
import os
import ssl
import tempfile
from typing import Optional, Callable, Dict, Awaitable

import websockets
from websockets.exceptions import ConnectionClosed

from .protocol import Packet, pack, unpack, sign_packet, verify_packet, T
from .auth import do_schnorr_auth

log = logging.getLogger(__name__)


def _build_server_ssl_ctx(cert_pem: bytes, key_pem: bytes) -> ssl.SSLContext:
    """Build SSLContext for WSS server from PEM bytes."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    with tempfile.TemporaryDirectory() as td:
        cert_path = os.path.join(td, "cert.pem")
        key_path  = os.path.join(td, "key.pem")
        with open(cert_path, "wb") as f:
            f.write(cert_pem)
        with open(key_path, "wb") as f:
            f.write(key_pem)
        ctx.load_cert_chain(cert_path, key_path)
    return ctx


def _build_client_ssl_ctx() -> ssl.SSLContext:
    """Build SSLContext for WSS client — no CA check, fingerprint verified manually."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _tls_fingerprint(ws) -> str:
    """Extract SHA-256 fingerprint of peer TLS cert from a connected websocket."""
    try:
        ssl_obj = ws.transport.get_extra_info("ssl_object")
        if ssl_obj is None:
            return ""
        cert_der = ssl_obj.getpeercert(binary_form=True)
        if not cert_der:
            return ""
        return hashlib.sha256(cert_der).hexdigest()
    except Exception:
        return ""

def _client_ip(ws) -> str:
    """The peer's address. A cell reaching node1/Nevod Open comes through the shared nginx
    in Docker, so the socket's own address is the proxy's — the real one is in X-Real-IP.
    That header is trusted only when the socket itself comes from a private/loopback
    address (the proxy); a client connecting directly can't spoof it from the internet."""
    import ipaddress
    try:
        host = ws.remote_address[0]
    except Exception:
        return ""
    try:
        addr = ipaddress.ip_address(host)
        behind_proxy = addr.is_private or addr.is_loopback
    except ValueError:
        behind_proxy = False
    if behind_proxy:
        request = getattr(ws, "request", None)
        headers = getattr(request, "headers", None) or getattr(ws, "request_headers", None)
        real = headers.get("X-Real-IP") if headers else None
        if real:
            return real.strip()
    return host


# Type alias: handler called after auth succeeds
PacketHandler = Callable[[Packet, "PeerConnection"], Awaitable[None]]


class PeerConnection:
    """Authenticated connection to a remote node."""

    def __init__(self, ws, peer_node_id: str, peer_signing_pubkey: bytes,
                 peer_enc_pubkey: bytes, local_node_id: str, remote_ip: str = ""):
        self.ws = ws
        self.remote_ip = remote_ip   # see _client_ip — for per-IP limits (node/limits.py)
        self.peer_node_id = peer_node_id
        self.peer_signing_pubkey = peer_signing_pubkey
        self.peer_enc_pubkey = peer_enc_pubkey
        self.local_node_id = local_node_id

    async def send(self, packet: Packet):
        try:
            await self.ws.send(pack(packet))
        except ConnectionClosed:
            log.debug("send failed: connection to %s closed", self.peer_node_id[:8])
            raise

    async def recv(self) -> Packet:
        data = await self.ws.recv()
        return unpack(data)

    async def close(self):
        await self.ws.close()


class ConnectionRegistry:
    """Thread-safe registry of authenticated peer connections."""

    def __init__(self):
        self._conns: Dict[str, PeerConnection] = {}
        self._lock = asyncio.Lock()

    async def add(self, conn: PeerConnection):
        async with self._lock:
            self._conns[conn.peer_node_id] = conn

    async def remove(self, node_id: str, conn: Optional[PeerConnection] = None) -> bool:
        """`conn`, when given, must still be the CURRENTLY registered connection for this
        node_id or the removal is skipped — guards against a second, later connection for
        the SAME peer_node_id (the same cell/identity opening more than one connection at
        once, e.g. NodeCellsBrowser's one-off probe alongside a client's own persistent
        connection) silently clobbering each other's registry slot. Without this, closing
        the OLDER of two overlapping connections could wipe the entry for the NEWER, still-
        live one — found 2026-09-19: a client's persistent connection stayed open the whole
        time (confirmed via its own logs — no reconnect anywhere near the incident), but a
        NodeCellsBrowser probe using the same identity registered moments later, overwriting
        the registry slot, and when the probe's own short-lived connection then closed,
        `remove()` deleted that slot entirely — leaving the still-open persistent connection
        completely untracked. Every send_to() for that cell_id found nothing, so delivered/
        read ACKs meant for it just buffered forever instead of ever reaching a live socket.
        Callers that don't have the connection object on hand can omit it to keep the old,
        unconditional-by-key behavior (only safe when the caller already knows no such
        overlap is possible). Returns whether an entry was actually removed — callers use
        this to skip on_disconnect (which re-buffers "unacked" messages as if the recipient
        really went away) when this closing connection had already been superseded and the
        peer is, from the registry's point of view, still there."""
        async with self._lock:
            if conn is None or self._conns.get(node_id) is conn:
                return self._conns.pop(node_id, None) is not None
            return False

    async def get(self, node_id: str) -> Optional[PeerConnection]:
        async with self._lock:
            return self._conns.get(node_id)

    async def all(self) -> list:
        async with self._lock:
            return list(self._conns.values())


class Transport:
    """
    WebSocket transport for a Nevod node.

    Usage:
        t = Transport(identity, on_packet=handler)
        await t.start("0.0.0.0", 8765)
        conn = await t.connect("192.168.1.1:8765")
        await t.stop()
    """

    def __init__(self, identity, on_packet: PacketHandler):
        self.identity = identity
        self.on_packet = on_packet
        self.connections = ConnectionRegistry()
        self._server = None
        self.on_disconnect = None   # Optional[Callable[[str], Awaitable[None]]]

    @property
    def node_id(self) -> str:
        return self.identity.node_id

    async def start(self, host: str = "0.0.0.0", port: int = 8765):
        ssl_ctx = None
        if self.identity.tls_cert_pem:
            ssl_ctx = _build_server_ssl_ctx(
                self.identity.tls_cert_pem, self.identity.tls_key_pem
            )
        self._server = await websockets.serve(
            self._handle_incoming,
            host,
            port,
            ssl=ssl_ctx,
            ping_interval=20,
            # The ping queues behind whatever is already on its way to the phone: a few 512 KB
            # file chunks on a slow mobile downlink held it past 20 s, the node dropped a live
            # connection with 1011 "keepalive ping timeout" every minute, and each drop cost
            # the chunks in flight plus any call signal (device logs 2026-10-20: videos never
            # completed, a hangup arrived after the call had already ended on its own).
            ping_timeout=60,
            max_size=10 * 1024 * 1024,  # 10 MB — for image/file transfers
        )
        proto = "wss" if ssl_ctx else "ws"
        log.info("node %s listening on %s://%s:%d", self.node_id[:8], proto, host, port)

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        for conn in await self.connections.all():
            await conn.close()

    async def connect(self, address: str,
                      expected_fingerprint: Optional[str] = None) -> PeerConnection:
        """Open outgoing WSS connection to address "host:port", perform mutual auth."""
        if ":" not in address:
            raise ValueError(f"invalid address: {address}")
        ssl_ctx = _build_client_ssl_ctx()
        ws = await websockets.connect(f"wss://{address}", ssl=ssl_ctx)
        if expected_fingerprint:
            actual = _tls_fingerprint(ws)
            if actual != expected_fingerprint:
                await ws.close()
                raise ValueError(
                    f"TLS fingerprint mismatch for {address}: "
                    f"expected {expected_fingerprint[:16]}… got {actual[:16]}…"
                )
        conn = await self._do_auth(ws, expected_node_id=None, initiator=True)
        await self.connections.add(conn)
        asyncio.create_task(self._recv_loop(conn))
        return conn

    async def connect_to_node(self, node_id: str, address: str,
                               expected_fingerprint: Optional[str] = None) -> PeerConnection:
        """Connect and verify the remote node is who we expect."""
        ssl_ctx = _build_client_ssl_ctx()
        ws = await websockets.connect(f"wss://{address}", ssl=ssl_ctx)
        if expected_fingerprint:
            actual = _tls_fingerprint(ws)
            if actual != expected_fingerprint:
                await ws.close()
                raise ValueError(
                    f"TLS fingerprint mismatch for {node_id[:8]}: "
                    f"expected {expected_fingerprint[:16]}… got {actual[:16]}…"
                )
        conn = await self._do_auth(ws, expected_node_id=node_id, initiator=True)
        await self.connections.add(conn)
        asyncio.create_task(self._recv_loop(conn))
        return conn

    def sign(self, packet: Packet) -> Packet:
        """Sign packet with this node's signing key."""
        return sign_packet(packet, self.identity.signing)

    async def send_via(self, conn: PeerConnection, packet: Packet):
        """Sign and send via a specific connection."""
        await conn.send(self.sign(packet))

    async def send_to(self, node_id: str, packet: Packet) -> bool:
        """Sign and send packet to a connected peer. Returns False if not connected."""
        conn = await self.connections.get(node_id)
        if not conn:
            return False
        try:
            await self.send_via(conn, packet)
            return True
        except ConnectionClosed:
            await self.connections.remove(node_id, conn)
            return False

    # --- internal ---

    async def _handle_incoming(self, ws, path: str = "/"):
        try:
            conn = await self._do_auth(ws, expected_node_id=None, initiator=False)
        except Exception as e:
            # Expected background noise on any internet-facing port — port
            # scanners, health checks, a peer's connection dropping mid-handshake.
            # Not actionable, so DEBUG (not WARNING): in production, with nodes
            # constantly exchanging address lists and gossip-pinging each other,
            # this would otherwise drown out genuinely useful log signal.
            log.debug("auth failed from %s: %s", ws.remote_address, e)
            await ws.close()
            return

        await self.connections.add(conn)
        log.info("peer connected: %s", conn.peer_node_id[:8])
        try:
            # remove_on_exit=False: the removal below must be the one that takes the entry
            # out — its result decides whether on_disconnect runs. Found 2026-10-13: with
            # _recv_loop removing it first, `removed` was always False and on_disconnect
            # never ran at all since 9307822 (2026-09-19) — unacked messages written into
            # a dead client socket were simply lost instead of being re-buffered.
            await self._recv_loop(conn, remove_on_exit=False)
        finally:
            removed = await self.connections.remove(conn.peer_node_id, conn)
            # Who closed and why — device logs 2026-10-21 showed a client dropping every
            # 1–2 min with nothing on either side saying which end gave up.
            ws = conn.ws
            first = getattr(ws, "close_rcvd_then_sent", None)
            closed_by = "peer" if first is True else "node" if first is False else "nobody (no close frame)"
            log.info("peer disconnected: %s code=%s reason=%r closed_by=%s", conn.peer_node_id[:8],
                     getattr(ws, "close_code", None), getattr(ws, "close_reason", None) or "", closed_by)
            # Only treat this as a real "the peer went away" event if this connection was
            # still the one on file — if it had already been superseded by a newer
            # connection for the same peer_node_id, that newer one is still live and
            # nothing was actually lost (see ConnectionRegistry.remove's own doc comment).
            if removed and self.on_disconnect:
                try:
                    await self.on_disconnect(conn.peer_node_id)
                except Exception as e:
                    log.debug("on_disconnect error: %s", e)

    async def _do_auth(self, ws, expected_node_id: Optional[str],
                       initiator: bool) -> PeerConnection:
        """Schnorr ZKP mutual auth (Fiat-Shamir). initiator flag is unused — protocol is symmetric."""
        result = await do_schnorr_auth(ws, self.identity, expected_peer_id=expected_node_id)
        return PeerConnection(
            ws=ws,
            peer_node_id=result.node_id,
            peer_signing_pubkey=result.signing_pubkey,
            peer_enc_pubkey=result.enc_pubkey,
            local_node_id=self.node_id,
            remote_ip=_client_ip(ws),
        )

    async def _recv_loop(self, conn: PeerConnection, remove_on_exit: bool = True):
        try:
            async for raw in conn.ws:
                pkt = unpack(raw)
                if not verify_packet(pkt, conn.peer_signing_pubkey):
                    log.warning(
                        "dropped packet type=%s from %s: invalid signature",
                        pkt.type, conn.peer_node_id[:8],
                    )
                    continue
                try:
                    await self.on_packet(pkt, conn)
                except Exception as e:
                    log.error("packet handler error from %s: %s", conn.peer_node_id[:8], e)
        except ConnectionClosed:
            pass
        finally:
            if remove_on_exit:
                await self.connections.remove(conn.peer_node_id, conn)
