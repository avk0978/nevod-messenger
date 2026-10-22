"""Per-IP limits for a public open node (Nevod Open).

On an invite-only node every registration was vouched for by whoever handed out the invite.
On an open one anybody can register, so a single address scripting thousands of identities
(to spam, or to grab names) is the thing to slow down. Limits are deliberately loose and
off by default: mobile carriers put many real users behind one address (CGNAT), so this is
a brake on scripts, not a quota on people.

Configured per node by environment variables (0 = no limit):
  NEVOD_NEW_CELLS_PER_IP_PER_HOUR      — new cells registering (reconnects never count)
  NEVOD_OPEN_NODE_JOINS_PER_IP_PER_DAY — nodes joining without an invite (default 3)
"""
import os
import time
from collections import deque
from typing import Deque, Dict


class RateLimiter:
    """At most `limit` events per key within `window` seconds; limit <= 0 disables it.
    In memory only — a restart forgives everyone, which is fine for a brake."""

    def __init__(self, limit: int, window: float):
        self.limit = limit
        self.window = window
        self._events: Dict[str, Deque[float]] = {}

    def allow(self, key: str) -> bool:
        """Records the event and returns True if it fits within the limit."""
        if self.limit <= 0 or not key:
            return True
        now = time.monotonic()
        q = self._events.setdefault(key, deque())
        while q and now - q[0] >= self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        if len(self._events) > 10_000:   # forget keys whose events have all expired
            self._events = {k: v for k, v in self._events.items() if v and now - v[-1] < self.window}
        return True


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def new_cells_limiter() -> RateLimiter:
    return RateLimiter(_env_int("NEVOD_NEW_CELLS_PER_IP_PER_HOUR", 0), 3600)


def open_node_joins_limiter() -> RateLimiter:
    return RateLimiter(_env_int("NEVOD_OPEN_NODE_JOINS_PER_IP_PER_DAY", 3), 24 * 3600)
