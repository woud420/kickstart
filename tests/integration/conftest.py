"""Shared fixtures for the integration test suite.

The integration tests invoke `kickstart` via `python -m src.cli.main` in a
subprocess. Both the argv prefix and the env override are identical across
every test, so we expose them as fixtures instead of repeating the boilerplate.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest


REPO_ROOT: Path = Path(__file__).resolve().parents[2]

# subprocess.run can return either a str-typed or bytes-typed CompletedProcess
# depending on whether the caller passes `text=True`. The integration tests use
# both shapes, so we keep the return type wide and let pytest catch real type
# mismatches at the call site.
KickstartCompleted = subprocess.CompletedProcess[str | bytes]
KickstartRunner = Callable[..., KickstartCompleted]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the kickstart repository root."""
    return REPO_ROOT


@pytest.fixture
def kickstart_env(repo_root: Path) -> dict[str, str]:
    """`os.environ`-shaped dict that lets `python -m src.cli.main` resolve `src.*`."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)
    return env


@pytest.fixture(scope="session")
def kickstart_argv() -> list[str]:
    """argv prefix for invoking kickstart from a subprocess in tests."""
    return [sys.executable, "-m", "src.cli.main"]


@pytest.fixture
def kickstart_run(kickstart_argv: list[str], kickstart_env: dict[str, str]) -> KickstartRunner:
    """Return a `subprocess.run`-style callable preconfigured for kickstart.

    Usage::

        kickstart_run("create", "service", "hello-api", cwd=tmp, check=True)

    Extra keyword arguments are passed straight through to ``subprocess.run``.
    ``env`` defaults to the PYTHONPATH-augmented copy of ``os.environ``.
    """

    def _run(*args: str, **kwargs: object) -> KickstartCompleted:
        kwargs.setdefault("env", kickstart_env)
        return subprocess.run([*kickstart_argv, *args], **kwargs)  # type: ignore[call-overload]

    return _run
