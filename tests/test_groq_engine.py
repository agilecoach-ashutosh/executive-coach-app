import io
import queue
import sys
import types
import unittest
import wave
from unittest.mock import Mock

# Keep helper tests independent of local PortAudio installation.
_fake_sounddevice = types.ModuleType("sounddevice")
_previous_sounddevice = sys.modules.get("sounddevice")
sys.modules["sounddevice"] = _fake_sounddevice
try:
    from groq_engine import GroqEngine, pcm_to_wav_bytes, split_for_tts
finally:
    if _previous_sounddevice is None:
        sys.modules.pop("sounddevice", None)
    else:
        sys.modules["sounddevice"] = _previous_sounddevice


class GroqEngineHelperTests(unittest.TestCase):
    def make_engine(self):
        return GroqEngine("test-secret", "test-model", "troy", None, None, queue.Queue())

    def test_split_for_tts_respects_orpheus_limit(self):
        text = (
            "This is a realistic coaching response that should be split into safe chunks. "
            "It contains several sentences so the splitter prefers natural boundaries. "
            "The final sentence is deliberately repeated to make the response longer. "
        ) * 4
        chunks = split_for_tts(text)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk for chunk in chunks))
        self.assertTrue(all(len(chunk) <= 190 for chunk in chunks))

    def test_split_for_tts_handles_single_long_sentence(self):
        text = "word " * 120
        chunks = split_for_tts(text)
        self.assertTrue(all(len(chunk) <= 190 for chunk in chunks))
        self.assertGreater(len(chunks), 1)

    def test_pcm_to_wav_bytes_builds_16khz_mono_pcm(self):
        pcm = b"\x00\x00" * 1600
        wav_bytes = pcm_to_wav_bytes(pcm)
        with wave.open(io.BytesIO(wav_bytes), "rb") as wav:
            self.assertEqual(wav.getnchannels(), 1)
            self.assertEqual(wav.getsampwidth(), 2)
            self.assertEqual(wav.getframerate(), 16000)
            self.assertEqual(wav.getnframes(), 1600)

    def test_transcription_upload_stays_in_memory(self):
        engine = self.make_engine()
        create = Mock(return_value=types.SimpleNamespace(text="  hello  "))
        engine.client = types.SimpleNamespace(
            audio=types.SimpleNamespace(
                transcriptions=types.SimpleNamespace(create=create),
            )
        )

        result = engine._transcribe(b"\x00\x00" * 1600)

        self.assertEqual(result, "hello")
        upload = create.call_args.kwargs["file"]
        self.assertEqual(upload[0], "presence-turn.wav")
        self.assertIsInstance(upload[1], bytes)
        self.assertTrue(upload[1].startswith(b"RIFF"))
        self.assertEqual(upload[2], "audio/wav")

    def test_tts_playback_stays_in_memory(self):
        engine = self.make_engine()
        response = types.SimpleNamespace(read=Mock(return_value=b"RIFF-in-memory"))
        create = Mock(return_value=response)
        engine.client = types.SimpleNamespace(
            audio=types.SimpleNamespace(
                speech=types.SimpleNamespace(create=create),
            )
        )
        engine._play_wav_bytes = Mock()

        engine._speak_chunk("What matters here?")

        engine._play_wav_bytes.assert_called_once_with(b"RIFF-in-memory", 0)
        create.assert_called_once_with(
            model=engine.tts_model,
            voice=engine.voice,
            input="What matters here?",
            response_format="wav",
        )

    def test_text_imminent_danger_stops_before_chat_generation(self):
        engine = self.make_engine()
        engine._generate_and_speak = Mock()

        engine._respond_to_text(
            'I have a plan to hurt myself now.',
            visible_input=True,
        )

        self.assertTrue(engine.stopping.is_set())
        self.assertTrue(any(kind == 'safety' for kind, _ in list(engine.events.queue)))
        engine._generate_and_speak.assert_not_called()

    def test_interrupt_during_blocking_chat_discards_pending_ai_reply(self):
        engine = self.make_engine()
        response = types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Late reply"))]
        )

        def create(**_kwargs):
            engine.command("interrupt")
            return response

        engine.client = types.SimpleNamespace(
            chat=types.SimpleNamespace(
                completions=types.SimpleNamespace(create=create),
            )
        )
        engine._speak_chunk = Mock()

        engine._respond_to_text("I want to explore this.", visible_input=True)

        emitted = list(engine.events.queue)
        self.assertFalse(any(kind == engine.output_role and value == "Late reply" for kind, value in emitted))
        engine._speak_chunk.assert_not_called()

    def test_stop_during_blocking_chat_does_not_append_or_emit_ai_reply(self):
        engine = self.make_engine()
        response = types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Too late"))]
        )

        def create(**_kwargs):
            engine.stop()
            return response

        engine.client = types.SimpleNamespace(
            chat=types.SimpleNamespace(
                completions=types.SimpleNamespace(create=create),
            )
        )
        engine._speak_chunk = Mock()

        engine._respond_to_text("End this session.", visible_input=True)

        emitted = list(engine.events.queue)
        self.assertFalse(any(kind == engine.output_role and value == "Too late" for kind, value in emitted))
        self.assertFalse(any(message.get("content") == "Too late" for message in engine.messages))
        engine._speak_chunk.assert_not_called()

    def test_tts_rate_limit_keeps_session_alive_and_surfaces_transcript_notice(self):
        engine = self.make_engine()
        rate_error = RuntimeError("429 Too Many Requests: rate limit")
        create = Mock(side_effect=[rate_error, rate_error])
        engine.client = types.SimpleNamespace(
            audio=types.SimpleNamespace(
                speech=types.SimpleNamespace(create=create),
            )
        )
        engine._wait_for_tts_slot = Mock(return_value=True)

        spoken = engine._speak_chunk("What matters here?", 0)

        self.assertFalse(spoken)
        self.assertFalse(engine.stopping.is_set())
        self.assertEqual(create.call_count, 2)
        self.assertTrue(
            any(
                kind == "notice" and "rate limit" in value.lower()
                for kind, value in list(engine.events.queue)
            )
        )


if __name__ == "__main__":
    unittest.main()
