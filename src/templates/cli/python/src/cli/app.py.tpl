from __future__ import annotations

from typing import Annotated

import typer

from src import __version__
from src.cli.commands.check import check_command

app = typer.Typer(
    add_completion=False,
    help="{{ service_name }} command line interface.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{{ package_name }} {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            help="Print version information.",
            is_eager=True,
        ),
    ] = False,
) -> None:
    _ = version


app.command("check", help="Run a scaffold smoke check.")(check_command)
