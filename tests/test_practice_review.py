import importlib
import queue
import sys
import types
import unittest

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
