"""Backward-compatible launcher for Presence Coach.

The production application is composed by session_export_mode.py. Keeping this
module as a thin alias avoids a second, divergent UI implementation while
preserving older launch commands and imports.
"""
import session_export_mode as entrypoint

base = entrypoint.base
PresenceApp = base.App


if __name__ == "__main__":
    PresenceApp().mainloop()
