# MUSWIN

Terminal-first, voice-capable Windows assistant with a sarcastic persona.

## Architecture

- `main.py` central loop.
- `config.py` env-backed key and model config.
- `brain/gemini_core.py` persona + session memory + function-call routing.
- `interface/terminal_ui.py` rich UI (banner, colors, spinner).
- `interface/audio_engine.py` free-library TTS and STT.
- `tools/system_ops.py` app launching, folder cleaning, routines.
- `tools/researcher.py` web research and markdown report generation.
- `tools/detective.py` OSINT-style public footprint lookup.
- `start_muswin.bat` startup launcher for Windows.

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
- optional: `SPOTIFY_CLIENT_ID`
- optional: `GEMINI_MODEL_NAME` (default: `gemini-3.1-pro-preview`)
- optional: `GEMINI_TTS_MODEL_NAME` (default: `gemini-2.5-flash-preview-tts`)

## Run

```powershell
python main.py
```

Type your command directly, or use `/voice` to capture one microphone utterance.

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

## Windows Startup Integration

1. Keep `start_muswin.bat` in the project root.
2. Open Task Scheduler.
3. Create Basic Task -> name it `Muswin Startup`.
4. Trigger: `When I log on`.
5. Action: `Start a program` -> browse to `start_muswin.bat`.
6. In task Properties, enable `Run whether user is logged on or not` if desired and set it to hidden/background behavior.

## Notes

- If `GEMINI_API_KEY` is missing, `config.py` raises a clear startup error.
- Tool calls are declared in Gemini core and routed to concrete handlers in `tools/`.
- This project uses `google.genai` (new SDK), not the deprecated `google.generativeai` package.
