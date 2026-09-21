import importlib
import sys
import types
import unittest

# Validate the complete layered entry point without requiring PortAudio or a display.
_fake_sounddevice = types.ModuleType("sounddevice")
_previous_sounddevice = sys.modules.get("sounddevice")
sys.modules["sounddevice"] = _fake_sounddevice
try:
    entrypoint = importlib.import_module("session_export_mode")
finally:
    if _previous_sounddevice is None:
        sys.modules.pop("sounddevice", None)
    else:
        sys.modules["sounddevice"] = _previous_sounddevice


class AppCompositionTests(unittest.TestCase):
    def test_final_entrypoint_contains_all_critical_layers(self):
        app_class = entrypoint.base.App
        for method in (
            "start",
            "poll",
            "show_session_review",
            "generate_coaching_review",
            "open_privacy_notice",
            "clear_session_data",
            "export_transcript_word",
            "export_session_audio",
            "export_coaching_review",
        ):
            self.assertTrue(hasattr(app_class, method), method)

        self.assertIs(entrypoint.base.Transcript, entrypoint.ElapsedTranscript)


if __name__ == "__main__":
    unittest.main()
