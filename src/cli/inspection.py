"""Read-only documentation and repository adoption commands."""

from pathlib import Path

import typer
from rich import print
from rich.markup import escape

from src.cli.drift import print_drift
from src.cli.ownership import ownership_plan
from src.generator.adoption import AdoptionTargetError, inspect_repo
from src.generator.docs_plan import DocsPlanTargetError, inspect_docs
from src.utils.errors import DriftTargetError


def plan(
    path: Path = typer.Argument(Path("."), help="Repository to inspect"),
    ownership: bool = typer.Option(False, "--ownership", help="Inspect only the persisted ownership index"),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable report"),
) -> None:
    """Show how managed docs differ from the standard's render (read-only).

    Compares each fenced managed doc against what the current standard would
    render from `.kickstart/scaffold.json`. `--ownership` instead checks the
    persisted regions and structural facts, excluding generated-once seeds.
    Exit codes: 0 = in sync, 1 = drift
    or structural findings, 2 = usage error (no repo or no plannable manifest).
    """
    if ownership:
        ownership_plan(path, json_output)
        return
    try:
        report = inspect_docs(path)
    except DocsPlanTargetError as error:
        print(f"[red]{escape(str(error))}[/]")
        raise typer.Exit(code=2) from error

    if json_output:
        # Machine-readable output must bypass rich: console printing wraps
        # long lines and interprets bracketed path segments as markup, both
        # of which corrupt the JSON.
        typer.echo(report.to_json(), nl=False)
    else:
        print(f"[bold]Docs plan for {escape(str(report.root))}[/]")
        for entry in report.entries:
            if entry.ok:
                suffix = f" (profile: {escape(entry.profile)})" if entry.profile else ""
                print(f"  [green]{entry.status}[/]  {escape(entry.target)}{suffix}")
            else:
                print(f"  [red]{entry.status}[/]  {escape(entry.target)} ({escape(entry.detail)})")
                if entry.diff:
                    typer.echo(entry.diff, nl=False)

    raise typer.Exit(code=0 if report.in_sync else 1)


def adopt(
    path: Path = typer.Argument(Path("."), help="Existing repository to inspect"),
    check: bool = typer.Option(False, "--check", help="Report standard-artifact status without writing"),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable report"),
) -> None:
    """Check standard artifacts and recorded scaffold drift without writing.

    Exit codes: 0 = repo matches the standard, 1 = gaps found, 2 = usage error.
    """
    if not check:
        print("[red]kickstart adopt only supports --check for now; writing is a future, explicit step.[/]")
        raise typer.Exit(code=2)

    try:
        report = inspect_repo(path)
    except (AdoptionTargetError, DriftTargetError) as error:
        print(f"[red]{escape(str(error))}[/]")
        raise typer.Exit(code=2) from error

    if json_output:
        # Machine-readable output must bypass rich: console printing wraps
        # long lines and interprets bracketed path segments as markup, both
        # of which corrupt the JSON.
        typer.echo(report.to_json(), nl=False)
    else:
        print(f"[bold]Adoption check for {escape(str(report.root))}[/]")
        level_color = "green" if report.complete else "red"
        print(
            f"  [{level_color}]level[/]   achieved: {escape(report.achieved_level)} / "
            f"claimed: {escape(report.claimed_level)}"
        )
        for status in report.artifacts:
            if status.ok:
                print(f"  [green]ok[/]      {escape(status.path)}")
            else:
                print(f"  [red]needed[/]  {escape(status.path)} ({escape(status.issue)})")

        if report.drift is not None:
            print_drift(report.drift)

    raise typer.Exit(code=0 if report.complete else 1)
