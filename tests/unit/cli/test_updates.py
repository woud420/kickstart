"""Upgrade outcomes and the managed-layout handoff protocol."""

from pathlib import Path
from unittest.mock import patch
import time

import pytest

from src.cli.main import app
from src.cli.updates import upgrade
from src.model.dto.telemetry import (
    CliUpgradeChecksumStatus,
    CliUpgradeErrorCategory,
    CliUpgradeOutcome,
)
from src.model.dto.upgrade import UpgradeResult
from src.utils.handoff import HANDOFF_COMMAND, Handoff, HandoffMode


@patch("src.cli.updates.capture_cli_upgrade_terminal")
@patch("src.cli.updates.check_for_update")
def test_upgrade_command(mock_check_for_update, mock_capture, runner):
    """Test the upgrade command calls check_for_update."""
    update_result = UpgradeResult(
        target_version="1.1.0",
        outcome=CliUpgradeOutcome.UPDATED,
        error_category=CliUpgradeErrorCategory.NONE,
        checksum_status=CliUpgradeChecksumStatus.VERIFIED,
    )
    mock_check_for_update.return_value = update_result
    result = runner.invoke(app, ["upgrade"])

    assert result.exit_code == 0
    mock_check_for_update.assert_called_once()
    mock_capture.assert_called_once()
    assert mock_capture.call_args.args[0] == update_result


@pytest.mark.parametrize(
    ("error", "outcome", "category"),
    [
        (KeyboardInterrupt(), CliUpgradeOutcome.CANCELLED, CliUpgradeErrorCategory.INTERRUPTED),
        (RuntimeError("private detail"), CliUpgradeOutcome.FAILED, CliUpgradeErrorCategory.UNEXPECTED_ERROR),
    ],
)
def test_upgrade_captures_unhandled_terminal_outcomes(error, outcome, category):
    with (
        patch("src.cli.updates.check_for_update", side_effect=error),
        patch("src.cli.updates.capture_cli_upgrade_terminal") as capture,
        pytest.raises(type(error)),
    ):
        upgrade()

    captured = capture.call_args.args[0]
    assert captured.outcome is outcome
    assert captured.error_category is category


def _stage_with_manifest(tmp_path: Path, *, mode: HandoffMode = HandoffMode.REPAIR) -> tuple[Path, Handoff]:
    """Build a stage dir holding a fake onedir payload and a manifest for a nested managed install."""
    app_root = tmp_path / "share" / "kickstart"
    bundle_dest = app_root / "current"
    (bundle_dest / "_internal").mkdir(parents=True)
    nested = bundle_dest / ".kickstart" / "current"
    (nested / "_internal").mkdir(parents=True)
    running = nested / "kickstart"
    running.write_text("#!/bin/sh\necho running\n")
    running.chmod(0o755)
    (bundle_dest / "kickstart").symlink_to(running)
    launcher_dir = tmp_path / "bin"
    launcher_dir.mkdir()
    (launcher_dir / "kickstart").symlink_to(bundle_dest / "kickstart")

    stage_dir = tmp_path / "stage"
    staged_root = stage_dir / "bundle"
    (staged_root / "_internal").mkdir(parents=True)
    staged = staged_root / "kickstart"
    staged.write_text("#!/bin/sh\necho staged\n")
    staged.chmod(0o755)
    handoff = Handoff(
        mode=mode,
        launcher_dir=launcher_dir,
        app_root=app_root,
        bundle_launcher=staged,
        target_version="1.0.0",
        checksum_status=CliUpgradeChecksumStatus.NOT_REACHED,
        started_at=time.time() - 7,
    )
    handoff.write(stage_dir)
    return stage_dir, handoff


def test_handoff_command_is_hidden_from_help(runner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert HANDOFF_COMMAND not in result.stdout


@patch("src.cli.updates.__version__", "1.0.0")
def test_handoff_activate_phase_repairs_layout_then_execs_finalize(runner, tmp_path, handoff_chain):
    stage_dir, handoff = _stage_with_manifest(tmp_path)

    with patch("src.cli.updates.capture_cli_upgrade_terminal") as capture:
        with pytest.raises(handoff_chain.replaced) as replaced:
            runner.invoke(
                app, [HANDOFF_COMMAND, "--stage-dir", str(stage_dir), "--phase", "activate"], catch_exceptions=False
            )

    # The activate hop hands off before its telemetry boundary; only the finalize hop (run
    # in-process by the chain fixture) produced the single terminal result.
    capture.assert_not_called()
    assert replaced.value.result.outcome is CliUpgradeOutcome.REPAIRED
    assert [call.phase.value for call in handoff_chain.calls] == ["finalize"]
    assert handoff.public_launcher.resolve() == handoff.canonical_launcher.resolve()
    assert handoff.canonical_launcher.read_text() == "#!/bin/sh\necho staged\n"
    assert not stage_dir.exists()


@patch("src.cli.updates.__version__", "1.0.0")
def test_handoff_finalize_phase_reports_once_and_exits_zero(runner, tmp_path):
    stage_dir, handoff = _stage_with_manifest(tmp_path)

    with patch("src.cli.updates.capture_cli_upgrade_terminal") as capture:
        result = runner.invoke(app, [HANDOFF_COMMAND, "--stage-dir", str(stage_dir), "--phase", "finalize"])

    assert result.exit_code == 0, result.stdout
    assert "Repaired the managed install layout" in result.stdout
    assert not stage_dir.exists()
    capture.assert_called_once()
    captured, duration = capture.call_args.args
    assert captured.outcome is CliUpgradeOutcome.REPAIRED
    assert captured.target_version == "1.0.0"
    assert 6 <= duration < 60, "duration must span the whole chain, not just the final hop"
    assert capture.call_args.kwargs["cli_version"] == "1.0.0"


@patch("src.cli.updates.__version__", "1.0.0")
def test_handoff_activate_failure_exits_non_zero_and_leaves_install(runner, tmp_path):
    stage_dir, handoff = _stage_with_manifest(tmp_path)
    running = handoff.public_launcher.resolve()

    def fail_copytree(*args, **kwargs):
        raise OSError("staging failed")

    with (
        patch("src.utils.installer.shutil.copytree", side_effect=fail_copytree),
        patch("src.cli.updates.capture_cli_upgrade_terminal") as capture,
    ):
        result = runner.invoke(app, [HANDOFF_COMMAND, "--stage-dir", str(stage_dir), "--phase", "activate"])

    assert result.exit_code == 1
    assert "Update failed" in result.stdout
    assert "previous installation was left in place" in result.stdout
    assert handoff.public_launcher.resolve() == running
    assert (handoff.app_root / "current" / ".kickstart").is_dir()
    captured = capture.call_args.args[0]
    assert captured.outcome is CliUpgradeOutcome.FAILED
    assert captured.error_category is CliUpgradeErrorCategory.INSTALLATION
    assert captured.target_version == "1.0.0"


def test_handoff_with_unreadable_manifest_reports_unexpected_error(runner, tmp_path):
    with patch("src.cli.updates.capture_cli_upgrade_terminal") as capture:
        result = runner.invoke(app, [HANDOFF_COMMAND, "--stage-dir", str(tmp_path), "--phase", "finalize"])

    assert result.exit_code == 1
    assert "cannot read handoff manifest" in result.stdout
    captured = capture.call_args.args[0]
    assert captured.outcome is CliUpgradeOutcome.FAILED
    assert captured.error_category is CliUpgradeErrorCategory.UNEXPECTED_ERROR
    assert captured.target_version == "unknown"
