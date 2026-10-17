"""Standalone scaffold drift command and the adoption report's shared renderer."""

from pathlib import Path

from rich import print
from rich.markup import escape
import typer

from src.generator.drift import DriftReport, inspect_drift
from src.utils.errors import DriftTargetError


def print_drift(report: DriftReport) -> None:
    print(f"Drift check for {escape(str(report.root))}")
    if not report.recorded:
        print("Ownership is unrecorded; drift coverage is unavailable.")
    for entry in report.entries:
        color = "green" if entry.ok else "red"
        print(f"  [{color}]{entry.status}[/] {escape(entry.artifact_class)}: {escape(entry.target)}")
        if entry.detail:
            print(f"    {escape(entry.detail)}")
        if entry.diff:
            typer.echo(entry.diff, nl=False)
    print(f"Generated-once seeds excluded: {report.seeds_excluded}")


def drift(
    path: Path = typer.Argument(Path("."), help="Repository to inspect"),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable report"),
) -> None:
    """Check recorded scaffold ownership without writing. Exit 0 = clean, 1 = findings or unavailable coverage, 2 = usage error."""
    try:
        report = inspect_drift(path)
    except DriftTargetError as error:
        print(f"[red]{escape(str(error))}[/]")
        raise typer.Exit(code=2) from error
    if json_output:
        typer.echo(report.to_json(), nl=False)
    else:
        print_drift(report)
    raise typer.Exit(code=0 if report.in_sync else 1)
