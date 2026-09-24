"""Windows-only setup helper for Presence Coach.

Uses the checked-in Presence-Coach.ico directly and creates the Desktop shortcut
with the Windows ShellLink API. This avoids the WScript.Shell automation layer,
which can reject shortcut properties on some Windows configurations.
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
    """Create the Presence Coach desktop shortcut using the native ShellLink API."""
    try:
        import pythoncom
        from win32com.shell import shell, shellcon
    except ImportError as exc:
        raise RuntimeError(
            "Windows shortcut support is missing. Run Setup.cmd again so pywin32 is installed."
        ) from exc

    target = (root / ".venv" / "Scripts" / "pythonw.exe").resolve()
    script = (root / "session_export_mode.py").resolve()
    if not target.exists():
        raise FileNotFoundError(f"Python launcher is missing: {target}")
    if not script.exists():
        raise FileNotFoundError(f"Presence Coach entry point is missing: {script}")

    desktop = Path(
        shell.SHGetFolderPath(
            0,
            shellcon.CSIDL_DESKTOPDIRECTORY,
            None,
            shellcon.SHGFP_TYPE_CURRENT,
        )
    )
    shortcut_path = desktop / "Presence Coach.lnk"

    if shortcut_path.exists():
        shortcut_path.unlink()

    pythoncom.CoInitialize()
    try:
        shortcut = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink,
            None,
            pythoncom.CLSCTX_INPROC_SERVER,
            shell.IID_IShellLink,
        )
        shortcut.SetPath(str(target))
        shortcut.SetArguments(f'"{script}"')
        shortcut.SetWorkingDirectory(str(root.resolve()))
        shortcut.SetIconLocation(str(icon_path), 0)
        shortcut.SetDescription("Presence Coach")

        persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
        persist_file.Save(str(shortcut_path), 0)
    finally:
        pythoncom.CoUninitialize()

    if not shortcut_path.exists():
        raise RuntimeError("Windows reported success, but the desktop shortcut was not created.")

    _refresh_windows_icons()
    return shortcut_path


def main() -> int:
    root = Path(__file__).resolve().parent
    try:
        icon = get_icon(root)
        shortcut = create_desktop_shortcut(root, icon)
    except Exception as exc:
        print(f"Desktop shortcut setup failed: {exc}", file=sys.stderr)
        return 1

    print(f"Using Presence icon: {icon}")
    print(f"Desktop shortcut created: {shortcut}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
