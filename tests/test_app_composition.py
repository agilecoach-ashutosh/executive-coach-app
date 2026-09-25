import importlib
import sys
import types
import unittest
from unittest.mock import patch

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


class _FakeButton:
    def __init__(self):
        self.config = {}

    def configure(self, **kwargs):
        self.config.update(kwargs)


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

    def test_role_segment_buttons_switch_ttk_styles_without_tk_button_options(self):
        launch = sys.modules["launch"]
        button = _FakeButton()

        launch.PresenceApp._set_segment_style(None, button, True)
        self.assertEqual(button.config, {"style": "Presence.PrimaryCompact.TButton"})

        button.config.clear()
        launch.PresenceApp._set_segment_style(None, button, False)
        self.assertEqual(button.config, {"style": "Presence.SecondaryCompact.TButton"})

    def test_mousewheel_units_supports_macos_windows_and_x11(self):
        launch = sys.modules["launch"]
        helper = launch.base.mousewheel_units

        with patch.object(launch.base.sys, "platform", "darwin"):
            self.assertEqual(helper(types.SimpleNamespace(delta=1)), -1)
            self.assertEqual(helper(types.SimpleNamespace(delta=-1)), 1)

        with patch.object(launch.base.sys, "platform", "win32"):
            self.assertEqual(helper(types.SimpleNamespace(delta=120)), -1)
            self.assertEqual(helper(types.SimpleNamespace(delta=-120)), 1)

        self.assertEqual(helper(types.SimpleNamespace(delta=0, num=4)), -1)
        self.assertEqual(helper(types.SimpleNamespace(delta=0, num=5)), 1)


if __name__ == "__main__":
    unittest.main()
