"""kickstart export backstage end-to-end on real generator output."""

from __future__ import annotations

from pathlib import Path

from tests.integration.conftest import KickstartRunner


def test_export_backstage_round_trip(
    kickstart_run: KickstartRunner, repo_root: Path, tmp_path: Path
) -> None:
    completed = kickstart_run(
        "create",
        "service",
        "exported-api",
        "--lang",
        "python",
        "--database",
        "postgres",
        "--root",
        str(tmp_path),
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    project = tmp_path / "exported-api"

    created = kickstart_run("export", "backstage", str(project), cwd=repo_root, capture_output=True, text=True)
    catalog = project / "catalog-info.yaml"
    first = catalog.read_text(encoding="utf-8")

    rerun = kickstart_run("export", "backstage", str(project), cwd=repo_root, capture_output=True, text=True)
    second = catalog.read_text(encoding="utf-8")

    catalog.write_text(
        first.replace("owner: group:default/unknown", "owner: group:default/team-api"), encoding="utf-8"
    )
    after_edit = kickstart_run(
        "export", "backstage", str(project), cwd=repo_root, capture_output=True, text=True
    )

    assert created.returncode == 0, created.stdout + created.stderr
    assert "created" in created.stdout
    assert "postgres" in first and "name: exported-api" in first
    assert rerun.returncode == 0
    assert "unchanged" in rerun.stdout
    assert first == second
    assert after_edit.returncode == 0
    assert "owner: group:default/team-api" in catalog.read_text(encoding="utf-8")
