"""Install and uninstall commands with terminal installation telemetry."""

from pathlib import Path
from time import monotonic
from typing import Optional

import typer
from rich import print
from rich.markup import escape

from src import __version__
from src.cli.install_context import (
    apply_path_update,
    clean_path_block,
    print_path_instructions,
    print_status,
    report_failure,
    resolve_context,
)
from src.model.dto.telemetry import CliArtifactKind, CliInstallErrorCategory, CliInstallOutcome
from src.telemetry.events import capture_cli_install_terminal, classify_cli_install_exception
from src.utils.installer import (
    BINARY_NAME,
    DEFAULT_APP_ROOT,
    DEFAULT_INSTALL_DIR,
    InstallResult,
    current_binary_path,
    install_binary,
    uninstall_binary,
)


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
    started_at = monotonic()
    outcome = CliInstallOutcome.FAILED
    error_category = CliInstallErrorCategory.UNEXPECTED_ERROR
    artifact_kind = CliArtifactKind.UNKNOWN
    already_on_path = False
    binary_ready = False
    during_path_update = False

    try:
        with report_failure("Install"):
            try:
                ctx = resolve_context(target, app_dir=app_dir, shell=shell, rc_file=rc_file)
                already_on_path = ctx.already_on_path
                source = current_binary_path()

                if check:
                    print_status(ctx, source)
                    return

                result: InstallResult = install_binary(
                    source,
                    ctx.install_dir,
                    overwrite=force,
                    app_root=ctx.app_root,
                )
                artifact_kind = CliArtifactKind.ONEDIR if result.app_path is not None else CliArtifactKind.SINGLE_FILE
                binary_ready = True
                outcome = CliInstallOutcome.NO_CHANGE if result.already_installed else CliInstallOutcome.SUCCESS
                error_category = CliInstallErrorCategory.NONE
                if result.already_installed:
                    print(f"[green]✔ kickstart is already installed at {escape(str(result.destination))}[/]")
                elif result.copied:
                    print(f"[green]✔ Installed kickstart to {escape(str(result.destination))}[/]")

                if ctx.already_on_path:
                    print(f"[green]✔ {escape(str(ctx.install_dir))} is already on your PATH.[/]")
                    print("[cyan]Run [bold]kickstart --help[/bold] to get started.[/cyan]")
                    return

                if update_path:
                    during_path_update = True
                    path_update = apply_path_update(ctx)
                    during_path_update = False
                    if path_update is None:
                        outcome = CliInstallOutcome.PARTIAL_SUCCESS
                        error_category = CliInstallErrorCategory.PATH_UPDATE
                    elif path_update.changed:
                        outcome = CliInstallOutcome.SUCCESS
                    return

                print_path_instructions(ctx)
            except KeyboardInterrupt:
                outcome = CliInstallOutcome.PARTIAL_SUCCESS if binary_ready else CliInstallOutcome.CANCELLED
                error_category = CliInstallErrorCategory.INTERRUPTED
                raise
            except Exception as exc:
                outcome = CliInstallOutcome.PARTIAL_SUCCESS if binary_ready else CliInstallOutcome.FAILED
                error_category = classify_cli_install_exception(
                    exc,
                    during_path_update=during_path_update,
                )
                raise
    finally:
        if not check:
            capture_cli_install_terminal(
                outcome,
                error_category,
                artifact_kind,
                path_update_requested=update_path,
                already_on_path=already_on_path,
                duration_seconds=monotonic() - started_at,
                cli_version=__version__,
            )


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
    with report_failure("Uninstall"):
        ctx = resolve_context(target, app_dir=app_dir, shell=shell, rc_file=rc_file)
        removed = uninstall_binary(ctx.install_dir, app_root=ctx.app_root)
        if removed is None:
            print(f"[yellow]Nothing to uninstall at {escape(str(ctx.install_dir / BINARY_NAME))}.[/]")
        else:
            print(f"[green]✔ Removed {escape(str(removed))}[/]")

        if clean_path:
            clean_path_block(ctx)
