"""Presence Coach uninstall helper.

Removes only API credentials stored by Presence Coach in the operating-system
credential store. It never prints credential values and does not touch exported
session files.
"""
from __future__ import annotations

import sys

import keyring


SERVICE = "PresenceCoach"
ACCOUNTS = ("gemini", "groq")


def remove_saved_credentials() -> int:
    failures: list[str] = []

    for account in ACCOUNTS:
        try:
            keyring.delete_password(SERVICE, account)
        except keyring.errors.PasswordDeleteError:
            print(f"No saved {account.title()} API key found.")
        except Exception as exc:
            failures.append(account)
            print(
                f"Could not remove the saved {account.title()} API key: {exc}",
                file=sys.stderr,
            )
        else:
            print(f"Removed saved {account.title()} API key.")

    if failures:
        print(
            "One or more saved credentials could not be removed. "
            "You can remove PresenceCoach entries manually from the operating-system "
            "credential store.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(remove_saved_credentials())
