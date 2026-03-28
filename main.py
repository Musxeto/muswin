"""Muswin main loop: UI, input handling, AI routing, and action execution."""

from __future__ import annotations

from typing import Callable

from brain import GeminiCore
from config import get_settings
from interface import AudioEngine, TerminalUI
from tools import clean_directory, open_app, osint_lookup, search_web, trigger_routine


def _build_tool_handlers() -> dict[str, Callable[..., str]]:
    return {
        "open_app": open_app,
        "clean_directory": clean_directory,
        "search_web": search_web,
        "trigger_routine": trigger_routine,
        "osint_lookup": osint_lookup,
    }


def run() -> None:
    settings = get_settings()
    ui = TerminalUI()
    audio = AudioEngine(
        picovoice_access_key=settings.picovoice_access_key,
        wake_model_path=settings.wake_word_model_path,
    )
    core = GeminiCore(tool_handlers=_build_tool_handlers())

    ui.clear()
    ui.print_banner()
    ui.print_muswin("Boot complete. Try not to waste my cycles.")

    wake_ready = audio.start_wake_word()
    if not wake_ready:
        ui.print_warning(
            "Wake word is disabled (missing PICOVOICE_ACCESS_KEY or WAKE_WORD_MODEL_PATH). "
            "Text mode and push-to-talk still work."
        )

    try:
        while True:
            # Wake-word path: user can press Enter to start a wake-word listen cycle.
            if wake_ready:
                cmd = input("Press Enter for wake-listen, type message, or 'exit': ").strip()
                if cmd.lower() in {"exit", "quit"}:
                    break

                if not cmd:
                    ui.print_muswin("Listening for wake word...")
                    if audio.wait_for_wake_word():
                        ui.print_muswin("Wake word detected. Say the command.")
                        user_text = audio.listen_once()
                    else:
                        user_text = ""
                else:
                    user_text = cmd
            else:
                user_text = input("You: ").strip()
                if user_text.lower() in {"exit", "quit"}:
                    break

            if not user_text:
                ui.print_warning("No input captured.")
                continue

            ui.print_user(user_text)
            with ui.show_thinking():
                reply = core.process_user_input(user_text)

            ui.print_muswin(reply)
            audio.speak(reply)
    finally:
        audio.stop_wake_word()


if __name__ == "__main__":
    run()
