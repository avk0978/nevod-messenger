"""
Per-user autostart registration for the headless Nevod node (M2).

Windows: HKCU Run key — no admin rights needed, standard per-user autostart.
Built and verified on Windows only so far. macOS (LaunchAgent) and Linux
(systemd --user) implementations follow the design from the M1/M2 planning
doc but have NOT been run on real macOS/Linux hardware yet.
"""

import subprocess
import sys
from pathlib import Path

APP_NAME = "NevodNode"


# ── Windows ──────────────────────────────────────────────────────────────

def _windows_enable(exe_path: Path):
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, winreg.KEY_SET_VALUE)
    with key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')


def _windows_disable():
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        with key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass


def _windows_is_enabled() -> bool:
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_READ)
        with key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False


# ── macOS (untested) ─────────────────────────────────────────────────────

def _macos_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / "com.nevod.node.plist"


def _macos_enable(exe_path: Path):
    plist = _macos_plist_path()
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.nevod.node</string>
  <key>ProgramArguments</key><array><string>{exe_path}</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict>
</plist>
""")
    subprocess.run(["launchctl", "load", str(plist)], check=False)


def _macos_disable():
    plist = _macos_plist_path()
    if plist.exists():
        subprocess.run(["launchctl", "unload", str(plist)], check=False)
        plist.unlink()


def _macos_is_enabled() -> bool:
    return _macos_plist_path().exists()


# ── Linux (untested) ─────────────────────────────────────────────────────

def _linux_unit_path() -> Path:
    return Path.home() / ".config" / "systemd" / "user" / "nevod-node.service"


def _linux_enable(exe_path: Path):
    unit = _linux_unit_path()
    unit.parent.mkdir(parents=True, exist_ok=True)
    unit.write_text(f"""[Unit]
Description=Nevod node

[Service]
ExecStart={exe_path}
Restart=on-failure

[Install]
WantedBy=default.target
""")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "--user", "enable", "--now", "nevod-node.service"], check=False)


def _linux_disable():
    subprocess.run(["systemctl", "--user", "disable", "--now", "nevod-node.service"], check=False)
    unit = _linux_unit_path()
    if unit.exists():
        unit.unlink()


def _linux_is_enabled() -> bool:
    return _linux_unit_path().exists()


# ── public API ───────────────────────────────────────────────────────────

def enable(exe_path: Path):
    if sys.platform == "win32":
        _windows_enable(exe_path)
    elif sys.platform == "darwin":
        _macos_enable(exe_path)
    else:
        _linux_enable(exe_path)


def disable():
    if sys.platform == "win32":
        _windows_disable()
    elif sys.platform == "darwin":
        _macos_disable()
    else:
        _linux_disable()


def is_enabled() -> bool:
    if sys.platform == "win32":
        return _windows_is_enabled()
    elif sys.platform == "darwin":
        return _macos_is_enabled()
    else:
        return _linux_is_enabled()
