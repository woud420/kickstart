import pytest

from scripts.run_evals import TIERS, EvalStep, StepResult, UnknownTierError, render_summary, tier_steps


def test_every_tier_has_steps_and_smoke_is_smallest() -> None:
    assert set(TIERS) == {"smoke", "pr", "full"}
    assert all(steps for steps in TIERS.values())
    assert len(TIERS["smoke"]) < len(TIERS["pr"]) < len(TIERS["full"])


def test_tier_steps_rejects_unknown_tier() -> None:
    with pytest.raises(UnknownTierError, match="unknown tier 'nope'"):
        tier_steps("nope")


@pytest.mark.parametrize("case", ["python-service-sqlite", "frontend"])
def test_pr_tier_runs_regression_bootstrap_cases(case: str) -> None:
    step = tier_steps("pr")[0]
    assert case in step.args


def test_pr_tier_gates_weight_baselines() -> None:
    names = [step.name for step in tier_steps("pr")]

    assert "scaffold weight baselines" in names


def test_render_summary_marks_failures_with_tail() -> None:
    step = EvalStep("demo", ("true",))
    results = (
        StepResult(step=step, returncode=0, seconds=1.2, tail="ok"),
        StepResult(step=step, returncode=1, seconds=0.4, tail="boom: detail"),
    )

    summary = render_summary("pr", results)

    assert "| demo | pass | 1.2 |" in summary
    assert "| demo | FAIL | 0.4 |" in summary
    assert "## FAIL: demo (exit 1)" in summary
    assert "boom: detail" in summary
