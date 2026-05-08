from typer.testing import CliRunner

from src.cli.app import app
from src.main import main

runner = CliRunner()


def test_check_command_succeeds() -> None:
    result = runner.invoke(app, ["check"])

    assert result.exit_code == 0
    assert result.output.strip() == "ok: local"


def test_help_flag_succeeds() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "check" in result.output


def test_version_flag_succeeds() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "{{ package_name }} 0.1.0" in result.output


def test_main_forwards_to_typer(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["{{ package_name }}", "check"])
    try:
        main()
    except SystemExit as error:
        assert error.code == 0
