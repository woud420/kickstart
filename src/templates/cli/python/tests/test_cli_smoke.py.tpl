import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from src.cli.app import app

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


def test_module_entry_point_dispatches_check() -> None:
    project = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "check"],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok: local"
