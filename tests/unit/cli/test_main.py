from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from src.cli.main import (
    _InstallContext,
    _report_install_failure,
    _resolve_install_context,
    app,
    upgrade,
)
from src.model.dto.telemetry import (
    CliArtifactKind,
    CliInstallErrorCategory,
    CliInstallOutcome,
    CliUpgradeChecksumStatus,
    CliUpgradeErrorCategory,
    CliUpgradeOutcome,
)
from src.model.dto.upgrade import UpgradeResult
from src.utils.errors import ExtensionError, KickstartError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config():
    return {"default_language": "python", "github_token": "test-token"}


@patch('src.cli.main.__version__', '1.0.0')
def test_version_command(runner):
    """Test the version command displays the correct version."""
    result = runner.invoke(app, ["version"])
    
    assert result.exit_code == 0
    assert "kickstart v1.0.0" in result.stdout


@patch("src.cli.main.capture_cli_upgrade_terminal")
@patch("src.cli.main.check_for_update")
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
        patch("src.cli.main.check_for_update", side_effect=error),
        patch("src.cli.main.capture_cli_upgrade_terminal") as capture,
        pytest.raises(type(error)),
    ):
        upgrade()

    captured = capture.call_args.args[0]
    assert captured.outcome is outcome
    assert captured.error_category is category


def test_completion_command_bash(runner):
    """Test completion command placeholder."""
    result = runner.invoke(app, ["completion", "bash"])
    
    assert result.exit_code == 0
    assert "Completion not implemented" in result.stdout


def test_completion_command_zsh(runner):
    """Test completion command placeholder."""
    result = runner.invoke(app, ["completion", "zsh"])
    
    assert result.exit_code == 0
    assert "Completion not implemented" in result.stdout


@patch('src.cli.main.create_service')
@patch('src.cli.main.load_config')
def test_create_service_with_args(mock_load_config, mock_create_service, runner, mock_config):
    """Test creating a service with command line arguments."""
    mock_load_config.return_value = mock_config
    
    result = runner.invoke(app, [
        "create", "service", "test-service",
        "--lang", "rust",
        "--gh",
        "--helm",
        "--root", "/tmp"
    ])
    
    assert result.exit_code == 0
    mock_create_service.assert_called_once_with(
        "test-service", "rust", True, mock_config, helm=True, root="/tmp"
    )


@patch('src.cli.main.create_frontend')
@patch('src.cli.main.load_config')
def test_create_frontend_with_args(mock_load_config, mock_create_frontend, runner, mock_config):
    """Test creating a frontend with command line arguments."""
    mock_load_config.return_value = mock_config
    
    result = runner.invoke(app, [
        "create", "frontend", "test-frontend",
        "--gh",
        "--root", "/tmp"
    ])
    
    assert result.exit_code == 0
    mock_create_frontend.assert_called_once_with(
        "test-frontend", True, mock_config, root="/tmp"
    )


@patch('src.cli.main.create_lib')
@patch('src.cli.main.load_config')
def test_create_lib_with_args(mock_load_config, mock_create_lib, runner, mock_config):
    """Test creating a library with command line arguments."""
    mock_load_config.return_value = mock_config
    
    result = runner.invoke(app, [
        "create", "lib", "test-lib",
        "--lang", "go",
        "--root", "/tmp"
    ])
    
    assert result.exit_code == 0
    mock_create_lib.assert_called_once_with(
        "test-lib", "go", False, mock_config, root="/tmp"
    )


@patch('src.cli.main.create_cli')
@patch('src.cli.main.load_config')
def test_create_cli_with_args(mock_load_config, mock_create_cli, runner, mock_config):
    """Test creating a CLI with command line arguments."""
    mock_load_config.return_value = mock_config
    
    result = runner.invoke(app, [
        "create", "cli", "test-cli",
        "--lang", "rust",
        "--root", "/tmp"
    ])
    
    assert result.exit_code == 0
    mock_create_cli.assert_called_once_with(
        "test-cli", "rust", False, mock_config, root="/tmp"
    )


@patch('src.cli.main.create_monorepo')
@patch('src.cli.main.load_config')
def test_create_monorepo_with_args(mock_load_config, mock_create_monorepo, runner, mock_config):
    """Test creating a monorepo with command line arguments."""
    mock_load_config.return_value = mock_config
    
    result = runner.invoke(app, [
        "create", "mono", "test-mono",
        "--helm",
        "--gh",
        "--root", "/tmp"
    ])
    
    assert result.exit_code == 0
    mock_create_monorepo.assert_called_once_with(
        "test-mono", True, mock_config, helm=True, root="/tmp"
    )


@patch('src.cli.main.create_monorepo')
@patch('src.cli.main.load_config')
def test_create_monorepo_with_cloud_and_knowledge(mock_load_config, mock_create_monorepo, runner, mock_config):
    """Test creating a monorepo with workflow profile options."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, [
        "create", "mono", "test-mono",
        "--root", "/tmp",
        "--cloud", "cloudflare",
        "--knowledge", "obsidian",
    ])

    assert result.exit_code == 0
    mock_create_monorepo.assert_called_once_with(
        "test-mono",
        False,
        mock_config,
        helm=False,
        root="/tmp",
        cloud="cloudflare",
        knowledge="obsidian",
    )


@patch('src.cli.main.create_service')
@patch('src.cli.main.load_config')
def test_create_service_with_runtime(mock_load_config, mock_create_service, runner, mock_config):
    """Test creating a service with an explicit execution profile."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, [
        "create", "service", "edge-api",
        "--lang", "typescript",
        "--runtime", "cloudflare-workers",
        "--root", "/tmp",
    ])

    assert result.exit_code == 0
    mock_create_service.assert_called_once_with(
        "edge-api",
        "typescript",
        False,
        mock_config,
        helm=False,
        root="/tmp",
        runtime="cloudflare-workers",
    )


@patch('src.cli.main.create_monorepo')
@patch('src.cli.main.load_config')
def test_create_monorepo_with_runtime(mock_load_config, mock_create_monorepo, runner, mock_config):
    """Test creating a system monorepo with an explicit platform profile."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, [
        "create", "mono", "edge-stack",
        "--cloud", "cloudflare",
        "--runtime", "cloudflare-workers",
        "--root", "/tmp",
    ])

    assert result.exit_code == 0
    mock_create_monorepo.assert_called_once_with(
        "edge-stack",
        False,
        mock_config,
        helm=False,
        root="/tmp",
        cloud="cloudflare",
        runtime="cloudflare-workers",
    )


@patch('src.cli.main.create_system')
@patch('src.cli.main.load_config')
def test_create_system_with_runtime(mock_load_config, mock_create_system, runner, mock_config):
    """Test creating a system with the canonical public project type."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, [
        "create", "system", "platform",
        "--cloud", "aws",
        "--runtime", "kubernetes",
        "--knowledge", "none",
        "--root", "/tmp",
    ])

    assert result.exit_code == 0
    mock_create_system.assert_called_once_with(
        "platform",
        False,
        mock_config,
        helm=False,
        root="/tmp",
        cloud="aws",
        runtime="kubernetes",
    )


@patch('src.cli.main.create_system')
@patch('src.cli.main.load_config')
def test_create_system_with_bun_turbo_workspace_tooling(mock_load_config, mock_create_system, runner, mock_config):
    """Test creating a system with explicit Bun + Turbo workspace tooling."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, [
        "create", "system", "platform",
        "--workspace-tooling", "bun-turbo",
        "--root", "/tmp",
    ])

    assert result.exit_code == 0
    mock_create_system.assert_called_once_with(
        "platform",
        False,
        mock_config,
        helm=False,
        root="/tmp",
        workspace_tooling="bun-turbo",
    )


@patch('src.cli.main.create_service')
@patch('src.cli.main.load_config')
@patch('src.cli.main.Confirm')
@patch('src.cli.main.Prompt')
def test_create_interactive_service(mock_prompt, mock_confirm, mock_load_config, mock_create_service, runner, mock_config):
    """Test creating a service interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["service", "my-service", "/tmp", "rust", "none", "none"]
    mock_confirm.ask.side_effect = [True, True]  # gh=True, helm=True
    
    result = runner.invoke(app, ["create"])
    
    assert result.exit_code == 0
    mock_create_service.assert_called_once_with(
        "my-service", "rust", True, mock_config, helm=True, root="/tmp"
    )


@patch('src.cli.main.create_service')
@patch('src.cli.main.load_config')
@patch('src.cli.main.Confirm')
@patch('src.cli.main.Prompt')
def test_create_interactive_rust_service_can_select_jwt(
    mock_prompt,
    mock_confirm,
    mock_load_config,
    mock_create_service,
    runner,
    mock_config,
):
    """Test selecting JWT for a Rust service interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["service", "my-service", "/tmp", "rust", "none", "jwt"]
    mock_confirm.ask.side_effect = [False, False]

    result = runner.invoke(app, ["create"])

    assert result.exit_code == 0
    mock_create_service.assert_called_once_with(
        "my-service", "rust", False, mock_config, helm=False, root="/tmp", auth="jwt"
    )


@patch('src.cli.main.create_service')
@patch('src.cli.main.load_config')
@patch('src.cli.main.Confirm')
@patch('src.cli.main.Prompt')
def test_create_interactive_typescript_service_can_select_postgres(
    mock_prompt,
    mock_confirm,
    mock_load_config,
    mock_create_service,
    runner,
    mock_config,
):
    """Test selecting Postgres for a TypeScript service interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["service", "my-service", "/tmp", "typescript", "postgres"]
    mock_confirm.ask.side_effect = [False, False]

    result = runner.invoke(app, ["create"])

    assert result.exit_code == 0
    mock_create_service.assert_called_once_with(
        "my-service", "typescript", False, mock_config, helm=False, root="/tmp", database="postgres"
    )


@patch('src.cli.main.create_frontend')
@patch('src.cli.main.load_config')
@patch('src.cli.main.Confirm')
@patch('src.cli.main.Prompt')
def test_create_interactive_frontend(mock_prompt, mock_confirm, mock_load_config, mock_create_frontend, runner, mock_config):
    """Test creating a frontend interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["frontend", "my-frontend", "/tmp", "python"]
    mock_confirm.ask.side_effect = [False]  # gh=False
    
    result = runner.invoke(app, ["create"])
    
    assert result.exit_code == 0
    mock_create_frontend.assert_called_once_with(
        "my-frontend", False, mock_config, root="/tmp"
    )


@patch('src.cli.main.create_lib')
@patch('src.cli.main.load_config')
@patch('src.cli.main.Confirm')
@patch('src.cli.main.Prompt')
def test_create_interactive_lib(mock_prompt, mock_confirm, mock_load_config, mock_create_lib, runner, mock_config):
    """Test creating a library interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["lib", "my-lib", "/tmp", "go"]
    mock_confirm.ask.side_effect = [True]  # gh=True
    
    result = runner.invoke(app, ["create"])
    
    assert result.exit_code == 0
    mock_create_lib.assert_called_once_with(
        "my-lib", "go", True, mock_config, root="/tmp"
    )


@patch('src.cli.main.create_cli')
@patch('src.cli.main.load_config')
@patch('src.cli.main.Confirm')
@patch('src.cli.main.Prompt')
def test_create_interactive_cli(mock_prompt, mock_confirm, mock_load_config, mock_create_cli, runner, mock_config):
    """Test creating a CLI interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["cli", "my-cli", "/tmp", "rust"]
    mock_confirm.ask.side_effect = [False]  # gh=False
    
    result = runner.invoke(app, ["create"])
    
    assert result.exit_code == 0
    mock_create_cli.assert_called_once_with(
        "my-cli", "rust", False, mock_config, root="/tmp"
    )


@patch('src.cli.main.create_monorepo')
@patch('src.cli.main.load_config')
@patch('src.cli.main.Confirm')
@patch('src.cli.main.Prompt')
def test_create_interactive_monorepo(mock_prompt, mock_confirm, mock_load_config, mock_create_monorepo, runner, mock_config):
    """Test creating a monorepo interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["mono", "my-mono", "/tmp", "python"]
    mock_confirm.ask.side_effect = [True, False]  # gh=True, helm=False
    
    result = runner.invoke(app, ["create"])
    
    assert result.exit_code == 0
    mock_create_monorepo.assert_called_once_with(
        "my-mono", True, mock_config, helm=False, root="/tmp"
    )


@patch('src.cli.main.load_config')
def test_create_unsupported_type(mock_load_config, runner, mock_config):
    """Test creating an unsupported project type."""
    mock_load_config.return_value = mock_config
    
    result = runner.invoke(app, ["create", "unsupported", "test", "--root", "/tmp"])

    assert result.exit_code == 1
    assert "Type 'unsupported' not supported" in result.stdout


@patch('src.cli.main.load_config') 
@patch('src.cli.main.Prompt')
def test_create_defaults_root_to_cwd_without_prompting(mock_prompt, mock_load_config, runner, mock_config):
    """A fully specified create must not ambush automation with a root prompt."""
    mock_load_config.return_value = mock_config

    with patch('src.cli.main.create_service') as mock_create_service:
        result = runner.invoke(app, ["create", "service", "test-service"])

        assert result.exit_code == 0
        mock_prompt.ask.assert_not_called()
        mock_create_service.assert_called_once_with(
            "test-service", "python", False, mock_config, helm=False, root=None
        )


def test_helm_option_only_for_service_and_mono():
    """Test that helm option is only prompted for service and mono project types."""
    with patch('src.cli.main.load_config') as mock_load_config, \
         patch('src.cli.main.Prompt') as mock_prompt, \
         patch('src.cli.main.Confirm') as mock_confirm, \
         patch('src.cli.main.create_frontend'):
        
        mock_load_config.return_value = {"default_language": "python"}
        mock_prompt.ask.side_effect = ["frontend", "test", "/tmp", "python"]
        mock_confirm.ask.return_value = False  # gh=False
        
        runner = CliRunner()
        result = runner.invoke(app, ["create"])
        
        assert result.exit_code == 0
        # Confirm.ask should only be called once for GitHub, not for Helm
        assert mock_confirm.ask.call_count == 1


@patch('src.cli.main.load_config')
@patch('src.cli.main.Prompt')
@patch('src.cli.main.Confirm')
def test_interactive_helm_prompt_for_service(mock_confirm, mock_prompt, mock_load_config, runner):
    """Test that helm is prompted for service type in interactive mode."""
    mock_load_config.return_value = {"default_language": "python"}
    mock_prompt.ask.side_effect = ["service", "test-service", "/tmp", "python", "none", "none", "none", "fastapi"]
    mock_confirm.ask.side_effect = [False, True]  # gh=False, helm=True
    
    with patch('src.cli.main.create_service') as mock_create_service:
        result = runner.invoke(app, ["create"])
        
        assert result.exit_code == 0
        # Should prompt for both GitHub and Helm
        assert mock_confirm.ask.call_count == 2
        mock_create_service.assert_called_once_with(
            "test-service", "python", False, {"default_language": "python"}, helm=True, root="/tmp"
        )


@patch('src.cli.main.load_config')
@patch('src.cli.main.Prompt')
@patch('src.cli.main.Confirm')
def test_interactive_helm_prompt_for_mono(mock_confirm, mock_prompt, mock_load_config, runner):
    """Test that helm is prompted for mono type in interactive mode."""
    mock_load_config.return_value = {"default_language": "python"}
    mock_prompt.ask.side_effect = ["mono", "test-mono", "/tmp", "python"]
    mock_confirm.ask.side_effect = [True, False]  # gh=True, helm=False
    
    with patch('src.cli.main.create_monorepo') as mock_create_monorepo:
        result = runner.invoke(app, ["create"])
        
        assert result.exit_code == 0
        # Should prompt for both GitHub and Helm
        assert mock_confirm.ask.call_count == 2
        mock_create_monorepo.assert_called_once_with(
            "test-mono", True, {"default_language": "python"}, helm=False, root="/tmp"
        )


def test_default_values():
    """Test that default values are used when not specified."""
    with patch('src.cli.main.load_config') as mock_load_config, \
         patch('src.cli.main.create_service') as mock_create_service:
        
        mock_load_config.return_value = {"default_language": "python"}
        
        runner = CliRunner()
        result = runner.invoke(app, ["create", "service", "test", "--root", "/tmp"])
        
        assert result.exit_code == 0
        mock_create_service.assert_called_once_with(
            "test", "python", False, {"default_language": "python"}, helm=False, root="/tmp"
        )


@patch('src.cli.main.load_config')
@patch('src.cli.main.Prompt')
def test_config_default_language_used_in_interactive(mock_prompt, mock_load_config, runner):
    """Test that config default language is used in interactive mode."""
    mock_load_config.return_value = {"default_language": "rust"}
    mock_prompt.ask.side_effect = ["lib", "test-lib", "/tmp", "rust"]  # Last rust is the prompted default
    
    with patch('src.cli.main.Confirm') as mock_confirm, \
         patch('src.cli.main.create_lib'):
        
        mock_confirm.ask.return_value = False
        
        result = runner.invoke(app, ["create"])
        
        assert result.exit_code == 0
        # Check that the prompt was called with the config default
        language_prompt_call = [call for call in mock_prompt.ask.call_args_list 
                               if call.args and call.args[0] == "Language"]
        assert len(language_prompt_call) == 1
        assert language_prompt_call[0].kwargs.get("default") == "rust"


def test_typer_app_creation():
    """Test that the Typer app is created with correct help text."""
    assert app.info.help == "kickstart: Full-stack project scaffolding CLI"


def test_command_registration():
    """Test that all expected commands are registered."""
    # Test by trying to get help - if commands are registered, help will show them
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    
    expected_commands = ["version", "upgrade", "completion", "create"]
    for expected_cmd in expected_commands:
        assert expected_cmd in result.stdout


@patch('src.cli.main.create_service')
@patch('src.cli.main.load_config')
def test_create_service_exception_propagation(mock_load_config, mock_create_service, runner):
    """Test that exceptions from create_service are propagated."""
    mock_load_config.return_value = {}
    mock_create_service.side_effect = ValueError("Test error")
    
    # This test should use root prompt, so mock it
    with patch('src.cli.main.Prompt') as mock_prompt:
        mock_prompt.ask.return_value = "/tmp"
        result = runner.invoke(app, ["create", "service", "test"])
    
    # Typer should catch the exception and exit with non-zero code
    assert result.exit_code != 0
    assert "Test error" in result.stdout


@patch('src.cli.main.create_service')
@patch('src.cli.main.load_config')
def test_create_service_validation_error_is_concise(mock_load_config, mock_create_service, runner):
    """Test expected validation errors do not print tracebacks."""
    mock_load_config.return_value = {}
    mock_create_service.side_effect = ExtensionError("cache extension 'redis' is not supported")

    result = runner.invoke(app, ["create", "service", "test", "--root", "/tmp", "--cache", "redis"])

    assert result.exit_code != 0
    assert "cache extension 'redis' is not supported" in result.stdout
    assert "Traceback" not in result.stdout


def test_completion_command_invalid_shell(runner):
    """Test completion command with invalid shell."""
    result = runner.invoke(app, ["completion", "invalid"])

    # Should still work since we just return a placeholder message
    assert result.exit_code == 0
    assert "Completion not implemented" in result.stdout


def _make_single_file_binary(tmp_path):
    source_dir = tmp_path / "src-bin"
    source_dir.mkdir()
    source = source_dir / "kickstart-source"
    source.write_text("#!/bin/sh\necho hi\n")
    source.chmod(0o755)
    return source


def test_install_command_check_mode(runner, tmp_path):
    """`install --check` reports status without modifying the filesystem."""
    source = _make_single_file_binary(tmp_path)
    target_dir = tmp_path / "user-bin"

    with (
        patch("src.cli.main.current_binary_path", return_value=source),
        patch("src.cli.main.capture_cli_install_terminal") as capture,
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


def test_install_command_copies_binary_and_prints_path_hint(runner, tmp_path):
    """Without --update-path the installer copies the binary and prints PATH instructions."""
    source = _make_single_file_binary(tmp_path)
    target_dir = tmp_path / "user-bin"

    with (
        patch("src.cli.main.current_binary_path", return_value=source),
        patch("src.cli.main.capture_cli_install_terminal") as capture,
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


def test_install_command_updates_rc_file(runner, tmp_path):
    """`install --update-path` writes a managed block into the rc file."""
    source = _make_single_file_binary(tmp_path)
    target_dir = tmp_path / "user-bin"
    rc_file = tmp_path / ".zshrc"
    rc_file.write_text("# existing\n")

    with patch("src.cli.main.current_binary_path", return_value=source):
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


def test_install_command_skips_path_when_already_on_path(runner, tmp_path):
    """When the install dir is already on PATH we never touch the rc file."""
    source = _make_single_file_binary(tmp_path)
    target_dir = tmp_path / "user-bin"
    rc_file = tmp_path / ".zshrc"

    with patch("src.cli.main.current_binary_path", return_value=source):
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


def test_install_command_refuses_overwrite_without_force(runner, tmp_path):
    """Without --force the install command exits non-zero if the destination exists."""
    source = _make_single_file_binary(tmp_path)
    target_dir = tmp_path / "user-bin"
    target_dir.mkdir()
    (target_dir / "kickstart").write_text("placeholder")

    with (
        patch("src.cli.main.current_binary_path", return_value=source),
        patch("src.cli.main.capture_cli_install_terminal") as capture,
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


def test_install_command_reports_partial_success_when_path_update_fails(runner, tmp_path):
    source = _make_single_file_binary(tmp_path)
    target_dir = tmp_path / "user-bin"

    with (
        patch("src.cli.main.current_binary_path", return_value=source),
        patch("src.cli.main._apply_path_update", side_effect=OSError("private detail")),
        patch("src.cli.main.capture_cli_install_terminal") as capture,
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


def test_install_command_captures_interrupt_before_binary_change(runner, tmp_path):
    with (
        patch("src.cli.main.current_binary_path", side_effect=KeyboardInterrupt),
        patch("src.cli.main.capture_cli_install_terminal") as capture,
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


def test_uninstall_command_removes_binary(runner, tmp_path):
    """The uninstall command removes the binary and optionally cleans the rc file."""
    target_dir = tmp_path / "user-bin"
    target_dir.mkdir()
    (target_dir / "kickstart").write_text("#!/bin/sh\n")
    rc_file = tmp_path / ".zshrc"
    rc_file.write_text(
        "# existing\n"
        "# >>> kickstart install >>>\n"
        f'export PATH="{target_dir}:$PATH"\n'
        "# <<< kickstart install <<<\n"
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


# --- Tests targeting the DRY helpers introduced by the refactor. -----------


def test_resolve_install_context_defaults_to_xdg(tmp_path, monkeypatch):
    """When --target is omitted the resolved install_dir falls back to ~/.local/bin."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.setattr("src.cli.main.path_contains", lambda *_args, **_kw: False)
    ctx = _resolve_install_context(target=None, shell=None, rc_file=None)
    # The default install_dir module-level constant is computed at import time, so we just
    # assert the structural invariants instead of comparing against the live HOME.
    assert ctx.install_dir.name == "bin"
    assert ctx.shell == "zsh"
    assert ctx.rc_file is not None
    assert ctx.rc_file.name == ".zshrc"
    assert ctx.snippet.startswith("export PATH=")
    assert ctx.already_on_path is False


def test_resolve_install_context_honors_explicit_overrides(tmp_path):
    """Explicit --target / --rc-file / --shell win over detection."""
    target = tmp_path / "custom-bin"
    rc = tmp_path / "rc"
    ctx = _resolve_install_context(target=target, shell="fish", rc_file=rc)
    assert ctx.install_dir == target
    assert ctx.shell == "fish"
    assert ctx.rc_file == rc
    assert ctx.snippet == f"fish_add_path -gp {target}"


def test_resolve_install_context_expands_user_paths(tmp_path, monkeypatch):
    """Tilde-prefixed paths should be expanded against HOME for both --target and --rc-file."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHELL", "/bin/zsh")
    ctx = _resolve_install_context(
        target=Path("~/bin"),
        shell=None,
        rc_file=Path("~/.zshrc-override"),
    )
    assert ctx.install_dir == tmp_path / "bin"
    assert ctx.rc_file == tmp_path / ".zshrc-override"


def test_report_install_failure_converts_kickstart_error(capsys):
    """A KickstartError inside the helper exits non-zero with a uniform red banner."""
    with pytest.raises(typer.Exit) as excinfo:
        with _report_install_failure("Install"):
            raise KickstartError("nope")
    assert excinfo.value.exit_code == 1
    out = capsys.readouterr().out
    assert "Install failed: nope" in out


def test_report_install_failure_converts_file_not_found(capsys):
    """FileNotFoundError is caught and reported under the same banner."""
    with pytest.raises(typer.Exit):
        with _report_install_failure("Uninstall"):
            raise FileNotFoundError("missing")
    out = capsys.readouterr().out
    assert "Uninstall failed: missing" in out


def test_report_install_failure_lets_other_exceptions_through():
    """Exceptions we don't recognize should not be silently swallowed."""
    with pytest.raises(RuntimeError):
        with _report_install_failure("Install"):
            raise RuntimeError("not handled")


def test_install_context_check_does_not_modify_filesystem(runner, tmp_path):
    """--check must not create the target directory or the rc file."""
    source = _make_single_file_binary(tmp_path)
    target_dir = tmp_path / "untouched"
    rc_file = tmp_path / ".not-touched"

    with patch("src.cli.main.current_binary_path", return_value=source):
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


def test_install_update_path_without_resolvable_rc(runner, tmp_path):
    """--update-path with an unknown shell prints manual instructions and exits 0."""
    source = _make_single_file_binary(tmp_path)
    target_dir = tmp_path / "user-bin"

    with patch("src.cli.main.current_binary_path", return_value=source):
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


def test_install_context_dataclass_is_frozen():
    """_InstallContext should be immutable so commands can't mutate shared state."""
    ctx = _InstallContext(
        install_dir=Path("/tmp/x"),
        app_root=Path("/tmp/x-app"),
        shell="zsh",
        rc_file=Path("/tmp/rc"),
        snippet='export PATH="/tmp/x:$PATH"',
        already_on_path=False,
    )
    with pytest.raises(Exception):
        ctx.install_dir = Path("/tmp/y")  # type: ignore[misc]
