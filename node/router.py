"""
Message routing.

Algorithm:
  1. Look up to_cell in presence_table → get visiting_node and home_node
  2. Try visiting_node first (where cell is currently online)
  3. Fallback to home_node
  4. If both unreachable → buffer the message (72h TTL)

Addressing: "cell_id@node_id" or just "node_id" for node-to-node messages.
"""

import asyncio
import logging
import random
import time
from collections import deque
from typing import TYPE_CHECKING, Optional, Dict, List, Tuple

from .protocol import (Packet, T, encode_payload, decode_payload, make_ping,
                       make_push_relay_request, sign_packet)

if TYPE_CHECKING:
    from .node import Node

log = logging.getLogger(__name__)

# Safety net against pathological rapid-resend bugs/loops — not meant to throttle
# routine conversation. See _send_push for why this dropped from 60s.
PUSH_RATE_LIMIT_SECS = 3.0

# One push per message id. A file's last chunk travels as plain MSG, and when the recipient
# keeps opening the app for a moment and leaving it, that chunk goes back to the buffer on
# every drop (on_connection_lost) or arrives again from the sender's node — each time a new
# "New message" push for a message that isn't there yet (a tester's phone 2026-10-20: a push on
# every exit from the app for a video still being assembled).
PUSHED_ID_TTL_SECS = 24 * 3600

# At most this many file chunks written to a client's connection and not yet acked. Whatever
# is written sits in socket and proxy buffers ahead of anything sent later, so with no limit a
# whole video was queued in front of a call's hangup: on a slow downlink (a 512 KB chunk every
# 3 s) the callee's call stayed up after the caller had hung up (device logs 2026-10-20). The
# rest wait in the node, behind which call signals and messages go out at once.
CHUNK_WINDOW = 2
# A client that doesn't ack chunks must not stall a transfer for good.
CHUNK_ACK_WAIT_SECS = 10.0

# A buffered call offer/signal replayed after this long is almost certainly a dead
# call, not a live one — the caller's own client gives up ringing well before this.
# Found 2026-09-02: a missed call (VoIP push failed with BadDeviceToken, see
# feedback_remind_apns_sandbox_flip) sat buffered for ~8 hours, then got replayed as
# a live incoming call the moment the recipient reopened the app the next morning.
CALL_SIGNAL_STALE_SECS = 60

# How far back ACKs are re-sent after a client's connection drops (see _remember_ack). A
# dead connection is noticed within ping_interval + ping_timeout = 80 s (transport.py), so
# anything older than this reached the client while the link was still alive.
ACK_RESEND_WINDOW_SECS = 90
# A re-sent ACK counts as freshly delivered again, so a client that keeps dropping its
# connection within the window would get the same ACKs over and over (seen on node1
# 2026-10-13: three acks re-sent 4 times in 2 minutes). Each one is re-sent at most this
# many times.
ACK_MAX_RESENDS = 3


def parse_addr(addr: str):
    """Split "cell_id@node_id" → (cell_id, node_id). Or (None, addr) for node-only."""
    if "@" in addr:
        cell_id, node_id = addr.split("@", 1)
        return cell_id, node_id
    return None, addr


class Router:
    def __init__(self, node: "Node"):
        self.node = node
        # cell_id → {msg_id → (Packet, seq)} — sent but not yet ACKed
        self._inflight: Dict[str, Dict[str, Tuple[Packet, int]]] = {}
        # cell_id → [(monotonic time sent, ACK Packet, seq)] — see _remember_ack
        self._recent_acks: Dict[str, List[Tuple[float, Packet, int]]] = {}
        # ACK packet id → (times re-sent, monotonic time of the last one) — see ACK_MAX_RESENDS
        self._ack_resends: Dict[str, Tuple[int, float]] = {}
        self._last_seq = 0
        # (recipient_cell_id, sender_cell_id) → monotonic time of last push sent
        self._push_times: Dict[tuple, float] = {}
        self._pushed_ids: Dict[str, float] = {}   # see PUSHED_ID_TTL_SECS
        # cell_id → chunks waiting for the window, ids written but not acked, sender task —
        # see CHUNK_WINDOW and _chunk_sender
        self._chunk_queue: Dict[str, "deque[Packet]"] = {}
        self._chunk_written: Dict[str, set] = {}
        self._chunk_tasks: Dict[str, "asyncio.Task"] = {}

    def _next_seq(self) -> int:
        """Strictly increasing across calls (and, via the wall clock, across restarts) —
        the packet's place in line if it ever has to be buffered, see buffer_message."""
        self._last_seq = max(time.time_ns(), self._last_seq + 1)
        return self._last_seq

    async def route(self, pkt: Packet, seq: Optional[int] = None):
        """Route a MSG packet to its destination. seq: only flush_buffer passes it — the
        packet's original place in line; everything else gets a fresh one here."""
        if seq is None:
            seq = self._next_seq()
        ack_tag = None
        if pkt.type == T.ACK:
            # ACK volume is low — log at info so this shows up without DEBUG enabled,
            # useful while chasing why a delivered/read ack didn't arrive.
            try:
                d = decode_payload(pkt.payload)
                ack_tag = "message_id=%s status=%s" % (d.get("message_id", "?")[:8], d.get("status", "?"))
            except Exception:
                ack_tag = "(undecodable payload)"
            log.info("router: routing ACK id=%s from=%s to=%s %s",
                     pkt.id[:8], pkt.from_addr[:24], pkt.to_addr[:24], ack_tag)

        cell_id, to_node_id = parse_addr(pkt.to_addr)

        if cell_id is None:
            # node-to-node message: deliver to connected peer directly
            await self._send_to_node(to_node_id, pkt)
            return

        # Recipient blocked this sender (chat_prefs {"blocked": true}) — drop before
        # delivery, buffering or any push. The block row only exists on the recipient's own
        # home node, so a cross-node packet passes through the sender's node untouched and
        # is dropped here once it reaches the recipient's node. Silent on purpose: the
        # sender just sees the message stay undelivered, same as other messengers.
        sender_cell = pkt.from_addr.split("@")[0] if "@" in pkt.from_addr else pkt.from_addr
        if sender_cell and await self.node.storage.is_blocked(cell_id, sender_cell):
            log.info("router: dropping %s %s — %s blocked sender %s",
                     pkt.type, pkt.id[:8], cell_id[:8], sender_cell[:8])
            # The sender gets the same generic "failed" ack as for a recipient that doesn't
            # exist (user decision 2026-09-28: "не доставлено" without a reason) — clearer
            # than a message stuck on "sent" forever, without revealing the block itself.
            await self._notify_undeliverable(pkt)
            return

        # cell message: resolve presence
        presence = await self.node.storage.get_presence(cell_id)
        if pkt.type == T.MSG:
            log.info("router: routing MSG id=%s from=%s to=%s presence=%s",
                     pkt.id[:8], pkt.from_addr[:24], pkt.to_addr[:24],
                     "none" if presence is None else "visiting=%s home=%s" % (
                         presence.visiting_node_id, presence.home_node_id))

        if presence is None:
            if ack_tag:
                log.info("router: ACK %s — no presence for %s", ack_tag, cell_id[:8])
            cell = await self.node.storage.get_cell(cell_id)
            if cell:
                sent = await self._deliver_local(pkt, seq)
                if ack_tag:
                    log.info("router: ACK %s — deliver_local(no presence)=%s", ack_tag, sent)
                if not sent:
                    # Cell registered here but offline and has no presence — buffer
                    # (ACKs too: a "read" receipt sent while the original sender happens
                    # to be disconnected must not just vanish — it should show up once
                    # they reconnect, same as any other message would).
                    log.info("router: buffering %s %s for offline cell %s (no presence)",
                             pkt.type, pkt.id[:8], cell_id[:8])
                    await self.node.storage.buffer_message(
                        pkt.id, cell_id, self.node.identity.node_id, _serialize_packet(pkt), seq
                    )
                    if pkt.type == T.MSG:
                        await self._send_push(cell_id, pkt)
                        await self._notify_offline(pkt)
                    elif pkt.type == T.MSG_SILENT:
                        await self._notify_offline(pkt)
                    elif pkt.type == T.VCALL_OFFER:
                        await self._send_voip_push(cell_id, pkt)
                    # VCALL_SIGNAL (ring/answer/ice/reject/hangup/busy): buffered above like
                    # anything else, but deliberately no push of either kind — only the
                    # initial offer should ever wake a killed app.
            elif to_node_id and to_node_id != self.node.identity.node_id:
                await self._send_to_node(to_node_id, pkt)
            else:
                log.info("router: unknown cell %s, dropping", cell_id[:8])
                if ack_tag:
                    log.info("router: ACK %s — unknown cell %s, DROPPED", ack_tag, cell_id[:8])
                else:
                    await self._notify_undeliverable(pkt)
            return

        # try visiting node first
        if presence.visiting_node_id:
            sent = await self._send_to_node(presence.visiting_node_id, pkt, seq)
            if ack_tag:
                log.info("router: ACK %s — visiting_node send=%s", ack_tag, sent)
            if sent:
                return

        # try home node
        sent = await self._send_to_node(presence.home_node_id, pkt, seq)
        if ack_tag:
            log.info("router: ACK %s — home_node send=%s", ack_tag, sent)
        if sent:
            return

        # Buffer regardless of type — a "read"/"delivered" ack sent while the recipient
        # (the original message's sender) is disconnected must survive until they
        # reconnect, same as any other message. Only MSG gets a push + "queued" notice;
        # nobody needs to be paged just because their own delivery receipt is pending.
        log.info("router: buffering %s %s for %s", pkt.type, pkt.id[:8], cell_id[:8])
        if ack_tag:
            log.info("router: ACK %s — buffering for %s", ack_tag, cell_id[:8])
        await self.node.storage.buffer_message(
            pkt.id, cell_id, presence.home_node_id, _serialize_packet(pkt), seq
        )
        if pkt.type == T.MSG:
            await self._send_push(cell_id, pkt)
            await self._notify_offline(pkt)
        elif pkt.type == T.MSG_SILENT:
            await self._notify_offline(pkt)
        elif pkt.type == T.VCALL_OFFER:
            await self._send_voip_push(cell_id, pkt)
        # VCALL_SIGNAL: buffered above, no push — see the other buffering branch's comment.

    async def _notify_offline(self, pkt: Packet):
        """Tell the original sender their message is queued, not delivered yet. Fires
        whenever we have to buffer — including when a push was also sent, since APNs
        gives no delivery confirmation: a push token existing doesn't mean the device is
        actually reachable right now (e.g. airplane mode), so "queued" is the only claim
        we can honestly make. flush_buffer() delivers (and a normal "delivered" ack
        follows) once the recipient actually reconnects."""
        if pkt.type not in (T.MSG, T.MSG_SILENT):
            return
        # The registrar (a synthetic, server-only identity — see node.py's
        # _ensure_registrar) is never a live transport peer, so a notice routed BACK to
        # it as the original sender can never be delivered either — it would just sit in
        # message_buffer until its TTL expires, same dead-letter problem node.py's
        # _dispatch already guards against for INCOMING packets. This is the other half:
        # found 2026-09-19 on node1 — 3 more stuck rows, all "status: offline" notices
        # this method generated for the registrar's own buffered sends, bypassing that
        # guard entirely since this calls route() directly, never through _dispatch.
        if self.node._is_service_address(pkt.from_addr):
            return
        notice = Packet(
            type=T.ACK,
            payload=encode_payload({"message_id": pkt.id, "status": "offline"}),
            from_addr=pkt.to_addr,
            to_addr=pkt.from_addr,
        )
        await self.route(notice)

    async def _notify_undeliverable(self, pkt: Packet):
        """Tell the sender their message will NEVER be delivered — the recipient cell
        doesn't exist here at all (self-deregistered/identity reset, or never registered),
        as opposed to _notify_offline's "queued, will retry" case. Without this, an
        unknown-cell MSG was silently dropped with zero feedback — the sender's client had
        no ack to react to and the message stayed stuck "sending" forever. status="failed"
        mirrors Message.MessageStatus.failed on the iOS side."""
        if pkt.type not in (T.MSG, T.MSG_SILENT):
            return
        # See _notify_offline's matching comment — same dead-letter guard, needed here
        # for the same reason even though this path is rarer for the registrar in
        # practice (its recipient not existing at all, vs. just being offline).
        if self.node._is_service_address(pkt.from_addr):
            return
        notice = Packet(
            type=T.ACK,
            payload=encode_payload({"message_id": pkt.id, "status": "failed"}),
            from_addr=pkt.to_addr,
            to_addr=pkt.from_addr,
        )
        await self.route(notice)

    async def _send_to_node(self, node_id: str, pkt: Packet, seq: int = 0) -> bool:
        my_id = self.node.identity.node_id
        if node_id == my_id:
            return await self._deliver_local(pkt, seq)

        # check existing connection
        sent = await self.node.transport.send_to(node_id, pkt)
        if sent:
            return True

        # try to connect
        entry = await self.node.storage.get_node(node_id)
        if not entry or entry.status != "online":
            return False

        try:
            conn = await self.node.transport.connect_to_node(
                node_id, entry.address,
                expected_fingerprint=entry.tls_fingerprint or None,
            )
            await self.node.transport.send_via(conn, pkt)
            return True
        except Exception as e:
            log.debug("router: failed to connect to %s: %s", node_id[:8], e)
            return False

    async def _deliver_local(self, pkt: Packet, seq: int = 0) -> bool:
        """Deliver to a cell connected on this node. Returns True if delivered."""
        cell_id, _ = parse_addr(pkt.to_addr)
        if cell_id and pkt.type == T.MSG_CHUNK and await self.node.transport.connections.get(cell_id):
            # Tracked as in flight right away, so a drop before it's even written buffers it
            # like the rest (on_connection_lost); _chunk_sender writes it when the window allows.
            self._inflight.setdefault(cell_id, {})[pkt.id] = (pkt, seq)
            self._chunk_queue.setdefault(cell_id, deque()).append(pkt)
            task = self._chunk_tasks.get(cell_id)
            if task is None or task.done():
                self._chunk_tasks[cell_id] = asyncio.create_task(self._chunk_sender(cell_id))
            return True
        if cell_id:
            sent = await self.node.transport.send_to(cell_id, pkt)
            if sent:
                # Track until we get an ACK — so we can buffer if connection dies. "Sent"
                # only means written to the socket: on a mobile link that has just dropped
                # it can sit in the TCP buffer and never arrive. MSG_CHUNK included: one lost
                # fragment leaves the whole file unassemblable on the receiver.
                if pkt.type in (T.MSG, T.MSG_SILENT, T.MSG_CHUNK):
                    self._inflight.setdefault(cell_id, {})[pkt.id] = (pkt, seq)
                elif pkt.type == T.ACK:
                    self._remember_ack(cell_id, pkt, seq)
                return True
        if self.node.on_message:
            await self.node.on_message(pkt)
            return True
        log.debug("router: cell %s not connected, no handler", pkt.to_addr[:16])
        return False

    async def _chunk_sender(self, cell_id: str):
        """Writes cell_id's queued chunks, keeping at most CHUNK_WINDOW of them unacked.
        Looks the queue up again each time: after a reconnect it is a new one."""
        try:
            while True:
                waited = 0.0
                while True:
                    written = self._chunk_written.setdefault(cell_id, set())
                    written.intersection_update(self._inflight.get(cell_id, {}).keys())  # acked leave
                    if len(written) < CHUNK_WINDOW or waited >= CHUNK_ACK_WAIT_SECS:
                        break
                    await asyncio.sleep(0.05)
                    waited += 0.05
                queue = self._chunk_queue.get(cell_id)
                if not queue:
                    break
                pkt = queue.popleft()
                if pkt.id not in self._inflight.get(cell_id, {}):
                    continue   # the connection dropped meanwhile — already buffered
                if not await self.node.transport.send_to(cell_id, pkt):
                    break      # gone: on_connection_lost buffers what's still in flight
                written.add(pkt.id)
        finally:
            if not self._chunk_queue.get(cell_id):
                self._chunk_queue.pop(cell_id, None)
                self._chunk_written.pop(cell_id, None)
            if self._chunk_tasks.get(cell_id) is asyncio.current_task():
                self._chunk_tasks.pop(cell_id, None)

    def on_ack_received(self, cell_id: str, msg_id: str) -> Optional[Packet]:
        """Called when cell_id sends ACK for msg_id — confirms delivery, removes from
        inflight. Returns the packet it confirmed, if it was being tracked here."""
        cell_inflight = self._inflight.get(cell_id)
        if not cell_inflight:
            return None
        entry = cell_inflight.pop(msg_id, None)
        if not cell_inflight:
            del self._inflight[cell_id]
        return entry[0] if entry else None

    def _remember_ack(self, cell_id: str, pkt: Packet, seq: int):
        """An ACK can't be tracked like a message — nobody acks an ack — yet it is lost the
        same way when written into a connection that is already dying (device log
        2026-10-13: an "offline" ack sent 12 s before the sender's socket dropped never
        arrived; the bubble kept its "sending" circle until "delivered" came a minute
        later, and a lost "delivered"/"read" could leave it there for good). So each one
        delivered here is kept for ACK_RESEND_WINDOW_SECS, and on_connection_lost re-queues
        the recent ones. Duplicates are harmless: the client only ever moves a message's
        status forward."""
        now = time.monotonic()
        recent = [e for e in self._recent_acks.get(cell_id, [])
                  if now - e[0] < ACK_RESEND_WINDOW_SECS]
        recent.append((now, pkt, seq))
        self._recent_acks[cell_id] = recent

    async def on_connection_lost(self, cell_id: str):
        """Called when connection to cell_id drops — buffer any unACKed messages, plus
        the ACKs sent to it just before (see _remember_ack)."""
        pending = self._inflight.pop(cell_id, {})
        # Queued chunks are in `pending` too (tracked when queued) — buffered below.
        queue = self._chunk_queue.pop(cell_id, None)
        if queue is not None:
            queue.clear()
        self._chunk_written.pop(cell_id, None)
        now = time.monotonic()
        # Forget counters nobody has touched for a while — an ACK still bouncing is re-sent
        # well within this.
        self._ack_resends = {k: v for k, v in self._ack_resends.items() if now - v[1] < 600}
        recent_acks = []
        for t, p, s in self._recent_acks.pop(cell_id, []):
            if now - t >= ACK_RESEND_WINDOW_SECS:
                continue
            count = self._ack_resends.get(p.id, (0, 0.0))[0]
            if count >= ACK_MAX_RESENDS:
                continue
            self._ack_resends[p.id] = (count + 1, now)
            recent_acks.append((p, s))
        if not pending and not recent_acks:
            return
        log.info("router: %d unACKed msg(s) + %d recent ack(s) for %s after disconnect — buffering",
                 len(pending), len(recent_acks), cell_id[:8])
        presence = await self.node.storage.get_presence(cell_id)
        if not presence:
            return
        for pkt, seq in recent_acks:
            await self.node.storage.buffer_message(
                pkt.id, cell_id, presence.home_node_id, _serialize_packet(pkt), seq
            )
        # Buffered with their ORIGINAL seq: chunks routed after the drop may already be in
        # the buffer, and these came before them (see get_buffered).
        for msg_id, (pkt, seq) in pending.items():
            await self.node.storage.buffer_message(
                msg_id, cell_id, presence.home_node_id, _serialize_packet(pkt), seq
            )
            if pkt.type == T.MSG:
                await self._send_push(cell_id, pkt)
            await self._notify_offline(pkt)

    async def _send_push(self, cell_id: str, pkt: Packet):
        """Send push if this node has credentials for the recipient's platform,
        or relay through a peer node that does (see _relay_push, node.py's
        _handle_push_relay_request) — most nodes will never hold real Apple/
        Firebase credentials themselves, only the node(s) the app publisher
        actually operates do."""
        apns = getattr(self.node, "apns", None)
        result = await self.node.storage.get_push_token(cell_id)
        if not result:
            log.info("router: _send_push %s — no push token for cell %s, skipping",
                     pkt.id[:8], cell_id[:8])
            return
        token, platform = result
        if platform != "apns":
            log.info("router: _send_push %s — platform=%s (not apns) for cell %s, skipping",
                     pkt.id[:8], platform, cell_id[:8])
            return

        sender = pkt.from_addr.split("@")[0] if "@" in pkt.from_addr else pkt.from_addr

        now_pushed = time.monotonic()
        if now_pushed - self._pushed_ids.get(pkt.id, -PUSHED_ID_TTL_SECS) < PUSHED_ID_TTL_SECS:
            log.info("router: _send_push %s — already pushed, skipping", pkt.id[:8])
            return
        if len(self._pushed_ids) > 10_000:
            self._pushed_ids = {k: t for k, t in self._pushed_ids.items()
                                if now_pushed - t < PUSHED_ID_TTL_SECS}

        # Muting a chat (ChatSettingsSheet's sound toggle, wire type chat_prefs) means
        # no notification at all, not just a silent one — check before the rate-limit
        # bookkeeping below so a muted sender never occupies a rate-limit slot either.
        if not await self.node.storage.get_sound_enabled(cell_id, sender):
            log.info("router: _send_push %s — muted by recipient %s for sender %s, skipping",
                     pkt.id[:8], cell_id[:8], sender[:8])
            return

        # Rate-limit: 1 push per (recipient, sender) per PUSH_RATE_LIMIT_SECS. Used to
        # be 60s specifically to survive a 45-chunk file transfer (<5s) without firing
        # 45 separate pushes — but that's now handled structurally: individual chunks
        # travel as MSG_CHUNK (never push-eligible, see route()), only the final chunk
        # of a transfer is plain MSG. A 60s window on top of that only hurt real
        # back-to-back human messages (confirmed live: two ordinary messages 20s apart
        # had their wake-up push silently dropped). What's left here is just a safety
        # net against pathological rapid-resend bugs/loops, not routine conversation.
        key = (cell_id, sender)
        now = time.monotonic()
        last = self._push_times.get(key, 0.0)
        if now - last < PUSH_RATE_LIMIT_SECS:
            log.info("router: push rate-limited for %s from %s (%.1fs since last)",
                     cell_id[:8], sender[:8], now - last)
            return
        self._push_times[key] = now

        sender_cell_obj = await self.node.storage.get_cell(sender)
        sender_name = sender_cell_obj.display_name if sender_cell_obj and sender_cell_obj.display_name else "Nevod"

        if apns is not None:
            ok = await apns.send(token, title=sender_name, body="New message",
                                  sound=True, sender_cell_id=sender)
            if ok:
                self._pushed_ids[pkt.id] = now_pushed
            log.info("router: _send_push %s to %s… result=%s", pkt.id[:8], token[:8], ok)
            return

        # Relay path (a peer node with its own APNs credentials sending on our behalf) —
        # the mute check above already gated this, so no separate sound-preference
        # threading is needed here.
        self._pushed_ids[pkt.id] = now_pushed
        await self._relay_push(pkt.id, platform, token, sender_name, "New message", sender)

    async def _relay_push(self, pkt_id: str, platform: str, token: str, title: str, body: str,
                          sender_cell_id: str = ""):
        """We have no credentials for `platform` ourselves — ask a known peer
        node that advertised relay capability for it to send instead."""
        candidates = [n for n in await self.node.storage.get_push_relay_nodes(platform)
                     if n.node_id != self.node.identity.node_id]
        if not candidates:
            log.info("router: _send_push %s — no push-relay node known for platform=%s, dropping",
                     pkt_id[:8], platform)
            return
        # Random pick, not always the same node — a relay node does real work on
        # our behalf (API call for push, or a lot more for TURN's media relay),
        # so spread requests across all capable nodes instead of overloading one.
        relay = random.choice(candidates)
        # caller_id doubles as sender_cell_id here — same field the voip relay path already
        # uses to carry the caller's cell id cross-node, reused rather than growing the wire
        # schema (see make_push_relay_request's kind="alert" vs "voip" doc comment).
        req = make_push_relay_request(self.node.identity.node_id, relay.node_id,
                                      platform, token, title, body, caller_id=sender_cell_id)
        sign_packet(req, self.node.identity.signing)
        ok = await self._send_to_node(relay.node_id, req)
        log.info("router: _send_push %s relayed via %s result=%s", pkt_id[:8], relay.node_id[:8], ok)

    async def _send_voip_push(self, cell_id: str, pkt: Packet):
        """VoIP push for a call offer — this is what actually wakes a killed/backgrounded
        app to show the CallKit incoming-call UI; a regular alert push physically cannot
        do that. No rate-limiting (unlike _send_push): a call offer is a one-off event,
        not part of a chunk-flood, and delaying it would mean a missed call."""
        token = await self.node.storage.get_voip_push_token(cell_id)
        if not token:
            log.debug("router: no voip token for %s, call offer %s not pushed",
                      cell_id[:8], pkt.id[:8])
            return
        sender = pkt.from_addr.split("@")[0] if "@" in pkt.from_addr else pkt.from_addr
        # Prefer the caller's own cleartext caller_name (works for any caller, any node —
        # see Packet.caller_name) over a local cells lookup, which only ever succeeds for
        # a caller registered on THIS node — cross-node calls would silently fall through
        # to "Nevod" otherwise, which is exactly the anonymous-caller bug this replaces.
        if pkt.caller_name:
            sender_name = pkt.caller_name
        else:
            sender_cell_obj = await self.node.storage.get_cell(sender)
            sender_name = sender_cell_obj.display_name if sender_cell_obj and sender_cell_obj.display_name else "Nevod"

        apns = getattr(self.node, "apns", None)
        if apns is not None:
            await apns.send_voip(token, caller_id=sender, caller_name=sender_name)
            return
        await self._relay_voip_push(pkt.id, token, sender, sender_name)

    async def _relay_voip_push(self, pkt_id: str, token: str, caller_id: str, caller_name: str):
        """We have no APNs credentials ourselves — ask a known peer node that advertised
        relay capability for "apns" to send the VoIP wakeup on our behalf. Same idea as
        _relay_push, just carrying the extra fields send_voip needs (see
        make_push_relay_request's kind="voip")."""
        candidates = [n for n in await self.node.storage.get_push_relay_nodes("apns")
                     if n.node_id != self.node.identity.node_id]
        if not candidates:
            log.info("router: _send_voip_push %s — no push-relay node known, dropping", pkt_id[:8])
            return
        relay = random.choice(candidates)
        req = make_push_relay_request(self.node.identity.node_id, relay.node_id,
                                      "apns", token, caller_name, "",
                                      kind="voip", caller_id=caller_id)
        sign_packet(req, self.node.identity.signing)
        ok = await self._send_to_node(relay.node_id, req)
        log.info("router: _send_voip_push %s relayed via %s result=%s", pkt_id[:8], relay.node_id[:8], ok)

    async def flush_buffer(self, cell_id: str):
        """Attempt to deliver all buffered messages for a cell that came online."""
        messages = await self.node.storage.get_buffered(cell_id)
        if messages:
            log.info("router: flushing %d buffered packet(s) for %s", len(messages), cell_id[:8])
        # Call signals and acks first, everything else after in seq order: each file chunk takes
        # a while on a slow downlink, and an offer buffered behind a video reached the callee
        # 30 s late — the call couldn't be answered, then rang again after the caller had
        # already given up (device logs 2026-10-20). Only those two: a silent signal (delete,
        # edit) or a reaction refers to a message, so it must not overtake it — a "delete for
        # everyone" sent first found nothing to delete and the message stayed (2026-10-21).
        pkts = [(msg, _deserialize_packet(msg.payload)) for msg in messages]
        jump_ahead = (T.VCALL_OFFER, T.VCALL_SIGNAL, T.ACK)
        pkts.sort(key=lambda mp: 0 if mp[1] and mp[1].type in jump_ahead else 1)
        for msg, pkt in pkts:
            if pkt:
                # Delete BEFORE route(), not after: if the cell disconnects again
                # mid-flush, route() re-buffers via buffer_message() (INSERT OR IGNORE
                # on the same message_id). Deleting afterwards would then wipe out that
                # fresh re-buffer — the row it "IGNORE"s into existing is the one we're
                # about to delete — silently losing the message forever instead of
                # retrying on the next reconnect.
                await self.node.storage.delete_buffered(msg.message_id)
                if (pkt.type in (T.VCALL_OFFER, T.VCALL_SIGNAL)
                        and time.time() - pkt.ts > CALL_SIGNAL_STALE_SECS):
                    log.info("router: dropping stale %s %s for %s (age=%.0fs)",
                             pkt.type, pkt.id[:8], cell_id[:8], time.time() - pkt.ts)
                    continue
                await self.route(pkt, seq=msg.seq or None)


def _serialize_packet(pkt: Packet) -> bytes:
    import msgpack
    return msgpack.packb({
        "type": pkt.type, "id": pkt.id,
        "from": pkt.from_addr, "to": pkt.to_addr,
        "payload": pkt.payload, "sig": pkt.sig, "ts": pkt.ts,
        "caller_name": pkt.caller_name,
    }, use_bin_type=True)


def _deserialize_packet(data: bytes) -> Optional[Packet]:
    try:
        from .protocol import unpack
        return unpack(data)
    except Exception:
        return None
