"""Explicit scaffold manifest migration command."""

from pathlib import Path
import typer
from rich import print
from rich.markup import escape

from src.generator.manifest_migration import apply_migration, plan_migration
from src.utils.errors import ManifestMigrationError


def migrate(
    path: Path = typer.Argument(Path("."), help="Repository whose scaffold manifest should migrate"),
    apply: bool = typer.Option(False, "--apply", help="Apply a fully resolved manifest plan"),
    language: str | None = typer.Option(None, "--language", help="Resolve missing recorded project language"),
    framework: str | None = typer.Option(None, "--framework", help="Resolve missing recorded framework"),
    expected_sha256: str | None = typer.Option(
        None, "--expected-sha256", help="Require the source hash from a reviewed plan"
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit the plan, diagnostics and action as JSON"),
) -> None:
    """Plan migration to schema 4.0; write only the manifest with --apply."""
    try:
        plan = plan_migration(path, language=language, framework=framework)
        action = apply_migration(plan, expected_sha256=expected_sha256) if apply and plan.ready else "planned"
    except ManifestMigrationError as error:
        print(f"[red]{escape(str(error))}[/]")
        raise typer.Exit(code=2) from error
    if json_output:
        typer.echo(plan.to_json(action), nl=False)
    else:
        print(f"Manifest migration for {escape(str(plan.root))}: {escape(action)}")
        for diagnostic in plan.diagnostics:
            print(f"  {escape(diagnostic.path)}: {escape(diagnostic.message)}")
        if plan.target_json is not None and not apply:
            typer.echo(plan.diff, nl=False)
            print("Ready; pass --apply to write this manifest plan.")
    raise typer.Exit(code=0 if plan.ready else 1)
