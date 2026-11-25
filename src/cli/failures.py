"""Shared CLI exits for failures that end a command."""

from typing import NoReturn

import typer
from rich import print
from rich.markup import escape


def exit_with_error(error: Exception, code: int) -> NoReturn:
    """Print `error` in red and exit with `code`, chaining the original exception."""
    print(f"[red]{escape(str(error))}[/]")
    raise typer.Exit(code=code) from error
