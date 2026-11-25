"""Shared CLI failure exits print literal messages and keep exit codes."""

import pytest
import typer

from src.cli.failures import exit_with_error


@pytest.mark.parametrize("code", [1, 2])
def test_exit_with_error_prints_literal_message_and_chains(code: int, capsys: pytest.CaptureFixture[str]) -> None:
    error = ValueError("missing [red]name[/]")

    with pytest.raises(typer.Exit) as raised:
        exit_with_error(error, code=code)

    assert raised.value.exit_code == code
    assert raised.value.__cause__ is error
    assert "missing [red]name[/]" in capsys.readouterr().out
