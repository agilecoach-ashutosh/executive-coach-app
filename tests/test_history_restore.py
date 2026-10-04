import importlib
import queue
import sys
import types
import unittest
from unittest.mock import Mock

import history_ui
from scenarios import COACHEE_SCENARIOS

# The full entrypoint must be composed before exercising restoration.
_previous_sd = sys.modules.get("sounddevice")
sys.modules["sounddevice"] = types.ModuleType("sounddevice")
try:
    importlib.import_module("session_export_mode")
finally:
    if _previous_sd is None: sys.modules.pop("sounddevice", None)
    else: sys.modules["sounddevice"] = _previous_sd


class HistoryRestoreTests(unittest.TestCase):
    def test_saved_review_restores_matching_evidence_offline_with_consent_reset(self):
        state = types.SimpleNamespace(_review_queue=queue.Queue(), _review_generation=0, _review_dialog=None,
            mode_button=Mock(), review_button=Mock(), practice_review_level=Mock(), muted=Mock(), hold=Mock(),
            state=Mock(), connection_state=Mock(), consent=Mock(), set_session_controls=Mock(), render=Mock(),
            show_session_review=Mock())
        state._review_queue.put((0, "ok", "stale previous result"))
        data = {"mode": "coach", "rows": [["00:00:00", "Coach", "What matters?"]], "review": "Original report",
                "level": "PCC", "duration_seconds": 42,
                "scenario": {"id": COACHEE_SCENARIOS[0]["id"], "persona": "Saved client", "practice_focus": "Presence"}}
        history_ui.restore_session(state, data)
        self.assertIsNone(state.engine)
        self.assertEqual(state.practice_review_text, "Original report")
        self.assertEqual(state._review_snapshot["rows"], [("00:00:00", "Coach", "What matters?")])
        self.assertEqual(state._review_snapshot["metrics"].duration_seconds, 42)
        self.assertEqual(state.current_scenario["practice_focus"], "Presence")
        self.assertTrue(state._review_queue.empty())
        state.consent.set.assert_called_once_with(False)
        state.show_session_review.assert_called_once()
        state.practice_review_level.set.assert_called_once_with("PCC")


if __name__ == "__main__": unittest.main()
