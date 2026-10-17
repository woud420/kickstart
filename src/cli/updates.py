"""Upgrade and managed-layout handoff commands."""

import time
from pathlib import Path
from time import monotonic

import typer
from rich import print
from rich.markup import escape

from src import __version__
from src.model.dto.telemetry import CliUpgradeChecksumStatus, CliUpgradeErrorCategory, CliUpgradeOutcome
from src.model.dto.upgrade import UNKNOWN_TARGET_VERSION, UpgradeResult
from src.telemetry.events import capture_cli_upgrade_terminal
from src.utils.handoff import Handoff, HandoffPhase, activate, finalize, load_handoff, unknown_failure
from src.utils.updater import check_for_update


def upgrade() -> None:
    """Upgrade to the latest version."""
    started_at = monotonic()
    result: UpgradeResult | None = None
    try:
        result = check_for_update()
    except KeyboardInterrupt:
        result = UpgradeResult(
            target_version=UNKNOWN_TARGET_VERSION,
            outcome=CliUpgradeOutcome.CANCELLED,
            error_category=CliUpgradeErrorCategory.INTERRUPTED,
            checksum_status=CliUpgradeChecksumStatus.NOT_REACHED,
        )
        raise
    except Exception:
        result = UpgradeResult(
            target_version=UNKNOWN_TARGET_VERSION,
            outcome=CliUpgradeOutcome.FAILED,
            error_category=CliUpgradeErrorCategory.UNEXPECTED_ERROR,
            checksum_status=CliUpgradeChecksumStatus.NOT_REACHED,
        )
        raise
    finally:
        if result is not None:
            capture_cli_upgrade_terminal(
                result,
                monotonic() - started_at,
                cli_version=__version__,
            )


def managed_layout_handoff(
    stage_dir: Path = typer.Option(..., "--stage-dir", help="Staging directory holding the handoff manifest."),
    phase: HandoffPhase = typer.Option(..., "--phase", help="Handoff hop to run."),
) -> None:
    """Continue a staged upgrade or managed-layout repair started by `kickstart upgrade`.

    Internal. `activate` runs in the staged payload outside the app root and
    replaces `<app_root>/current`; `finalize` runs in the activated payload,
    removes the staging directory, and reports the single terminal result.
    """
    fallback_started_at = time.time()
    handoff: Handoff | None = None
    result: UpgradeResult | None = None
    exit_code = 0
    try:
        handoff = load_handoff(stage_dir)
        if phase is HandoffPhase.ACTIVATE:
            result = activate(handoff, stage_dir)
        else:
            result = finalize(handoff, stage_dir)
    except KeyboardInterrupt:
        result = (
            handoff.failure(CliUpgradeErrorCategory.INTERRUPTED)
            if handoff is not None
            else unknown_failure(CliUpgradeErrorCategory.INTERRUPTED)
        )
        raise
    except Exception as exc:
        print(f"[red]✖ Update failed: {escape(str(exc))}")
        if phase is HandoffPhase.ACTIVATE and handoff is not None:
            print("  The previous installation was left in place.")
        category = (
            CliUpgradeErrorCategory.INSTALLATION if handoff is not None else CliUpgradeErrorCategory.UNEXPECTED_ERROR
        )
        result = handoff.failure(category) if handoff is not None else unknown_failure(category)
        exit_code = 1
    finally:
        if result is not None:
            started_at = handoff.started_at if handoff is not None else fallback_started_at
            capture_cli_upgrade_terminal(result, time.time() - started_at, cli_version=__version__)
    if exit_code:
        raise typer.Exit(code=exit_code)
