import io
import unittest
import wave

from groq_engine import pcm_to_wav_bytes, split_for_tts


class GroqEngineHelperTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
