"""Create validation, defaults and failure reporting."""

from unittest.mock import patch

from typer.testing import CliRunner


from tests.unit.cli.command_helpers import CREATE

from src.cli.main import app
from src.utils.errors import ExtensionError


@patch.object(CREATE, "load_config")
def test_create_unsupported_type(mock_load_config, runner, mock_config):
    """Test creating an unsupported project type."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, ["create", "unsupported", "test", "--root", "/tmp"])

    assert result.exit_code == 1
    assert "Type 'unsupported' not supported" in result.stdout


@patch.object(CREATE, "load_config")
@patch.object(CREATE, "Prompt")
def test_create_defaults_root_to_cwd_without_prompting(mock_prompt, mock_load_config, runner, mock_config):
    """A fully specified create must not ambush automation with a root prompt."""
    mock_load_config.return_value = mock_config

    with patch.object(CREATE, "create_service") as mock_create_service:
        result = runner.invoke(app, ["create", "service", "test-service"])

        assert result.exit_code == 0
        mock_prompt.ask.assert_not_called()
        mock_create_service.assert_called_once_with("test-service", "python", False, mock_config, helm=False, root=None)


def test_helm_option_only_for_service_and_mono():
    """Test that helm option is only prompted for service and mono project types."""
    with (
        patch.object(CREATE, "load_config") as mock_load_config,
        patch.object(CREATE, "Prompt") as mock_prompt,
        patch.object(CREATE, "Confirm") as mock_confirm,
        patch.object(CREATE, "create_frontend"),
    ):
        mock_load_config.return_value = {"default_language": "python"}
        mock_prompt.ask.side_effect = ["frontend", "test", "/tmp", "python"]
        mock_confirm.ask.return_value = False  # gh=False

        runner = CliRunner()
        result = runner.invoke(app, ["create"])

        assert result.exit_code == 0
        # Confirm.ask should only be called once for GitHub, not for Helm
        assert mock_confirm.ask.call_count == 1


def test_default_values():
    """Test that default values are used when not specified."""
    with (
        patch.object(CREATE, "load_config") as mock_load_config,
        patch.object(CREATE, "create_service") as mock_create_service,
    ):
        mock_load_config.return_value = {"default_language": "python"}

        runner = CliRunner()
        result = runner.invoke(app, ["create", "service", "test", "--root", "/tmp"])

        assert result.exit_code == 0
        mock_create_service.assert_called_once_with(
            "test", "python", False, {"default_language": "python"}, helm=False, root="/tmp"
        )


@patch.object(CREATE, "create_service")
@patch.object(CREATE, "load_config")
def test_create_service_exception_propagation(mock_load_config, mock_create_service, runner):
    """Test that exceptions from create_service are propagated."""
    mock_load_config.return_value = {}
    mock_create_service.side_effect = ValueError("Test error")

    # This test should use root prompt, so mock it
    with patch.object(CREATE, "Prompt") as mock_prompt:
        mock_prompt.ask.return_value = "/tmp"
        result = runner.invoke(app, ["create", "service", "test"])

    # Typer should catch the exception and exit with non-zero code
    assert result.exit_code != 0
    assert "Test error" in result.stdout


@patch.object(CREATE, "create_service")
@patch.object(CREATE, "load_config")
def test_create_service_validation_error_is_concise(mock_load_config, mock_create_service, runner):
    """Test expected validation errors do not print tracebacks."""
    mock_load_config.return_value = {}
    mock_create_service.side_effect = ExtensionError("cache extension 'redis' is not supported")

    result = runner.invoke(app, ["create", "service", "test", "--root", "/tmp", "--cache", "redis"])

    assert result.exit_code != 0
    assert "cache extension 'redis' is not supported" in result.stdout
    assert "Traceback" not in result.stdout
