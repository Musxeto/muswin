# MUSWIN

Terminal-first, voice-capable Windows assistant with a sarcastic persona.

## Implemented Foundation (Current)

- `config.py` for environment-backed settings.
- `brain/gemini_core.py` for Gemini initialization, system persona, chat memory, and tool-call routing.
- `.env` as the active local secrets/config file.

## Prerequisites

- Windows 11
- Python 3.10+
- A virtual environment (already present in this repo)
- Gemini API key

## Setup

1. Activate the virtual environment:

```powershell
.\.venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Fill values in `.env`:

- required: `GEMINI_API_KEY`
- optional now: `PICOVOICE_ACCESS_KEY`, `SPOTIFY_CLIENT_ID`
- optional: `GEMINI_MODEL_NAME` (default: `gemini-3.1-pro-preview`)
- optional: `GEMINI_TTS_MODEL_NAME` (default: `gemini-2.5-flash-preview-tts`)

## Quick Sanity Check

Run this one-liner to verify initialization and one response path:

```powershell
python -c "from brain import GeminiCore; core=GeminiCore(); print(core.process_user_input('Say hi in one sentence.'))"
```

To verify memory continuity, run in Python REPL:

```python
from brain import GeminiCore
core = GeminiCore()
print(core.process_user_input("My codename is Ghost."))
print(core.process_user_input("What codename did I just tell you?"))
```

## Notes

- If `GEMINI_API_KEY` is missing, `config.py` raises a clear startup error.
- Tool calls are declared in Gemini core, but handlers are intentionally fallback-safe until the `tools/` modules are implemented.
