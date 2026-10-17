"""Human and JSON consumers share bounded drift findings and exit codes."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.cli.main import app
from src.generator.service import ServiceGenerator


@pytest.fixture
def project(tmp_path: Path) -> Path:
    ServiceGenerator("api", "python", False, {}, root=str(tmp_path)).create()
    return tmp_path / "api"


def test_human_output_names_classes_and_finding(project: Path) -> None:
    (project / ".github/workflows/ci.yml").write_text("jobs: {custom: {}}\n")
    result = CliRunner().invoke(app, ["drift", str(project)])
    assert result.exit_code == 1, result.output
    assert "stale" in result.output and "ci:" in result.output
    assert "standard job 'check'" in result.output


def test_adopt_and_drift_report_the_same_ci_finding(project: Path) -> None:
    (project / ".github/workflows/ci.yml").write_text("jobs: {custom: {}}\n")
    runner = CliRunner()
    standalone = runner.invoke(app, ["drift", str(project), "--json"])
    adopted = runner.invoke(app, ["adopt", str(project), "--check", "--json"])
    assert standalone.exit_code == adopted.exit_code == 1
    assert json.loads(adopted.output)["drift"] == json.loads(standalone.output)
    human = runner.invoke(app, ["adopt", str(project), "--check"])
    assert human.exit_code == 1 and "standard job 'check'" in human.output


def test_unrecorded_coverage_and_usage_errors_are_distinct(project: Path, tmp_path: Path) -> None:
    path = project / ".kickstart/scaffold.json"
    manifest = json.loads(path.read_text())
    del manifest["ownership"]
    path.write_text(json.dumps(manifest))
    runner = CliRunner()
    result = runner.invoke(app, ["drift", str(project), "--json"])
    assert result.exit_code == 1
    assert not json.loads(result.output)["recorded"]
    assert runner.invoke(app, ["drift", str(tmp_path / "missing")]).exit_code == 2
    assert runner.invoke(app, ["drift", str(tmp_path)]).exit_code == 2


def test_json_with_brackets_and_long_paths_is_valid(tmp_path: Path) -> None:
    root = tmp_path / ("[literal]-" + "long" * 25)
    root.mkdir()
    ServiceGenerator("api", "python", False, {}, root=str(root)).create()
    result = CliRunner().invoke(app, ["drift", str(root / "api"), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["root"] == str(root / "api")
