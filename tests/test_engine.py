"""Transport tests use a fake audio device; they never send audio to Google."""
import asyncio
import importlib
import queue
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

# Allows transport tests on headless machines without PortAudio.
with patch.dict(sys.modules, {'sounddevice': types.ModuleType('sounddevice')}):
    engine_module = importlib.import_module('engine')


class TransportTests(unittest.IsolatedAsyncioTestCase):
    def make_engine(self):
        engine = engine_module.LiveEngine('test-secret', 'test-model', 'Kore', None, None, queue.Queue())
        engine.session = types.SimpleNamespace(send_realtime_input=AsyncMock(), send_client_content=AsyncMock())
        return engine

    async def test_finishing_interrupted_turn_reenables_reply(self):
        engine = self.make_engine()
        engine.gate.active = True
        engine.suppress = True
        await engine.finish_turn()
        self.assertFalse(engine.gate.active)
        self.assertFalse(engine.suppress)
        self.assertTrue(engine.generating)
        self.assertIn('activity_end', engine.session.send_realtime_input.call_args.kwargs)

    async def test_muted_capture_never_queues_audio(self):
        engine = self.make_engine()
        engine.muted = True
        engine.capture(b'private audio', 0, None, None)
        self.assertTrue(engine.audio_in.empty())
        engine.stop()
        engine.muted = False
        engine.capture(b'more audio', 0, None, None)
        self.assertTrue(engine.audio_in.empty())

    async def test_stopping_clears_playback(self):
        engine = self.make_engine()
        engine.output.extend(b'\x01\x02' * 20)
        engine.stop()
        self.assertEqual(engine.output, b'')

    async def test_playback_meter_tracks_audio_and_returns_to_zero(self):
        engine = self.make_engine()
        engine.output.extend(b'\x00\x40' * 4)
        out = bytearray(8)
        engine.playback(out, 4, None, None)
        self.assertAlmostEqual(engine.output_level, .5)
        self.assertGreater(engine.playback_until, 0)
        engine.playback(out, 4, None, None)
        self.assertEqual(engine.output_level, 0)
        self.assertEqual(out, b'\0' * 8)
        engine.clear_output()
        self.assertEqual(engine.playback_until, 0)

    async def test_receive_handles_all_parts_and_transcripts(self):
        engine = self.make_engine()
        def ns(**kwargs):
            return types.SimpleNamespace(**kwargs)
        content = ns(interrupted=False, input_transcription=ns(text='I feel stuck'),
                     output_transcription=ns(text='What feels stuck?'),
                     model_turn=ns(parts=[ns(inline_data=ns(data=b'12')), ns(inline_data=ns(data=b'34'))]),
                     turn_complete=True)
        async def receive():
            yield ns(go_away=None, server_content=content)
            engine.stopping.set()
        engine.session.receive = receive
        await engine.receive_loop()
        self.assertEqual(engine.output, b'1234')
        events = list(engine.events.queue)
        self.assertIn(('Coachee', 'I feel stuck'), events)
        self.assertIn(('Coach', 'What feels stuck?'), events)

    async def test_mute_command_drains_already_captured_audio(self):
        engine = self.make_engine()
        engine.audio_in.put(b'private')
        engine.command('mute', True)
        task = asyncio.create_task(engine.send_loop())
        await asyncio.sleep(.03)
        engine.stop()
        await task
        self.assertTrue(engine.audio_in.empty())
        engine.session.send_realtime_input.assert_not_called()


if __name__ == '__main__':
    unittest.main()
