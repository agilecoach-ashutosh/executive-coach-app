#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1
printf "Close Presence Coach before updating. This updater does not require Git.\n\n"

PYTHON_BIN=""
for candidate in python3.12 python3; do
  candidate_path="$(command -v "$candidate" 2>/dev/null || true)"
  if [ -n "$candidate_path" ] && "$candidate_path" -c \
    'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' \
    >/dev/null 2>&1; then
    PYTHON_BIN="$candidate_path"
    break
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  printf "Python 3.12 is required. Run Setup-Mac.command or install Python 3.12 first.\n"
  status=1
else
  "$PYTHON_BIN" "$SCRIPT_DIR/update_app.py"
  status=$?
fi

if [ "$status" -ne 0 ]; then
  printf "\nYour previous installation was left in place or restored. Read the message above.\n"
fi
printf "\nPress Return to close this window."
read -r _
exit "$status"
