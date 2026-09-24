import importlib
import queue
import sys
import types
import unittest
from unittest.mock import patch


class _Var:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def _load_app_module():
    if "app" in sys.modules:
        return sys.modules["app"]

    fake_sounddevice = types.ModuleType("sounddevice")
    previous = sys.modules.get("sounddevice")
    sys.modules["sounddevice"] = fake_sounddevice
    try:
        return importlib.import_module("app")
    finally:
        if previous is None:
            sys.modules.pop("sounddevice", None)
        else:
            sys.modules["sounddevice"] = previous


app = _load_app_module()


class RuntimeStateTests(unittest.TestCase):
    def make_state(self):
        state = types.SimpleNamespace()
        state.events = queue.Queue()
        state.transcript = types.SimpleNamespace(add=lambda *args: None, boundary=False)
        state.dirty = False
        state.level = 0
        state._runtime_error_active = False
        state._safety_alerted = False
        state.state = _Var("Connecting…")
        state.connection_state = _Var("●  Connecting")
        state.display_state = _Var("Connecting")
        state.display_hint = _Var("")
        state.provider = _Var("Google Gemini")
        state.consent = _Var(True)
        state._privacy_last_state = "Connecting…"
        state._privacy_resetting_consent = False
        state.set_session_controls = lambda live: None
        state.render = lambda: None
        state.poll = lambda: None
        state.after = lambda *args: None
        return state

    def test_error_then_disconnect_remains_needs_attention(self):
        state = self.make_state()
        state.events.put(("error", "503 Service Unavailable"))
        state.events.put(("disconnected", ""))

        with patch.object(app.messagebox, "showerror") as showerror:
            app.App.poll(state)

        self.assertTrue(state._runtime_error_active)
        self.assertEqual(state.state.get(), "Connection issue")
        self.assertEqual(state.connection_state.get(), "●  Needs attention")
        self.assertEqual(state.display_state.get(), "Connection issue")
        showerror.assert_called_once()

    def test_successful_disconnect_is_session_complete(self):
        state = self.make_state()
        state.events.put(("connected", ""))
        state.events.put(("disconnected", ""))

        app.App.poll(state)

        self.assertFalse(state._runtime_error_active)
        self.assertEqual(state.state.get(), "Session complete")
        self.assertEqual(state.connection_state.get(), "●  Ready")


if __name__ == "__main__":
    unittest.main()
