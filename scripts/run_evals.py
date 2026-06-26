"""One entrypoint for kickstart's eval suite, in tiers.

Modeled on the tiered-suite practice from headroom's benchmark harness
(`docs/decisions/headroom-benchmark-learnings.md`): a single command runs a
named tier and prints one summary table, so "did the evals pass" has exactly
one answer per tier.

Tiers:

- ``smoke``: the headline bootstrap case. Seconds with a warm cache.
- ``pr``: what CI gates per pull request — the four fast bootstrap cases
  plus the scaffold-weight baseline check.
- ``full``: the whole bootstrap matrix, token savings with baselines, and
  the determinism + website-examples test suites. What the weekly run and
  release validation use.

Usage::

    PYTHONPATH=$(pwd) poetry run python scripts/run_evals.py --tier pr
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import tempfile
import time


class UnknownTierError(Exception):
    """Raised when a requested tier does not exist."""

    def __init__(self, tier: str, known: tuple[str, ...]) -> None:
        super().__init__(f"unknown tier '{tier}'; known tiers: {', '.join(known)}")


@dataclass(frozen=True)
class EvalStep:
    """One command within a tier."""

    name: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class StepResult:
    """Outcome of one executed step."""

    step: EvalStep
    returncode: int
    seconds: float
    tail: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


_SCRATCH = Path(tempfile.gettempdir())
_PYTHON = sys.executable

_BOOTSTRAP_COMMON = (
    _PYTHON,
    "scripts/bootstrap_eval.py",
    "--output-root",
    str(_SCRATCH / "kickstart-run-evals-bootstrap"),
    "--cache-root",
    str(_SCRATCH / "kickstart-eval-cache"),
    "--report",
    str(_SCRATCH / "kickstart-run-evals-bootstrap.md"),
)

_PR_BOOTSTRAP_CASES = ("python-cli-kickstart-like", "python-service", "typescript-worker", "rust-cli")

_TOKEN_BASELINES = (
    _PYTHON,
    "scripts/token_savings_eval.py",
    "--check-baselines",
    "--output-root",
    str(_SCRATCH / "kickstart-run-evals-tokens"),
    "--report",
    str(_SCRATCH / "kickstart-run-evals-tokens.md"),
)

_PYTEST = (_PYTHON, "-m", "pytest", "-q")

TIERS: dict[str, tuple[EvalStep, ...]] = {
    "smoke": (
        EvalStep("bootstrap (headline case)", (*_BOOTSTRAP_COMMON, "--cases", "python-cli-kickstart-like")),
    ),
    "pr": (
        EvalStep("bootstrap (CI cases)", (*_BOOTSTRAP_COMMON, "--cases", *_PR_BOOTSTRAP_CASES)),
        EvalStep("scaffold weight baselines", _TOKEN_BASELINES),
    ),
    "full": (
        EvalStep("bootstrap (full matrix)", _BOOTSTRAP_COMMON),
        EvalStep("scaffold weight baselines", _TOKEN_BASELINES),
        EvalStep("determinism tests", (*_PYTEST, "tests/integration/test_scaffold_determinism.py")),
        EvalStep("website examples tests", (*_PYTEST, "tests/integration/test_website_examples.py")),
    ),
}


def tier_steps(tier: str) -> tuple[EvalStep, ...]:
    """Resolve a tier name, failing loudly on unknown tiers."""
    try:
        return TIERS[tier]
    except KeyError as error:
        raise UnknownTierError(tier, tuple(TIERS)) from error


def run_step(step: EvalStep, repo_root: Path) -> StepResult:
    """Run one step, capturing its tail for the summary."""
    started = time.monotonic()
    completed = subprocess.run(step.args, cwd=repo_root, capture_output=True, text=True, check=False)
    elapsed = time.monotonic() - started
    tail = "\n".join((completed.stdout + completed.stderr).strip().splitlines()[-8:])
    return StepResult(step=step, returncode=completed.returncode, seconds=elapsed, tail=tail)


def render_summary(tier: str, results: tuple[StepResult, ...]) -> str:
    """Render the single summary table for a tier run."""
    lines = [
        f"# kickstart evals — tier: {tier}",
        "",
        "| step | result | seconds |",
        "| --- | --- | ---: |",
    ]
    for result in results:
        lines.append(f"| {result.step.name} | {'pass' if result.passed else 'FAIL'} | {result.seconds:.1f} |")
    lines.append("")
    for result in results:
        if not result.passed:
            lines.extend([f"## FAIL: {result.step.name} (exit {result.returncode})", "", result.tail, ""])
    return "\n".join(lines)


def main() -> int:
    """Run an eval tier from the command line."""
    parser = argparse.ArgumentParser(description="Run kickstart's eval suite by tier.")
    parser.add_argument("--tier", choices=sorted(TIERS), default="smoke")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    results = tuple(run_step(step, repo_root) for step in tier_steps(args.tier))
    print(render_summary(args.tier, results))
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
