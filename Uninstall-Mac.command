#!/bin/bash

# Presence Coach uninstaller for macOS.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

pause_before_exit() {
  printf "\nPress Return to close this window."
  read -r _
}

printf "\nPresence Coach - uninstall\n"
printf "==========================\n\n"
printf "This removes the local Python environment created by Presence Coach.\n"
printf "It does NOT remove Python, Apple Command Line Tools, Homebrew, PortAudio,\n"
printf "or exported transcripts/reports/audio. The project folder remains.\n\n"

printf "Continue with uninstall? [y/N]: "
read -r CONTINUE
case "$CONTINUE" in
  y|Y|yes|YES) ;;
  *)
    printf "Uninstall cancelled.\n"
    pause_before_exit
    exit 0
    ;;
esac

printf "\nRemove saved Gemini/Groq API keys from macOS Keychain? [y/N]: "
read -r REMOVE_KEYS
case "$REMOVE_KEYS" in
  y|Y|yes|YES)
    printf "\nRemoving saved Presence Coach API keys...\n"
    if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
      "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/uninstall_cleanup.py" ||         printf "WARNING: One or more saved API keys could not be removed automatically.\n"
    elif command -v python3.12 >/dev/null 2>&1 &&          python3.12 -c 'import keyring' >/dev/null 2>&1; then
      python3.12 "$SCRIPT_DIR/uninstall_cleanup.py" ||         printf "WARNING: One or more saved API keys could not be removed automatically.\n"
    else
      printf "WARNING: Presence Coach's local Python environment is missing, so saved API keys could not be removed automatically.\n"
      printf "Remove any PresenceCoach entries manually from Keychain Access if needed.\n"
    fi
    ;;
esac

printf "\nRemoving local application environment...\n"
rm -rf "$SCRIPT_DIR/.venv"
find "$SCRIPT_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "$SCRIPT_DIR/.pytest_cache"

printf "\nPresence Coach has been removed from this Mac account.\n"
printf "Your exported transcripts, reports, and audio files were not deleted.\n\n"
printf "The source/project folder is still here:\n%s\n" "$SCRIPT_DIR"
printf "You may move that folder to Trash if you no longer want the source files.\n"
pause_before_exit
