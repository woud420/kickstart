"""CLI diagnostics and install paths preserve literal Rich markup."""

from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from src.cli.install_context import report_failure
from src.cli.main import app
from src.utils.errors import KickstartError
from src.utils.handoff import HANDOFF_COMMAND


@pytest.mark.parametrize("marker", ["[/oops]", "[red]name"])
@pytest.mark.parametrize("error_type", [KickstartError, ValueError, RuntimeError])
def test_create_failure_keeps_literal_message(marker: str, error_type: type[Exception]) -> None:
    message = f"failed for {marker}"
    with (
        patch("src.cli.create.load_config", return_value={}),
        patch("src.cli.create.create_service", side_effect=error_type(message)),
        patch("src.cli.create.capture_scaffold_create_terminal") as capture,
    ):
        result = CliRunner().invoke(app, ["create", "service", "demo"])

    assert result.exit_code == 1
    assert message in result.stdout
    capture.assert_called_once()


@pytest.mark.parametrize("marker", ["[/oops]", "[red]name"])
def test_install_failure_keeps_literal_message(marker: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(typer.Exit) as failure:
        with report_failure("Install"):
            raise OSError(f"failed for {marker}")

    assert failure.value.exit_code == 1
    assert f"Install failed: failed for {marker}" in capsys.readouterr().out


@pytest.mark.parametrize("marker", ["[/oops]", "[red]name"])
def test_install_status_keeps_literal_path(marker: str, tmp_path: Path, single_file_binary: Path) -> None:
    target = tmp_path / marker
    with patch("src.cli.installation.current_binary_path", return_value=single_file_binary):
        result = CliRunner().invoke(
            app,
            ["install", "--check", "--target", str(target), "--shell", "zsh"],
            env={"COLUMNS": "1000"},
        )

    assert result.exit_code == 0
    assert str(target) in result.stdout
    assert not target.exists()


@pytest.mark.parametrize("marker", ["[/oops]", "[red]name"])
def test_handoff_failure_keeps_literal_path(marker: str, tmp_path: Path) -> None:
    stage = tmp_path / marker
    with patch("src.cli.updates.capture_cli_upgrade_terminal") as capture:
        result = CliRunner().invoke(
            app,
            [HANDOFF_COMMAND, "--stage-dir", str(stage), "--phase", "finalize"],
            env={"COLUMNS": "1000"},
        )

    assert result.exit_code == 1
    assert str(stage) in result.stdout
    capture.assert_called_once()
