"""Human and JSON output for bounded persisted-ownership planning."""

from pathlib import Path
import typer
from rich import print
from rich.markup import escape

from src.generator.ownership_check import inspect_ownership
from src.utils.errors import OwnershipPlanTargetError


def ownership_plan(path: Path, json_output: bool) -> None:
    try:
        report = inspect_ownership(path)
    except OwnershipPlanTargetError as error:
        print(f"[red]{escape(str(error))}[/]")
        raise typer.Exit(code=2) from error
    if json_output:
        typer.echo(report.to_json(), nl=False)
    else:
        print(f"Ownership plan for {escape(str(report.root))}")
        if not report.recorded:
            print("Ownership is unrecorded; current files were not classified.")
        for entry in report.entries:
            print(f"  {escape(entry.status)}  {escape(entry.target)} ({escape(entry.detail)})")
            if entry.diff:
                typer.echo(entry.diff, nl=False)
        print(f"Generated-once seeds excluded: {report.seeds_excluded}")
    raise typer.Exit(code=0 if report.in_sync else 1)
