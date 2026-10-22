#!/usr/bin/env python3
"""
update_checker.py — periodic, signature-verified auto-update for a Nevod node.

Run via cron (see setup_node.sh): checks for a new, Ed25519-signed release,
verifies it against MAINTAINER_PUBLIC_KEY_HEX below, and if valid AND newer
than what's currently deployed, checks out that exact commit and rebuilds.

Trust model: the ONLY thing that matters is the Ed25519 signature over
RELEASE.json's raw bytes (produced by `nevod.py release sign`, see nevod.py).
WHERE those bytes come from — GitHub, a peer node's admin endpoint — is
irrelevant to security: an untrusted/malicious source can only ever supply
garbage that fails verification, it cannot forge a valid signature. This is
why _fetch_release() below is allowed to fall back to asking peer nodes
(reachable via this node's own node_table, no admin auth needed since it's
this node's own local sqlite db) if GitHub itself is unreachable.

Runs entirely synchronously and standalone (not asyncio, not aiosqlite) —
this is a one-shot cron job, not a long-lived service; there's nothing to
gain from concurrency here.
"""
import json
import logging
import sqlite3
import subprocess
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from node.crypto import verify  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
log = logging.getLogger("update_checker")

# Public half of the maintainer's Ed25519 signing key (see `nevod.py release
# keygen` / `nevod.py release sign`). This is the ONE thing this script
# trusts — never derived from anything fetched over the network. The private
# half must never exist on any node server, only on the maintainer's own
# offline machine.
MAINTAINER_PUBLIC_KEY_HEX = "785dfb3a8e38a28bba78ff18d9d2ddb5c512bd99d9819c03ea4ba1224cae8ee7"

REPO_DIR = Path(__file__).resolve().parent
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/avk0978/Node-update/master"
COMPOSE_FILE = "docker-compose.nevod.yml"
ADMIN_PORT = 8766


def _run(cmd: list) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True)


def _known_peer_hosts() -> list:
    """Reads this node's own node_table directly from its sqlite db — used only
    as a fallback transport if GitHub is unreachable. No admin auth needed
    (this is the node's own local file, not a network call), and the node
    process doesn't even need to be running for this to work."""
    db_path = REPO_DIR / "data" / "node.db"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(db_path)
        try:
            rows = conn.execute("SELECT address FROM node_table").fetchall()
        finally:
            conn.close()
        return [r[0].split(":")[0] for r in rows if r[0]]
    except Exception as e:
        log.warning("could not read peer list: %s", e)
        return []


def _fetch_github():
    try:
        with httpx.Client(timeout=10) as client:
            manifest = client.get(f"{GITHUB_RAW_BASE}/RELEASE.json")
            sig = client.get(f"{GITHUB_RAW_BASE}/RELEASE.sig")
        if manifest.status_code == 200 and sig.status_code == 200:
            return manifest.content, sig.content
    except Exception as e:
        log.warning("GitHub fetch failed: %s", e)
    return None


def _fetch_peer(host: str):
    try:
        with httpx.Client(timeout=5) as client:
            manifest = client.get(f"http://{host}:{ADMIN_PORT}/nevod-update/release.json")
            sig = client.get(f"http://{host}:{ADMIN_PORT}/nevod-update/release.sig")
        if manifest.status_code == 200 and sig.status_code == 200:
            return manifest.content, sig.content
    except Exception:
        pass
    return None


def _fetch_release():
    """Returns (manifest_bytes, sig_bytes, source_description) or None."""
    result = _fetch_github()
    if result:
        return result[0], result[1], "github"
    log.info("GitHub unreachable, trying known peers…")
    for host in _known_peer_hosts():
        result = _fetch_peer(host)
        if result:
            return result[0], result[1], f"peer:{host}"
    return None


def _current_version() -> int:
    local = REPO_DIR / "RELEASE.json"
    if not local.exists():
        return 0
    try:
        return int(json.loads(local.read_text())["version"])
    except Exception:
        return 0


def _apply_update(manifest_bytes: bytes, sig_bytes: bytes, commit: str, version: int) -> bool:
    log.info("applying update: commit=%s version=%d", commit[:8], version)

    remotes = _run(["git", "remote"]).stdout.split()
    fetched_via = None
    for remote in ("origin", "mirror"):
        if remote not in remotes:
            continue
        if _run(["git", "fetch", remote]).returncode == 0:
            fetched_via = remote
            break
    if fetched_via is None:
        log.error("git fetch failed on all configured remotes (%s)", remotes)
        return False

    r = _run(["git", "checkout", commit])
    if r.returncode != 0:
        log.error("git checkout %s failed (via %s): %s", commit[:8], fetched_via, r.stderr)
        return False

    # Persist the verified manifest/signature — becomes "current version" for
    # next run's comparison, and what this node hands out to peers as a
    # fallback transport (see admin.py's /nevod-update routes). Written AFTER
    # checkout succeeds so a failed checkout doesn't claim a version it never
    # actually reached.
    (REPO_DIR / "RELEASE.json").write_bytes(manifest_bytes)
    (REPO_DIR / "RELEASE.sig").write_bytes(sig_bytes)

    r = _run(["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", "--build"])
    if r.returncode != 0:
        log.error("docker compose rebuild failed: %s", r.stderr)
        return False

    log.info("update applied successfully — now running commit %s (version %d)", commit[:8], version)
    return True


def main():
    if MAINTAINER_PUBLIC_KEY_HEX == "REPLACE_WITH_MAINTAINER_PUBLIC_KEY_HEX":
        log.error("MAINTAINER_PUBLIC_KEY_HEX not configured — refusing to run")
        sys.exit(1)

    fetched = _fetch_release()
    if fetched is None:
        log.warning("no reachable source for RELEASE.json/.sig (GitHub + all known peers failed)")
        return
    manifest_bytes, sig_bytes, source = fetched

    try:
        signature = bytes.fromhex(sig_bytes.decode().strip())
    except Exception:
        log.warning("malformed signature from %s — ignoring", source)
        return

    pubkey = bytes.fromhex(MAINTAINER_PUBLIC_KEY_HEX)
    if not verify(manifest_bytes, signature, pubkey):
        log.warning("signature verification FAILED (source=%s) — ignoring, nothing applied", source)
        return

    try:
        manifest = json.loads(manifest_bytes)
        commit = str(manifest["commit"])
        new_version = int(manifest["version"])
    except Exception as e:
        log.warning("signed manifest is malformed (%s) — ignoring", e)
        return

    current = _current_version()
    if new_version <= current:
        log.info("already up to date (current=%d, seen=%d from %s)", current, new_version, source)
        return

    log.info("verified new release: version=%d (current=%d), source=%s", new_version, current, source)
    _apply_update(manifest_bytes, sig_bytes, commit, new_version)


if __name__ == "__main__":
    main()
