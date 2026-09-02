"""Shared fixtures for the unit suite.

The managed-install handoff (`src.utils.handoff`) replaces the running process
with `os.execve`. A unit test that reaches it by accident would replace the
pytest process with whatever fake launcher it built, so every unit test starts
with the handoff disarmed; tests that exercise the chain opt in through the
`handoff_chain` fixture, which runs each hop in-process instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from src.model.dto.upgrade import UpgradeResult
from src.utils import handoff


class ProcessReplaced(BaseException):
    """Raised by the fake exec where the real one would replace the process.

    Derives from BaseException, like SystemExit, so it passes through the
    ``except Exception`` boundaries that real code keeps around an exec.
    """

    def __init__(self, result: UpgradeResult) -> None:
        super().__init__(result.outcome.value)
        self.result = result


@dataclass(frozen=True)
class ExecCall:
    """One recorded `exec_launcher` invocation."""

    launcher: Path
    args: tuple[str, ...]
    env: dict[str, str]

    @property
    def phase(self) -> handoff.HandoffPhase:
        return handoff.HandoffPhase(self.args[self.args.index("--phase") + 1])

    @property
    def stage_dir(self) -> Path:
        return Path(self.args[self.args.index("--stage-dir") + 1])


@dataclass
class HandoffChain:
    """Runs handoff hops in-process and records every exec the chain requested."""

    calls: list[ExecCall] = field(default_factory=list)
    replaced: type[ProcessReplaced] = ProcessReplaced

    def exec(self, launcher: Path, args: list[str], env: dict[str, str]) -> None:
        call = ExecCall(launcher=launcher, args=tuple(args), env=dict(env))
        self.calls.append(call)
        assert args[0] == handoff.HANDOFF_COMMAND, args
        assert launcher.is_file(), f"exec target {launcher} does not exist"
        loaded = handoff.load_handoff(call.stage_dir)
        if call.phase is handoff.HandoffPhase.ACTIVATE:
            result = handoff.activate(loaded, call.stage_dir)
        else:
            result = handoff.finalize(loaded, call.stage_dir)
        raise ProcessReplaced(result)


_REAL_EXEC_LAUNCHER = handoff.exec_launcher


@pytest.fixture
def real_exec_launcher():
    """The production `exec_launcher`, for tests that stub `os.execve` themselves."""
    return _REAL_EXEC_LAUNCHER


@pytest.fixture(autouse=True)
def _disarm_process_handoff(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(launcher: Path, args: list[str], env: dict[str, str]) -> None:
        raise AssertionError(f"test attempted a real process handoff to {launcher}; use the handoff_chain fixture")

    monkeypatch.setattr(handoff, "exec_launcher", refuse)


@pytest.fixture
def handoff_chain(monkeypatch: pytest.MonkeyPatch) -> HandoffChain:
    """Route `exec_launcher` through an in-process chain runner."""
    chain = HandoffChain()
    monkeypatch.setattr(handoff, "exec_launcher", chain.exec)
    return chain
