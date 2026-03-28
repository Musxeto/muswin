"""Audio pipeline: free-library TTS and STT."""

from __future__ import annotations

import threading

import pyttsx3
import speech_recognition as sr


class AudioEngine:
    """Provides speech output/input without external wake-word services."""

    def __init__(self, mic_device_index: int | None = None) -> None:
        self._tts = self._init_tts_engine()
        self._configure_tts()
        self._tts_lock = threading.Lock()
        self._is_speaking = False
        self._tts_available = self._tts is not None
        self._last_tts_error = ""

        self._recognizer = sr.Recognizer()
        self._recognizer.dynamic_energy_threshold = True
        self._mic_device_index = mic_device_index
        self._last_error = ""

    def _init_tts_engine(self):
        try:
            return pyttsx3.init(driverName="sapi5")
        except Exception:
            try:
                return pyttsx3.init()
            except Exception:
                return None

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def tts_available(self) -> bool:
        return self._tts_available

    @property
    def last_tts_error(self) -> str:
        return self._last_tts_error

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    @staticmethod
    def list_microphones() -> list[str]:
        try:
            return sr.Microphone.list_microphone_names()
        except Exception:
            return []

    def _configure_tts(self) -> None:
        if self._tts is None:
            return

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
        self._tts.setProperty("volume", 1.0)

    def speak(self, text: str) -> None:
        if not text:
            return
        if self._tts is None:
            self._tts_available = False
            self._last_tts_error = "TTS engine is unavailable on this machine."
            return

        with self._tts_lock:
            self._is_speaking = True
            try:
                self._tts.say(text)
                self._tts.runAndWait()
                self._tts_available = True
                self._last_tts_error = ""
            except Exception as exc:  # noqa: BLE001
                self._tts_available = False
                self._last_tts_error = f"TTS playback failed: {exc}"
            finally:
                self._is_speaking = False

    def listen_once(
        self,
        timeout: float = 6.0,
        phrase_time_limit: float = 12.0,
        adjust_noise: bool = True,
        ambient_duration: float = 1.0,
    ) -> str:
        self._last_error = ""
        try:
            with sr.Microphone(device_index=self._mic_device_index) as source:
                if adjust_noise:
                    self._recognizer.adjust_for_ambient_noise(source, duration=ambient_duration)
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            return self._recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            self._last_error = "Timed out waiting for speech. Try speaking immediately after /voice."
            return ""
        except sr.UnknownValueError:
            self._last_error = "Heard audio but could not understand it."
            return ""
        except sr.RequestError:
            self._last_error = "Speech service unavailable. Check internet connection."
            return ""
        except OSError as exc:
            self._last_error = f"Microphone error: {exc}"
            return ""
        except Exception:
            self._last_error = "Voice capture failed unexpectedly."
            return ""
