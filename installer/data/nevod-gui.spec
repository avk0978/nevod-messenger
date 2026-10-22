# PyInstaller spec for the Nevod node installer wizard (M1+M2, Windows).
# Build from the repo root:
#   pyinstaller installer/data/nevod-gui.spec
#
# Produces a single-file, windowed (no console) executable: dist/nevod-gui.exe
# Expects a sibling dist/nevod-node.exe (built from nevod-node.spec) — the
# wizard spawns it after a successful join and registers it for autostart.

import sys
from pathlib import Path

block_cipher = None

repo_root = Path(SPECPATH).resolve().parent.parent

a = Analysis(
    [str(repo_root / "installer" / "wizard.py")],
    pathex=[str(repo_root), str(repo_root / "installer")],
    binaries=[],
    datas=[],
    # cryptography/websockets sometimes need their submodules spelled out for
    # PyInstaller's static import scan to find everything.
    hiddenimports=[
        "node.node", "node.identity", "node.storage", "node.transport",
        "node.gossip", "node.router", "node.protocol", "node.auth", "node.crypto",
        "cryptography.hazmat.backends.openssl",
        "winreg",
        "netcheck", "miniupnpc",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="nevod-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
