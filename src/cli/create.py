"""Create command options, interactive resolution and terminal telemetry."""

import logging
from pathlib import Path
from time import monotonic
from typing import Optional, cast

import typer
from rich import print
from rich.markup import escape
from rich.prompt import Confirm, Prompt

from src import __version__
from src.api import create_cli, create_frontend, create_lib, create_monorepo, create_service, create_system
from src.cli.dispatch import ProjectCreators, dispatch_project_creation
from src.cli.options import CreateCommandOptions, CreateOptions
from src.cli.prompts import ConfirmReader, PromptReader, prompt_for_missing_args
from src.model.dto.telemetry import ScaffoldCreateContext, ScaffoldCreateErrorCategory, ScaffoldCreateOutcome
from src.telemetry.events import capture_scaffold_create_terminal, classify_scaffold_create_exception
from src.utils.config import load_config
from src.utils.errors import KickstartError
from src.utils.types import GeneratorConfig


logger = logging.getLogger(__name__)
CREATE_EPILOG = (
    "Examples:\n\n"
    "  kickstart create service my-api --lang python --database postgres --auth jwt\n\n"
    "  kickstart create service edge --lang typescript --runtime cloudflare-workers\n\n"
    "  kickstart create cli ops-tool --lang rust\n\n"
    "  kickstart create system platform --cloud aws --runtime kubernetes\n\n"
    "Every project generates with tests, docs, and a Makefile; verify with: make check"
)


def _creators() -> ProjectCreators:
    return ProjectCreators(
        service=create_service,
        frontend=create_frontend,
        lib=create_lib,
        cli=create_cli,
        system=create_system,
        monorepo=create_monorepo,
    )


def _telemetry_context(
    options: CreateCommandOptions | CreateOptions,
    *,
    interactive: bool,
) -> ScaffoldCreateContext:
    """Copy only telemetry-approved create options; exclude name and root."""
    return ScaffoldCreateContext(
        project_type=options.project_type,
        language=options.lang,
        runtime=options.runtime,
        cloud=options.cloud,
        framework=options.framework,
        database=options.database,
        cache=options.cache,
        auth=options.auth,
        knowledge=options.knowledge,
        workspace_tooling=options.workspace_tooling,
        helm=options.helm,
        github_requested=options.gh,
        interactive=interactive,
    )


def create(
    project_type: Optional[str] = typer.Argument(None, help="service, frontend, lib, cli, or system"),
    name: Optional[str] = typer.Argument(
        None, help="Lowercase project name: letters, digits, dashes, underscores (e.g. my-api)"
    ),
    root: Optional[str] = typer.Option(None, "--root", "-r", help="Root directory where the project will be created"),
    lang: str = typer.Option(
        "python",
        "--lang",
        "-l",
        help="Language: python, rust, typescript, go, cpp (services); python, rust, typescript (libs/CLIs)",
    ),
    gh: bool = typer.Option(False, "--gh", help="Create GitHub repo"),
    helm: bool = typer.Option(False, "--helm", help="Add Helm scaffolding (services or systems only)"),
    database: Optional[str] = typer.Option(
        None,
        "--database",
        help="Database extension (postgres: Python/FastAPI and TypeScript containers; sqlite: Python/FastAPI containers)",
    ),
    cache: Optional[str] = typer.Option(
        None,
        "--cache",
        help="Cache extension (implemented: redis for Python/FastAPI and Rust container services)",
    ),
    auth: Optional[str] = typer.Option(
        None,
        "--auth",
        help="Authentication extension (implemented: jwt for Python/FastAPI, Rust, and TypeScript container services)",
    ),
    framework: Optional[str] = typer.Option(
        None,
        "--framework",
        help="HTTP framework (minimal for standard library, default is FastAPI)",
    ),
    cloud: str = typer.Option("multi", "--cloud", help="System provider target (aws, gcp, cloudflare, multi, none)"),
    knowledge: str = typer.Option(
        "none", "--knowledge", help="External knowledge adapter metadata (none, obsidian, backstage, both)"
    ),
    runtime: Optional[str] = typer.Option(
        None,
        "--runtime",
        help="Execution/platform profile. Services: container or cloudflare-workers. Systems: kubernetes, cloudflare-workers, hybrid.",
    ),
    workspace_tooling: Optional[str] = typer.Option(
        None,
        "--workspace-tooling",
        help="System root workspace tooling (none or bun-turbo).",
    ),
) -> None:
    """Create a new service, lib, CLI, frontend, or system."""
    command_options = CreateCommandOptions(
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
        workspace_tooling=workspace_tooling,
    )
    interactive = not project_type or not name
    telemetry_context = _telemetry_context(command_options, interactive=interactive)
    started_at = monotonic()
    outcome = ScaffoldCreateOutcome.UNEXPECTED_ERROR
    error_category = ScaffoldCreateErrorCategory.UNEXPECTED_ERROR
    try:
        config: GeneratorConfig = load_config()
        options = prompt_for_missing_args(
            command_options,
            config,
            prompt=cast(PromptReader, Prompt),
            confirm=cast(ConfirmReader, Confirm),
        )
        telemetry_context = _telemetry_context(options, interactive=interactive)
        dispatch_project_creation(options, config, _creators())
        project_path = Path(options.root) / options.name if options.root else Path(options.name)
        print(
            f"\nNext steps:\n"
            f"  cd {escape(str(project_path))} && make check   [dim]# install deps, lint, typecheck, test[/]\n"
            f"  cat AGENTS.md                  [dim]# orientation map; scaffold metadata in .kickstart/scaffold.json[/]"
        )
        outcome = ScaffoldCreateOutcome.SUCCESS
        error_category = ScaffoldCreateErrorCategory.NONE

    except KeyboardInterrupt:
        outcome = ScaffoldCreateOutcome.CANCELLED
        error_category = ScaffoldCreateErrorCategory.INTERRUPTED
        print("\n[yellow]Operation cancelled by user.[/]")
        # Conventional SIGINT exit status; cancel must not read as success.
        raise typer.Exit(code=130) from None
    except EOFError as exc:
        outcome = ScaffoldCreateOutcome.INPUT_ENDED
        error_category = ScaffoldCreateErrorCategory.INPUT_ENDED
        print(
            "[bold red]Interactive input ended before required arguments were provided. "
            "Pass them explicitly, for example: kickstart create service my-api --lang python[/]"
        )
        raise typer.Exit(code=2) from exc
    except (KickstartError, ValueError) as exc:
        outcome, error_category = classify_scaffold_create_exception(exc)
        print(f"[bold red]Failed to create project: {escape(str(exc))}[/]")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        outcome, error_category = classify_scaffold_create_exception(exc)
        print(f"[bold red]Failed to create project: {escape(str(exc))}[/]")
        logger.exception("Project creation failed")
        raise typer.Exit(code=1) from exc
    finally:
        capture_scaffold_create_terminal(
            telemetry_context,
            outcome,
            error_category,
            monotonic() - started_at,
            cli_version=__version__,
        )
