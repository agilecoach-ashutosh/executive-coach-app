"""Windows-only setup helpers for Presence Coach.

Creates the branded icon and Desktop shortcut without invoking PowerShell. Keeping
these actions in ordinary Python avoids antivirus heuristics commonly triggered by
CMD -> PowerShell -> Base64 decode patterns.
"""
from __future__ import annotations

import base64
import ctypes
import struct
import sys
from pathlib import Path


def _validate_ico(path: Path) -> None:
    """Fail early if the decoded asset is not a real Windows ICO container."""
    data = path.read_bytes()
    if len(data) < 6:
        raise RuntimeError("Presence icon file is incomplete.")

    reserved, icon_type, image_count = struct.unpack("<HHH", data[:6])
    if reserved != 0 or icon_type != 1 or image_count < 1:
        raise RuntimeError("Presence icon file is not a valid Windows ICO.")

    directory_size = 6 + image_count * 16
    if len(data) < directory_size:
        raise RuntimeError("Presence icon directory is incomplete.")

    # Check every directory entry points to actual bytes inside the file.
    for index in range(image_count):
        entry = data[6 + index * 16 : 6 + (index + 1) * 16]
        image_size = struct.unpack("<I", entry[8:12])[0]
        image_offset = struct.unpack("<I", entry[12:16])[0]
        if image_size <= 0 or image_offset < directory_size or image_offset + image_size > len(data):
            raise RuntimeError("Presence icon contains an invalid image entry.")


def materialize_icon(root: Path) -> Path:
    source = root / "assets" / "presence.ico.b64"
    target = root / "assets" / "presence.ico"
    if not source.exists():
        raise FileNotFoundError(f"Presence icon asset is missing: {source}")

    encoded = "".join(source.read_text(encoding="ascii").split())
    target.write_bytes(base64.b64decode(encoded, validate=True))
    _validate_ico(target)
    return target.resolve()


def _refresh_windows_icons() -> None:
    """Ask Explorer to refresh shell icons after replacing the shortcut/icon."""
    try:
        # SHCNE_ASSOCCHANGED + SHCNF_IDLIST is the standard broad shell refresh.
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
    except Exception:
        # The shortcut is still valid if Explorer declines/defers the refresh.
        pass


def create_desktop_shortcut(root: Path, icon_path: Path) -> Path:
    try:
        import win32com.client
    except ImportError as exc:
        raise RuntimeError(
            "Windows shortcut support is missing. Run Setup.cmd again so pywin32 is installed."
        ) from exc

    if not icon_path.exists():
        raise FileNotFoundError(f"Presence icon was not created: {icon_path}")
    _validate_ico(icon_path)

    shell = win32com.client.Dispatch("WScript.Shell")
    desktop = Path(shell.SpecialFolders("Desktop"))
    shortcut_path = desktop / "Presence Coach.lnk"

    # Delete the old shortcut first so Explorer does not keep metadata from a
    # previously broken/generic-icon .lnk.
    if shortcut_path.exists():
        shortcut_path.unlink()

    shortcut = shell.CreateShortcut(str(shortcut_path))
    shortcut.TargetPath = str((root / ".venv" / "Scripts" / "pythonw.exe").resolve())
    shortcut.Arguments = "session_export_mode.py"
    shortcut.WorkingDirectory = str(root.resolve())

    # Microsoft documents an .ico path directly for WshShortcut.IconLocation.
    # Avoid appending an icon-resource index for a standalone .ico file.
    shortcut.IconLocation = str(icon_path)
    shortcut.Description = "Presence Coach"
    shortcut.Save()

    _refresh_windows_icons()
    return shortcut_path


def main() -> int:
    root = Path(__file__).resolve().parent
    try:
        icon = materialize_icon(root)
        shortcut = create_desktop_shortcut(root, icon)
    except Exception as exc:
        print(f"Windows setup failed: {exc}", file=sys.stderr)
        return 1

    print(f"Presence icon created and validated: {icon}")
    print(f"Desktop shortcut created: {shortcut}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
