"""
SQLite storage for a Nevod node.

Tables:
  node_table      — all known nodes in the network
  cells           — cells registered on this node
  presence_table  — where each home-cell is currently located
  message_buffer  — buffered messages for offline recipients (TTL 72h)
  invite_codes    — one-time cell invite codes (TTL 24h by default, admin may pick)
  allowed_cells   — cells that have been admitted to the node
  join_requests   — invite_mode="admin" registration requests, see node.py's
                    _handle_join_request and MD_Discuss/DISCUSS_REGISTRATION_CHANNEL.md
"""

import secrets
import time
import aiosqlite
from dataclasses import dataclass, field
from typing import Optional, List

INVITE_TTL_SECS   = 600              # 10 minutes — node invites (operator-to-operator, done live)
# Cell invite codes are handed to people, who open them hours later — 10 minutes was far too
# short (device test 2026-10-16). The admin panel can pick another lifetime from this list.
CELL_INVITE_TTL_SECS = 24 * 3600
CELL_INVITE_TTL_CHOICES = (3600, 24 * 3600, 7 * 24 * 3600)
CARD_TTL_SECS     = 7 * 24 * 3600   # 7 days
USED_INVITE_HISTORY_SECS = 7 * 24 * 3600  # how long a USED code still shows in the admin list
INVITE_ALPHABET   = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # no 0/O/1/I/L

TTL_NODE_OFFLINE_SECS = 72 * 3600    # 72h → remove from node_table
TTL_MESSAGE_SECS      = 72 * 3600    # 72h → drop undelivered message
MISSED_PINGS_OFFLINE  = 3


SCHEMA = """
CREATE TABLE IF NOT EXISTS node_table (
    node_id              TEXT PRIMARY KEY,
    address              TEXT NOT NULL,
    type                 TEXT NOT NULL DEFAULT 'permanent',
    access               TEXT NOT NULL DEFAULT 'closed',
    cert                 BLOB,
    tls_fingerprint      TEXT NOT NULL DEFAULT '',
    parent_node          TEXT,
    name                 TEXT NOT NULL DEFAULT '',
    push_relay_platforms TEXT NOT NULL DEFAULT '',
    turn_relay           INTEGER NOT NULL DEFAULT 0,
    last_seen            INTEGER NOT NULL,
    missed_pings         INTEGER NOT NULL DEFAULT 0,
    status               TEXT NOT NULL DEFAULT 'online',
    added_at             INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cells (
    cell_id         TEXT PRIMARY KEY,
    signing_pubkey  BLOB NOT NULL,
    enc_pubkey      BLOB NOT NULL,
    registered_at   INTEGER NOT NULL,
    is_home         INTEGER NOT NULL DEFAULT 1,
    display_name    TEXT NOT NULL DEFAULT ''
);

-- Admin-curated SUBSET of `cells` this node's operator has explicitly chosen to
-- surface for discovery (the "Explore Network" cell/moon list under a planet) --
-- deliberately separate from the `cells` table itself, which holds every
-- registered cell including ordinary private users; exposing that table as-is
-- would leak their identities. Gated by NodeIdentity.cells_visibility.
CREATE TABLE IF NOT EXISTS published_cells (
    cell_id         TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    kind            TEXT NOT NULL DEFAULT 'bot',
    landing_md      TEXT NOT NULL DEFAULT '',
    published_at    INTEGER NOT NULL,
    -- BYOK AI bot: comma-separated providers it accepts the USER's key for
    -- (anthropic,openai,gemini — node/ai_providers.py). Empty = not an AI bot.
    ai_providers    TEXT NOT NULL DEFAULT ''
);

-- BYOK AI bots the operator runs INSIDE this node process (admin page "AI-боты",
-- node/ai_bots.py). Each is an ordinary cell of this node; its keys live in
-- ai_bots/<cell_id>.json next to node.json. Nothing here unless the admin adds one.
CREATE TABLE IF NOT EXISTS ai_bots (
    cell_id         TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    system_prompt   TEXT NOT NULL,
    providers       TEXT NOT NULL,
    enabled         INTEGER NOT NULL DEFAULT 1,
    created_at      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS presence_table (
    cell_id             TEXT PRIMARY KEY,
    home_node_id        TEXT NOT NULL,
    visiting_node_id    TEXT,
    updated_at          INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS message_buffer (
    message_id  TEXT PRIMARY KEY,
    to_cell     TEXT NOT NULL,
    to_node     TEXT NOT NULL,
    payload     BLOB NOT NULL,
    created_at  INTEGER NOT NULL,
    expires_at  INTEGER NOT NULL,
    seq         INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_buf_to_cell  ON message_buffer(to_cell);
CREATE INDEX IF NOT EXISTS idx_buf_expires  ON message_buffer(expires_at);
CREATE INDEX IF NOT EXISTS idx_node_status  ON node_table(status);

CREATE TABLE IF NOT EXISTS invite_codes (
    code        TEXT PRIMARY KEY,
    created_by  TEXT NOT NULL,
    created_at  INTEGER NOT NULL,
    expires_at  INTEGER NOT NULL,
    used        INTEGER NOT NULL DEFAULT 0,
    used_by     TEXT
);

CREATE TABLE IF NOT EXISTS allowed_cells (
    cell_id     TEXT PRIMARY KEY,
    invited_by  TEXT NOT NULL,
    joined_at   INTEGER NOT NULL,
    can_invite  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS join_requests (
    cell_id        TEXT PRIMARY KEY,
    signing_pubkey TEXT NOT NULL,
    enc_pubkey     TEXT NOT NULL,
    note           TEXT NOT NULL DEFAULT '',
    display_name   TEXT NOT NULL DEFAULT '',
    created_at     INTEGER NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending',
    resolved_at    INTEGER
);

CREATE TABLE IF NOT EXISTS node_invites (
    code        TEXT PRIMARY KEY,
    created_by  TEXT NOT NULL,
    created_at  INTEGER NOT NULL,
    expires_at  INTEGER NOT NULL,
    used        INTEGER NOT NULL DEFAULT 0,
    used_by     TEXT
);

-- Per-admin panel logins (Безопасность page) — additional to, never a replacement
-- for, the single NEVOD_ADMIN_PASSWORD/installer credential AdminServer is
-- constructed with, which stays a permanent break-glass login (see admin.py's
-- _check_auth). password_hash is never a plaintext password — see admin.py's
-- _hash_password/_verify_password (PBKDF2-HMAC-SHA256, random per-row salt).
CREATE TABLE IF NOT EXISTS admin_users (
    username      TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS contact_cards (
    code        TEXT PRIMARY KEY,
    cell_id     TEXT NOT NULL,
    enc_pub     TEXT NOT NULL,
    created_at  INTEGER NOT NULL,
    expires_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS push_tokens (
    cell_id     TEXT PRIMARY KEY,
    token       TEXT NOT NULL,
    platform    TEXT NOT NULL DEFAULT 'apns',
    updated_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS voip_push_tokens (
    cell_id     TEXT PRIMARY KEY,
    token       TEXT NOT NULL,
    updated_at  INTEGER NOT NULL
);

-- Per-(recipient, sender) push sound preference. A row only exists when the
-- recipient has turned sound OFF for that sender's chat -- absence of a row
-- means "sound on" (the default), so the common case needs no row at all.
CREATE TABLE IF NOT EXISTS chat_push_prefs (
    owner_cell_id   TEXT NOT NULL,
    sender_cell_id  TEXT NOT NULL,
    updated_at      INTEGER NOT NULL,
    PRIMARY KEY (owner_cell_id, sender_cell_id)
);

-- Per-(recipient, sender) block. A row means the owner blocked that sender: the router
-- drops everything the sender addresses to the owner (messages, reactions, calls) before
-- buffering or pushing -- see Router.route. Set via chat_prefs {"blocked": true}.
CREATE TABLE IF NOT EXISTS chat_blocks (
    owner_cell_id   TEXT NOT NULL,
    sender_cell_id  TEXT NOT NULL,
    updated_at      INTEGER NOT NULL,
    PRIMARY KEY (owner_cell_id, sender_cell_id)
);

-- Appeals to this node's built-in "administrator" cell (node.py _ensure_administrator):
-- complaints/questions users send from the app, and the operator's replies from the admin
-- panel's Обращения page. direction: 'in' (from the user) | 'out' (administrator's reply).
-- enc_pub is kept for 'in' rows so a reply can reach a sender homed on another node.
CREATE TABLE IF NOT EXISTS appeals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    cell_id       TEXT NOT NULL,
    node_id       TEXT NOT NULL DEFAULT '',
    display_name  TEXT NOT NULL DEFAULT '',
    enc_pub       TEXT NOT NULL DEFAULT '',
    direction     TEXT NOT NULL,
    text          TEXT NOT NULL,
    created_at    INTEGER NOT NULL,
    seen          INTEGER NOT NULL DEFAULT 0
);

-- Diagnostic logs users send to the administrator (app: Профиль → Диагностика, when the phone
-- has no Mail account). Kept raw-deflate compressed as received; the appeal row that announces
-- one carries "[log:ID]", which the Обращения page turns into a download link.
CREATE TABLE IF NOT EXISTS diag_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cell_id     TEXT NOT NULL,
    created_at  INTEGER NOT NULL,
    size        INTEGER NOT NULL,
    data        BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_appeals_cell ON appeals(cell_id, id);
"""


@dataclass
class NodeEntry:
    node_id: str
    address: str
    type: str                    = "permanent"
    access: str                  = "closed"
    cert: bytes                  = b""
    tls_fingerprint: str         = ""
    parent_node: str             = ""
    name: str                    = ""
    # Comma-joined platform tags this node can relay push notifications for on
    # behalf of a node that has no push credentials of its own — e.g. "apns", or
    # "apns,fcm" once an Android/FCM-capable node exists. Empty = no relay
    # capability. See push_relay_platforms_list() / node.py's Node.__init__.
    push_relay_platforms: str    = ""
    # True if this node holds real TURN_SECRET/coturn and will generate TURN
    # credentials for a cell belonging to a node that has none of its own — see
    # turn_relay_nodes() / node.py's Node._request_turn_relay. Unlike push relay
    # (a cheap API call), TURN relay carries actual call media through the relay
    # node's coturn, so it's a real bandwidth cost — chosen at random from all
    # capable nodes rather than always the same one, to spread the load.
    turn_relay: bool              = False
    last_seen: int                = 0
    missed_pings: int             = 0
    status: str                   = "online"
    added_at: int                 = 0

    def push_relay_platforms_list(self) -> List[str]:
        return [p for p in self.push_relay_platforms.split(",") if p]

    def to_dict(self) -> dict:
        return {
            "node_id":              self.node_id,
            "address":              self.address,
            "type":                 self.type,
            "access":               self.access,
            "tls_fingerprint":      self.tls_fingerprint,
            "parent_node":          self.parent_node,
            "name":                 self.name,
            "push_relay_platforms": self.push_relay_platforms,
            "turn_relay":           self.turn_relay,
            "last_seen":            self.last_seen,
            "status":               self.status,
        }


@dataclass
class InviteCode:
    code: str
    created_by: str
    created_at: int
    expires_at: int
    used: bool
    used_by: Optional[str]


@dataclass
class NodeInvite:
    code: str
    created_by: str
    created_at: int
    expires_at: int
    used: bool
    used_by: Optional[str]


@dataclass
class AllowedCell:
    cell_id: str
    invited_by: str
    joined_at: int
    can_invite: bool
    display_name: str = ""
    invited_by_name: str = ""


@dataclass
class JoinRequest:
    cell_id: str
    signing_pubkey: str
    enc_pubkey: str
    note: str
    display_name: str
    created_at: int
    status: str
    resolved_at: Optional[int]


@dataclass
class AdminUser:
    username: str
    created_at: int


@dataclass
class Appeal:
    id: int
    cell_id: str
    node_id: str
    display_name: str
    enc_pub: str
    direction: str   # "in" | "out"
    text: str
    created_at: int
    seen: bool


@dataclass
class CellEntry:
    cell_id: str
    signing_pubkey: bytes
    enc_pubkey: bytes
    registered_at: int
    is_home: bool = True
    display_name: str = ""


@dataclass
class PublishedCellEntry:
    cell_id: str
    name: str
    description: str
    kind: str  # "bot" | "page"
    landing_md: str
    published_at: int
    ai_providers: List[str] = field(default_factory=list)  # BYOK AI bot if non-empty


@dataclass
class AIBotEntry:
    cell_id: str
    name: str
    description: str
    system_prompt: str
    providers: List[str]
    enabled: bool
    created_at: int


@dataclass
class PresenceEntry:
    cell_id: str
    home_node_id: str
    visiting_node_id: Optional[str]
    updated_at: int


@dataclass
class BufferedMessage:
    message_id: str
    to_cell: str
    to_node: str
    payload: bytes
    created_at: int
    expires_at: int
    seq: int = 0


class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def open(self):
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
        for migration in [
            "ALTER TABLE node_table ADD COLUMN tls_fingerprint TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE node_table ADD COLUMN name TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE node_table ADD COLUMN push_relay_platforms TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE node_table ADD COLUMN turn_relay INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE cells ADD COLUMN display_name TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE join_requests ADD COLUMN display_name TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE message_buffer ADD COLUMN seq INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE published_cells ADD COLUMN ai_providers TEXT NOT NULL DEFAULT ''",
        ]:
            try:
                await self._db.execute(migration)
            except Exception:
                pass  # Column already exists
        await self._db.commit()

    async def close(self):
        if self._db:
            await self._db.close()
            self._db = None

    # --- node_table ---

    async def upsert_node(self, entry: NodeEntry):
        now = entry.added_at or int(time.time())
        await self._db.execute(
            """
            INSERT INTO node_table
                (node_id, address, type, access, cert, tls_fingerprint, parent_node,
                 name, push_relay_platforms, turn_relay, last_seen, missed_pings, status, added_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(node_id) DO UPDATE SET
                address               = excluded.address,
                last_seen             = excluded.last_seen,
                missed_pings          = excluded.missed_pings,
                status                = excluded.status,
                cert                  = excluded.cert,
                tls_fingerprint       = excluded.tls_fingerprint,
                name                  = CASE WHEN excluded.name != '' THEN excluded.name ELSE node_table.name END,
                push_relay_platforms  = excluded.push_relay_platforms,
                turn_relay            = excluded.turn_relay
            """,
            (
                entry.node_id, entry.address, entry.type, entry.access,
                entry.cert, entry.tls_fingerprint, entry.parent_node,
                entry.name, entry.push_relay_platforms, int(entry.turn_relay),
                entry.last_seen, entry.missed_pings, entry.status, now,
            ),
        )
        await self._db.commit()

    async def refresh_own_node_flags(self, node_id: str, access: str, node_type: str):
        """Directly updates type/access for OUR OWN row only — unlike upsert_node's
        ON CONFLICT clause (which deliberately never touches these two columns, since
        gossip.py reuses upsert_node for THIRD-PARTY nodes and a relayed rumor about
        someone else's access/type shouldn't be able to clobber a locally-verified
        classification, see gossip.py's own comment). Our own identity is unambiguously
        authoritative about our own access/type though, so node.py's start() calls this
        every boot to pick up a changed value (e.g. via `nevod.py set-access`)."""
        await self._db.execute(
            "UPDATE node_table SET access=?, type=? WHERE node_id=?",
            (access, node_type, node_id),
        )
        await self._db.commit()

    async def get_node(self, node_id: str) -> Optional[NodeEntry]:
        async with self._db.execute(
            "SELECT * FROM node_table WHERE node_id = ?", (node_id,)
        ) as cur:
            row = await cur.fetchone()
            return _row_to_node(row) if row else None

    async def get_all_nodes(self) -> List[NodeEntry]:
        async with self._db.execute("SELECT * FROM node_table") as cur:
            return [_row_to_node(r) for r in await cur.fetchall()]

    async def get_online_nodes(self) -> List[NodeEntry]:
        async with self._db.execute(
            "SELECT * FROM node_table WHERE status = 'online'"
        ) as cur:
            return [_row_to_node(r) for r in await cur.fetchall()]

    async def get_push_relay_nodes(self, platform: str) -> List[NodeEntry]:
        """Online nodes that advertised the ability to relay push for `platform`
        (e.g. "apns") on behalf of a node with no push credentials of its own.
        Filtered in Python rather than SQL — the platform list is tiny (a handful
        of comma-joined tags per row), not worth a fiddly LIKE pattern."""
        online = await self.get_online_nodes()
        return [n for n in online if platform in n.push_relay_platforms_list()]

    async def get_turn_relay_nodes(self) -> List[NodeEntry]:
        """Online nodes that hold real TURN_SECRET/coturn and will generate TURN
        credentials on behalf of a node with none of its own."""
        online = await self.get_online_nodes()
        return [n for n in online if n.turn_relay]

    async def update_node_ping(self, node_id: str, success: bool):
        now = int(time.time())
        if success:
            await self._db.execute(
                "UPDATE node_table SET last_seen=?, missed_pings=0, status='online' WHERE node_id=?",
                (now, node_id),
            )
        else:
            await self._db.execute(
                """
                UPDATE node_table
                SET missed_pings = missed_pings + 1,
                    status = CASE WHEN missed_pings + 1 >= ? THEN 'offline' ELSE status END
                WHERE node_id = ?
                """,
                (MISSED_PINGS_OFFLINE, node_id),
            )
        await self._db.commit()

    async def remove_node(self, node_id: str):
        await self._db.execute("DELETE FROM node_table WHERE node_id = ?", (node_id,))
        await self._db.commit()

    async def cleanup_expired_nodes(self):
        cutoff = int(time.time()) - TTL_NODE_OFFLINE_SECS
        await self._db.execute(
            "DELETE FROM node_table WHERE status='offline' AND last_seen < ?",
            (cutoff,),
        )
        await self._db.commit()

    # --- cells ---

    async def register_cell(self, cell_id: str, signing_pubkey: bytes,
                             enc_pubkey: bytes, is_home: bool = True,
                             display_name: str = "") -> bool:
        """Returns True if this cell_id had no prior row (a genuinely new member,
        not just a reconnect/re-register of someone already known here) — callers
        use this to decide whether to announce a new member to already-connected
        cells (see Node._broadcast_member_added)."""
        now = int(time.time())
        async with self._db.execute(
            "SELECT 1 FROM cells WHERE cell_id=?", (cell_id,)
        ) as cur:
            is_new = await cur.fetchone() is None
        await self._db.execute(
            """
            INSERT INTO cells (cell_id, signing_pubkey, enc_pubkey, registered_at, is_home, display_name)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(cell_id) DO UPDATE SET
                signing_pubkey = excluded.signing_pubkey,
                enc_pubkey     = excluded.enc_pubkey,
                display_name   = CASE WHEN excluded.display_name != ''
                                      THEN excluded.display_name
                                      ELSE cells.display_name END
            """,
            (cell_id, signing_pubkey, enc_pubkey, now, int(is_home), display_name.strip()[:64]),
        )
        await self._db.commit()
        return is_new

    async def set_display_name(self, cell_id: str, name: str):
        await self._db.execute(
            "UPDATE cells SET display_name=? WHERE cell_id=?", (name.strip()[:64], cell_id)
        )
        await self._db.commit()

    async def get_cell(self, cell_id: str) -> Optional[CellEntry]:
        async with self._db.execute(
            "SELECT * FROM cells WHERE cell_id = ?", (cell_id,)
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            return CellEntry(
                cell_id=row["cell_id"],
                signing_pubkey=bytes(row["signing_pubkey"]),
                enc_pubkey=bytes(row["enc_pubkey"]),
                registered_at=row["registered_at"],
                is_home=bool(row["is_home"]),
                display_name=row["display_name"] or "",
            )

    async def get_cell_by_name(self, name: str) -> Optional[str]:
        """Return cell_id of any cell with this display_name (case-insensitive), or None."""
        async with self._db.execute(
            "SELECT cell_id FROM cells WHERE LOWER(display_name) = LOWER(?) AND display_name != ''",
            (name.strip(),),
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else None

    async def list_cells(self, home_only: bool = False) -> List[CellEntry]:
        q = "SELECT * FROM cells"
        if home_only:
            q += " WHERE is_home = 1"
        async with self._db.execute(q) as cur:
            rows = await cur.fetchall()
        return [
            CellEntry(
                cell_id=r["cell_id"],
                signing_pubkey=bytes(r["signing_pubkey"]),
                enc_pubkey=bytes(r["enc_pubkey"]),
                registered_at=r["registered_at"],
                is_home=bool(r["is_home"]),
                display_name=r["display_name"] or "",
            )
            for r in rows
        ]

    # --- published cells (discovery) ---

    async def publish_cell(self, cell_id: str, name: str, description: str = "",
                           kind: str = "bot", landing_md: str = "",
                           ai_providers: Optional[List[str]] = None):
        now = int(time.time())
        await self._db.execute(
            """
            INSERT INTO published_cells
                (cell_id, name, description, kind, landing_md, published_at, ai_providers)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(cell_id) DO UPDATE SET
                name         = excluded.name,
                description  = excluded.description,
                kind         = excluded.kind,
                landing_md   = excluded.landing_md,
                ai_providers = excluded.ai_providers
            """,
            (cell_id, name.strip()[:64], description.strip()[:280], kind, landing_md, now,
             ",".join(ai_providers or [])),
        )
        await self._db.commit()

    async def unpublish_cell(self, cell_id: str):
        await self._db.execute("DELETE FROM published_cells WHERE cell_id=?", (cell_id,))
        await self._db.commit()

    # --- AI bots run inside the node (node/ai_bots.py) ---

    async def save_ai_bot(self, cell_id: str, name: str, description: str,
                          system_prompt: str, providers: List[str], enabled: bool = True):
        """Insert or update; created_at is kept on update."""
        await self._db.execute(
            """
            INSERT INTO ai_bots (cell_id, name, description, system_prompt, providers, enabled, created_at)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(cell_id) DO UPDATE SET
                name          = excluded.name,
                description   = excluded.description,
                system_prompt = excluded.system_prompt,
                providers     = excluded.providers,
                enabled       = excluded.enabled
            """,
            (cell_id, name, description, system_prompt, ",".join(providers), int(enabled),
             int(time.time())),
        )
        await self._db.commit()

    async def list_ai_bots(self) -> List[AIBotEntry]:
        async with self._db.execute("SELECT * FROM ai_bots ORDER BY created_at") as cur:
            rows = await cur.fetchall()
        return [AIBotEntry(cell_id=r["cell_id"], name=r["name"], description=r["description"],
                           system_prompt=r["system_prompt"],
                           providers=[p for p in r["providers"].split(",") if p],
                           enabled=bool(r["enabled"]), created_at=r["created_at"])
                for r in rows]

    async def get_ai_bot(self, cell_id: str) -> Optional[AIBotEntry]:
        return next((b for b in await self.list_ai_bots() if b.cell_id == cell_id), None)

    async def get_published_cells(self) -> List[PublishedCellEntry]:
        async with self._db.execute(
            "SELECT * FROM published_cells ORDER BY published_at"
        ) as cur:
            rows = await cur.fetchall()
        return [
            PublishedCellEntry(
                cell_id=r["cell_id"], name=r["name"], description=r["description"],
                kind=r["kind"], landing_md=r["landing_md"], published_at=r["published_at"],
                ai_providers=[p for p in r["ai_providers"].split(",") if p],
            )
            for r in rows
        ]

    # --- presence ---

    async def update_presence(self, cell_id: str, home_node_id: str,
                               visiting_node_id: Optional[str] = None):
        now = int(time.time())
        await self._db.execute(
            """
            INSERT INTO presence_table (cell_id, home_node_id, visiting_node_id, updated_at)
            VALUES (?,?,?,?)
            ON CONFLICT(cell_id) DO UPDATE SET
                home_node_id     = excluded.home_node_id,
                visiting_node_id = excluded.visiting_node_id,
                updated_at       = excluded.updated_at
            """,
            (cell_id, home_node_id, visiting_node_id, now),
        )
        await self._db.commit()

    async def get_presence_by_home(self, home_node_id: str) -> List[PresenceEntry]:
        """Return all presence entries whose home_node_id matches."""
        async with self._db.execute(
            "SELECT * FROM presence_table WHERE home_node_id = ?", (home_node_id,)
        ) as cur:
            rows = await cur.fetchall()
        return [
            PresenceEntry(
                cell_id=r["cell_id"],
                home_node_id=r["home_node_id"],
                visiting_node_id=r["visiting_node_id"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    async def get_presence(self, cell_id: str) -> Optional[PresenceEntry]:
        async with self._db.execute(
            "SELECT * FROM presence_table WHERE cell_id = ?", (cell_id,)
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            return PresenceEntry(
                cell_id=row["cell_id"],
                home_node_id=row["home_node_id"],
                visiting_node_id=row["visiting_node_id"],
                updated_at=row["updated_at"],
            )

    # --- message_buffer ---

    async def buffer_message(self, message_id: str, to_cell: str,
                              to_node: str, payload: bytes, seq: int = 0):
        """seq: the router's ordering number for this packet — taken when it FIRST reached
        this node (Router.route), not when it ended up here. get_buffered() orders by it,
        so a packet re-buffered later (written to a socket that turned out dead — Router.
        on_connection_lost — or bounced mid-flush) still takes its original place in line."""
        now = int(time.time())
        await self._db.execute(
            """
            INSERT OR IGNORE INTO message_buffer
                (message_id, to_cell, to_node, payload, created_at, expires_at, seq)
            VALUES (?,?,?,?,?,?,?)
            """,
            (message_id, to_cell, to_node, payload, now, now + TTL_MESSAGE_SECS, seq),
        )
        await self._db.commit()

    async def get_buffered(self, to_cell: str) -> List[BufferedMessage]:
        # ORDER BY seq: a chunked file transfer buffers dozens of packets that all land
        # within the same created_at second, and the receiver rebuilds the file by chunk
        # arrival order, header chunk (index 0) first — any reordering here drops or
        # corrupts the transfer. seq is the packet's original arrival order (see
        # buffer_message), not insertion order: chunks that were in flight when the
        # recipient's connection died get buffered AFTER later chunks may already have
        # been, yet must come out first. rowid breaks ties (rows from before seq existed
        # are all 0, and older than anything since).
        now = int(time.time())
        async with self._db.execute(
            "SELECT * FROM message_buffer WHERE to_cell=? AND expires_at > ? ORDER BY seq, rowid",
            (to_cell, now),
        ) as cur:
            rows = await cur.fetchall()
        return [
            BufferedMessage(
                message_id=r["message_id"],
                to_cell=r["to_cell"],
                to_node=r["to_node"],
                payload=bytes(r["payload"]),
                created_at=r["created_at"],
                expires_at=r["expires_at"],
                seq=r["seq"],
            )
            for r in rows
        ]

    async def delete_cell(self, cell_id: str):
        for table, col in [("cells", "cell_id"), ("presence_table", "cell_id"),
                           ("message_buffer", "to_cell"), ("allowed_cells", "cell_id"),
                           ("push_tokens", "cell_id"), ("voip_push_tokens", "cell_id"),
                           ("published_cells", "cell_id"), ("ai_bots", "cell_id"),
                           ("chat_push_prefs", "owner_cell_id"), ("chat_push_prefs", "sender_cell_id"),
                           ("chat_blocks", "owner_cell_id"), ("chat_blocks", "sender_cell_id")]:
            await self._db.execute(f"DELETE FROM {table} WHERE {col} = ?", (cell_id,))  # noqa: S608
        await self._db.commit()

    async def buffer_count(self) -> dict[str, int]:
        """Return buffered message count per cell_id (non-expired only)."""
        now = int(time.time())
        async with self._db.execute(
            "SELECT to_cell, COUNT(*) as cnt FROM message_buffer WHERE expires_at > ? GROUP BY to_cell",
            (now,),
        ) as cur:
            rows = await cur.fetchall()
        return {r["to_cell"]: r["cnt"] for r in rows}

    async def delete_buffered(self, message_id: str):
        await self._db.execute(
            "DELETE FROM message_buffer WHERE message_id = ?", (message_id,)
        )
        await self._db.commit()

    async def cleanup_expired_messages(self):
        now = int(time.time())
        await self._db.execute(
            "DELETE FROM message_buffer WHERE expires_at <= ?", (now,)
        )
        await self._db.commit()

    async def wipe_all(self):
        """Delete all data from all tables. Used for group/node destruction."""
        for table in ("message_buffer", "presence_table", "cells", "node_table"):
            await self._db.execute(f"DELETE FROM {table}")  # noqa: S608
        await self._db.commit()

    # ── Invite codes ──────────────────────────────────────────────────────────

    def _gen_code(self) -> str:
        chars = [secrets.choice(INVITE_ALPHABET) for _ in range(8)]
        return f"{''.join(chars[:4])}-{''.join(chars[4:])}"

    async def create_invite(self, created_by: str, ttl_secs: int = CELL_INVITE_TTL_SECS) -> str:
        code = self._gen_code()
        now = int(time.time())
        await self._db.execute(
            "INSERT INTO invite_codes (code, created_by, created_at, expires_at) VALUES (?,?,?,?)",
            (code, created_by, now, now + ttl_secs),
        )
        await self._db.commit()
        return code

    async def use_invite(self, code: str, cell_id: str) -> bool:
        """Validate code, mark as used, add cell to allowed_cells. Returns True on success."""
        now = int(time.time())
        async with self._db.execute(
            "SELECT created_by FROM invite_codes WHERE code=? AND used=0 AND expires_at>?",
            (code, now),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return False
        created_by = row[0]
        await self._db.execute(
            "UPDATE invite_codes SET used=1, used_by=? WHERE code=?", (cell_id, code)
        )
        await self._admit_cell(cell_id, created_by)
        await self._db.commit()
        return True

    async def _admit_cell(self, cell_id: str, invited_by: str):
        """Shared by use_invite (a spent code admits its user) and resolve_join_request
        (admin approval admits the exact requesting cell_id directly, no code involved) —
        one place that actually grants membership. Caller commits."""
        await self._db.execute(
            "INSERT OR IGNORE INTO allowed_cells (cell_id, invited_by, joined_at) VALUES (?,?,?)",
            (cell_id, invited_by, int(time.time())),
        )

    async def is_cell_allowed(self, cell_id: str) -> bool:
        async with self._db.execute(
            "SELECT 1 FROM allowed_cells WHERE cell_id=?", (cell_id,)
        ) as cur:
            return await cur.fetchone() is not None

    async def can_cell_invite(self, cell_id: str) -> bool:
        async with self._db.execute(
            "SELECT can_invite FROM allowed_cells WHERE cell_id=?", (cell_id,)
        ) as cur:
            row = await cur.fetchone()
            return bool(row and row[0])

    async def grant_invite_right(self, cell_id: str):
        await self._db.execute(
            "UPDATE allowed_cells SET can_invite=1 WHERE cell_id=?", (cell_id,)
        )
        await self._db.commit()

    async def revoke_invite_right(self, cell_id: str):
        await self._db.execute(
            "UPDATE allowed_cells SET can_invite=0 WHERE cell_id=?", (cell_id,)
        )
        await self._db.commit()

    async def list_invites(self) -> List[InviteCode]:
        # expires_at>now: still-active codes, regardless of age. used=1 AND created_at>cutoff:
        # a used code stays visible for a while so an admin can see who just joined, then drops
        # off — an expired-and-never-used code was already excluded by neither clause matching,
        # this just stops a USED code from cluttering the list forever (see admin panel, months
        # of history piling up with nothing to distinguish "recent" from "ancient").
        now = int(time.time())
        recent_cutoff = now - USED_INVITE_HISTORY_SECS
        async with self._db.execute(
            "SELECT code, created_by, created_at, expires_at, used, used_by "
            "FROM invite_codes WHERE expires_at>? OR (used=1 AND created_at>?) "
            "ORDER BY created_at DESC LIMIT 50",
            (now, recent_cutoff),
        ) as cur:
            rows = await cur.fetchall()
        return [InviteCode(r[0], r[1], r[2], r[3], bool(r[4]), r[5]) for r in rows]

    # ── Join requests (invite_mode="admin") ─────────────────────────────────────

    async def create_join_request(self, cell_id: str, signing_pubkey: str,
                                   enc_pubkey: str, note: str = "",
                                   display_name: str = "") -> bool:
        """Returns False if a request for this cell_id already exists (any status) —
        caller uses this to decide whether to re-notify admins or stay quiet on a
        resubmit/retry."""
        cur = await self._db.execute(
            "INSERT OR IGNORE INTO join_requests "
            "(cell_id, signing_pubkey, enc_pubkey, note, display_name, created_at, status) "
            "VALUES (?,?,?,?,?,?,'pending')",
            (cell_id, signing_pubkey, enc_pubkey, note, display_name, int(time.time())),
        )
        await self._db.commit()
        return cur.rowcount > 0

    async def list_join_requests(self, status: str = "pending") -> List[JoinRequest]:
        async with self._db.execute(
            "SELECT cell_id, signing_pubkey, enc_pubkey, note, display_name, created_at, "
            "status, resolved_at FROM join_requests WHERE status=? ORDER BY created_at",
            (status,),
        ) as cur:
            rows = await cur.fetchall()
        return [JoinRequest(*r) for r in rows]

    async def resolve_join_request(self, cell_id: str, status: str, invited_by: str = "admin"):
        """status: "approved" or "denied". "approved" also admits the cell directly —
        no code, the requester is already the exact cryptographic identity that asked."""
        await self._db.execute(
            "UPDATE join_requests SET status=?, resolved_at=? WHERE cell_id=?",
            (status, int(time.time()), cell_id),
        )
        if status == "approved":
            await self._admit_cell(cell_id, invited_by)
        await self._db.commit()

    # ── Admin panel logins (Безопасность page) ──────────────────────────────────

    async def set_admin_password(self, username: str, password_hash: str):
        """Upsert — covers both "add a new admin" and "change an existing admin's
        password" with one call, since from the DB's perspective they're the same
        write. password_hash is opaque here (see admin.py's _hash_password)."""
        await self._db.execute(
            "INSERT INTO admin_users (username, password_hash, created_at) VALUES (?,?,?) "
            "ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash",
            (username, password_hash, int(time.time())),
        )
        await self._db.commit()

    async def get_admin_password_hash(self, username: str) -> Optional[str]:
        async with self._db.execute(
            "SELECT password_hash FROM admin_users WHERE username=?", (username,)
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else None

    async def list_admin_users(self) -> List[AdminUser]:
        async with self._db.execute(
            "SELECT username, created_at FROM admin_users ORDER BY created_at"
        ) as cur:
            rows = await cur.fetchall()
        return [AdminUser(*r) for r in rows]

    async def delete_admin_user(self, username: str):
        await self._db.execute("DELETE FROM admin_users WHERE username=?", (username,))
        await self._db.commit()

    # ── Appeals (built-in administrator cell) ─────────────────────────────────

    async def add_appeal(self, cell_id: str, node_id: str, display_name: str,
                         enc_pub: str, direction: str, text: str):
        await self._db.execute(
            "INSERT INTO appeals (cell_id, node_id, display_name, enc_pub, direction, text, "
            "created_at, seen) VALUES (?,?,?,?,?,?,?,?)",
            (cell_id, node_id, display_name, enc_pub, direction, text, int(time.time()),
             1 if direction == "out" else 0))
        await self._db.commit()

    async def get_appeal_thread(self, cell_id: str) -> List[Appeal]:
        async with self._db.execute(
            "SELECT id, cell_id, node_id, display_name, enc_pub, direction, text, created_at, seen "
            "FROM appeals WHERE cell_id=? ORDER BY id", (cell_id,)
        ) as cur:
            rows = await cur.fetchall()
        return [Appeal(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], bool(r[8])) for r in rows]

    async def list_appeal_threads(self) -> List[dict]:
        """One row per sender: latest message, unread count, best-known name — newest first."""
        async with self._db.execute(
            "SELECT a.cell_id, "
            "  (SELECT display_name FROM appeals b WHERE b.cell_id=a.cell_id AND b.display_name!='' "
            "     ORDER BY b.id DESC LIMIT 1), "
            "  (SELECT text FROM appeals c WHERE c.cell_id=a.cell_id ORDER BY c.id DESC LIMIT 1), "
            "  (SELECT direction FROM appeals d WHERE d.cell_id=a.cell_id ORDER BY d.id DESC LIMIT 1), "
            "  MAX(a.created_at), SUM(CASE WHEN a.seen=0 THEN 1 ELSE 0 END) "
            "FROM appeals a GROUP BY a.cell_id ORDER BY MAX(a.id) DESC"
        ) as cur:
            rows = await cur.fetchall()
        return [{"cell_id": r[0], "display_name": r[1] or "", "last_text": r[2] or "",
                 "last_direction": r[3] or "", "last_at": r[4] or 0, "unread": r[5] or 0}
                for r in rows]

    async def mark_appeals_seen(self, cell_id: str):
        await self._db.execute("UPDATE appeals SET seen=1 WHERE cell_id=? AND seen=0", (cell_id,))
        await self._db.commit()

    async def add_diag_log(self, cell_id: str, packed: bytes, size: int) -> int:
        cur = await self._db.execute(
            "INSERT INTO diag_logs (cell_id, created_at, size, data) VALUES (?,?,?,?)",
            (cell_id, int(time.time()), size, packed))
        await self._db.commit()
        return cur.lastrowid

    async def count_diag_logs_since(self, cell_id: str, since: int) -> int:
        async with self._db.execute(
            "SELECT COUNT(*) FROM diag_logs WHERE cell_id=? AND created_at>=?", (cell_id, since)
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else 0

    async def get_diag_log(self, log_id: int) -> Optional[tuple]:
        """(cell_id, created_at, packed bytes) or None."""
        async with self._db.execute(
            "SELECT cell_id, created_at, data FROM diag_logs WHERE id=?", (log_id,)
        ) as cur:
            row = await cur.fetchone()
        return (row[0], row[1], bytes(row[2])) if row else None

    async def unread_appeals_count(self) -> int:
        async with self._db.execute("SELECT COUNT(*) FROM appeals WHERE seen=0") as cur:
            row = await cur.fetchone()
        return row[0] if row else 0

    # ── Node invites ──────────────────────────────────────────────────────────

    async def create_node_invite(self, created_by: str) -> str:
        code = self._gen_code()
        now = int(time.time())
        await self._db.execute(
            "INSERT INTO node_invites (code, created_by, created_at, expires_at) VALUES (?,?,?,?)",
            (code, created_by, now, now + INVITE_TTL_SECS),
        )
        await self._db.commit()
        return code

    async def use_node_invite(self, code: str, node_id: str) -> bool:
        """Validate code, mark as used. Returns True on success. Admission itself is
        recorded by the caller via upsert_node — there's no allowed_cells-equivalent
        table for nodes."""
        now = int(time.time())
        async with self._db.execute(
            "SELECT 1 FROM node_invites WHERE code=? AND used=0 AND expires_at>?",
            (code, now),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return False
        await self._db.execute(
            "UPDATE node_invites SET used=1, used_by=? WHERE code=?", (node_id, code)
        )
        await self._db.commit()
        return True

    async def list_node_invites(self) -> List[NodeInvite]:
        # Same reasoning as list_invites() above — a used code stays visible for a while, then
        # drops off instead of accumulating forever.
        now = int(time.time())
        recent_cutoff = now - USED_INVITE_HISTORY_SECS
        async with self._db.execute(
            "SELECT code, created_by, created_at, expires_at, used, used_by "
            "FROM node_invites WHERE expires_at>? OR (used=1 AND created_at>?) "
            "ORDER BY created_at DESC LIMIT 50",
            (now, recent_cutoff),
        ) as cur:
            rows = await cur.fetchall()
        return [NodeInvite(r[0], r[1], r[2], r[3], bool(r[4]), r[5]) for r in rows]

    async def list_allowed_cells(self) -> List[AllowedCell]:
        async with self._db.execute(
            """SELECT a.cell_id, a.invited_by, a.joined_at, a.can_invite,
                      COALESCE(c.display_name,   '') AS display_name,
                      COALESCE(inv.display_name, '') AS invited_by_name
               FROM allowed_cells a
               LEFT JOIN cells c   ON c.cell_id   = a.cell_id
               LEFT JOIN cells inv ON inv.cell_id  = a.invited_by
               ORDER BY a.joined_at"""
        ) as cur:
            rows = await cur.fetchall()
        return [AllowedCell(r[0], r[1], r[2], bool(r[3]), r[4], r[5]) for r in rows]

    async def wipe_registrations(self):
        """Test reset: clear cells/presence/buffer but keep allowed_cells (no re-invite needed)."""
        for table in ("message_buffer", "presence_table", "cells"):
            await self._db.execute(f"DELETE FROM {table}")  # noqa: S608
        await self._db.commit()

    async def full_reset(self):
        """Full reset: wipe everything including allowed_cells and invite_codes."""
        for table in ("message_buffer", "presence_table", "cells", "invite_codes",
                      "allowed_cells", "contact_cards", "join_requests"):
            await self._db.execute(f"DELETE FROM {table}")  # noqa: S608
        await self._db.commit()

    # ── Contact cards (short shareable codes) ────────────────────────────────────

    async def create_contact_card(self, cell_id: str, enc_pub_hex: str) -> str:
        code = self._gen_code()
        now = int(time.time())
        await self._db.execute(
            "INSERT OR REPLACE INTO contact_cards (code, cell_id, enc_pub, created_at, expires_at) "
            "VALUES (?,?,?,?,?)",
            (code, cell_id, enc_pub_hex, now, now + CARD_TTL_SECS),
        )
        await self._db.commit()
        return code

    async def lookup_contact_card(self, code: str) -> Optional[dict]:
        now = int(time.time())
        async with self._db.execute(
            "SELECT cell_id, enc_pub, expires_at FROM contact_cards WHERE code=? AND expires_at>?",
            (code, now),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return None
        return {"cell_id": row[0], "enc_pub": row[1], "expires_at": row[2]}


    # ── Push tokens ──────────────────────────────────────────────────────────────

    async def save_push_token(self, cell_id: str, token: str, platform: str = "apns"):
        await self._db.execute(
            "INSERT OR REPLACE INTO push_tokens (cell_id, token, platform, updated_at) VALUES (?,?,?,?)",
            (cell_id, token, platform, int(time.time())),
        )
        await self._db.commit()

    async def get_push_token(self, cell_id: str) -> Optional[tuple[str, str]]:
        """Returns (token, platform) or None."""
        async with self._db.execute(
            "SELECT token, platform FROM push_tokens WHERE cell_id=?", (cell_id,)
        ) as cur:
            row = await cur.fetchone()
        return (row[0], row[1]) if row else None

    async def delete_push_token(self, cell_id: str):
        await self._db.execute("DELETE FROM push_tokens WHERE cell_id=?", (cell_id,))
        await self._db.commit()

    # ── VoIP push tokens (separate table — a cell needs both a regular alert token
    #    for chat messages and a VoIP token for incoming calls, at the same time) ──

    async def save_voip_push_token(self, cell_id: str, token: str):
        await self._db.execute(
            "INSERT OR REPLACE INTO voip_push_tokens (cell_id, token, updated_at) VALUES (?,?,?)",
            (cell_id, token, int(time.time())),
        )
        await self._db.commit()

    async def get_voip_push_token(self, cell_id: str) -> Optional[str]:
        async with self._db.execute(
            "SELECT token FROM voip_push_tokens WHERE cell_id=?", (cell_id,)
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else None

    async def delete_voip_push_token(self, cell_id: str):
        await self._db.execute("DELETE FROM voip_push_tokens WHERE cell_id=?", (cell_id,))
        await self._db.commit()

    # ── Per-chat push sound preference ──────────────────────────────────────────

    async def get_sound_enabled(self, owner_cell_id: str, sender_cell_id: str) -> bool:
        """True (sound on) unless the owner explicitly turned sound off for this sender."""
        async with self._db.execute(
            "SELECT 1 FROM chat_push_prefs WHERE owner_cell_id=? AND sender_cell_id=?",
            (owner_cell_id, sender_cell_id),
        ) as cur:
            row = await cur.fetchone()
        return row is None

    async def set_sound_enabled(self, owner_cell_id: str, sender_cell_id: str, enabled: bool):
        if enabled:
            await self._db.execute(
                "DELETE FROM chat_push_prefs WHERE owner_cell_id=? AND sender_cell_id=?",
                (owner_cell_id, sender_cell_id),
            )
        else:
            await self._db.execute(
                "INSERT OR REPLACE INTO chat_push_prefs (owner_cell_id, sender_cell_id, updated_at) "
                "VALUES (?,?,?)",
                (owner_cell_id, sender_cell_id, int(time.time())),
            )
        await self._db.commit()

    # ── Per-chat block ──────────────────────────────────────────────────────────

    async def is_blocked(self, owner_cell_id: str, sender_cell_id: str) -> bool:
        async with self._db.execute(
            "SELECT 1 FROM chat_blocks WHERE owner_cell_id=? AND sender_cell_id=?",
            (owner_cell_id, sender_cell_id),
        ) as cur:
            row = await cur.fetchone()
        return row is not None

    async def set_blocked(self, owner_cell_id: str, sender_cell_id: str, blocked: bool):
        if blocked:
            await self._db.execute(
                "INSERT OR REPLACE INTO chat_blocks (owner_cell_id, sender_cell_id, updated_at) "
                "VALUES (?,?,?)",
                (owner_cell_id, sender_cell_id, int(time.time())),
            )
        else:
            await self._db.execute(
                "DELETE FROM chat_blocks WHERE owner_cell_id=? AND sender_cell_id=?",
                (owner_cell_id, sender_cell_id),
            )
        await self._db.commit()


def _row_to_node(row) -> NodeEntry:
    return NodeEntry(
        node_id=row["node_id"],
        address=row["address"],
        type=row["type"],
        access=row["access"],
        cert=bytes(row["cert"]) if row["cert"] else b"",
        tls_fingerprint=row["tls_fingerprint"] or "",
        parent_node=row["parent_node"] or "",
        name=row["name"] or "",
        push_relay_platforms=row["push_relay_platforms"] or "",
        turn_relay=bool(row["turn_relay"]),
        last_seen=row["last_seen"],
        missed_pings=row["missed_pings"],
        status=row["status"],
        added_at=row["added_at"],
    )
