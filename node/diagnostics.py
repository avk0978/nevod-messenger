"""
Self-diagnostics — the checks this project's debugging sessions kept re-deriving by hand
(which process actually owns the port, whether the running build understands a new packet
type, node.json vs node_table drift, missing optional deps) collapsed into one callable so
the admin panel / CLI can report them instead of SSH + sqlite archaeology (see 2026-08-08
session: hours spent finding that a frozen exe nobody had restarted in months silently
ignored node_list_request, plus a locale-dependent encoding bug in identity.py).
"""

import os
from dataclasses import dataclass, asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .node import Node

# Handler methods expected to exist on Node — extend this whenever a new client- or
# peer-facing packet type is added. A missing one is the strongest available signal
# that an installed build (especially a frozen exe nobody has rebuilt) predates that
# feature — exactly the bug that left node_list_request silently unanswered for months.
_EXPECTED_HANDLERS = [
    "_handle_node_list_request",
    "_handle_group_members_request",
    "_handle_push_relay_request",
    "_handle_turn_relay_request",
    "_handle_chat_prefs",
    "_handle_reachability_probe",
]


@dataclass
class Check:
    id: str
    label: str
    status: str  # "ok" | "warn" | "fail"
    detail: str


async def run_diagnostics(node: "Node") -> list[dict]:
    checks = [
        _check_build_currency(node),
        await _check_identity_db_consistency(node),
        _check_dependencies(node),
        await _check_peer_reachability(node),
    ]
    return [asdict(c) for c in checks]


def _check_build_currency(node: "Node") -> Check:
    missing = [h for h in _EXPECTED_HANDLERS if not hasattr(node, h)]
    if missing:
        return Check(
            "build_currency", "Актуальность кода", "fail",
            "Не найдены обработчики: " + ", ".join(missing) +
            " — установленная сборка старее текущего протокола, нужна пересборка/переустановка.",
        )
    return Check("build_currency", "Актуальность кода", "ok",
                 "Все ожидаемые обработчики протокола присутствуют.")


async def _check_identity_db_consistency(node: "Node") -> Check:
    entry = await node.storage.get_node(node.identity.node_id)
    if entry is None:
        return Check("identity_db", "Согласованность identity/DB", "warn",
                      "Собственная запись отсутствует в node_table — появится после следующего старта.")
    mismatches = []
    if entry.access != node.identity.access:
        mismatches.append(f"access: node.json={node.identity.access!r}, DB={entry.access!r}")
    if entry.address != node.identity.address:
        mismatches.append(f"address: node.json={node.identity.address!r}, DB={entry.address!r}")
    if entry.name != node.identity.name:
        mismatches.append(f"name: node.json={node.identity.name!r}, DB={entry.name!r}")
    if mismatches:
        return Check(
            "identity_db", "Согласованность identity/DB", "fail",
            "Расхождение (перезапустите ноду, чтобы синхронизировать из node.json): "
            + "; ".join(mismatches),
        )
    return Check("identity_db", "Согласованность identity/DB", "ok",
                 "node.json и node_table совпадают (access/address/name).")


def _check_dependencies(node: "Node") -> Check:
    problems = []
    try:
        from . import push as _push
        if not _push._HAS_JWT:
            problems.append("PyJWT не установлен — push-уведомления (APNs) отключены")
    except Exception:
        pass
    if node.turn_relay and not os.environ.get("TURN_SECRET"):
        problems.append("TURN_SECRET не задан, но turn_relay включён — TURN-креды выдаваться не будут")
    apns_key = os.environ.get("APNS_PRIVATE_KEY")
    if apns_key and not os.path.exists(apns_key):
        problems.append(f"APNS_PRIVATE_KEY указывает на несуществующий файл: {apns_key}")
    if problems:
        return Check("dependencies", "Зависимости и конфигурация", "warn", "; ".join(problems))
    return Check("dependencies", "Зависимости и конфигурация", "ok", "Проблем не найдено.")


async def _check_peer_reachability(node: "Node") -> Check:
    nodes = await node.storage.get_all_nodes()
    peers = [n for n in nodes if n.node_id != node.identity.node_id]
    if not peers:
        return Check("reachability", "Внешняя доступность", "warn",
                      "Нет известных пиров, через которых можно проверить — узел ни с кем не связан (join).")
    for peer in peers:
        result = await node.probe_reachability_via(peer.node_id)
        if result is None:
            continue  # this peer itself unreachable/didn't answer — try the next one
        if result:
            return Check("reachability", "Внешняя доступность", "ok",
                         f"{peer.node_id[:8]} подтвердил доступность снаружи: {node.identity.address}")
        return Check("reachability", "Внешняя доступность", "fail",
                     f"{peer.node_id[:8]} НЕ смог достучаться до адреса: {node.identity.address} — "
                     f"проверьте проброс порта/файрвол.")
    return Check("reachability", "Внешняя доступность", "warn",
                 "Ни один известный пир не ответил на проверку (все офлайн?).")
