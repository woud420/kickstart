"""kickstart command line interface."""

import logging
from typing import Optional, cast

import typer
from rich import print
from rich.prompt import Confirm, Prompt

from src import __version__
from src.api import (
    create_cli,
    create_frontend,
    create_lib,
    create_monorepo,
    create_service,
)
from src.cli.dispatch import ProjectCreators, dispatch_project_creation
from src.cli.options import CreateCommandOptions, CreateOptions, ResolvedCreateArgs
from src.cli.prompts import ConfirmReader, PromptReader, prompt_for_missing_args
from src.utils.error_handling import KickstartError
from src.utils.config import load_config
from src.utils.types import GeneratorConfig
from src.utils.updater import check_for_update

logger = logging.getLogger(__name__)

app: typer.Typer = typer.Typer(help="kickstart: Full-stack project scaffolding CLI")


@app.command()
def version() -> None:
    """Show the current version."""
    print(f"[bold cyan]kickstart v{__version__}[/]")


@app.command()
def upgrade() -> None:
    """Upgrade to the latest version."""
    check_for_update()


@app.command()
def completion(shell: str = typer.Argument(..., help="bash | zsh | fish | powershell")) -> None:
    """Generate shell completion script."""
    typer.echo("Completion not implemented")


def _project_creators() -> ProjectCreators:
    return ProjectCreators(
        service=create_service,
        frontend=create_frontend,
        lib=create_lib,
        cli=create_cli,
        monorepo=create_monorepo,
    )


def _prompt_for_missing_args(
    project_type: Optional[str],
    name: Optional[str],
    root: Optional[str],
    lang: str,
    gh: bool,
    helm: bool,
    config: GeneratorConfig,
    database: Optional[str] = None,
    cache: Optional[str] = None,
    auth: Optional[str] = None,
    framework: Optional[str] = None,
    cloud: str = "multi",
    knowledge: str = "none",
    runtime: Optional[str] = None,
) -> ResolvedCreateArgs:
    """Prompt user for any missing arguments in interactive mode."""
    options = prompt_for_missing_args(
        CreateCommandOptions(
            project_type=project_type,
            name=name,
            root=root,
            lang=lang,
            gh=gh,
            helm=helm,
            database=database,
            cache=cache,
            auth=auth,
            framework=framework,
            cloud=cloud,
            knowledge=knowledge,
            runtime=runtime,
        ),
        config,
        prompt=cast(PromptReader, Prompt),
        confirm=cast(ConfirmReader, Confirm),
    )
    return options.as_tuple()


def _dispatch_project_creation(
    project_type: str,
    name: str,
    root: Optional[str],
    lang: str,
    gh: bool,
    helm: bool,
    config: GeneratorConfig,
    database: Optional[str] = None,
    cache: Optional[str] = None,
    auth: Optional[str] = None,
    framework: Optional[str] = None,
    cloud: str = "multi",
    knowledge: str = "none",
    runtime: Optional[str] = None,
) -> None:
    """Dispatch to the appropriate project creation function."""
    dispatch_project_creation(
        CreateOptions(
            project_type=project_type,
            name=name,
            root=root,
            lang=lang,
            gh=gh,
            helm=helm,
            database=database,
            cache=cache,
            auth=auth,
            framework=framework,
            cloud=cloud,
            knowledge=knowledge,
            runtime=runtime,
        ),
        config,
        _project_creators(),
    )


@app.command()
def create(
    project_type: Optional[str] = typer.Argument(None),
    name: Optional[str] = typer.Argument(None),
    root: Optional[str] = typer.Option(None, "--root", "-r", help="Root directory where the project will be created"),
    lang: str = typer.Option("python", "--lang", "-l"),
    gh: bool = typer.Option(False, "--gh", help="Create GitHub repo"),
    helm: bool = typer.Option(False, "--helm", help="Add Helm scaffolding (services or mono only)"),
    database: Optional[str] = typer.Option(
        None,
        "--database",
        help="Database extension (implemented: postgres for Python/FastAPI, Rust, and TypeScript container services)",
    ),
    cache: Optional[str] = typer.Option(
        None,
        "--cache",
        help="Cache extension (implemented: redis for Python/FastAPI, Rust, and TypeScript container services)",
    ),
    auth: Optional[str] = typer.Option(
        None,
        "--auth",
        help="Authentication extension (implemented: jwt for Python/FastAPI and Rust container services)",
    ),
    framework: Optional[str] = typer.Option(
        None,
        "--framework",
        help="HTTP framework (minimal for standard library, default is FastAPI)",
    ),
    cloud: str = typer.Option("multi", "--cloud", help="System provider target (aws, gcp, cloudflare, multi, none)"),
    knowledge: str = typer.Option("none", "--knowledge", help="External knowledge adapter metadata (none, obsidian, backstage, both)"),
    runtime: Optional[str] = typer.Option(
        None,
        "--runtime",
        help="Execution/platform profile. Services: container or cloudflare-workers. Systems: kubernetes, cloudflare-workers, hybrid.",
    )
) -> None:
    """Create a new service, lib, CLI, frontend, or mono repo."""
    try:
        config: GeneratorConfig = load_config()
        options = prompt_for_missing_args(
            CreateCommandOptions(
                project_type=project_type,
                name=name,
                root=root,
                lang=lang,
                gh=gh,
                helm=helm,
                database=database,
                cache=cache,
                auth=auth,
                framework=framework,
                cloud=cloud,
                knowledge=knowledge,
                runtime=runtime,
            ),
            config,
            prompt=cast(PromptReader, Prompt),
            confirm=cast(ConfirmReader, Confirm),
        )
        dispatch_project_creation(options, config, _project_creators())

    except KeyboardInterrupt:
        print("\n[yellow]Operation cancelled by user.[/]")
    except KickstartError as exc:
        print(f"[bold red]Failed to create project: {exc}[/]")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        print(f"[bold red]Failed to create project: {exc}[/]")
        logger.exception("Project creation failed")
        raise typer.Exit(code=1) from exc


def main() -> None:
    """Run the Typer application when executed as a script."""
    app()


if __name__ == "__main__":
    main()
