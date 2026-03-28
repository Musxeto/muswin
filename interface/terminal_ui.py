"""Terminal presentation layer powered by rich."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from rich.console import Console
from rich.panel import Panel


class TerminalUI:
    """Rich-based CLI output helpers."""

    def __init__(self) -> None:
        self.console = Console()

    def clear(self) -> None:
        self.console.clear()

    def print_banner(self) -> None:
        banner = (
            "███╗   ███╗██╗   ██╗███████╗██╗    ██╗██╗███╗   ██╗\n"
            "████╗ ████║██║   ██║██╔════╝██║    ██║██║████╗  ██║\n"
            "██╔████╔██║██║   ██║███████╗██║ █╗ ██║██║██╔██╗ ██║\n"
            "██║╚██╔╝██║██║   ██║╚════██║██║███╗██║██║██║╚██╗██║\n"
            "██║ ╚═╝ ██║╚██████╔╝███████║╚███╔███╔╝██║██║ ╚████║\n"
            "╚═╝     ╚═╝ ╚═════╝ ╚══════╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝"
        )
        self.console.print(Panel.fit(banner, title="Muswin", border_style="bright_green"))

    def print_user(self, text: str) -> None:
        self.console.print(f"[cyan]You:[/cyan] {text}")

    def print_muswin(self, text: str) -> None:
        self.console.print(f"[bright_green]Muswin:[/bright_green] {text}")

    def print_warning(self, text: str) -> None:
        self.console.print(f"[yellow]Warning:[/yellow] {text}")

    def print_error(self, text: str) -> None:
        self.console.print(f"[red]Error:[/red] {text}")

    @contextmanager
    def show_thinking(self, message: str = "Muswin is judging your request...") -> Iterator[None]:
        with self.console.status(message, spinner="dots"):
            yield
