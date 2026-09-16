"""Gemini Live transport; Tk widgets are never accessed from this thread."""
import asyncio
import collections
import queue
import threading
import time
import numpy as np
import sounddevice as sd
from google import genai
from google.genai import types
from coaching import SYSTEM_PROMPT, TurnGate


class LiveEngine(threading.Thread):
    def __init__(self, key, model, voice, mic, speaker, events, pause=6, threshold=.018):
        super().__init__(daemon=True)
        self.key, self.model, self.voice = key, model, voice
        self.mic, self.speaker, self.events = mic, speaker, events
        self.commands = queue.Queue()
        self.audio_in = queue.Queue(maxsize=100)
        self.output = bytearray()
        self.lock = threading.Lock()
        self.gate = TurnGate(pause, threshold)
        self.muted = False
        self.hold = False
        self.stopping = threading.Event()
        self.generating = False
        self.suppress = False
        self.cooldown = 0.0
        self.pending = collections.deque(maxlen=10)
        self.overrun = False
        self.output_level = 0.0
        self.playback_until = 0.0

    def emit(self, kind, value=''):
        self.events.put((kind, value))

    def command(self, name, value=None):
        self.commands.put((name, value))

    def stop(self):
        self.stopping.set()
        self.output_level = 0.0
        self.playback_until = 0.0
        with self.lock:
            self.output.clear()

    def clear_output(self):
        self.output_level = 0.0
        self.playback_until = 0.0
        with self.lock:
            self.output.clear()

    def capture(self, data, frames, timing, status):
        if self.stopping.is_set() or self.muted:
            return
        try:
            self.audio_in.put_nowait(bytes(data))
        except queue.Full:
            self.overrun = True

    def playback(self, out, frames, timing, status):
        count = frames * 2
        with self.lock:
            part = bytes(self.output[:count])
            del self.output[:count]
        out[:] = part + b'\0' * (count - len(part))
        self.output_level = float(np.sqrt(np.mean(np.frombuffer(part, dtype='<i2').astype(float)**2))) / 32768 if part else 0.0
        if part:
            self.playback_until = time.monotonic() + frames / 24000 + .06
            self.cooldown = time.monotonic() + .5

    def run(self):
        try:
            asyncio.run(self.main())
        except Exception as exc:
            detail = str(exc).replace(self.key, '[redacted]')
            self.emit('error', detail[:600])
        finally:
            self.clear_output()
            self.emit('disconnected')

    async def main(self):
        client = genai.Client(api_key=self.key, http_options={'api_version': 'v1beta'})
        config = types.LiveConnectConfig(
            response_modalities=['AUDIO'], system_instruction=SYSTEM_PROMPT,
            input_audio_transcription={}, output_audio_transcription={},
            speech_config={'voice_config': {'prebuilt_voice_config': {'voice_name': self.voice}}},
            realtime_input_config={'automatic_activity_detection': {'disabled': True}},
            context_window_compression={'sliding_window': {}},
        )
        try:
            async with client.aio.live.connect(model=self.model, config=config) as session:
                self.session = session
                with sd.RawInputStream(samplerate=16000, channels=1, dtype='int16',
                                       blocksize=640, device=self.mic, callback=self.capture), \
                     sd.RawOutputStream(samplerate=24000, channels=1, dtype='int16',
                                        blocksize=960, device=self.speaker, callback=self.playback):
                    self.emit('connected')
                    tasks = [asyncio.create_task(self.send_loop()),
                             asyncio.create_task(self.receive_loop()),
                             asyncio.create_task(self.wait_stop())]
                    try:
                        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                        for task in done:
                            task.result()
                    finally:
                        for task in tasks:
                            task.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            await client.aio.aclose()

    async def wait_stop(self):
        while not self.stopping.is_set():
            await asyncio.sleep(.05)

    async def finish_turn(self):
        if self.gate.active:
            self.gate.reset()
            self.pending.clear()
            self.suppress = False
            await self.session.send_realtime_input(activity_end=types.ActivityEnd())
            self.generating = True
            self.emit('status', 'Reflecting')

    async def send_loop(self):
        while not self.stopping.is_set():
            while not self.commands.empty():
                name, value = self.commands.get_nowait()
                if name == 'mute':
                    self.muted = value
                    # Muting is privacy control: finish captured speech, then stop sending.
                    if value:
                        await self.finish_turn()
                    self.pending.clear()
                    while not self.audio_in.empty():
                        self.audio_in.get_nowait()
                    self.emit('status', 'Microphone muted' if value else 'Listening')
                elif name == 'hold':
                    self.hold = value
                elif name == 'finish':
                    await self.finish_turn()
                elif name == 'interrupt':
                    self.clear_output()
                    self.suppress = True
                    self.generating = False
                    self.cooldown = 0
                    if not self.gate.active:
                        await self.session.send_realtime_input(activity_start=types.ActivityStart())
                        self.gate.active = True
                        self.gate.last_voice = time.monotonic()
                    self.emit('status', 'Listening — your turn')
                elif name == 'text':
                    await self.finish_turn()
                    self.clear_output()
                    self.suppress = False
                    self.generating = True
                    await self.session.send_client_content(
                        turns={'role': 'user', 'parts': [{'text': value}]}, turn_complete=True)
                    self.emit('user_text', value)
                    self.emit('status', 'Reflecting')
            if self.overrun:
                raise RuntimeError('Audio input cannot keep up. Stop and reconnect; check your connection.')
            try:
                chunk = self.audio_in.get_nowait()
            except queue.Empty:
                await asyncio.sleep(.01)
                continue
            level = float(np.sqrt(np.mean(np.frombuffer(chunk, dtype='<i2').astype(float)**2))) / 32768
            self.emit('level', level)
            with self.lock:
                playing = bool(self.output)
            # Half-duplex avoids the coach hearing itself on laptop speakers.
            # A dedicated interrupt button transfers the floor immediately.
            if self.muted or self.generating or playing or time.monotonic() < self.cooldown:
                self.pending.clear()
                continue
            was_active = self.gate.active
            self.pending.append(chunk)
            action = self.gate.feed(level, time.monotonic(), self.hold)
            if action == 'start':
                self.suppress = False
                await self.session.send_realtime_input(activity_start=types.ActivityStart())
                for buffered in self.pending:
                    await self.send_audio(buffered)
                self.pending.clear()
                self.emit('status', 'Listening — take your time')
            elif action == 'end':
                self.suppress = False
                await self.send_audio(chunk)
                await self.session.send_realtime_input(activity_end=types.ActivityEnd())
                self.generating = True
                self.pending.clear()
                self.emit('status', 'Reflecting')
            elif was_active:
                await self.send_audio(chunk)
                self.pending.clear()

    async def send_audio(self, chunk):
        await self.session.send_realtime_input(audio=types.Blob(data=chunk, mime_type='audio/pcm;rate=16000'))

    async def receive_loop(self):
        while not self.stopping.is_set():
            async for message in self.session.receive():
                content = message.server_content
                if message.go_away:
                    self.emit('notice', 'The provider will close this connection shortly. Export your transcript, then start a new session.')
                if not content:
                    continue
                if content.interrupted:
                    self.clear_output()
                    self.generating = False
                    self.emit('boundary')
                    self.emit('notice', 'Coach interrupted; its transcript may include words not played.')
                if content.input_transcription and content.input_transcription.text:
                    self.emit('Coachee', content.input_transcription.text)
                if content.output_transcription and content.output_transcription.text and not self.suppress:
                    self.emit('Coach', content.output_transcription.text)
                if content.model_turn and not self.suppress:
                    for part in content.model_turn.parts or []:
                        if part.inline_data and part.inline_data.data:
                            self.generating = True
                            with self.lock:
                                if len(self.output) > 24000 * 2 * 120:
                                    raise RuntimeError('Playback buffer exceeded two minutes; reconnect.')
                                self.output.extend(part.inline_data.data)
                            self.emit('status', 'Speaking')
                if content.turn_complete:
                    self.generating = False
                    self.emit('boundary')
                    self.emit('status', 'Listening' if not self.muted else 'Microphone muted')
