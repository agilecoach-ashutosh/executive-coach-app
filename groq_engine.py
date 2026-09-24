"""Turn-based Groq voice engine for Presence Coach.

Pipeline: local mic -> Groq Whisper STT -> Groq chat model -> Groq Orpheus TTS.
The interface intentionally mirrors LiveEngine closely so the Tk UI can swap
providers without changing transcript or session-control behavior.
"""
from __future__ import annotations

import collections
import contextlib
import io
import queue
import re
import threading
import time
import wave

import numpy as np
import sounddevice as sd
from groq import Groq

from coaching import IMMINENT_DANGER_RESPONSE, TurnGate, detects_imminent_danger
from session_export import SessionAudioRecorder

DEFAULT_CHAT_MODEL = "openai/gpt-oss-120b"
DEFAULT_STT_MODEL = "whisper-large-v3-turbo"
DEFAULT_TTS_MODEL = "canopylabs/orpheus-v1-english"
DEFAULT_VOICE = "troy"
REQUEST_TIMEOUT_SECONDS = 30.0


def split_for_tts(text: str, limit: int = 190) -> list[str]:
    """Split text under Orpheus' 200-character input limit."""
    clean = re.sub(r"[`*_#]", "", text or "")
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", clean)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= limit:
            candidate = f"{current} {sentence}".strip()
            if len(candidate) <= limit:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = sentence
            continue

        if current:
            chunks.append(current)
            current = ""
        words = sentence.split()
        part = ""
        for word in words:
            candidate = f"{part} {word}".strip()
            if len(candidate) <= limit:
                part = candidate
            else:
                if part:
                    chunks.append(part)
                part = word[:limit]
        if part:
            current = part

    if current:
        chunks.append(current)
    return chunks


def pcm_to_wav_bytes(pcm: bytes, sample_rate: int = 16000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return buffer.getvalue()


class GroqEngine(threading.Thread):
    def __init__(
        self,
        key,
        model,
        voice,
        mic,
        speaker,
        events,
        pause=6,
        threshold=.018,
        system_prompt="",
        input_role="Coachee",
        output_role="Coach",
        kickoff=None,
        response_status="Reflecting",
        stt_model=DEFAULT_STT_MODEL,
        tts_model=DEFAULT_TTS_MODEL,
    ):
        super().__init__(daemon=True)
        self.key = key
        self.model = model or DEFAULT_CHAT_MODEL
        self.voice = voice or DEFAULT_VOICE
        self.mic, self.speaker, self.events = mic, speaker, events
        self.system_prompt = system_prompt
        self.input_role = input_role
        self.output_role = output_role
        self.kickoff = kickoff
        self.response_status = response_status
        self.stt_model = stt_model or DEFAULT_STT_MODEL
        self.tts_model = tts_model or DEFAULT_TTS_MODEL

        self.commands = queue.Queue()
        self.audio_in = queue.Queue(maxsize=180)
        self.gate = TurnGate(pause, threshold)
        self.pending = collections.deque(maxlen=10)
        self.current_audio = bytearray()
        self.stopping = threading.Event()
        self.interrupting = threading.Event()
        self.muted = False
        self.hold = False
        self.generating = False
        self.output_level = 0.0
        self.playback_until = 0.0
        self.client = None
        self.messages = [{"role": "system", "content": system_prompt}]
        self.recorder = SessionAudioRecorder()
        self.recorder.start(time.monotonic())

    def emit(self, kind, value=""):
        self.events.put((kind, value))

    def command(self, name, value=None):
        if name == "interrupt":
            self.interrupting.set()
        self.commands.put((name, value))

    def stop(self):
        self.stopping.set()
        self.interrupting.set()
        self.output_level = 0.0
        self.playback_until = 0.0

    def has_audio(self):
        return self.recorder.has_audio()

    def export_audio(self, filename):
        self.recorder.export_mp3(filename)

    def audio_truncated(self):
        return self.recorder.is_truncated()

    def capture(self, data, frames, timing, status):
        if self.stopping.is_set() or self.muted or self.generating:
            return
        pcm = bytes(data)
        self.recorder.append(pcm, 16000, 1, now=time.monotonic())
        try:
            self.audio_in.put_nowait(pcm)
        except queue.Full:
            self.emit("error", "Audio input cannot keep up. Stop and reconnect.")
            self.stop()

    def run(self):
        try:
            self.client = Groq(
                api_key=self.key,
                timeout=REQUEST_TIMEOUT_SECONDS,
                max_retries=1,
            )
            with contextlib.ExitStack() as audio_stack:
                try:
                    mic_stream = sd.RawInputStream(
                        samplerate=16000,
                        channels=1,
                        dtype="int16",
                        blocksize=640,
                        device=self.mic,
                        callback=self.capture,
                    )
                    audio_stack.enter_context(mic_stream)
                except Exception as exc:
                    raise RuntimeError(f"MIC_DEVICE_ERROR: {exc}") from exc

                self.emit("connected")
                if self.kickoff:
                    self._respond_to_text(self.kickoff, visible_input=False)
                self._loop()
        except Exception as exc:
            detail = str(exc).replace(self.key, "[redacted]")
            self.emit("error", detail[:800])
        finally:
            self.output_level = 0.0
            self.playback_until = 0.0
            self.emit("disconnected")

    def _loop(self):
        while not self.stopping.is_set():
            self._handle_commands()
            if self.stopping.is_set():
                break

            try:
                chunk = self.audio_in.get(timeout=.02)
            except queue.Empty:
                continue

            level = (
                float(np.sqrt(np.mean(np.frombuffer(chunk, dtype="<i2").astype(float) ** 2)))
                / 32768
            )
            self.emit("level", level)

            was_active = self.gate.active
            self.pending.append(chunk)
            action = self.gate.feed(level, time.monotonic(), self.hold)

            if action == "start":
                self.current_audio.clear()
                for buffered in self.pending:
                    self.current_audio.extend(buffered)
                self.pending.clear()
                self.emit("status", "Listening — take your time")
            elif was_active:
                self.current_audio.extend(chunk)
                self.pending.clear()

            if action == "end":
                audio = bytes(self.current_audio)
                self.current_audio.clear()
                self.pending.clear()
                if audio:
                    self._respond_to_audio(audio)

    def _handle_commands(self):
        while True:
            try:
                name, value = self.commands.get_nowait()
            except queue.Empty:
                return

            if name == "mute":
                self.muted = bool(value)
                if self.muted and self.gate.active and self.current_audio:
                    audio = bytes(self.current_audio)
                    self.current_audio.clear()
                    self.gate.reset()
                    self._respond_to_audio(audio)
                self.pending.clear()
                self._drain_audio_queue()
                self.emit("status", "Microphone muted" if self.muted else "Listening")
            elif name == "hold":
                self.hold = bool(value)
            elif name == "finish":
                if self.gate.active and self.current_audio:
                    audio = bytes(self.current_audio)
                    self.current_audio.clear()
                    self.pending.clear()
                    self.gate.reset()
                    self._respond_to_audio(audio)
            elif name == "interrupt":
                self.interrupting.set()
                self.emit("status", "Listening — your turn")
            elif name == "text" and value:
                self.current_audio.clear()
                self.pending.clear()
                self.gate.reset()
                self._respond_to_text(str(value), visible_input=True)

    def _drain_audio_queue(self):
        while True:
            try:
                self.audio_in.get_nowait()
            except queue.Empty:
                break

    def _respond_to_audio(self, pcm: bytes):
        if self.stopping.is_set():
            return
        self.generating = True
        self.emit("status", "Transcribing")
        try:
            text = self._transcribe(pcm)
            if not text:
                self.emit("status", "Listening")
                return
            self.emit("boundary")
            self.emit(self.input_role, text)
            if self.input_role == "Coachee" and detects_imminent_danger(text):
                self.emit("safety", IMMINENT_DANGER_RESPONSE)
                self.stop()
                return
            self._generate_and_speak(text)
        finally:
            self.generating = False
            self._drain_audio_queue()

    def _respond_to_text(self, text: str, visible_input: bool):
        if self.stopping.is_set():
            return
        self.generating = True
        try:
            if visible_input:
                self.emit("boundary")
                self.emit(self.input_role, text)
                if self.input_role == "Coachee" and detects_imminent_danger(text):
                    self.emit("safety", IMMINENT_DANGER_RESPONSE)
                    self.stop()
                    return
            self._generate_and_speak(text, keep_user=visible_input)
        finally:
            self.generating = False
            self._drain_audio_queue()

    def _transcribe(self, pcm: bytes) -> str:
        wav_bytes = pcm_to_wav_bytes(pcm)
        result = self.client.audio.transcriptions.create(
            file=("presence-turn.wav", wav_bytes, "audio/wav"),
            model=self.stt_model,
            response_format="json",
            temperature=0.0,
        )
        return (getattr(result, "text", "") or "").strip()

    def _generate_and_speak(self, user_text: str, keep_user: bool = True):
        self.emit("status", self.response_status)
        request_messages = list(self.messages)
        request_messages.append({"role": "user", "content": user_text})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=request_messages,
            temperature=.6,
            max_completion_tokens=900,
        )
        reply = (response.choices[0].message.content or "").strip()
        if not reply:
            self.emit("status", "Listening")
            return

        if keep_user:
            self.messages.append({"role": "user", "content": user_text})
        self.messages.append({"role": "assistant", "content": reply})
        self._trim_history()

        self.emit("boundary")
        self.emit(self.output_role, reply)
        self.interrupting.clear()
        interrupted = False
        for chunk in split_for_tts(reply):
            if self.stopping.is_set() or self.interrupting.is_set():
                interrupted = True
                break
            self._speak_chunk(chunk)

        self.output_level = 0.0
        self.playback_until = 0.0
        if interrupted and not self.stopping.is_set():
            self.emit("boundary")
            self.emit(
                "notice",
                f"{self.output_role} response was interrupted; its transcript may include words not played.",
            )
        self.interrupting.clear()
        self.emit("status", "Microphone muted" if self.muted else "Listening")

    def _trim_history(self):
        if len(self.messages) <= 42:
            return
        system = self.messages[0]
        self.messages = [system] + self.messages[-40:]

    def _speak_chunk(self, text: str):
        if not text:
            return
        self.emit("status", "Speaking")
        response = self.client.audio.speech.create(
            model=self.tts_model,
            voice=self.voice,
            input=text,
            response_format="wav",
        )
        self._play_wav_bytes(response.read())

    def _play_wav_bytes(self, wav_bytes: bytes):
        with wave.open(io.BytesIO(wav_bytes), "rb") as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()
            if sample_width != 2:
                raise RuntimeError(
                    f"Groq TTS returned unsupported {sample_width * 8}-bit WAV audio."
                )

            with contextlib.ExitStack() as audio_stack:
                try:
                    speaker_stream = sd.RawOutputStream(
                        samplerate=sample_rate,
                        channels=channels,
                        dtype="int16",
                        device=self.speaker,
                        blocksize=960,
                    )
                    stream = audio_stack.enter_context(speaker_stream)
                except Exception as exc:
                    raise RuntimeError(f"SPEAKER_DEVICE_ERROR: {exc}") from exc

                while not self.stopping.is_set() and not self.interrupting.is_set():
                    data = wav.readframes(960)
                    if not data:
                        break
                    samples = np.frombuffer(data, dtype="<i2").astype(float)
                    self.output_level = (
                        float(np.sqrt(np.mean(samples ** 2))) / 32768 if len(samples) else 0.0
                    )
                    frames = max(1, len(data) // (2 * channels))
                    now = time.monotonic()
                    self.recorder.append(data, sample_rate, channels, now=now)
                    self.playback_until = now + frames / sample_rate + .06
                    stream.write(data)
