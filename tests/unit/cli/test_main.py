import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from src.cli.main import app


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
    assert "Kickstart v1.0.0" in result.stdout


@patch('src.cli.main.check_for_update')
def test_upgrade_command(mock_check_for_update, runner):
    """Test the upgrade command calls check_for_update."""
    result = runner.invoke(app, ["upgrade"])
    
    assert result.exit_code == 0
    mock_check_for_update.assert_called_once()


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
        "--lang", "java",
        "--root", "/tmp"
    ])
    
    assert result.exit_code == 0
    mock_create_cli.assert_called_once_with(
        "test-cli", "java", False, mock_config, root="/tmp"
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


@patch('src.cli.main.create_service')
@patch('src.cli.main.load_config')
@patch('src.cli.main.Confirm')
@patch('src.cli.main.Prompt')
def test_create_interactive_service(mock_prompt, mock_confirm, mock_load_config, mock_create_service, runner, mock_config):
    """Test creating a service interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["service", "my-service", "/tmp", "rust"]
    mock_confirm.ask.side_effect = [True, True]  # gh=True, helm=True
    
    result = runner.invoke(app, ["create"])
    
    assert result.exit_code == 0
    mock_create_service.assert_called_once_with(
        "my-service", "rust", True, mock_config, helm=True, root="/tmp"
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
    
    assert result.exit_code == 0
    assert "Type 'unsupported' not supported" in result.stdout


@patch('src.cli.main.load_config') 
@patch('src.cli.main.Prompt')
def test_create_prompts_for_root_when_missing(mock_prompt, mock_load_config, runner, mock_config):
    """Test that root directory is prompted for when missing with project_type specified."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.return_value = "/custom/path"
    
    with patch('src.cli.main.create_service') as mock_create_service:
        result = runner.invoke(app, ["create", "service", "test-service"])
        
        assert result.exit_code == 0
        mock_prompt.ask.assert_called_with("Where should the project be created?")
        mock_create_service.assert_called_once_with(
            "test-service", "python", False, mock_config, helm=False, root="/custom/path"
        )


def test_helm_option_only_for_service_and_mono():
    """Test that helm option is only prompted for service and mono project types."""
    with patch('src.cli.main.load_config') as mock_load_config, \
         patch('src.cli.main.Prompt') as mock_prompt, \
         patch('src.cli.main.Confirm') as mock_confirm, \
         patch('src.cli.main.create_frontend') as mock_create:
        
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
    mock_prompt.ask.side_effect = ["service", "test-service", "/tmp", "python"]
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
         patch('src.cli.main.create_lib') as mock_create_lib:
        
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
    assert app.info.help == "Kickstart: Full-stack project scaffolding CLI"


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


def test_completion_command_invalid_shell(runner):
    """Test completion command with invalid shell."""
    result = runner.invoke(app, ["completion", "invalid"])
    
    # Should still work since we just return a placeholder message
    assert result.exit_code == 0
    assert "Completion not implemented" in result.stdout