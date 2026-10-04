import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from session_history import SessionHistory, validate_record


class SessionHistoryTests(unittest.TestCase):
    def test_manual_save_round_trip_and_delete_exclude_private_scenario(self):
        with tempfile.TemporaryDirectory() as root:
            store = SessionHistory(Path(root)/"history")
            self.assertEqual(store.list_sessions(), [])
            self.assertFalse(store.directory.exists())
            identifier = store.save(mode="coach", rows=[("00:00:01", "Coach", "मुझे बताइए")],
                review="Practice feedback", level="PCC", duration_seconds=25,
                scenario={"title": "Test client", "practice_focus": "Presence", "hidden_context": "Private", "api_key": "secret"})
            data = store.load(identifier)
            self.assertEqual(data["rows"][0][2], "मुझे बताइए")
            self.assertEqual(data["review"], "Practice feedback")
            self.assertEqual(data["scenario"], {"title": "Test client", "practice_focus": "Presence"})
            self.assertEqual(store.list_sessions()[0]["id"], identifier)
            store.delete(identifier)
            self.assertEqual(store.list_sessions(), [])

    def test_bad_identifiers_and_corrupt_records_are_not_loaded(self):
        with tempfile.TemporaryDirectory() as root:
            store = SessionHistory(root)
            for value in ("../outside", "", "123.json"):
                with self.assertRaises(ValueError): store.load(value)
                with self.assertRaises(ValueError): store.delete(value)
            (Path(root)/("a"*32+".json")).write_text('{"version":99}')
            self.assertEqual(store.list_sessions(), [])
            with self.assertRaises(ValueError): store.load("a"*32)

    def test_failed_save_does_not_leave_partial_session(self):
        with tempfile.TemporaryDirectory() as root:
            store = SessionHistory(root)
            with patch("session_history.os.replace", side_effect=OSError("disk full")), self.assertRaises(OSError):
                store.save(mode="coachee", rows=[("00:00:00", "Coachee", "Hello")])
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_invalid_turns_and_review_levels_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as root:
            store = SessionHistory(root)
            for changes in ({"rows": [("stamp", "Unknown", "text")]}, {"review": "Report", "level": None},
                            {"duration_seconds": float("nan")}, {"level": "MCC-PASS"}):
                args = {"mode": "coach", "rows": [("stamp", "Coach", "Hello")]}
                args.update(changes)
                with self.subTest(changes=changes), self.assertRaises(ValueError): store.save(**args)
            self.assertEqual(list(Path(root).iterdir()), [])


if __name__ == "__main__": unittest.main()
