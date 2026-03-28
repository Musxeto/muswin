"""Audio pipeline: free-library TTS and STT."""

from __future__ import annotations

import pyttsx3
import speech_recognition as sr


class AudioEngine:
    """Provides speech output/input without external wake-word services."""

    def __init__(self) -> None:
        self._tts = pyttsx3.init()
        self._configure_tts()

        self._recognizer = sr.Recognizer()

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
