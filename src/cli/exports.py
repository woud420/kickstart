"""CLI adapters for explicit derived exporters."""

from enum import Enum
from pathlib import Path

import typer
from rich import print
from rich.markup import escape

from src.generator.backstage_export import BackstageExportError, BackstageExportUsageError, export_backstage
from src.generator.external_io_contract import ExternalIOContractError
from src.generator.external_io_evidence import verify_external_io_sources
from src.generator.external_io_read import load_external_io_contract
from src.generator.external_io_render import render_external_io_json, render_external_io_markdown

export_app: typer.Typer = typer.Typer(help="Deterministic exports for scaffold state and declared external I/O.")


@export_app.command()
def backstage(
    path: Path = typer.Argument(Path("."), help="Repository to export"),
) -> None:
    """Write or refresh catalog-info.yaml from .kickstart/scaffold.json.

    Derived fields live inside kickstart fences and are refreshed on every
    export; spec.owner/lifecycle/type and everything else outside the fences
    are user-owned and never rewritten. Exit codes: 0 = exported cleanly,
    1 = exported with validation issues or refused (unfenced existing file),
    2 = usage error (no repo or no usable manifest).
    """
    try:
        result = export_backstage(path)
    except BackstageExportUsageError as error:
        print(f"[red]{escape(str(error))}[/]")
        raise typer.Exit(code=2) from error
    except BackstageExportError as error:
        print(f"[red]{escape(str(error))}[/]")
        raise typer.Exit(code=1) from error

    print(f"[bold]{result.action}[/] {escape(str(result.path))}")
    for issue in result.issues:
        print(f"  [yellow]warning[/] {escape(issue)}")
    raise typer.Exit(code=1 if result.issues else 0)


class ExternalIOFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"


@export_app.command("external-io")
def external_io(
    path: Path = typer.Argument(Path("."), exists=True, file_okay=False, help="Repository whose sources are cited"),
    input_file: Path = typer.Option(
        ..., "--input", exists=True, dir_okay=False, help="Declared version-1 JSON contract"
    ),
    format: ExternalIOFormat = typer.Option(ExternalIOFormat.JSON, "--format", help="Output representation"),
) -> None:
    """Check declaration shape and source locations; print a partial JSON or Markdown map."""
    try:
        contract = load_external_io_contract(input_file)
        verify_external_io_sources(contract, path)
    except ExternalIOContractError as error:
        typer.echo(f"cannot export external I/O: {error}", err=True)
        raise typer.Exit(code=2) from error
    rendered = (
        render_external_io_json(contract) if format is ExternalIOFormat.JSON else render_external_io_markdown(contract)
    )
    typer.echo(rendered, nl=False)
