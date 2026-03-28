"""Configuration loader for Muswin.

Loads required secrets from environment variables or a local .env file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when required configuration values are missing."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings for Muswin services."""

    gemini_api_key: str
    picovoice_access_key: str
    spotify_client_id: str
    gemini_model_name: str = "gemini-3.1-pro-preview"
    gemini_tts_model_name: str = "gemini-2.5-flash-preview-tts"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and validate settings from environment variables.

    Returns:
        Settings: Immutable settings object.

    Raises:
        ConfigError: If one or more required keys are missing.
    """

    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path, override=False)

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    picovoice_access_key = os.getenv("PICOVOICE_ACCESS_KEY", "").strip()
    spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    gemini_model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-pro-preview").strip()
    gemini_tts_model_name = os.getenv(
        "GEMINI_TTS_MODEL_NAME", "gemini-2.5-flash-preview-tts"
    ).strip()

    missing: list[str] = []
    if not gemini_api_key:
        missing.append("GEMINI_API_KEY")

    if missing:
        missing_csv = ", ".join(missing)
        raise ConfigError(
            f"Missing required environment variables: {missing_csv}. "
            "Set them in your shell or in a local .env file."
        )

    return Settings(
        gemini_api_key=gemini_api_key,
        picovoice_access_key=picovoice_access_key,
        spotify_client_id=spotify_client_id,
        gemini_model_name=gemini_model_name or "gemini-3.1-pro-preview",
        gemini_tts_model_name=gemini_tts_model_name or "gemini-2.5-flash-preview-tts",
    )
