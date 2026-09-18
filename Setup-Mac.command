#!/bin/bash

# Presence Coach first-time setup for macOS.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

pause_before_exit() {
  printf "\nPress Return to close this window."
  read -r _
}

fail() {
  printf "\nSetup failed: %s\n" "$1"
  pause_before_exit
  exit 1
}

printf "Presence Coach - first-time macOS setup\n"
printf "Requires Python 3.12 and an internet connection.\n\n"

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
  fail "Python 3.12 was not found. Install it from https://www.python.org/downloads/macos/ and run this file again."
fi

printf "Using %s\n" "$PYTHON_BIN"
"$PYTHON_BIN" -m venv .venv || fail "Could not create the local Python environment."

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
"$VENV_PYTHON" -m pip install --upgrade pip || fail "Could not update pip."
"$VENV_PYTHON" -m pip install -r requirements.txt || fail "Could not install the application dependencies."

"$VENV_PYTHON" -c 'import tkinter' || \
  fail "Python was installed without Tk support. Install the official Python 3.12 package from python.org and run setup again."
"$VENV_PYTHON" -c 'import keyring, sounddevice' || \
  fail "An audio or credential dependency could not load. If the error mentions PortAudio, install it with Homebrew using: brew install portaudio"

printf "\nSetup complete. Double-click Start-Mac.command to open Presence Coach.\n"
printf "macOS will ask for microphone access the first time a session starts.\n"
pause_before_exit
