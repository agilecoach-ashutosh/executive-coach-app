"""Visible startup and Tk callback diagnostics for the Windows GUI launcher."""
from __future__ import annotations

import os
import traceback
import ctypes
from pathlib import Path


def report_failure(title: str, error: BaseException) -> None:
    folder = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "PresenceCoach"
    log = folder / "startup-error.log"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as handle:
            handle.write("\n" + title + "\n")
            traceback.print_exception(type(error), error, error.__traceback__, file=handle)
        detail = f"The error was saved to:\n{log}"
    except OSError:
        detail = f"Could not write an error log.\n\n{type(error).__name__}: {error}"

    # This also works if importing or initializing Tkinter itself failed.
    ctypes.windll.user32.MessageBoxW(
        None,
        f"Presence Coach could not continue.\n\n{detail}",
        "Presence Coach — " + title,
        0x10,
    )


def main() -> int:
    try:
        from session_export_mode import base

        app = base.App()

        def on_callback_error(exc_type, exc_value, exc_traceback):
            exc_value = exc_value.with_traceback(exc_traceback)
            report_failure("Application error", exc_value)

        app.report_callback_exception = on_callback_error
        app.mainloop()
        return 0
    except Exception as exc:
        report_failure("Startup error", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
