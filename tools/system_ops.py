"""Windows-oriented system actions for Muswin."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from config import get_settings


APP_MAP = {
    "vscode": r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "spotify": r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
    "notepad": "notepad.exe",
    "powershell": "powershell.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
}


def _resolve_app_path(app_name: str) -> str:
    key = app_name.strip().lower()
    raw_path = APP_MAP.get(key, app_name)
    return os.path.expandvars(raw_path)


def open_app(app_name: str) -> str:
    """Launch an application by mapped alias or provided path/command."""

    target = _resolve_app_path(app_name)
    try:
        if Path(target).exists() or target.lower().endswith(".exe"):
            subprocess.Popen([target], shell=False)
        else:
            subprocess.Popen(target, shell=True)
        return f"Opened {app_name}."
    except Exception as exc:  # noqa: BLE001
        return f"Could not open {app_name}: {exc}"


def clean_directory(path: str) -> str:
    """Sort files in a directory into category subfolders."""

    base = Path(path).expanduser().resolve()
    if not base.exists() or not base.is_dir():
        return f"Directory not found: {base}"

    categories = {
        "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"},
        "Installers": {".exe", ".msi", ".msix", ".msixbundle"},
        "Documents": {".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx"},
        "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
        "Code": {".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs"},
    }

    moved_count = 0
    for item in base.iterdir():
        if not item.is_file():
            continue

        suffix = item.suffix.lower()
        target_folder_name = "Other"
        for folder, extensions in categories.items():
            if suffix in extensions:
                target_folder_name = folder
                break

        target_folder = base / target_folder_name
        target_folder.mkdir(parents=True, exist_ok=True)

        destination = target_folder / item.name
        if destination.exists():
            stem = item.stem
            ext = item.suffix
            counter = 1
            while destination.exists():
                destination = target_folder / f"{stem}_{counter}{ext}"
                counter += 1

        shutil.move(str(item), str(destination))
        moved_count += 1

    return f"Cleaned {base}. Moved {moved_count} files."


def trigger_routine(routine_name: str) -> str:
    """Run named action bundles."""

    routine = routine_name.strip().lower()

    if routine == "coding_mode":
        steps: list[str] = []
        steps.append(open_app("vscode"))

        settings = get_settings()
        if settings.spotify_client_id:
            steps.append(open_app("spotify"))
        else:
            steps.append("Spotify key missing; skipped Spotify step.")

        return " | ".join(steps)

    if routine == "focus_mode":
        return open_app("notepad")

    return f"Unknown routine: {routine_name}"
