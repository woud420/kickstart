"""Root command registration, version and completion behavior."""

from unittest.mock import patch

from typer.testing import CliRunner


from src.cli.main import app


@patch("src.cli.main.__version__", "1.0.0")
def test_version_command(runner):
    """Test the version command displays the correct version."""
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "kickstart v1.0.0" in result.stdout


def test_command_registration():
    """Test that all expected commands are registered."""
    # Test by trying to get help - if commands are registered, help will show them
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    expected_commands = ["version", "upgrade", "completion", "create"]
    for expected_cmd in expected_commands:
        assert expected_cmd in result.stdout
