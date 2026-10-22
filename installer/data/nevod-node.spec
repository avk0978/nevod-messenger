# PyInstaller spec for the headless Nevod node process (M2, Windows).
# Build from the repo root:
#   pyinstaller installer/data/nevod-node.spec
#
# Produces a single-file, no-console executable: dist/nevod-node.exe
# This is what installer/autostart.py registers to launch at login, and
# what installer/wizard.py spawns as a detached background process.

from pathlib import Path

block_cipher = None

repo_root = Path(SPECPATH).resolve().parent.parent

a = Analysis(
    [str(repo_root / "installer" / "node_headless.py")],
    pathex=[str(repo_root), str(repo_root / "installer")],
    binaries=[],
    datas=[],
    hiddenimports=[
        "node.node", "node.identity", "node.storage", "node.transport",
        "node.gossip", "node.router", "node.protocol", "node.auth", "node.crypto",
        "node.admin", "node.push",
        "cryptography.hazmat.backends.openssl",
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
    name="nevod-node",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
