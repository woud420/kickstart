"""kickstart command line interface."""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, cast

import typer
from rich import print
from rich.markup import escape
from rich.prompt import Confirm, Prompt

from src import __version__
from src.api import (
    create_cli,
    create_frontend,
    create_lib,
    create_monorepo,
    create_service,
    create_system,
)
from src.cli.dispatch import ProjectCreators, dispatch_project_creation
from src.generator.adoption import AdoptionTargetError, inspect_repo
from src.cli.options import CreateCommandOptions, CreateOptions, ResolvedCreateArgs
from src.cli.prompts import ConfirmReader, PromptReader, prompt_for_missing_args
from src.utils.errors import KickstartError
from src.utils.config import load_config
from src.utils.installer import (
    BINARY_NAME,
    DEFAULT_APP_ROOT,
    DEFAULT_INSTALL_DIR,
    InstallResult,
    PathUpdateResult,
    current_binary_path,
    default_app_root,
    default_rc_for_shell,
    detect_shell,
    install_binary,
    path_contains,
    path_update_snippet,
    remove_path_block_from_rc,
    uninstall_binary,
    update_path_in_rc,
)
from src.utils.types import GeneratorConfig
from src.utils.updater import check_for_update

logger = logging.getLogger(__name__)

app: typer.Typer = typer.Typer(help="kickstart: Full-stack project scaffolding CLI")


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


@app.command()
def upgrade() -> None:
    """Upgrade to the latest version."""
    check_for_update()


@app.command()
def adopt(
    path: Path = typer.Argument(Path("."), help="Existing repository to inspect"),
    check: bool = typer.Option(False, "--check", help="Report standard-artifact status without writing"),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable report"),
) -> None:
    """Check an existing repo against the kickstart scaffold standard (read-only).

    Exit codes: 0 = repo matches the standard, 1 = gaps found, 2 = usage error.
    """
    if not check:
        print("[red]kickstart adopt only supports --check for now; writing is a future, explicit step.[/]")
        raise typer.Exit(code=2)

    try:
        report = inspect_repo(path)
    except AdoptionTargetError as error:
        print(f"[red]{error}[/]")
        raise typer.Exit(code=2) from error

    if json_output:
        # Machine-readable output must bypass rich: console printing wraps
        # long lines and interprets bracketed path segments as markup, both
        # of which corrupt the JSON.
        typer.echo(report.to_json(), nl=False)
    else:
        print(f"[bold]Adoption check for {escape(str(report.root))}[/]")
        for status in report.artifacts:
            if status.ok:
                print(f"  [green]ok[/]      {escape(status.path)}")
            else:
                print(f"  [red]needed[/]  {escape(status.path)} ({escape(status.issue)})")

    raise typer.Exit(code=0 if report.complete else 1)


@dataclass(frozen=True)
class _InstallContext:
    """Resolved arguments shared by `kickstart install` and `kickstart uninstall`."""

    install_dir: Path
    app_root: Path
    shell: Optional[str]
    rc_file: Optional[Path]
    snippet: str
    already_on_path: bool


def _resolve_install_context(
    target: Optional[Path],
    shell: Optional[str],
    rc_file: Optional[Path],
    app_dir: Optional[Path] = None,
) -> _InstallContext:
    """Normalize the install-related CLI options into a single shared context."""
    install_dir = (target or DEFAULT_INSTALL_DIR).expanduser()
    resolved_app_root = (app_dir or default_app_root(install_dir)).expanduser()
    resolved_shell = shell or detect_shell()
    rc_target = rc_file.expanduser() if rc_file is not None else default_rc_for_shell(resolved_shell)
    return _InstallContext(
        install_dir=install_dir,
        app_root=resolved_app_root,
        shell=resolved_shell,
        rc_file=rc_target,
        snippet=path_update_snippet(resolved_shell, install_dir),
        already_on_path=path_contains(install_dir),
    )


@contextmanager
def _report_install_failure(operation: str) -> Generator[None, None, None]:
    """Print a uniform error message and exit non-zero on the install/uninstall failure surface."""
    try:
        yield
    except KickstartError as exc:
        print(f"[bold red]{operation} failed: {exc}[/]")
        raise typer.Exit(code=1) from exc
    except (FileNotFoundError, FileExistsError, PermissionError, OSError) as exc:
        print(f"[bold red]{operation} failed: {exc}[/]")
        raise typer.Exit(code=1) from exc


@app.command()
def install(
    target: Optional[Path] = typer.Option(
        None,
        "--target",
        "-t",
        help="Directory to install the kickstart binary into. Defaults to ~/.local/bin.",
    ),
    update_path: bool = typer.Option(
        False,
        "--update-path",
        help="Append a PATH entry for the install directory to your shell rc file.",
    ),
    rc_file: Optional[Path] = typer.Option(
        None,
        "--rc-file",
        help="Shell rc file to modify when --update-path is set. Defaults to a sensible file for $SHELL.",
    ),
    app_dir: Optional[Path] = typer.Option(
        None,
        "--app-dir",
        help=(
            "Directory for the kickstart binary payload. Default: derived from --target; "
            "if --target ends in /bin, use <target_parent>/share/kickstart, otherwise <target>/.kickstart "
            f"(so the default --target {DEFAULT_INSTALL_DIR} resolves to {DEFAULT_APP_ROOT})."
        ),
    ),
    shell: Optional[str] = typer.Option(
        None,
        "--shell",
        help="Override shell detection: bash, zsh, or fish. Used for both PATH snippet and rc file defaults.",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing kickstart binary at the destination."),
    check: bool = typer.Option(False, "--check", help="Only report install/PATH status; do not modify anything."),
) -> None:
    """Install the kickstart binary to a user-writable directory and help configure PATH."""
    with _report_install_failure("Install"):
        ctx = _resolve_install_context(target, app_dir=app_dir, shell=shell, rc_file=rc_file)
        source = current_binary_path()

        if check:
            _print_install_status(ctx, source)
            return

        result: InstallResult = install_binary(source, ctx.install_dir, overwrite=force, app_root=ctx.app_root)
        if result.already_installed:
            print(f"[green]✔ kickstart is already installed at {result.destination}[/]")
        elif result.copied:
            print(f"[green]✔ Installed kickstart to {result.destination}[/]")

        if ctx.already_on_path:
            print(f"[green]✔ {ctx.install_dir} is already on your PATH.[/]")
            print("[cyan]Run [bold]kickstart --help[/bold] to get started.[/cyan]")
            return

        if update_path:
            _apply_path_update(ctx)
            return

        _print_manual_path_instructions(ctx)


@app.command()
def uninstall(
    target: Optional[Path] = typer.Option(
        None,
        "--target",
        "-t",
        help="Directory the kickstart binary lives in. Defaults to ~/.local/bin.",
    ),
    clean_path: bool = typer.Option(
        False,
        "--clean-path",
        help="Also remove the managed PATH block kickstart appended to your shell rc file.",
    ),
    rc_file: Optional[Path] = typer.Option(
        None,
        "--rc-file",
        help="Shell rc file to clean when --clean-path is set. Defaults to a sensible file for $SHELL.",
    ),
    app_dir: Optional[Path] = typer.Option(
        None,
        "--app-dir",
        help=(
            "Directory for the kickstart binary payload. Default: derived from --target; "
            "if --target ends in /bin, use <target_parent>/share/kickstart, otherwise <target>/.kickstart "
            f"(so the default --target {DEFAULT_INSTALL_DIR} resolves to {DEFAULT_APP_ROOT})."
        ),
    ),
    shell: Optional[str] = typer.Option(
        None,
        "--shell",
        help="Override shell detection: bash, zsh, or fish.",
    ),
) -> None:
    """Remove an installed kickstart binary and optionally restore the shell rc file."""
    with _report_install_failure("Uninstall"):
        ctx = _resolve_install_context(target, app_dir=app_dir, shell=shell, rc_file=rc_file)
        removed = uninstall_binary(ctx.install_dir, app_root=ctx.app_root)
        if removed is None:
            print(f"[yellow]Nothing to uninstall at {ctx.install_dir / BINARY_NAME}.[/]")
        else:
            print(f"[green]✔ Removed {removed}[/]")

        if clean_path:
            _clean_managed_path_block(ctx)


def _print_install_status(ctx: _InstallContext, source: Path) -> None:
    """Print the read-only `install --check` report."""
    destination = ctx.install_dir / BINARY_NAME
    print("[bold]Install status[/]")
    print(f"  source:      {source}")
    print(f"  destination: {destination} ({'present' if destination.exists() else 'missing'})")
    print(f"  app dir:     {ctx.app_root}")
    print(f"  on PATH:     {'yes' if ctx.already_on_path else 'no'}")
    print(f"  shell:       {ctx.shell or 'unknown'}")
    if ctx.rc_file is not None:
        print(f"  rc file:     {ctx.rc_file}")


def _apply_path_update(ctx: _InstallContext) -> None:
    """Write (or refresh) the managed PATH block in the resolved rc file, or fall back to instructions."""
    if ctx.rc_file is None:
        print(
            "[yellow]Could not infer a shell rc file. Re-run with [bold]--rc-file PATH[/bold] "
            "or [bold]--shell bash|zsh|fish[/bold].[/yellow]"
        )
        _print_manual_path_instructions(ctx, suppress_rc_hint=True)
        return
    changed = update_path_in_rc(ctx.rc_file, ctx.snippet)
    update = PathUpdateResult(rc_file=ctx.rc_file, snippet=ctx.snippet, changed=changed, on_path_now=False)
    if update.changed:
        print(f"[green]✔ Updated {update.rc_file} with a managed PATH entry.[/]")
    else:
        print(f"[green]✔ {update.rc_file} already contains the managed PATH entry.[/]")
    print(
        "[cyan]Restart your shell or run "
        f"[bold]source {update.rc_file}[/bold] to pick up the new PATH.[/cyan]"
    )


def _clean_managed_path_block(ctx: _InstallContext) -> None:
    """Remove the managed PATH block during uninstall, or explain why we can't."""
    if ctx.rc_file is None:
        print(
            "[yellow]Could not infer a shell rc file. Pass [bold]--rc-file PATH[/bold] "
            "or [bold]--shell bash|zsh|fish[/bold] to clean PATH manually.[/yellow]"
        )
        return
    if remove_path_block_from_rc(ctx.rc_file):
        print(f"[green]✔ Removed managed PATH block from {ctx.rc_file}[/]")
    else:
        print(f"[yellow]No managed PATH block found in {ctx.rc_file}.[/]")


def _print_manual_path_instructions(ctx: _InstallContext, *, suppress_rc_hint: bool = False) -> None:
    """Tell the user how to add the install directory to PATH themselves."""
    print(f"[yellow]⚠ {ctx.install_dir} is not on your PATH yet.[/]")
    print("[cyan]Add this line to your shell startup file:[/]")
    print(f"  [bold]{ctx.snippet}[/]")
    if suppress_rc_hint:
        return
    if ctx.rc_file is not None:
        print(
            f"[cyan]Suggested file: [bold]{ctx.rc_file}[/bold]. Or re-run with "
            f"[bold]kickstart install --update-path[/bold] to do it for you.[/]"
        )
    else:
        print(
            "[cyan]Re-run with [bold]kickstart install --update-path --shell bash|zsh|fish[/bold] "
            "to have kickstart update the file for you.[/]"
        )


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
        system=create_system,
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
    workspace_tooling: Optional[str] = None,
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
            workspace_tooling=workspace_tooling,
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
    workspace_tooling: Optional[str] = None,
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
            workspace_tooling=workspace_tooling,
        ),
        config,
        _project_creators(),
    )


@app.command(
    epilog=(
        "Examples:\n\n"
        "  kickstart create service my-api --lang python --database postgres --auth jwt\n\n"
        "  kickstart create service edge --lang typescript --runtime cloudflare-workers\n\n"
        "  kickstart create cli ops-tool --lang rust\n\n"
        "  kickstart create system platform --cloud aws --runtime kubernetes\n\n"
        "Every project generates with tests, docs, and a Makefile; verify with: make check"
    )
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
        help="Database extension (implemented: postgres for Python/FastAPI and TypeScript container services)",
    ),
    cache: Optional[str] = typer.Option(
        None,
        "--cache",
        help="Cache extension (implemented: redis for Python/FastAPI and Rust container services)",
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
    ),
    workspace_tooling: Optional[str] = typer.Option(
        None,
        "--workspace-tooling",
        help="System root workspace tooling (none or bun-turbo).",
    ),
) -> None:
    """Create a new service, lib, CLI, frontend, or system."""
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
                workspace_tooling=workspace_tooling,
            ),
            config,
            prompt=cast(PromptReader, Prompt),
            confirm=cast(ConfirmReader, Confirm),
        )
        dispatch_project_creation(options, config, _project_creators())
        project_path = Path(options.root) / options.name if options.root else Path(options.name)
        print(
            f"\nNext steps:\n"
            f"  cd {escape(str(project_path))} && make check   [dim]# install deps, lint, typecheck, test[/]\n"
            f"  cat AGENTS.md                  [dim]# orientation map; scaffold metadata in .kickstart/scaffold.json[/]"
        )

    except KeyboardInterrupt:
        print("\n[yellow]Operation cancelled by user.[/]")
        # Conventional SIGINT exit status; cancel must not read as success.
        raise typer.Exit(code=130) from None
    except EOFError as exc:
        print(
            "[bold red]Interactive input ended before required arguments were provided. "
            "Pass them explicitly, for example: kickstart create service my-api --lang python[/]"
        )
        raise typer.Exit(code=2) from exc
    except KickstartError as exc:
        print(f"[bold red]Failed to create project: {exc}[/]")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        # Stack-registry validation errors (unknown runtime/cloud/...) are
        # user-input problems: report them cleanly without a traceback.
        print(f"[bold red]Failed to create project: {exc}[/]")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        print(f"[bold red]Failed to create project: {exc}[/]")
        logger.exception("Project creation failed")
        raise typer.Exit(code=1) from exc


def main() -> None:
    """Run the Typer application when executed as a script."""
    app(prog_name="kickstart")


if __name__ == "__main__":
    main()
