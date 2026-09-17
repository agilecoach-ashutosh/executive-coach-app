"""Windows-only setup helper for Presence Coach.

Uses the checked-in Presence-Coach.ico directly and creates the Desktop shortcut
without PowerShell, Base64 decoding, or image conversion during installation.
"""
from __future__ import annotations

import ctypes
import sys
from pathlib import Path


def get_icon(root: Path) -> Path:
    """Return the checked-in Windows icon and perform a lightweight ICO sanity check."""
    icon = root / "Presence-Coach.ico"
    if not icon.exists():
        raise FileNotFoundError(f"Presence icon is missing: {icon}")

    data = icon.read_bytes()
    if len(data) < 6 or data[:4] != b"\x00\x00\x01\x00":
        raise RuntimeError("Presence-Coach.ico is not a valid Windows icon file.")
    return icon.resolve()


def _refresh_windows_icons() -> None:
    """Ask Explorer to refresh shell icons after replacing the shortcut."""
    try:
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
    except Exception:
        pass


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

    if shortcut_path.exists():
        shortcut_path.unlink()

    shortcut = shell.CreateShortcut(str(shortcut_path))
    shortcut.TargetPath = str((root / ".venv" / "Scripts" / "pythonw.exe").resolve())
    shortcut.Arguments = "session_export_mode.py"
    shortcut.WorkingDirectory = str(root.resolve())
    shortcut.IconLocation = f"{icon_path},0"
    shortcut.Description = "Presence Coach"
    shortcut.Save()

    _refresh_windows_icons()
    return shortcut_path


def main() -> int:
    root = Path(__file__).resolve().parent
    try:
        icon = get_icon(root)
        shortcut = create_desktop_shortcut(root, icon)
    except Exception as exc:
        print(f"Windows setup failed: {exc}", file=sys.stderr)
        return 1

    print(f"Using Presence icon: {icon}")
    print(f"Desktop shortcut created: {shortcut}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
