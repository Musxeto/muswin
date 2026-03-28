"""Muswin main loop: UI, input handling, AI routing, and action execution."""

from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
from typing import Callable

from brain import GeminiCore
from config import get_settings
from interface import AudioEngine, MicOverlay, TerminalUI
from tools import (
    clean_directory,
    copy_path,
    create_directory,
    delete_path,
    get_system_info,
    kill_process,
    list_directory,
    list_processes,
    move_path,
    open_app,
    open_folder,
    osint_lookup,
    run_shell_command,
    search_web,
    trigger_routine,
)


def _build_tool_handlers() -> dict[str, Callable[..., str]]:
    return {
        "open_app": open_app,
        "open_folder": open_folder,
        "clean_directory": clean_directory,
        "list_directory": list_directory,
        "create_directory": create_directory,
        "move_path": move_path,
        "copy_path": copy_path,
        "delete_path": delete_path,
        "run_shell_command": run_shell_command,
        "list_processes": list_processes,
        "kill_process": kill_process,
        "get_system_info": get_system_info,
        "search_web": search_web,
        "trigger_routine": trigger_routine,
        "osint_lookup": osint_lookup,
    }


def _handle_local_intent(text: str) -> str | None:
    lowered = text.lower().strip()
    desktop = str(Path.home() / "Desktop")
    downloads = str(Path.home() / "Downloads")
    documents = str(Path.home() / "Documents")

    if lowered.startswith("open folder "):
        target = text[len("open folder ") :].strip()
        if target:
            return open_folder(target)

    desktop_signals = [
        "desktop",
        "what are the things on my desktop",
        "what's on my desktop",
        "whats on my desktop",
        "list my desktop",
        "show desktop files",
    ]

    if any(sig in lowered for sig in desktop_signals):
        return list_directory(desktop)

    if "downloads" in lowered and ("list" in lowered or "show" in lowered):
        return list_directory(downloads)

    if "documents" in lowered and ("list" in lowered or "show" in lowered):
        return list_directory(documents)

    if "clean downloads" in lowered or "organize downloads" in lowered:
        return clean_directory(downloads)

    if "system info" in lowered:
        return get_system_info()

    if lowered.startswith("open "):
        app_name = lowered.replace("open ", "", 1).strip()
        if app_name:
            return open_app(app_name)

    return None


def run() -> None:
    settings = get_settings()
    ui = TerminalUI()
    audio = AudioEngine(mic_device_index=settings.mic_device_index)
    overlay = MicOverlay()
    core = GeminiCore(tool_handlers=_build_tool_handlers())
    input_queue: queue.Queue[tuple[str, str]] = queue.Queue()
    stop_event = threading.Event()

    def text_input_worker() -> None:
        while not stop_event.is_set():
            try:
                text = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                input_queue.put(("text", "exit"))
                return
            input_queue.put(("text", text))

    def voice_input_worker() -> None:
        while not stop_event.is_set():
            if audio.is_speaking:
                time.sleep(0.2)
                continue

            overlay.set_state("listening", "Listening...")
            spoken = audio.listen_once(
                timeout=1.8,
                phrase_time_limit=8.0,
                adjust_noise=False,
            ).strip()
            if spoken:
                input_queue.put(("voice", spoken))

    overlay.start()
    overlay.set_state("listening", "Listening...")

    text_thread = threading.Thread(target=text_input_worker, daemon=True)
    voice_thread = threading.Thread(target=voice_input_worker, daemon=True)
    text_thread.start()
    voice_thread.start()

    ui.clear()
    ui.print_banner()
    ui.print_muswin("Boot complete. Voice is always on. Type anytime, or say commands.")

    if not audio.tts_available:
        ui.print_warning("TTS unavailable at startup. Check audio engine/voice driver.")

    while not stop_event.is_set():
        try:
            source, user_text = input_queue.get(timeout=0.25)
        except queue.Empty:
            continue

        user_text = user_text.strip()
        if user_text.lower() in {"exit", "quit"}:
            stop_event.set()
            break

        if user_text.lower() == "/voice":
            ui.print_muswin("Voice is already on in background.")
            continue

        if user_text.lower() == "/mics":
            microphones = audio.list_microphones()
            if not microphones:
                ui.print_warning("No microphones detected.")
                continue

            for index, name in enumerate(microphones):
                ui.print_muswin(f"Mic {index}: {name}")
            continue

        if not user_text:
            if source == "text":
                if audio.last_error:
                    ui.print_warning(f"No input captured. {audio.last_error}")
                else:
                    ui.print_warning("No input captured.")
            continue

        if source == "voice":
            ui.print_user(f"(voice) {user_text}")

        local_result = _handle_local_intent(user_text)
        if local_result is not None:
            overlay.set_state("speaking", "Speaking local result")
            ui.print_muswin(local_result)
            audio.speak(local_result)
            if audio.last_tts_error:
                ui.print_warning(audio.last_tts_error)
            overlay.set_state("listening", "Listening...")
            continue

        overlay.set_state("transcribing", "Thinking...")
        with ui.show_thinking():
            reply = core.process_user_input(user_text)

        overlay.set_state("speaking", "Speaking reply")
        ui.print_muswin(reply)
        audio.speak(reply)
        if audio.last_tts_error:
            ui.print_warning(audio.last_tts_error)
        overlay.set_state("listening", "Listening...")

    stop_event.set()
    overlay.stop()


if __name__ == "__main__":
    run()
