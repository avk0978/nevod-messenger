"""
Nevod headless node process (M2).

Minimal daemon entrypoint: loads the identity/db already created by the
installer wizard (installer/wizard.py) and keeps the node running with no
GUI — this is what actually gets registered for autostart at login (see
installer/autostart.py). Equivalent to `nevod.py start`, but with fixed
paths (the app-data dir shared with the wizard) and a locally-generated
admin password so the wizard's status screen can poll it without the user
ever typing one.

Run from source:  python installer/node_headless.py
Frozen build:     see installer/data/nevod-node.spec (PyInstaller)
"""

import asyncio
import logging
import logging.handlers
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import identity_path, db_path, ensure_admin_meta, log_path, write_pid  # noqa: E402

# Without this, the root logger defaults to WARNING — every log.info() across
# the whole node (routing decisions, push-relay activity, etc.) is silently
# dropped before it even reaches admin.py's log ring buffer. nevod.py's CLI
# entry point sets this up; this headless entry point (launched directly by
# the installer/wizard, not through nevod.py) needs its own copy.
#
# A plain StreamHandler alone (the old behavior) went nowhere on a frozen
# Windows build — node-headless.spec builds with console=False, so stdout/
# stderr aren't attached to anything, and the admin panel's ring buffer only
# holds the last 300 lines in memory (gone on restart). Confirmed live
# 2026-08-26: diagnosing a dropped reaction needed history the ring buffer
# still had, but a restart would have lost it — this is the only durable
# copy. Same 3MB rotation size as the iOS client's NevLogger, for the same
# reason (bounded growth, keep recent history).
_file_handler = logging.handlers.RotatingFileHandler(
    log_path(), maxBytes=3_000_000, backupCount=2, encoding="utf-8",
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[_file_handler, logging.StreamHandler()],
)


async def main():
    from node.node import Node
    from node.admin import AdminServer

    # Recorded so the wizard's uninstall flow can find and stop this exact
    # process later — more reliable than trusting the PID subprocess.Popen()
    # reports at spawn time, which can be a PyInstaller onefile bootstrap
    # wrapper rather than the actual long-running process on some setups.
    write_pid(os.getpid())

    # identity.address is the PUBLIC address other peers dial — the local
    # socket almost always can't bind that exact address behind NAT, so bind
    # broadly and let the public address be purely advertised, not bound to.
    os.environ["NEVOD_BIND"] = "0.0.0.0"

    meta = ensure_admin_meta()
    node = await Node.create(str(identity_path()), str(db_path()))
    await node.start()

    admin = AdminServer(node, meta["password"], meta.get("username") or None,
                         identity_path=str(identity_path()))
    await admin.start(meta["port"])

    await asyncio.Event().wait()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
