"""
Best-effort UPnP port forwarding (M3).

Tries to ask the LAN's UPnP Internet Gateway Device to forward the chosen
port to this machine — works on many home routers with UPnP enabled, saves
the user a trip into the router's admin UI. Silently does nothing if UPnP
is unavailable/disabled (common — e.g. MikroTik routers ship with it off
by default, confirmed on the hardware this was built against) or the
miniupnpc dependency isn't present. Never raises — the join flow's own
reachability test (node/node.py:_test_reachability) is the actual source
of truth for whether the node ended up reachable, regardless of whether
this succeeded.
"""

import logging

log = logging.getLogger(__name__)


def try_forward_port(port: int, description: str = "Nevod node") -> bool:
    try:
        import miniupnpc
    except ImportError:
        return False
    try:
        u = miniupnpc.UPnP()
        u.discoverdelay = 2000
        if u.discover() < 1:
            log.info("UPnP: no Internet Gateway Device found")
            return False
        u.selectigd()
        try:
            u.deleteportmapping(port, "TCP")  # clear a stale mapping from a previous run
        except Exception:
            pass
        ok = bool(u.addportmapping(port, "TCP", u.lanaddr, port, description, ""))
        if ok:
            log.info("UPnP: forwarded TCP port %d -> %s", port, u.lanaddr)
        return ok
    except Exception as e:
        log.info("UPnP port forward attempt failed/unavailable: %s", e)
        return False
