"""Simple utilities for rich colored console logging."""

from typing import Protocol

from rich import print


class Logger(Protocol):
    """Protocol describing a basic logger interface."""

    def info(self, msg: str) -> None:
        """Log an informational message."""
        ...

    def success(self, msg: str) -> None:
        """Log a success message."""
        ...

    def warn(self, msg: str) -> None:
        """Log a warning message."""
        ...

    def error(self, msg: str) -> None:
        """Log an error message."""
        ...


def info(msg: str) -> None:
    """Display an informational message."""
    print(f"[cyan]➤ {msg}")


def success(msg: str) -> None:
    """Display a success message."""
    print(f"[green]✔ {msg}")


def warn(msg: str) -> None:
    """Display a warning message."""
    print(f"[yellow]⚠ {msg}")


def error(msg: str) -> None:
    """Display an error message."""
    print(f"[red]✖ {msg}")


__all__ = ["Logger", "info", "success", "warn", "error"]
