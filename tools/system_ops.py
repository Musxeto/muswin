"""Windows-oriented system actions for Muswin."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import importlib
from datetime import datetime
from pathlib import Path

from config import get_settings


APP_MAP = {
    "vscode": r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "spotify": r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
    "notepad": "notepad.exe",
    "powershell": "powershell.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
}

COMMAND_FALLBACKS = {
    "vscode": "code",
    "spotify": "spotify",
    "chrome": "chrome",
}


def _resolve_app_path(app_name: str) -> str:
    key = app_name.strip().lower()
    raw_path = APP_MAP.get(key, app_name)
    return os.path.expandvars(raw_path)


def open_app(app_name: str) -> str:
    """Launch an application by mapped alias or provided path/command."""

    key = app_name.strip().lower()
    target = _resolve_app_path(app_name)
    try:
        if Path(target).exists():
            subprocess.Popen([target], shell=False)
        elif target.lower().endswith(".exe") and key in COMMAND_FALLBACKS:
            subprocess.Popen(COMMAND_FALLBACKS[key], shell=True)
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


def list_directory(path: str, limit: int = 60) -> str:
    """List files/folders in a directory with simple type labels."""

    base = Path(path).expanduser().resolve()
    if not base.exists() or not base.is_dir():
        return f"Directory not found: {base}"

    rows: list[str] = []
    items = sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    for item in items[: max(1, limit)]:
        kind = "DIR" if item.is_dir() else "FILE"
        rows.append(f"[{kind}] {item.name}")

    total = len(items)
    visible = len(rows)
    header = f"Contents of {base} ({visible}/{total} shown):"
    if not rows:
        return f"{header}\n(empty)"

    suffix = ""
    if total > visible:
        suffix = "\n... (truncated)"

    return header + "\n" + "\n".join(rows) + suffix


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


def open_folder(path: str) -> str:
    folder = Path(path).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        return f"Directory not found: {folder}"
    try:
        os.startfile(str(folder))
        return f"Opened folder: {folder}"
    except Exception as exc:  # noqa: BLE001
        return f"Failed to open folder: {exc}"


def create_directory(path: str) -> str:
    folder = Path(path).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    return f"Directory ready: {folder}"


def move_path(source: str, destination: str) -> str:
    src = Path(source).expanduser().resolve()
    dst = Path(destination).expanduser().resolve()
    if not src.exists():
        return f"Source not found: {src}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return f"Moved {src} -> {dst}"


def copy_path(source: str, destination: str) -> str:
    src = Path(source).expanduser().resolve()
    dst = Path(destination).expanduser().resolve()
    if not src.exists():
        return f"Source not found: {src}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)
    return f"Copied {src} -> {dst}"


def delete_path(path: str, force: bool = False) -> str:
    target = Path(path).expanduser().resolve()
    if not target.exists():
        return f"Path not found: {target}"
    if not force:
        return "Refused delete. Pass force=true to confirm destructive action."

    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    return f"Deleted: {target}"


def run_shell_command(command: str) -> str:
    """Run a shell command and return concise output."""

    try:
        completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = (completed.stdout or completed.stderr or "").strip()
        if not output:
            output = "(no output)"
        return f"Exit {completed.returncode}: {output[:3000]}"
    except Exception as exc:  # noqa: BLE001
        return f"Command failed: {exc}"


def list_processes(limit: int = 30) -> str:
    try:
        command = (
            'powershell -NoProfile -Command "Get-Process | '
            'Sort-Object CPU -Descending | Select-Object -First '
            f'{max(1, limit)} Name,Id,CPU | Format-Table -AutoSize | Out-String"'
        )
        return run_shell_command(command)
    except Exception as exc:  # noqa: BLE001
        return f"Failed to list processes: {exc}"


def kill_process(identifier: str) -> str:
    ident = identifier.strip()
    if not ident:
        return "No process identifier provided."

    if ident.isdigit():
        cmd = f"taskkill /PID {ident} /F"
    else:
        cmd = f"taskkill /IM {ident} /F"

    return run_shell_command(cmd)


def get_system_info() -> str:
    psutil = importlib.import_module("psutil")
    now = datetime.now().isoformat(timespec="seconds")
    os_name = f"{platform.system()} {platform.release()}"
    cpu_name = platform.processor() or "Unknown CPU"
    ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    used_gb = round(psutil.virtual_memory().used / (1024**3), 2)
    disks = []
    for part in psutil.disk_partitions(all=False):
        if not part.mountpoint:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append(
                f"{part.device} {round(usage.used/(1024**3),1)}GB/{round(usage.total/(1024**3),1)}GB"
            )
        except Exception:  # noqa: BLE001
            continue

    disk_line = "; ".join(disks[:4]) if disks else "Unavailable"
    return (
        f"Timestamp: {now}\n"
        f"OS: {os_name}\n"
        f"CPU: {cpu_name}\n"
        f"RAM: {used_gb}GB / {ram_gb}GB\n"
        f"Disks: {disk_line}"
    )
