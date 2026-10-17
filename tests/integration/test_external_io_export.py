"""Read-only external I/O export through the real source CLI entrypoint."""

import json
from pathlib import Path

import pytest

from tests.integration.conftest import KickstartRunner


@pytest.mark.parametrize("format", ["json", "markdown"])
def test_declared_map_exports_from_unmanaged_repository(
    kickstart_run: KickstartRunner, repo_root: Path, tmp_path: Path, format: str
) -> None:
    root = tmp_path / "unmanaged"
    (root / "src").mkdir(parents=True)
    (root / "docs/contracts").mkdir(parents=True)
    (root / "src/app.py").write_text("# Source is cited by the caller, not semantically analyzed\n")
    (root / "docs/contracts/README.md").write_text("# User-owned contract\n")
    source = tmp_path / "declared.json"
    source.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "coverage": "partial",
                "project": "declared",
                "surfaces": [
                    {
                        "surface": {"kind": "http", "method": "GET", "path": "/declared"},
                        "evidence": [{"path": "src/app.py", "start_line": 1}],
                    }
                ],
                "unknowns": [{"category": "all", "reason": "Other surfaces have not been inspected"}],
            }
        )
    )
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    result = kickstart_run(
        "export",
        "external-io",
        str(root),
        "--input",
        str(source),
        "--format",
        format,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    if format == "json":
        data = json.loads(result.stdout)
        assert data["project"] == "declared"
        assert data["coverage"] == "partial"
    else:
        assert "## External I/O" in result.stdout
        assert "src/app.py:1" in result.stdout
    assert {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    assert not (root / ".kickstart").exists()


def test_invalid_citation_fails_without_partial_output(
    kickstart_run: KickstartRunner, repo_root: Path, tmp_path: Path
) -> None:
    source = tmp_path / "declared.json"
    source.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "coverage": "partial",
                "project": "declared",
                "surfaces": [
                    {
                        "surface": {"kind": "http", "method": "GET", "path": "/"},
                        "evidence": [{"path": "missing.py", "start_line": 1}],
                    }
                ],
                "unknowns": [],
            }
        )
    )

    result = kickstart_run(
        "export",
        "external-io",
        str(tmp_path),
        "--input",
        str(source),
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "cited source is not a file" in result.stderr
    assert sorted(p.name for p in tmp_path.iterdir()) == ["declared.json"]
