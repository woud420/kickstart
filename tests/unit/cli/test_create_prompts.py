"""Interactive create choices and option defaults."""

from unittest.mock import patch


from tests.unit.cli.command_helpers import CREATE

from src.cli.main import app


@patch.object(CREATE, "create_service")
@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Confirm")
@patch.object(CREATE, "Prompt")
def test_create_interactive_service(
    mock_prompt, mock_confirm, mock_load_config, mock_create_service, runner, mock_config
):
    """Test creating a service interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["service", "my-service", "/tmp", "rust", "none", "none"]
    mock_confirm.ask.side_effect = [True, True]  # gh=True, helm=True

    result = runner.invoke(app, ["create"])

    assert result.exit_code == 0
    mock_create_service.assert_called_once_with("my-service", "rust", True, mock_config, helm=True, root="/tmp")


@patch.object(CREATE, "create_service")
@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Confirm")
@patch.object(CREATE, "Prompt")
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


@patch.object(CREATE, "create_service")
@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Confirm")
@patch.object(CREATE, "Prompt")
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


@patch.object(CREATE, "create_frontend")
@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Confirm")
@patch.object(CREATE, "Prompt")
def test_create_interactive_frontend(
    mock_prompt, mock_confirm, mock_load_config, mock_create_frontend, runner, mock_config
):
    """Test creating a frontend interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["frontend", "my-frontend", "/tmp", "python"]
    mock_confirm.ask.side_effect = [False]  # gh=False

    result = runner.invoke(app, ["create"])

    assert result.exit_code == 0
    mock_create_frontend.assert_called_once_with("my-frontend", False, mock_config, root="/tmp")


@patch.object(CREATE, "create_lib")
@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Confirm")
@patch.object(CREATE, "Prompt")
def test_create_interactive_lib(mock_prompt, mock_confirm, mock_load_config, mock_create_lib, runner, mock_config):
    """Test creating a library interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["lib", "my-lib", "/tmp", "go"]
    mock_confirm.ask.side_effect = [True]  # gh=True

    result = runner.invoke(app, ["create"])

    assert result.exit_code == 0
    mock_create_lib.assert_called_once_with("my-lib", "go", True, mock_config, root="/tmp")


@patch.object(CREATE, "create_cli")
@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Confirm")
@patch.object(CREATE, "Prompt")
def test_create_interactive_cli(mock_prompt, mock_confirm, mock_load_config, mock_create_cli, runner, mock_config):
    """Test creating a CLI interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["cli", "my-cli", "/tmp", "rust"]
    mock_confirm.ask.side_effect = [False]  # gh=False

    result = runner.invoke(app, ["create"])

    assert result.exit_code == 0
    mock_create_cli.assert_called_once_with("my-cli", "rust", False, mock_config, root="/tmp")


@patch.object(CREATE, "create_monorepo")
@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Confirm")
@patch.object(CREATE, "Prompt")
def test_create_interactive_monorepo(
    mock_prompt, mock_confirm, mock_load_config, mock_create_monorepo, runner, mock_config
):
    """Test creating a monorepo interactively."""
    mock_load_config.return_value = mock_config
    mock_prompt.ask.side_effect = ["mono", "my-mono", "/tmp", "python"]
    mock_confirm.ask.side_effect = [True, False]  # gh=True, helm=False

    result = runner.invoke(app, ["create"])

    assert result.exit_code == 0
    mock_create_monorepo.assert_called_once_with("my-mono", True, mock_config, helm=False, root="/tmp")


@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Prompt")
@patch.object(CREATE, "Confirm")
def test_interactive_helm_prompt_for_service(mock_confirm, mock_prompt, mock_load_config, runner):
    """Test that helm is prompted for service type in interactive mode."""
    mock_load_config.return_value = {"default_language": "python"}
    mock_prompt.ask.side_effect = ["service", "test-service", "/tmp", "python", "none", "none", "none", "fastapi"]
    mock_confirm.ask.side_effect = [False, True]  # gh=False, helm=True

    with patch.object(CREATE, "create_service") as mock_create_service:
        result = runner.invoke(app, ["create"])

        assert result.exit_code == 0
        # Should prompt for both GitHub and Helm
        assert mock_confirm.ask.call_count == 2
        mock_create_service.assert_called_once_with(
            "test-service", "python", False, {"default_language": "python"}, helm=True, root="/tmp"
        )


@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Prompt")
@patch.object(CREATE, "Confirm")
def test_interactive_helm_prompt_for_mono(mock_confirm, mock_prompt, mock_load_config, runner):
    """Test that helm is prompted for mono type in interactive mode."""
    mock_load_config.return_value = {"default_language": "python"}
    mock_prompt.ask.side_effect = ["mono", "test-mono", "/tmp", "python"]
    mock_confirm.ask.side_effect = [True, False]  # gh=True, helm=False

    with patch.object(CREATE, "create_monorepo") as mock_create_monorepo:
        result = runner.invoke(app, ["create"])

        assert result.exit_code == 0
        # Should prompt for both GitHub and Helm
        assert mock_confirm.ask.call_count == 2
        mock_create_monorepo.assert_called_once_with(
            "test-mono", True, {"default_language": "python"}, helm=False, root="/tmp"
        )


@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Prompt")
def test_config_default_language_used_in_interactive(mock_prompt, mock_load_config, runner):
    """Test that config default language is used in interactive mode."""
    mock_load_config.return_value = {"default_language": "rust"}
    mock_prompt.ask.side_effect = ["lib", "test-lib", "/tmp", "rust"]  # Last rust is the prompted default

    with patch.object(CREATE, "Confirm") as mock_confirm, patch.object(CREATE, "create_lib"):
        mock_confirm.ask.return_value = False

        result = runner.invoke(app, ["create"])

        assert result.exit_code == 0
        # Check that the prompt was called with the config default
        language_prompt_call = [
            call for call in mock_prompt.ask.call_args_list if call.args and call.args[0] == "Language"
        ]
        assert len(language_prompt_call) == 1
        assert language_prompt_call[0].kwargs.get("default") == "rust"
