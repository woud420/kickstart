"""Resolved install paths and shared shell PATH instructions."""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import typer
from rich import print
from rich.markup import escape

from src.utils.errors import KickstartError
from src.utils.installer import (
    BINARY_NAME,
    DEFAULT_INSTALL_DIR,
    PathUpdateResult,
    default_app_root,
    default_rc_for_shell,
    detect_shell,
    path_contains,
    path_update_snippet,
    remove_path_block_from_rc,
    update_path_in_rc,
)


@dataclass(frozen=True)
class InstallContext:
    """Resolved arguments shared by `kickstart install` and `kickstart uninstall`."""

    install_dir: Path
    app_root: Path
    shell: str | None
    rc_file: Path | None
    snippet: str
    already_on_path: bool


def resolve_context(
    target: Path | None,
    shell: str | None,
    rc_file: Path | None,
    app_dir: Path | None = None,
) -> InstallContext:
    """Normalize the install-related CLI options into a single shared context."""
    install_dir = (target or DEFAULT_INSTALL_DIR).expanduser()
    resolved_app_root = (app_dir or default_app_root(install_dir)).expanduser()
    resolved_shell = shell or detect_shell()
    rc_target = rc_file.expanduser() if rc_file is not None else default_rc_for_shell(resolved_shell)
    return InstallContext(
        install_dir=install_dir,
        app_root=resolved_app_root,
        shell=resolved_shell,
        rc_file=rc_target,
        snippet=path_update_snippet(resolved_shell, install_dir),
        already_on_path=path_contains(install_dir),
    )


@contextmanager
def report_failure(operation: str) -> Generator[None, None, None]:
    """Print a uniform error message and exit non-zero on the install/uninstall failure surface."""
    try:
        yield
    except (KickstartError, OSError) as exc:
        print(f"[bold red]{operation} failed: {escape(str(exc))}[/]")
        raise typer.Exit(code=1) from exc


def print_status(ctx: InstallContext, source: Path) -> None:
    """Print the read-only `install --check` report."""
    destination = ctx.install_dir / BINARY_NAME
    print("[bold]Install status[/]")
    print(f"  source:      {escape(str(source))}")
    print(f"  destination: {escape(str(destination))} ({'present' if destination.exists() else 'missing'})")
    print(f"  app dir:     {escape(str(ctx.app_root))}")
    print(f"  on PATH:     {'yes' if ctx.already_on_path else 'no'}")
    print(f"  shell:       {escape(str(ctx.shell or 'unknown'))}")
    if ctx.rc_file is not None:
        print(f"  rc file:     {escape(str(ctx.rc_file))}")


def apply_path_update(ctx: InstallContext) -> PathUpdateResult | None:
    """Write (or refresh) the managed PATH block in the resolved rc file, or fall back to instructions."""
    if ctx.rc_file is None:
        print(
            "[yellow]Could not infer a shell rc file. Re-run with [bold]--rc-file PATH[/bold] "
            "or [bold]--shell bash|zsh|fish[/bold].[/yellow]"
        )
        print_path_instructions(ctx, suppress_rc_hint=True)
        return None
    changed = update_path_in_rc(ctx.rc_file, ctx.snippet)
    update = PathUpdateResult(rc_file=ctx.rc_file, snippet=ctx.snippet, changed=changed, on_path_now=False)
    if update.changed:
        print(f"[green]✔ Updated {escape(str(update.rc_file))} with a managed PATH entry.[/]")
    else:
        print(f"[green]✔ {escape(str(update.rc_file))} already contains the managed PATH entry.[/]")
    print(
        f"[cyan]Restart your shell or run [bold]source {escape(str(update.rc_file))}[/bold] to pick up the new PATH.[/cyan]"
    )
    return update


def clean_path_block(ctx: InstallContext) -> None:
    """Remove the managed PATH block during uninstall, or explain why we can't."""
    if ctx.rc_file is None:
        print(
            "[yellow]Could not infer a shell rc file. Pass [bold]--rc-file PATH[/bold] "
            "or [bold]--shell bash|zsh|fish[/bold] to clean PATH manually.[/yellow]"
        )
        return
    if remove_path_block_from_rc(ctx.rc_file):
        print(f"[green]✔ Removed managed PATH block from {escape(str(ctx.rc_file))}[/]")
    else:
        print(f"[yellow]No managed PATH block found in {escape(str(ctx.rc_file))}.[/]")


def print_path_instructions(ctx: InstallContext, *, suppress_rc_hint: bool = False) -> None:
    """Tell the user how to add the install directory to PATH themselves."""
    print(f"[yellow]⚠ {escape(str(ctx.install_dir))} is not on your PATH yet.[/]")
    print("[cyan]Add this line to your shell startup file:[/]")
    print(f"  [bold]{escape(str(ctx.snippet))}[/]")
    if suppress_rc_hint:
        return
    if ctx.rc_file is not None:
        print(
            f"[cyan]Suggested file: [bold]{escape(str(ctx.rc_file))}[/bold]. Or re-run with "
            f"[bold]kickstart install --update-path[/bold] to do it for you.[/]"
        )
    else:
        print(
            "[cyan]Re-run with [bold]kickstart install --update-path --shell bash|zsh|fish[/bold] "
            "to have kickstart update the file for you.[/]"
        )
