"""Kickstart application registration and root command entrypoints."""

from typing import Optional

import typer
from rich import print

from src import __version__
from src.cli.create import CREATE_EPILOG, create
from src.cli.drift import drift
from src.cli.exports import export_app
from src.cli.inspection import adopt, plan
from src.cli.installation import install, uninstall
from src.cli.migrate import migrate
from src.cli.telemetry import telemetry_app
from src.cli.updates import managed_layout_handoff, upgrade
from src.utils.handoff import HANDOFF_COMMAND


app: typer.Typer = typer.Typer(help="kickstart: Full-stack project scaffolding CLI")
app.add_typer(telemetry_app, name="telemetry")
app.command()(migrate)
app.command()(drift)


def _print_version_and_exit(value: bool) -> None:
    if value:
        print(f"[bold cyan]kickstart v{__version__}[/]")
        raise typer.Exit()


@app.callback()
def _root_options(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=_print_version_and_exit,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """kickstart: Full-stack project scaffolding CLI."""


@app.command()
def version() -> None:
    """Show the current version."""
    print(f"[bold cyan]kickstart v{__version__}[/]")


app.command()(upgrade)
app.command(HANDOFF_COMMAND, hidden=True)(managed_layout_handoff)
app.add_typer(export_app, name="export")
app.command()(plan)
app.command()(adopt)
app.command()(install)
app.command()(uninstall)


@app.command()
def completion(shell: str = typer.Argument(..., help="bash | zsh | fish | powershell")) -> None:
    """Generate shell completion script."""
    typer.echo("Completion not implemented")


app.command(epilog=CREATE_EPILOG)(create)


def main() -> None:
    """Run the Typer application when executed as a script."""
    app(prog_name="kickstart")


if __name__ == "__main__":
    main()
