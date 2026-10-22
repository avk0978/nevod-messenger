"""
Shared helpers between installer/wizard.py (GUI) and installer/node_headless.py
(the background node process the wizard spawns and registers for autostart).

Kept in one module rather than duplicated: PyInstaller builds nevod-gui.exe
and nevod-node.exe as two independent onefile bundles, each with its own
Analysis pass that discovers and bundles this file on its own — there's no
runtime coupling between the two built executables, so sharing source here
costs nothing at build time.
"""

import json
import os
import secrets
import sys
from pathlib import Path

IDENTITY_FILENAME = "node.json"
DB_FILENAME = "node.db"
ADMIN_META_FILENAME = "admin.json"
PID_FILENAME = "node.pid"
LOG_FILENAME = "node.log"
DEFAULT_ADMIN_PORT = 8766


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".nevod")
    d = Path(base) / "Nevod"
    d.mkdir(parents=True, exist_ok=True)
    return d


def identity_path() -> Path:
    return app_data_dir() / IDENTITY_FILENAME


def db_path() -> Path:
    return app_data_dir() / DB_FILENAME


def admin_meta_path() -> Path:
    return app_data_dir() / ADMIN_META_FILENAME


def pid_path() -> Path:
    return app_data_dir() / PID_FILENAME


def log_path() -> Path:
    return app_data_dir() / LOG_FILENAME


def write_pid(pid: int):
    pid_path().write_text(str(pid))


def read_pid() -> int | None:
    p = pid_path()
    if not p.exists():
        return None
    try:
        return int(p.read_text().strip())
    except Exception:
        return None


def read_admin_meta() -> dict | None:
    p = admin_meta_path()
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_admin_meta(password: str, port: int = DEFAULT_ADMIN_PORT, username: str = "") -> dict:
    meta = {"password": password, "port": port, "username": username}
    admin_meta_path().write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return meta


def ensure_admin_meta() -> dict:
    """Idempotent: reuses the existing admin credentials/port if this install
    already has one. Installs from before the wizard started asking for a
    name/username (M1, or the first cut of M2) just get a random password
    and no username generated here — AdminServer treats a missing/empty
    username as "don't check it", so those installs keep working exactly as
    before instead of getting silently locked out."""
    meta = read_admin_meta()
    if meta:
        return meta
    return write_admin_meta(secrets.token_urlsafe(24))


def node_exe_command() -> list[str]:
    """Command to launch the headless node process: the sibling nevod-node.exe
    next to this executable when frozen, or `python node_headless.py` when
    running from source (dev/testing)."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        return [str(exe_dir / "nevod-node.exe")]
    here = Path(__file__).resolve().parent
    return [sys.executable, str(here / "node_headless.py")]


def frozen_node_exe_path() -> Path | None:
    """The path to register for autostart — only meaningful once actually
    built and installed; None in dev mode (nothing sensible to autostart)."""
    if not getattr(sys, "frozen", False):
        return None
    return Path(sys.executable).resolve().parent / "nevod-node.exe"
