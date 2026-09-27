"""Regression checks for session-data and review-label lifecycle boundaries."""
import importlib
import queue
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


fake_sounddevice = types.ModuleType("sounddevice")
previous_sounddevice = sys.modules.get("sounddevice")
sys.modules["sounddevice"] = fake_sounddevice
try:
    practice = importlib.import_module("practice_mode")
    review = importlib.import_module("practice_review")
    privacy = importlib.import_module("privacy_mode")
    export = importlib.import_module("session_export_mode")
finally:
    if previous_sounddevice is None:
        sys.modules.pop("sounddevice", None)
    else:
        sys.modules["sounddevice"] = previous_sounddevice


class Variable:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class SessionLifecycleTests(unittest.TestCase):
    def test_mode_switch_checks_unexported_audio_even_without_dirty_transcript(self):
        state = types.SimpleNamespace(dirty=False, practice_mode="coach")
        state.confirm_unsaved = Mock(return_value=False)
        practice.select_coachee_mode(state)
        state.confirm_unsaved.assert_called_once_with()
        self.assertEqual(state.practice_mode, "coach")

    def test_scenario_switch_checks_unexported_audio_even_without_dirty_transcript(self):
        state = types.SimpleNamespace(dirty=False, practice_mode="coach")
        state.confirm_unsaved = Mock(return_value=False)
        practice.select_scenario(state, {"persona": "Client"})
        state.confirm_unsaved.assert_called_once_with()
        self.assertEqual(state.practice_mode, "coach")

    def test_discard_during_audio_export_preserves_session(self):
        recorder = Mock()
        state = types.SimpleNamespace(
            _audio_export_in_progress=True,
            engine=types.SimpleNamespace(recorder=recorder),
        )
        with patch.object(privacy.messagebox, "showinfo") as notice:
            result = privacy.clear_session_data(state, parent=object())
        self.assertFalse(result)
        recorder.clear.assert_not_called()
        notice.assert_called_once()


class ReviewLevelTests(unittest.TestCase):
    def make_state(self):
        return types.SimpleNamespace(
            _review_generation=0,
            _review_queue=queue.Queue(),
            _review_started_at=None,
            _review_last_elapsed=-1,
            _review_generate_button=None,
            _review_export_button=None,
            _review_output=None,
            practice_review_level=Variable("ACC"),
            practice_review_text="Existing PCC findings",
            practice_review_generated_level="PCC",
        )

    def test_changing_level_invalidates_pending_result_and_saved_review(self):
        state = self.make_state()
        pending = review._begin_review_generation(state)
        state.practice_review_text = "PCC findings"
        state.practice_review_generated_level = "PCC"
        review._review_level_changed(state)
        state._review_queue.put((pending, "ok", "late PCC findings"))
        review._poll_review_result(state)
        self.assertEqual(state.practice_review_text, "")
        self.assertIsNone(state.practice_review_generated_level)

    def test_word_export_refuses_mismatched_lens(self):
        state = self.make_state()
        with patch.object(export.messagebox, "showinfo") as notice, patch.object(
            export.filedialog, "asksaveasfilename"
        ) as save_dialog:
            self.assertFalse(export.export_coaching_review_word(state))
        notice.assert_called_once()
        save_dialog.assert_not_called()


class WindowsLauncherTests(unittest.TestCase):
    def test_startup_error_is_logged_and_shown_without_tk(self):
        import windows_launch

        with tempfile.TemporaryDirectory() as folder:
            user32 = types.SimpleNamespace(MessageBoxW=Mock())
            with patch.dict(windows_launch.os.environ, {"LOCALAPPDATA": folder}), patch.object(
                windows_launch.ctypes, "windll", types.SimpleNamespace(user32=user32), create=True
            ):
                try:
                    raise RuntimeError("Startup example")
                except RuntimeError as error:
                    windows_launch.report_failure("Startup error", error)

            log = Path(folder) / "PresenceCoach" / "startup-error.log"
            self.assertIn("Startup example", log.read_text(encoding="utf-8"))
            self.assertIn(str(log), user32.MessageBoxW.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
