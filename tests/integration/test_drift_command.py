"""Drift findings are shared by the standalone command and adoption check."""

import json
from pathlib import Path

from tests.integration.conftest import KickstartRunner


def test_drift_checks_a_fresh_scaffold_without_writing(
    kickstart_run: KickstartRunner, repo_root: Path, tmp_path: Path
) -> None:
    created = kickstart_run(
        "create",
        "service",
        "drift-api",
        "--lang",
        "python",
        "--root",
        str(tmp_path),
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert created.returncode == 0, created.stdout + created.stderr
    project = tmp_path / "drift-api"
    before = {str(p.relative_to(project)): p.read_bytes() for p in project.rglob("*") if p.is_file()}

    completed = kickstart_run("drift", str(project), "--json", cwd=repo_root, capture_output=True, text=True)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["in_sync"] and payload["recorded"]
    assert {e["class"] for e in payload["entries"]} == {"scaffold", "docs", "ci", "artifact"}
    assert payload["seeds_excluded"] > 0
    assert before == {str(p.relative_to(project)): p.read_bytes() for p in project.rglob("*") if p.is_file()}
