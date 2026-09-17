"""Windows-only setup helpers for Presence Coach.

Creates the branded icon and Desktop shortcut without invoking PowerShell. Keeping
these actions in ordinary Python avoids antivirus heuristics commonly triggered by
CMD -> PowerShell -> Base64 decode patterns.
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path


def materialize_icon(root: Path) -> Path:
    source = root / "assets" / "presence.ico.b64"
    target = root / "assets" / "presence.ico"
    if not source.exists():
        raise FileNotFoundError(f"Presence icon asset is missing: {source}")

    encoded = "".join(source.read_text(encoding="ascii").split())
    target.write_bytes(base64.b64decode(encoded, validate=True))
    return target


def create_desktop_shortcut(root: Path, icon_path: Path) -> Path:
    try:
        import win32com.client
    except ImportError as exc:
        raise RuntimeError(
            "Windows shortcut support is missing. Run Setup.cmd again so pywin32 is installed."
        ) from exc

    shell = win32com.client.Dispatch("WScript.Shell")
    desktop = Path(shell.SpecialFolders("Desktop"))
    shortcut_path = desktop / "Presence Coach.lnk"
    shortcut = shell.CreateShortcut(str(shortcut_path))
    shortcut.TargetPath = str(root / ".venv" / "Scripts" / "pythonw.exe")
    shortcut.Arguments = "session_export_mode.py"
    shortcut.WorkingDirectory = str(root)
    shortcut.IconLocation = f"{icon_path},0"
    shortcut.Description = "Presence Coach"
    shortcut.Save()
    return shortcut_path


def main() -> int:
    root = Path(__file__).resolve().parent
    try:
        icon = materialize_icon(root)
        shortcut = create_desktop_shortcut(root, icon)
    except Exception as exc:
        print(f"Windows setup failed: {exc}", file=sys.stderr)
        return 1

    print(f"Presence icon created: {icon}")
    print(f"Desktop shortcut created: {shortcut}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
