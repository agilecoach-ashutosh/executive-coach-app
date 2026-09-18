#!/bin/bash

# Launch Presence Coach from its repository folder on macOS.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

pause_before_exit() {
  printf "\nPress Return to close this window."
  read -r _
}

if [ ! -x "$SCRIPT_DIR/.venv/bin/python" ]; then
  printf "Presence Coach has not been set up yet.\n"
  printf "Double-click Setup-Mac.command first.\n"
  pause_before_exit
  exit 1
fi

"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/session_export_mode.py"
status=$?

if [ "$status" -ne 0 ]; then
  printf "\nPresence Coach closed with an error (exit code %s).\n" "$status"
  pause_before_exit
fi

exit "$status"
