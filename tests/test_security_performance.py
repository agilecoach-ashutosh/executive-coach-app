import queue
import types
import unittest
from unittest.mock import Mock, patch

from runtime_errors import redact_error
from ui_helpers import begin_transcript_update, mark_last_turn
from groq_engine import GroqEngine, MAX_TURN_AUDIO_BYTES
import practice_review
import provider_mode


class SecurityPerformanceTests(unittest.TestCase):
    def test_credentials_removed_before_display(self):
        text = redact_error('bad private-secret key=query-secret Authorization: Bearer auth-secret gsk_abc123', 'private-secret')
        for secret in ('private-secret', 'query-secret', 'auth-secret', 'gsk_abc123'):
            self.assertNotIn(secret, text)

    def test_review_denial_starts_no_worker_for_either_provider(self):
        state = types.SimpleNamespace(transcript=types.SimpleNamespace(rows=[('0', 'Coach', 'Hello')]),
            key=Mock(get=lambda: 'secret'), groq_key=Mock(get=lambda: 'secret'),
            provider=Mock(get=lambda: provider_mode.GROQ))
        with patch.object(practice_review.messagebox, 'askyesno', return_value=False) as consent, \
                patch.object(practice_review.threading, 'Thread') as worker:
            practice_review.generate_coaching_review(state)
            provider_mode.provider_generate_review(state)
        self.assertEqual(consent.call_count, 2)
        worker.assert_not_called()

    def test_incremental_render_replaces_only_last_turn(self):
        state = types.SimpleNamespace(transcript=types.SimpleNamespace(rows=[('0', 'Coach', 'Hello')]), log=Mock())
        self.assertEqual(begin_transcript_update(state, 'coach'), 0)
        mark_last_turn(state, 0)
        state.log.reset_mock()
        state.transcript.rows += [('1', 'Coachee', 'Hi')]
        self.assertEqual(begin_transcript_update(state, 'coach'), 0)
        state.log.delete.assert_called_once_with('presence_last_turn', 'end')
        begin_transcript_update(state, 'coach')
        self.assertEqual(begin_transcript_update(state, 'coach'), 1)
        state.transcript = types.SimpleNamespace(rows=[('0', 'Coach', 'New session')])
        self.assertEqual(begin_transcript_update(state, 'coach'), 0)
        state.log.delete.assert_called_with('1.0', 'end')

    def test_stop_closes_transport_without_blocking_ui(self):
        engine = GroqEngine('secret', 'model', 'voice', None, None, queue.Queue())
        engine.client = Mock()
        with patch('groq_engine.threading.Thread') as thread:
            engine.stop()
        self.assertTrue(engine.stopping.is_set())
        thread.return_value.start.assert_called_once()
        thread.call_args.kwargs['target']()
        engine.client.close.assert_called_once()

    def test_groq_long_turn_is_processed_even_on_hold(self):
        engine = GroqEngine('secret', 'model', 'voice', None, None, queue.Queue())
        engine.hold = True
        engine.gate.active = True
        engine.current_audio = bytearray(MAX_TURN_AUDIO_BYTES - 1280)
        engine.audio_in.put(b'\0' * 1280)
        engine._respond_to_audio = Mock(side_effect=lambda audio: engine.stopping.set())
        engine._loop()
        self.assertEqual(len(engine._respond_to_audio.call_args.args[0]), MAX_TURN_AUDIO_BYTES)
        self.assertEqual(len(engine.current_audio), 0)
        self.assertTrue(any(kind == 'notice' and 'five-minute' in text for kind, text in engine.events.queue))


if __name__ == '__main__':
    unittest.main()
