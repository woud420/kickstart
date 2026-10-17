"""Installation terminal telemetry and partial-success outcomes."""

from unittest.mock import patch


from src.cli.main import app
from src.model.dto.telemetry import (
    CliArtifactKind,
    CliInstallErrorCategory,
    CliInstallOutcome,
)


def test_install_command_reports_partial_success_when_path_update_fails(runner, tmp_path, single_file_binary):
    source = single_file_binary
    target_dir = tmp_path / "user-bin"

    with (
        patch("src.cli.installation.current_binary_path", return_value=source),
        patch("src.cli.installation.apply_path_update", side_effect=OSError("private detail")),
        patch("src.cli.installation.capture_cli_install_terminal") as capture,
    ):
        result = runner.invoke(
            app,
            ["install", "--target", str(target_dir), "--shell", "zsh", "--update-path"],
            env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "SHELL": "/bin/zsh"},
        )

    assert result.exit_code == 1
    assert (target_dir / "kickstart").exists()
    capture.assert_called_once()
    assert capture.call_args.args[0] is CliInstallOutcome.PARTIAL_SUCCESS
    assert capture.call_args.args[1] is CliInstallErrorCategory.PATH_UPDATE
    assert capture.call_args.args[2] is CliArtifactKind.SINGLE_FILE


def test_install_command_reports_partial_success_when_path_update_fails_after_binary_noop(runner, tmp_path):
    target_dir = tmp_path / "user-bin"
    target_dir.mkdir()
    source = target_dir / "kickstart"
    source.write_text("#!/bin/sh\n")
    source.chmod(0o755)

    with (
        patch("src.cli.installation.current_binary_path", return_value=source),
        patch("src.cli.installation.apply_path_update", side_effect=OSError("private detail")),
        patch("src.cli.installation.capture_cli_install_terminal") as capture,
    ):
        result = runner.invoke(
            app,
            ["install", "--target", str(target_dir), "--shell", "zsh", "--update-path"],
            env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "SHELL": "/bin/zsh"},
        )

    assert result.exit_code == 1
    capture.assert_called_once()
    assert capture.call_args.args[0] is CliInstallOutcome.PARTIAL_SUCCESS
    assert capture.call_args.args[1] is CliInstallErrorCategory.PATH_UPDATE


def test_install_command_reports_success_for_path_only_change(runner, tmp_path):
    target_dir = tmp_path / "user-bin"
    target_dir.mkdir()
    source = target_dir / "kickstart"
    source.write_text("#!/bin/sh\n")
    source.chmod(0o755)
    rc_file = tmp_path / ".zshrc"

    with (
        patch("src.cli.installation.current_binary_path", return_value=source),
        patch("src.cli.installation.capture_cli_install_terminal") as capture,
    ):
        result = runner.invoke(
            app,
            [
                "install",
                "--target",
                str(target_dir),
                "--rc-file",
                str(rc_file),
                "--shell",
                "zsh",
                "--update-path",
            ],
            env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "SHELL": "/bin/zsh"},
        )

    assert result.exit_code == 0, result.stdout
    assert rc_file.exists()
    capture.assert_called_once()
    assert capture.call_args.args[0] is CliInstallOutcome.SUCCESS
    assert capture.call_args.args[1] is CliInstallErrorCategory.NONE


def test_install_command_reports_partial_success_when_path_update_cannot_be_resolved(
    runner, tmp_path, single_file_binary
):
    source = single_file_binary
    target_dir = tmp_path / "user-bin"

    with (
        patch("src.cli.installation.current_binary_path", return_value=source),
        patch("src.cli.installation.capture_cli_install_terminal") as capture,
    ):
        result = runner.invoke(
            app,
            ["install", "--target", str(target_dir), "--update-path"],
            env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "SHELL": "/bin/unknown"},
        )

    assert result.exit_code == 0, result.stdout
    assert "Could not infer a shell rc file" in result.stdout
    capture.assert_called_once()
    assert capture.call_args.args[0] is CliInstallOutcome.PARTIAL_SUCCESS
    assert capture.call_args.args[1] is CliInstallErrorCategory.PATH_UPDATE


def test_install_command_captures_interrupt_before_binary_change(runner, tmp_path):
    with (
        patch("src.cli.installation.current_binary_path", side_effect=KeyboardInterrupt),
        patch("src.cli.installation.capture_cli_install_terminal") as capture,
    ):
        result = runner.invoke(
            app,
            ["install", "--target", str(tmp_path / "user-bin"), "--shell", "zsh"],
            env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "SHELL": "/bin/zsh"},
        )

    assert result.exit_code != 0
    capture.assert_called_once()
    assert capture.call_args.args[0] is CliInstallOutcome.CANCELLED
    assert capture.call_args.args[1] is CliInstallErrorCategory.INTERRUPTED
