"""Windows-only setup helper for Presence Coach.

Uses the checked-in Presence-Coach.ico directly and creates current-user
Desktop and Start Menu shortcuts with the Windows ShellLink API. This avoids
the WScript.Shell automation layer, which can reject shortcut properties on
some Windows configurations.
"""
from __future__ import annotations

import ctypes
import os
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
    """Ask Explorer to refresh shell icons after creating or replacing shortcuts."""
    try:
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
    except Exception:
        pass


def _save_shortcut(
    pythoncom,
    shell,
    shortcut_path: Path,
    target: Path,
    arguments: str,
    working_directory: Path,
    icon_path: Path,
    description: str,
) -> None:
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)
    if shortcut_path.exists():
        shortcut_path.unlink()

    shortcut = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink,
        None,
        pythoncom.CLSCTX_INPROC_SERVER,
        shell.IID_IShellLink,
    )
    shortcut.SetPath(str(target))
    shortcut.SetArguments(arguments)
    shortcut.SetWorkingDirectory(str(working_directory))
    shortcut.SetIconLocation(str(icon_path), 0)
    shortcut.SetDescription(description)

    persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
    persist_file.Save(str(shortcut_path), 0)

    if not shortcut_path.exists():
        raise RuntimeError(
            f"Windows reported success, but the shortcut was not created: {shortcut_path}"
        )


def create_shortcuts(root: Path, icon_path: Path) -> list[Path]:
    """Create launch and uninstall shortcuts for the current Windows user."""
    try:
        import pythoncom
        from win32com.shell import shell, shellcon
    except ImportError as exc:
        raise RuntimeError(
            "Windows shortcut support is missing. Run Setup.cmd again so pywin32 is installed."
        ) from exc

    target = (root / ".venv" / "Scripts" / "pythonw.exe").resolve()
    script = (root / "session_export_mode.py").resolve()
    uninstall_script = (root / "Uninstall.cmd").resolve()

    if not target.exists():
        raise FileNotFoundError(f"Python launcher is missing: {target}")
    if not script.exists():
        raise FileNotFoundError(f"Presence Coach entry point is missing: {script}")
    if not uninstall_script.exists():
        raise FileNotFoundError(f"Presence Coach uninstaller is missing: {uninstall_script}")

    desktop = Path(
        shell.SHGetFolderPath(
            0,
            shellcon.CSIDL_DESKTOPDIRECTORY,
            None,
            shellcon.SHGFP_TYPE_CURRENT,
        )
    )
    programs = Path(
        shell.SHGetFolderPath(
            0,
            shellcon.CSIDL_PROGRAMS,
            None,
            shellcon.SHGFP_TYPE_CURRENT,
        )
    )
    start_menu = programs / "Presence Coach"

    app_arguments = f'"{script}"'
    command_processor = Path(
        os.environ.get(
            "COMSPEC",
            str(Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "cmd.exe"),
        )
    )
    uninstall_arguments = f'/d /c ""{uninstall_script}""'

    shortcuts = [
        (desktop / "Presence Coach.lnk", target, app_arguments, "Presence Coach"),
        (start_menu / "Presence Coach.lnk", target, app_arguments, "Presence Coach"),
        (
            start_menu / "Uninstall Presence Coach.lnk",
            command_processor,
            uninstall_arguments,
            "Uninstall Presence Coach",
        ),
    ]

    pythoncom.CoInitialize()
    try:
        for shortcut_path, shortcut_target, arguments, description in shortcuts:
            _save_shortcut(
                pythoncom,
                shell,
                shortcut_path,
                shortcut_target,
                arguments,
                root.resolve(),
                icon_path,
                description,
            )
    finally:
        pythoncom.CoUninitialize()

    _refresh_windows_icons()
    return [item[0] for item in shortcuts]


def main() -> int:
    root = Path(__file__).resolve().parent
    try:
        icon = get_icon(root)
        shortcuts = create_shortcuts(root, icon)
    except Exception as exc:
        print(f"Shortcut setup failed: {exc}", file=sys.stderr)
        return 1

    print(f"Using Presence icon: {icon}")
    for shortcut in shortcuts:
        print(f"Shortcut created: {shortcut}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
