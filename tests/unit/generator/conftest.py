"""Keep generator unit-test writes outside the source checkout."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_generator_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
