"""Audio pipeline: TTS, STT, and wake-word detection."""

from __future__ import annotations

import struct
import time
import importlib
from pathlib import Path

import pyttsx3
import speech_recognition as sr


class AudioEngine:
    """Provides speech output/input and optional wake word loop."""

    def __init__(self, picovoice_access_key: str = "", wake_model_path: str = "") -> None:
        self._tts = pyttsx3.init()
        self._configure_tts()

        self._recognizer = sr.Recognizer()
        self._picovoice_access_key = picovoice_access_key.strip()
        self._wake_model_path = wake_model_path.strip()

        self._porcupine = None
        self._pa = None
        self._audio_stream = None

    def _configure_tts(self) -> None:
        voices = self._tts.getProperty("voices") or []
        chosen_voice_id = None
        for voice in voices:
            voice_name = str(getattr(voice, "name", "")).lower()
            if "zira" in voice_name or "david" in voice_name:
                chosen_voice_id = getattr(voice, "id", None)
                break

        if chosen_voice_id:
            self._tts.setProperty("voice", chosen_voice_id)

        rate = int(self._tts.getProperty("rate") or 200)
        self._tts.setProperty("rate", max(120, rate - 25))

    def speak(self, text: str) -> None:
        if not text:
            return
        self._tts.say(text)
        self._tts.runAndWait()

    def listen_once(self, timeout: float = 6.0, phrase_time_limit: float = 12.0) -> str:
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            return self._recognizer.recognize_google(audio)
        except Exception:
            return ""

    def wake_word_ready(self) -> bool:
        return bool(self._picovoice_access_key and self._wake_model_path)

    def start_wake_word(self) -> bool:
        """Initialize Porcupine if config and dependencies are available."""

        if not self.wake_word_ready():
            return False

        model_path = Path(self._wake_model_path)
        if not model_path.exists():
            return False

        try:
            pvporcupine = importlib.import_module("pvporcupine")
            pyaudio = importlib.import_module("pyaudio")

            self._porcupine = pvporcupine.create(
                access_key=self._picovoice_access_key,
                keyword_paths=[str(model_path)],
            )
            self._pa = pyaudio.PyAudio()
            self._audio_stream = self._pa.open(
                rate=self._porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self._porcupine.frame_length,
            )
            return True
        except Exception:
            self.stop_wake_word()
            return False

    def stop_wake_word(self) -> None:
        if self._audio_stream is not None:
            try:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
            finally:
                self._audio_stream = None

        if self._pa is not None:
            try:
                self._pa.terminate()
            finally:
                self._pa = None

        if self._porcupine is not None:
            try:
                self._porcupine.delete()
            finally:
                self._porcupine = None

    def wait_for_wake_word(self, poll_sleep: float = 0.01) -> bool:
        """Block until wake word detected. Returns False if not initialized."""

        if not (self._porcupine and self._audio_stream):
            return False

        while True:
            pcm_bytes = self._audio_stream.read(self._porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm_bytes)
            detected_index = self._porcupine.process(pcm)
            if detected_index >= 0:
                return True
            time.sleep(poll_sleep)
