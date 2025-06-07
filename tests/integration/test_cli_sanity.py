from typer.testing import CliRunner
from src.cli.main import app

def test_help_output():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Kickstart" in result.stdout
    assert "create" in result.stdout

