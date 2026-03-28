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
    _ = get_settings()
    ui = TerminalUI()
    audio = AudioEngine()
    core = GeminiCore(tool_handlers=_build_tool_handlers())

    ui.clear()
    ui.print_banner()
    ui.print_muswin("Boot complete. Type /voice for microphone input or type normally.")

    while True:
        user_text = input("You: ").strip()
        if user_text.lower() in {"exit", "quit"}:
            break

        if user_text.lower() == "/voice":
            ui.print_muswin("Speak now.")
            user_text = audio.listen_once()

        if not user_text:
            ui.print_warning("No input captured.")
            continue

        ui.print_user(user_text)
        with ui.show_thinking():
            reply = core.process_user_input(user_text)

        ui.print_muswin(reply)
        audio.speak(reply)


if __name__ == "__main__":
    run()
