"""Small always-on-top microphone status window."""

from __future__ import annotations

import threading
import tkinter as tk


class MicOverlay:
    """Animated mic indicator window running in its own UI thread."""

    def __init__(self) -> None:
        self._state = "idle"
        self._status = "Idle"
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        self._root: tk.Tk | None = None
        self._canvas: tk.Canvas | None = None
        self._status_label: tk.Label | None = None
        self._tick = 0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._ui_main, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._root is not None:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass

    def set_state(self, state: str, status: str | None = None) -> None:
        with self._lock:
            self._state = state
            if status is not None:
                self._status = status

    def _ui_main(self) -> None:
        self._root = tk.Tk()
        self._root.title("Muswin Mic")
        self._root.geometry("300x140+30+30")
        self._root.attributes("-topmost", True)
        self._root.resizable(False, False)

        frame = tk.Frame(self._root, bg="#111111")
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text="MUSWIN MIC", fg="#59ff8a", bg="#111111", font=("Consolas", 12, "bold"))
        title.pack(pady=(8, 4))

        self._canvas = tk.Canvas(frame, width=260, height=52, bg="#111111", highlightthickness=0)
        self._canvas.pack()

        self._status_label = tk.Label(
            frame,
            text="Idle",
            fg="#d0d0d0",
            bg="#111111",
            font=("Consolas", 10),
        )
        self._status_label.pack(pady=(4, 8))

        self._animate()
        self._root.protocol("WM_DELETE_WINDOW", self.stop)
        self._root.mainloop()

    def _animate(self) -> None:
        if not self._running or self._root is None or self._canvas is None:
            return

        self._canvas.delete("all")
        with self._lock:
            state = self._state
            status = self._status

        if self._status_label is not None:
            self._status_label.config(text=status)

        colors = {
            "idle": "#808080",
            "listening": "#00d4ff",
            "transcribing": "#ffcc00",
            "speaking": "#59ff8a",
            "error": "#ff4d4d",
        }
        color = colors.get(state, "#808080")

        base_x = 20
        spacing = 20
        self._tick = (self._tick + 1) % 8

        for i in range(10):
            pulse = ((i + self._tick) % 8)
            height = 12 + (pulse * 4 if state in {"listening", "speaking", "transcribing"} else 0)
            x1 = base_x + i * spacing
            y1 = 44 - height
            x2 = x1 + 10
            y2 = 44
            self._canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        self._root.after(120, self._animate)
