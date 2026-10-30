"""
Tests for the push relay a node serves for nodes without APNs credentials
(node.py _handle_push_relay_request, names.relayed_push_title): the requester's
text is never used, reserved names never reach the title, and alerts are
limited per device rather than per requesting node.
"""

import time
from types import SimpleNamespace

from node import node as node_mod
from node.identity import NodeIdentity
from node.names import relayed_push_title, PUSH_TITLE_DEFAULT, PUSH_TITLE_MAX
from node.node import Node, RELAY_PUSH_BODY
from node.protocol import make_push_relay_request
from node.storage import NodeEntry

REQUESTER = "ab" * 32


class FakeAPNs:
    def __init__(self):
        self.alerts: list[dict] = []
        self.voips: list[dict] = []

    async def send(self, token, title, body, sound=True, sender_cell_id=""):
        self.alerts.append({"token": token, "title": title, "body": body,
                            "sender_cell_id": sender_cell_id})
        return True

    async def send_voip(self, token, caller_id, caller_name):
        self.voips.append({"token": token, "caller_id": caller_id, "caller_name": caller_name})
        return True


async def make_relay_node(tmp_path, known: bool = True) -> tuple[Node, FakeAPNs]:
    id_path = str(tmp_path / "n.json")
    NodeIdentity.generate("127.0.0.1:19700").save(id_path)
    node = await Node.create(id_path, str(tmp_path / "n.db"))
    apns = FakeAPNs()
    node.apns = apns
    if known:
        now = int(time.time())
        await node.storage.upsert_node(NodeEntry(node_id=REQUESTER, address="1.2.3.4:8765",
                                                 access="open", last_seen=now, added_at=now))
    return node, apns


async def relay(node: Node, token: str, title: str = "Alice", body: str = "New message",
                kind: str = "alert", caller_id: str = "cd" * 32):
    pkt = make_push_relay_request(REQUESTER, node.identity.node_id, "apns", token,
                                  title, body, kind=kind, caller_id=caller_id)
    await node._handle_push_relay_request(pkt, SimpleNamespace(peer_node_id=REQUESTER))


class TestRelayedPushTitle:
    def test_plain_name_kept(self):
        assert relayed_push_title("Alice") == "Alice"

    def test_control_chars_and_newlines_flattened(self):
        assert relayed_push_title("Ali\nce\t\x00 B") == "Ali ce B"

    def test_capped(self):
        assert len(relayed_push_title("x" * 100)) == PUSH_TITLE_MAX

    def test_reserved_names_replaced(self):
        for name in ("Nevod", "Nevod Support", "nevod team", "Nеvod" ,  # Cyrillic е
                     "N.e.v.o.d", "Служба Невод", "administrator", "Support"):
            assert relayed_push_title(name) == PUSH_TITLE_DEFAULT, name

    def test_empty_falls_back(self):
        assert relayed_push_title("  \n ") == PUSH_TITLE_DEFAULT


class TestPushRelay:
    async def test_body_is_always_ours(self, tmp_path):
        node, apns = await make_relay_node(tmp_path)
        await relay(node, "t1", body="Your account is blocked, open http://evil.example")
        assert [a["body"] for a in apns.alerts] == [RELAY_PUSH_BODY]

    async def test_reserved_title_replaced(self, tmp_path):
        node, apns = await make_relay_node(tmp_path)
        await relay(node, "t1", title="Nevod Security")
        await relay(node, "t2", kind="voip", title="Nevod Support")
        assert apns.alerts[0]["title"] == PUSH_TITLE_DEFAULT
        assert apns.voips[0]["caller_name"] == PUSH_TITLE_DEFAULT

    async def test_unknown_node_refused(self, tmp_path):
        node, apns = await make_relay_node(tmp_path, known=False)
        await relay(node, "t1")
        assert apns.alerts == []

    async def test_many_devices_of_one_node_all_get_alerts(self, tmp_path):
        # The old guard allowed one alert per requesting node per minute — 50 users
        # of one node written to at once lost 49 notifications.
        node, apns = await make_relay_node(tmp_path)
        for i in range(50):
            await relay(node, f"token{i}")
        assert len(apns.alerts) == 50

    async def test_same_device_rate_limited(self, tmp_path):
        node, apns = await make_relay_node(tmp_path)
        await relay(node, "t1")
        await relay(node, "t1")
        assert len(apns.alerts) == 1

    async def test_voip_not_limited_per_device(self, tmp_path):
        node, apns = await make_relay_node(tmp_path)
        await relay(node, "v1", kind="voip")
        await relay(node, "v1", kind="voip")
        assert len(apns.voips) == 2

    async def test_per_node_ceiling(self, tmp_path, monkeypatch):
        monkeypatch.setattr(node_mod, "RELAY_PUSH_PER_NODE_PER_MIN", 5)
        node, apns = await make_relay_node(tmp_path)
        for i in range(8):
            await relay(node, f"token{i}")
        await relay(node, "v1", kind="voip")
        assert len(apns.alerts) == 5 and apns.voips == []
