"""kickstart plan end-to-end: generate a scaffold, drift it, read the report."""

from __future__ import annotations

import json
from pathlib import Path

from tests.integration.conftest import KickstartRunner


def _create_service(kickstart_run: KickstartRunner, repo_root: Path, root: Path) -> Path:
    completed = kickstart_run(
        "create",
        "service",
        "planned-api",
        "--lang",
        "python",
        "--root",
        str(root),
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, f"generation failed:\n{completed.stdout}\n{completed.stderr}"
    return root / "planned-api"


def test_plan_is_green_on_a_fresh_scaffold(
    kickstart_run: KickstartRunner, repo_root: Path, tmp_path: Path
) -> None:
    project = _create_service(kickstart_run, repo_root, tmp_path)

    completed = kickstart_run(
        "plan", str(project), "--json", cwd=repo_root, capture_output=True, text=True
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["in_sync"] is True


def test_plan_reports_fence_edits_but_tolerates_user_content(
    kickstart_run: KickstartRunner, repo_root: Path, tmp_path: Path
) -> None:
    project = _create_service(kickstart_run, repo_root, tmp_path)
    agents = project / "AGENTS.md"

    agents.write_text(
        agents.read_text(encoding="utf-8") + "\n## Team conventions\n\nUser-owned notes.\n",
        encoding="utf-8",
    )
    outside_only = kickstart_run("plan", str(project), cwd=repo_root, capture_output=True, text=True)

    agents.write_text(
        agents.read_text(encoding="utf-8").replace("orientation surface", "renamed surface"),
        encoding="utf-8",
    )
    drifted = kickstart_run("plan", str(project), cwd=repo_root, capture_output=True, text=True)

    assert outside_only.returncode == 0, outside_only.stdout + outside_only.stderr
    assert drifted.returncode == 1
    assert "content-drift" in drifted.stdout
    assert "renamed surface" in drifted.stdout


def test_plan_without_a_manifest_is_a_usage_error(
    kickstart_run: KickstartRunner, repo_root: Path, tmp_path: Path
) -> None:
    completed = kickstart_run("plan", str(tmp_path), cwd=repo_root, capture_output=True, text=True)

    assert completed.returncode == 2


def test_generated_scaffold_is_adopted_as_managed(
    kickstart_run: KickstartRunner, repo_root: Path, tmp_path: Path
) -> None:
    """The stack's central premise: real generator output achieves Level 2."""
    project = _create_service(kickstart_run, repo_root, tmp_path)

    completed = kickstart_run(
        "adopt", str(project), "--check", "--json", cwd=repo_root, capture_output=True, text=True
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["complete"] is True
    assert payload["achieved_level"] == "managed"
    assert payload["claimed_level"] == "managed"
