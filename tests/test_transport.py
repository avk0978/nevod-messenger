"""Tests for ConnectionRegistry — specifically the overlapping-connection class of bug
found 2026-09-19: a second connection authenticating with the SAME peer_node_id (e.g. a
client's persistent connection plus a short-lived probe like NodeCellsBrowser, both using
the same identity) used to silently clobber each other's registry slot. Closing the OLDER
of the two then wiped the registry entry for the NEWER, still-live one entirely — every
send_to() for that peer_node_id found nothing, so ACKs/messages meant for it just buffered
forever instead of reaching the connection that was actually still open.
"""

from node.transport import ConnectionRegistry, PeerConnection


def make_conn(peer_node_id: str) -> PeerConnection:
    """A PeerConnection with no real websocket — ConnectionRegistry only ever compares
    identity and peer_node_id, never touches .ws, so this is a safe stand-in."""
    return PeerConnection(
        ws=None, peer_node_id=peer_node_id,
        peer_signing_pubkey=b"\x00" * 32, peer_enc_pubkey=b"\x00" * 32,
        local_node_id="local",
    )


class TestConnectionRegistryOverlap:
    async def test_second_connection_becomes_authoritative(self):
        reg = ConnectionRegistry()
        a = make_conn("peer1")
        b = make_conn("peer1")
        await reg.add(a)
        await reg.add(b)
        # Same peer_node_id — registry only ever tracks one "current" connection per
        # identity by design; the newest add() wins, matching existing behavior.
        assert await reg.get("peer1") is b

    async def test_closing_superseded_connection_does_not_evict_the_newer_one(self):
        """The actual bug: A registers, B (same peer_node_id) registers and becomes
        current, then A's OWN cleanup runs (e.g. a stale/duplicate connection finally
        closing) — this must NOT remove B's still-live entry."""
        reg = ConnectionRegistry()
        a = make_conn("peer1")
        b = make_conn("peer1")
        await reg.add(a)
        await reg.add(b)

        removed = await reg.remove("peer1", a)  # A is stale — no longer the current entry

        assert removed is False
        assert await reg.get("peer1") is b  # B (still live) must survive

    async def test_closing_the_current_connection_does_evict_it(self):
        reg = ConnectionRegistry()
        a = make_conn("peer1")
        await reg.add(a)

        removed = await reg.remove("peer1", a)

        assert removed is True
        assert await reg.get("peer1") is None

    async def test_remove_without_conn_arg_keeps_old_unconditional_behavior(self):
        """Callers that don't have the connection object on hand (existing call sites
        that predate this fix, or ones that genuinely can't have an overlap) can still
        omit it — same as before, removes whatever's there by key alone."""
        reg = ConnectionRegistry()
        a = make_conn("peer1")
        await reg.add(a)

        removed = await reg.remove("peer1")

        assert removed is True
        assert await reg.get("peer1") is None
