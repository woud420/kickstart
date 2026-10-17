"""Installation, read-only status and uninstallation behavior."""

from unittest.mock import patch


from tests.unit.cli.command_helpers import INSTALL

from src.cli.main import app
from src.model.dto.telemetry import (
    CliInstallErrorCategory,
    CliInstallOutcome,
)


def test_install_from_nested_payload_refuses_and_points_at_upgrade(runner, tmp_path):
    """ENG-205 fallback: `install --force` from inside the app root must not delete itself."""
    app_root = tmp_path / "share" / "kickstart"
    nested = app_root / "current" / ".kickstart" / "current"
    (nested / "_internal").mkdir(parents=True)
    (app_root / "current" / "_internal").mkdir()
    running = nested / "kickstart"
    running.write_text("#!/bin/sh\n")
    running.chmod(0o755)

    with (
        patch.object(INSTALL, "current_binary_path", return_value=running),
        patch.object(INSTALL, "capture_cli_install_terminal") as capture,
    ):
        result = runner.invoke(
            app,
            ["install", "--target", str(tmp_path / "bin"), "--app-dir", str(app_root), "--force"],
        )

    assert result.exit_code == 1
    assert "Install failed" in result.stdout
    assert "kickstart upgrade" in result.stdout
    assert running.exists()
    assert capture.call_args.args[0] is CliInstallOutcome.FAILED
    assert capture.call_args.args[1] is CliInstallErrorCategory.EXPECTED_ERROR


def test_install_command_check_mode(runner, tmp_path, single_file_binary):
    """`install --check` reports status without modifying the filesystem."""
    source = single_file_binary
    target_dir = tmp_path / "user-bin"

    with (
        patch.object(INSTALL, "current_binary_path", return_value=source),
        patch.object(INSTALL, "capture_cli_install_terminal") as capture,
    ):
        result = runner.invoke(
            app,
            ["install", "--target", str(target_dir), "--check", "--shell", "zsh"],
            env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "SHELL": "/bin/zsh"},
        )

    assert result.exit_code == 0
    assert "Install status" in result.stdout
    assert "missing" in result.stdout
    assert not (target_dir / "kickstart").exists()
    capture.assert_not_called()


def test_install_command_copies_binary_and_prints_path_hint(runner, tmp_path, single_file_binary):
    """Without --update-path the installer copies the binary and prints PATH instructions."""
    source = single_file_binary
    target_dir = tmp_path / "user-bin"

    with (
        patch.object(INSTALL, "current_binary_path", return_value=source),
        patch.object(INSTALL, "capture_cli_install_terminal") as capture,
    ):
        result = runner.invoke(
            app,
            ["install", "--target", str(target_dir), "--shell", "zsh"],
            env={
                "PATH": "/usr/bin:/bin",
                "HOME": str(tmp_path),
                "SHELL": "/bin/zsh",
                "COLUMNS": "400",
                "TERM": "dumb",
            },
        )

    assert result.exit_code == 0, result.stdout
    assert (target_dir / "kickstart").exists()
    assert f'export PATH="{target_dir}:$PATH"' in result.stdout
    assert "not on your PATH" in result.stdout
    capture.assert_called_once()
    assert capture.call_args.args[0].value == "success"
    assert capture.call_args.args[1].value == "none"
    assert capture.call_args.args[2].value == "single_file"


def test_install_command_updates_rc_file(runner, tmp_path, single_file_binary):
    """`install --update-path` writes a managed block into the rc file."""
    source = single_file_binary
    target_dir = tmp_path / "user-bin"
    rc_file = tmp_path / ".zshrc"
    rc_file.write_text("# existing\n")

    with patch.object(INSTALL, "current_binary_path", return_value=source):
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
    contents = rc_file.read_text()
    assert "# existing" in contents
    assert f'export PATH="{target_dir}:$PATH"' in contents


def test_install_command_skips_path_when_already_on_path(runner, tmp_path, single_file_binary):
    """When the install dir is already on PATH we never touch the rc file."""
    source = single_file_binary
    target_dir = tmp_path / "user-bin"
    rc_file = tmp_path / ".zshrc"

    with patch.object(INSTALL, "current_binary_path", return_value=source):
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
            env={"PATH": str(target_dir), "HOME": str(tmp_path), "SHELL": "/bin/zsh"},
        )

    assert result.exit_code == 0
    assert "already on your PATH" in result.stdout
    assert not rc_file.exists()


def test_install_command_refuses_overwrite_without_force(runner, tmp_path, single_file_binary):
    """Without --force the install command exits non-zero if the destination exists."""
    source = single_file_binary
    target_dir = tmp_path / "user-bin"
    target_dir.mkdir()
    (target_dir / "kickstart").write_text("placeholder")

    with (
        patch.object(INSTALL, "current_binary_path", return_value=source),
        patch.object(INSTALL, "capture_cli_install_terminal") as capture,
    ):
        result = runner.invoke(
            app,
            ["install", "--target", str(target_dir), "--shell", "zsh"],
            env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "SHELL": "/bin/zsh"},
        )

    assert result.exit_code != 0
    capture.assert_called_once()
    assert capture.call_args.args[0].value == "failed"
    assert capture.call_args.args[1].value == "destination_conflict"


def test_uninstall_command_removes_binary(runner, tmp_path):
    """The uninstall command removes the binary and optionally cleans the rc file."""
    target_dir = tmp_path / "user-bin"
    target_dir.mkdir()
    (target_dir / "kickstart").write_text("#!/bin/sh\n")
    rc_file = tmp_path / ".zshrc"
    rc_file.write_text(
        f'# existing\n# >>> kickstart install >>>\nexport PATH="{target_dir}:$PATH"\n# <<< kickstart install <<<\n'
    )

    result = runner.invoke(
        app,
        [
            "uninstall",
            "--target",
            str(target_dir),
            "--rc-file",
            str(rc_file),
            "--shell",
            "zsh",
            "--clean-path",
        ],
        env={"HOME": str(tmp_path), "SHELL": "/bin/zsh"},
    )

    assert result.exit_code == 0, result.stdout
    assert not (target_dir / "kickstart").exists()
    assert "# >>> kickstart install >>>" not in rc_file.read_text()


def test_uninstall_command_when_nothing_installed(runner, tmp_path):
    """The uninstall command is graceful when the binary is not present."""
    result = runner.invoke(
        app,
        ["uninstall", "--target", str(tmp_path / "missing")],
        env={"HOME": str(tmp_path), "SHELL": "/bin/zsh"},
    )

    assert result.exit_code == 0
    assert "Nothing to uninstall" in result.stdout


def test_install_context_check_does_not_modify_filesystem(runner, tmp_path, single_file_binary):
    """--check must not create the target directory or the rc file."""
    source = single_file_binary
    target_dir = tmp_path / "untouched"
    rc_file = tmp_path / ".not-touched"

    with patch.object(INSTALL, "current_binary_path", return_value=source):
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
                "--check",
            ],
            env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "SHELL": "/bin/zsh", "COLUMNS": "400", "TERM": "dumb"},
        )

    assert result.exit_code == 0
    assert not target_dir.exists()
    assert not rc_file.exists()
    assert "Install status" in result.stdout


def test_install_update_path_without_resolvable_rc(runner, tmp_path, single_file_binary):
    """--update-path with an unknown shell prints manual instructions and exits 0."""
    source = single_file_binary
    target_dir = tmp_path / "user-bin"

    with patch.object(INSTALL, "current_binary_path", return_value=source):
        result = runner.invoke(
            app,
            [
                "install",
                "--target",
                str(target_dir),
                "--shell",
                "unknown-shell",
                "--update-path",
            ],
            env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "SHELL": "", "COLUMNS": "400", "TERM": "dumb"},
        )

    assert result.exit_code == 0
    assert (target_dir / "kickstart").exists()
    assert "Could not infer a shell rc file" in result.stdout


def test_uninstall_with_clean_path_no_block_present(runner, tmp_path):
    """uninstall --clean-path against an rc file with no managed block reports gracefully."""
    target_dir = tmp_path / "user-bin"
    target_dir.mkdir()
    (target_dir / "kickstart").write_text("#!/bin/sh\n")
    rc_file = tmp_path / ".zshrc"
    rc_file.write_text("# user content only\n")

    result = runner.invoke(
        app,
        [
            "uninstall",
            "--target",
            str(target_dir),
            "--rc-file",
            str(rc_file),
            "--shell",
            "zsh",
            "--clean-path",
        ],
        env={"HOME": str(tmp_path), "SHELL": "/bin/zsh", "COLUMNS": "400", "TERM": "dumb"},
    )

    assert result.exit_code == 0
    assert "No managed PATH block" in result.stdout
    assert rc_file.read_text() == "# user content only\n"
