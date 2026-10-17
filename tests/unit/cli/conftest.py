"""Shared CLI command fixtures."""

from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def mock_config() -> dict[str, str]:
    return {"default_language": "python", "github_token": "test-token"}


@pytest.fixture
def single_file_binary(tmp_path: Path) -> Path:
    source_dir = tmp_path / "src-bin"
    source_dir.mkdir()
    source = source_dir / "kickstart-source"
    source.write_text("#!/bin/sh\necho hi\n")
    source.chmod(0o755)
    return source
