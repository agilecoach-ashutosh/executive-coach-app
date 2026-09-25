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

    def test_compatibility_launcher_points_to_the_production_app_class(self):
        launch = importlib.import_module("launch")
        self.assertIs(launch.PresenceApp, entrypoint.base.App)
        self.assertIs(launch.base.App, entrypoint.base.App)

    def test_provider_selector_is_locked_for_live_sessions(self):
        provider_mode = sys.modules["provider_mode"]
        fake = types.SimpleNamespace(
            interrupt_button=_FakeButton(),
            ready_button=_FakeButton(),
            end_button=_FakeButton(),
            start_button=_FakeButton(),
            _provider_combo=_FakeButton(),
            _active_provider="Groq",
        )

        provider_mode.provider_set_session_controls(fake, True)
        self.assertEqual(fake._provider_combo.config["state"], "disabled")
        self.assertEqual(fake.start_button.config["state"], "disabled")

        provider_mode.provider_set_session_controls(fake, False)
        self.assertEqual(fake._provider_combo.config["state"], "readonly")
        self.assertIsNone(fake._active_provider)

    def test_mousewheel_units_supports_macos_windows_and_x11(self):
        helper = entrypoint.base.mousewheel_units

        with patch.object(entrypoint.base.sys, "platform", "darwin"):
            self.assertEqual(helper(types.SimpleNamespace(delta=1)), -1)
            self.assertEqual(helper(types.SimpleNamespace(delta=-1)), 1)

        with patch.object(entrypoint.base.sys, "platform", "win32"):
            self.assertEqual(helper(types.SimpleNamespace(delta=120)), -1)
            self.assertEqual(helper(types.SimpleNamespace(delta=-120)), 1)

        self.assertEqual(helper(types.SimpleNamespace(delta=0, num=4)), -1)
        self.assertEqual(helper(types.SimpleNamespace(delta=0, num=5)), 1)


if __name__ == "__main__":
    unittest.main()
