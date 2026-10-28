"""Run generated Python code against a disposable Postgres database."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.generator.service import ServiceGenerator


@pytest.mark.parametrize("auth", [None, "jwt"], ids=["postgres", "postgres-jwt"])
def test_generated_postgres_contract(tmp_path: Path, auth: str | None) -> None:
    if not os.environ.get("KICKSTART_TEST_POSTGRES_DSN"):
        pytest.skip("set KICKSTART_TEST_POSTGRES_DSN to a disposable Postgres database")

    ServiceGenerator("api", "python", False, {}, root=str(tmp_path), database="postgres", auth=auth).create()
    project = tmp_path / "api"
    probe = Path(__file__).parents[1] / "fixtures" / "python_postgres_probe.py"
    # A separate process imports the generated src package, not kickstart's src.
    result = subprocess.run(
        [os.environ.get("KICKSTART_GENERATED_PYTHON", sys.executable), str(probe), auth or "none"],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project)},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
