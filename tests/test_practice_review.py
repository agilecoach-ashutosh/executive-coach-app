import importlib
import queue
import sys
import types
import unittest
from unittest.mock import Mock, patch

# Import the UI layer without requiring PortAudio on headless CI hosts.
_fake_sounddevice = types.ModuleType("sounddevice")
_previous_sounddevice = sys.modules.get("sounddevice")
sys.modules["sounddevice"] = _fake_sounddevice
try:
    practice_review = importlib.import_module("practice_review")
finally:
    if _previous_sounddevice is None:
        sys.modules.pop("sounddevice", None)
    else:
        sys.modules["sounddevice"] = _previous_sounddevice


class PracticeReviewGenerationTests(unittest.TestCase):
    def test_cancelled_gemini_restart_preserves_previous_review(self):
        state = self.make_state()
        state.practice_mode = "coach"
        state.engine = None
        state.current_scenario = {"title": "test"}
        state.key = Mock(get=lambda: "test-key")
        state.consent = Mock(get=lambda: True)
        state.pause = Mock(get=lambda: "6")
        state.threshold = Mock(get=lambda: ".018")
        state.confirm_unsaved = lambda: False
        state.practice_review_text = "Completed review"
        state.practice_review_generated_level = "PCC"
        state.practice_session_started_at = 10
        state.practice_session_ended_at = 20
        practice_review.review_start(state)
        self.assertEqual(state.practice_review_text, "Completed review")
        self.assertEqual(state.practice_review_generated_level, "PCC")
        self.assertEqual(state.practice_session_started_at, 10)
        self.assertEqual(state.practice_session_ended_at, 20)

    def test_new_session_closes_previous_review_and_discards_snapshot(self):
        state = self.make_state()
        state._review_dialog = Mock()
        dialog = state._review_dialog
        state._review_snapshot = {"rows": ["previous evidence"]}
        practice_review._clear_review_state(state)
        dialog.destroy.assert_called_once()
        self.assertIsNone(state._review_dialog)
        self.assertIsNone(state._review_snapshot)

    def test_export_uses_generation_snapshot_after_transcript_changes(self):
        exports = importlib.import_module("session_export_mode")
        state = self.make_state()
        state.transcript = types.SimpleNamespace(rows=[("00:00:01", "Coach", "Original turn")])
        state.current_scenario = {"title": "Original client", "nested": {"name": "Original"}}
        state.practice_session_started_at = 10
        state.practice_session_ended_at = 20
        practice_review._begin_review_generation(state)
        snapshot = practice_review._capture_review_snapshot(state)
        state.practice_review_text = "Original review"
        state.practice_review_generated_level = "PCC"
        state.practice_review_level = Mock(get=lambda: "PCC")
        state.transcript.rows.append(("00:00:30", "Coach", "Later turn"))
        state.current_scenario["nested"]["name"] = "Changed"
        state.practice_session_ended_at = 100
        with patch.object(exports.filedialog, "asksaveasfilename", return_value="review.docx"), \
                patch.object(exports, "export_review_docx") as export, \
                patch.object(exports.messagebox, "showinfo"):
            self.assertTrue(exports.export_coaching_review_word(state))
        args = export.call_args.args
        self.assertEqual(args[3].duration_seconds, 10)
        self.assertEqual(args[4]["nested"]["name"], "Original")
        self.assertEqual(args[5], [("00:00:01", "Coach", "Original turn")])
        self.assertIs(args[3], snapshot["metrics"])

    def make_state(self):
        return types.SimpleNamespace(
            _review_generation=0,
            _review_queue=queue.Queue(),
            _review_started_at=None,
            _review_last_elapsed=-1,
            practice_session_started_at=None,
            practice_session_ended_at=None,
            practice_review_shown=False,
            practice_review_text="",
        )

    def test_result_from_discarded_generation_is_ignored(self):
        state = self.make_state()
        stale_generation = practice_review._begin_review_generation(state)
        practice_review._clear_review_state(state)
        state._review_queue.put((stale_generation, "ok", "stale private review"))

        practice_review._poll_review_result(state)

        self.assertEqual(state.practice_review_text, "")
        self.assertEqual(state._review_generation, stale_generation + 1)


if __name__ == "__main__":
    unittest.main()
