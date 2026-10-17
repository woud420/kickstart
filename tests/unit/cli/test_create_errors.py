"""Literal user input remains visible in create command failures."""

import pytest
from typer.testing import CliRunner

from src.cli.main import app


@pytest.mark.parametrize("project_type", ["[/oops]", "[red]service"])
def test_create_reports_literal_invalid_type(project_type: str) -> None:
    result = CliRunner().invoke(app, ["create", project_type, "demo"])

    assert result.exit_code == 1
    assert project_type in result.stdout
    assert "not supported" in result.stdout
    assert type(result.exception).__name__ != "MarkupError"
