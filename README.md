# MUSWIN

Terminal-first, voice-capable Windows assistant with a sarcastic persona.

## Implemented Foundation (Current)

- `config.py` for environment-backed settings.
- `brain/gemini_core.py` for Gemini initialization, system persona, chat memory, and tool-call routing.
- `.env.example` with required key names.

## Prerequisites

- Windows 11
- Python 3.10+
- A virtual environment (already present in this repo)
- Gemini API key

## Setup

1. Activate the virtual environment:

```powershell
.\venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install google-generativeai python-dotenv
```

3. Create your environment file:

```powershell
Copy-Item .env.example .env
```

4. Fill values in `.env`:

- `GEMINI_API_KEY`
- `PICOVOICE_ACCESS_KEY`
- `SPOTIFY_CLIENT_ID`
- optional: `GEMINI_MODEL_NAME`

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

- If any required keys are missing, `config.py` raises a clear startup error.
- Tool calls are declared in Gemini core, but handlers are intentionally fallback-safe until the `tools/` modules are implemented.
