"""Windows-only setup helpers for Presence Coach.

Creates the branded icon and Desktop shortcut without invoking PowerShell. The checked-in
asset is a compact JPEG source; Pillow generates a standard multi-size Windows ICO.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import sys
from io import BytesIO
from pathlib import Path


def materialize_icon(root: Path) -> Path:
    """Decode the compact source image and generate a proper multi-resolution ICO."""
    source = root / "assets" / "presence_source.jpg.b64"
    target = root / "assets" / "presence.ico"
    if not source.exists():
        raise FileNotFoundError(f"Presence icon source is missing: {source}")

    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required to generate the Presence icon. Run Setup.cmd again.") from exc

    encoded = "".join(source.read_text(encoding="ascii").split())
    raw = base64.b64decode(encoded, validate=True)
    image = Image.open(BytesIO(raw)).convert("RGBA")

    # Build all Windows shell sizes from one clean 256px source.
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="ICO", sizes=sizes)

    # Ask Pillow to reopen the file so malformed output fails immediately.
    with Image.open(target) as check:
        if check.format != "ICO":
            raise RuntimeError("Presence icon generation did not produce a valid Windows ICO.")

    return target.resolve()


def _refresh_windows_icons() -> None:
    """Ask Explorer to refresh shell icons after replacing the shortcut/icon."""
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

    if not icon_path.exists():
        raise FileNotFoundError(f"Presence icon was not created: {icon_path}")

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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--icon-only",
        action="store_true",
        help="Generate assets/presence.ico without creating a Desktop shortcut.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    try:
        icon = materialize_icon(root)
        print(f"Presence icon created: {icon}")
        if not args.icon_only:
            shortcut = create_desktop_shortcut(root, icon)
            print(f"Desktop shortcut created: {shortcut}")
    except Exception as exc:
        print(f"Windows setup failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
