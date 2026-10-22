"""
Gossip protocol — node_table synchronization.

Every 30 seconds:
  1. Ping all known nodes → update last_seen / missed_pings / status
  2. Exchange node_table with 3-5 random online peers (push-pull)
  3. Propagate pending removals (offline > 72h)

Propagation speed: O(log N) rounds to reach all nodes.
"""

import asyncio
import logging
import random
import time
from typing import TYPE_CHECKING

from .protocol import (
    T, Packet,
    make_ping, make_pong,
    make_gossip, encode_payload, decode_payload,
)
from .storage import NodeEntry

if TYPE_CHECKING:
    from .node import Node

log = logging.getLogger(__name__)

GOSSIP_INTERVAL  = 30    # seconds
GOSSIP_FANOUT    = 3     # random peers per gossip round
PING_TIMEOUT     = 10    # seconds to wait for pong


class GossipEngine:
    def __init__(self, node: "Node"):
        self.node = node
        self._task: asyncio.Task | None = None

    def start(self):
        self._task = asyncio.create_task(self._loop(), name="gossip")

    def stop(self):
        if self._task:
            self._task.cancel()

    async def _loop(self):
        while True:
            try:
                await self._round()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("gossip round error: %s", e)
            await asyncio.sleep(GOSSIP_INTERVAL)

    async def _round(self):
        nodes = await self.node.storage.get_all_nodes()
        my_id = self.node.identity.node_id

        for entry in nodes:
            if entry.node_id == my_id:
                continue
            await self._ping_node(entry)

        await self.node.storage.cleanup_expired_nodes()
        await self.node.storage.cleanup_expired_messages()

        online = [n for n in nodes if n.status == "online" and n.node_id != my_id]
        peers = random.sample(online, min(GOSSIP_FANOUT, len(online)))
        for peer in peers:
            await self._exchange(peer)

    async def _ping_node(self, entry: NodeEntry):
        conn = await self.node.transport.connections.get(entry.node_id)
        if not conn:
            try:
                conn = await asyncio.wait_for(
                    self.node.transport.connect_to_node(
                        entry.node_id, entry.address,
                        expected_fingerprint=entry.tls_fingerprint or None,
                    ),
                    timeout=PING_TIMEOUT,
                )
            except Exception:
                await self.node.storage.update_node_ping(entry.node_id, success=False)
                return

        pkt = make_ping(self.node.identity.node_id, entry.node_id)
        try:
            await asyncio.wait_for(
                self.node.transport.send_via(conn, pkt),
                timeout=PING_TIMEOUT,
            )
            await self.node.storage.update_node_ping(entry.node_id, success=True)
        except Exception:
            await self.node.storage.update_node_ping(entry.node_id, success=False)

    async def _exchange(self, peer: NodeEntry):
        conn = await self.node.transport.connections.get(peer.node_id)
        if not conn:
            return
        all_nodes = await self.node.storage.get_all_nodes()
        entries = [n.to_dict() for n in all_nodes]

        # Include cell presence only if this node is open
        presence_entries = []
        if self.node.identity.access == "open":
            my_id = self.node.identity.node_id
            presences = await self.node.storage.get_presence_by_home(my_id)
            presence_entries = [
                {"cell_id": p.cell_id, "home_node_id": p.home_node_id}
                for p in presences
            ]

        pkt = make_gossip(self.node.identity.node_id, entries,
                          presence_entries or None)
        try:
            await self.node.transport.send_via(conn, pkt)
        except Exception as e:
            log.debug("gossip send to %s failed: %s", peer.node_id[:8], e)

    async def handle_gossip(self, pkt: Packet):
        """Process incoming GOSSIP packet — merge node_table and presence."""
        try:
            data = decode_payload(pkt.payload)
            remote_nodes = data.get("nodes", [])
        except Exception:
            return

        for n in remote_nodes:
            node_id = n.get("node_id", "")
            address = n.get("address", "")
            if not node_id or not address or node_id == self.node.identity.node_id:
                continue
            existing = await self.node.storage.get_node(node_id)
            # Always upsert, not just on first discovery — a node's capabilities
            # (push_relay_platforms/turn_relay) or address can change after we
            # first learned about it, and only periodic gossip will ever tell us
            # (see node.py's start() comment for the same problem on our own
            # row). upsert_node's ON CONFLICT clause doesn't touch type/access,
            # so re-sending those here can't clobber a locally-decided value.
            entry = NodeEntry(
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
                added_at=existing.added_at if existing else int(time.time()),
            )
            await self.node.storage.upsert_node(entry)
            if existing is None:
                log.info("gossip: discovered new node %s", node_id[:8])

        # Merge presence entries from open nodes (don't overwrite locally-known cells)
        for p in data.get("presence", []):
            cell_id      = p.get("cell_id", "")
            home_node_id = p.get("home_node_id", "")
            if not cell_id or not home_node_id:
                continue
            local_cell = await self.node.storage.get_cell(cell_id)
            if local_cell:
                continue  # we know this cell locally — trust our data
            await self.node.storage.update_presence(cell_id, home_node_id)
            log.debug("gossip: learned presence of cell %s @ %s",
                      cell_id[:8], home_node_id[:8])

    async def handle_ping(self, pkt: Packet, conn):
        pong = make_pong(self.node.identity.node_id, pkt.from_addr, pkt.id)
        await self.node.transport.send_via(conn, pong)

    async def handle_pong(self, pkt: Packet):
        node_id = pkt.from_addr
        await self.node.storage.update_node_ping(node_id, success=True)
