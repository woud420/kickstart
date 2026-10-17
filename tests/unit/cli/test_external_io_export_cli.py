"""External I/O export through the public CLI."""

import json
from pathlib import Path

import pytest
from click import unstyle
from typer import rich_utils
from typer.testing import CliRunner

from src.cli.main import app


def _declaration() -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "coverage": "partial",
            "project": "declared-project",
            "surfaces": [
                {
                    "surface": {"kind": "http", "method": "GET", "path": "/declared"},
                    "evidence": [{"path": "app.py", "start_line": 1}],
                }
            ],
            "unknowns": [{"category": "all", "reason": "Other surfaces are uninspected"}],
        }
    )


@pytest.mark.parametrize("project", ["sample", "café " + chr(0x1F600)])
def test_external_io_unknowns_export_is_read_only(tmp_path: Path, project: str) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    declaration = {
        "schema_version": 1,
        "coverage": "partial",
        "project": project,
        "surfaces": [],
        "unknowns": [{"category": "all", "reason": "Source surfaces have not been inspected"}],
    }
    source = tmp_path / "declaration.json"
    source.write_text(json.dumps(declaration), encoding="utf-8")

    result = CliRunner().invoke(app, ["export", "external-io", str(root), "--input", str(source)])

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == declaration
    assert list(root.iterdir()) == []


@pytest.mark.parametrize("format", ["json", "markdown"])
def test_both_outputs_are_deterministic_without_touching_repository(tmp_path: Path, format: str) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "app.py").write_text("# User declaration is not semantic discovery\n")
    (root / "README.md").write_text("User-authored docs\n")
    (root / ".kickstart").mkdir()
    (root / ".kickstart/scaffold.json").write_text("not a readable manifest\n")
    source = tmp_path / "declaration.json"
    source.write_text(_declaration())
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    args = ["export", "external-io", str(root), "--input", str(source), "--format", format]

    first = CliRunner().invoke(app, args)
    second = CliRunner().invoke(app, args)

    assert first.exit_code == second.exit_code == 0, first.output + second.output
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr == ""
    assert {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    assert source.read_text() == _declaration()
    assert "User declaration" not in first.stdout
    if format == "json":
        payload = json.loads(first.stdout)
        assert payload["project"] == "declared-project"
        assert payload["coverage"] == "partial"
    else:
        assert first.stdout.startswith("## External I/O\n")
        assert "Coverage: partial." in first.stdout
        assert "app.py:1" in first.stdout


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("{", "invalid external I/O JSON"),
        (_declaration().replace('"schema_version": 1', '"schema_version": 2'), "schema_version"),
        (_declaration().replace('"start_line": 1', '"start_line": 2'), "line count"),
        (_declaration().replace('"app.py"', '"missing.py"'), "not a file"),
        (_declaration().replace('"app.py"', '"../outside.py"'), "root-relative"),
    ],
)
def test_invalid_declarations_leave_stdout_and_sources_untouched(
    tmp_path: Path, replacement: str, message: str
) -> None:
    (tmp_path / "app.py").write_text("source\n")
    source = tmp_path / "input.json"
    source.write_text(replacement)
    result = CliRunner().invoke(app, ["export", "external-io", str(tmp_path), "--input", str(source)])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert message in result.stderr
    assert (tmp_path / "app.py").read_text() == "source\n"
    assert source.read_text() == replacement


def test_environment_values_are_never_expanded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXPORT_TEST_TOKEN", "never-export-this-value")
    payload = json.loads(_declaration())
    payload["surfaces"][0]["surface"] = {"kind": "config", "name": "EXPORT_TEST_TOKEN", "source": "env"}
    (tmp_path / "app.py").write_text("source\n")
    source = tmp_path / "input.json"
    source.write_text(json.dumps(payload))
    result = CliRunner().invoke(app, ["export", "external-io", str(tmp_path), "--input", str(source)])
    assert result.exit_code == 0, result.output
    assert "EXPORT_TEST_TOKEN" in result.stdout
    assert "never-export-this-value" not in result.output


def test_invalid_output_format_is_usage_error(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    source.write_text(_declaration())
    result = CliRunner().invoke(
        app,
        [
            "export",
            "external-io",
            str(tmp_path),
            "--input",
            str(source),
            "--format",
            "yaml",
        ],
    )
    assert result.exit_code == 2
    assert "Invalid value" in result.stderr


@pytest.mark.parametrize("force_terminal", [False, True])
def test_input_is_required_and_existing_export_is_still_registered(
    monkeypatch: pytest.MonkeyPatch, force_terminal: bool
) -> None:
    monkeypatch.setattr(rich_utils, "FORCE_TERMINAL", force_terminal)
    runner = CliRunner()
    missing = runner.invoke(app, ["export", "external-io"])
    assert missing.exit_code == 2
    assert "--input" in unstyle(missing.stderr)
    help_output = runner.invoke(app, ["export", "--help"])
    assert help_output.exit_code == 0
    assert "backstage" in unstyle(help_output.stdout)
    assert "external-io" in unstyle(help_output.stdout)


def test_root_defaults_to_current_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("source\n")
    source = tmp_path / "input.json"
    source.write_text(_declaration())
    result = CliRunner().invoke(app, ["export", "external-io", "--input", str(source)])
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize("codepoint", [0xD800, 0xDFFF])
def test_non_utf8_declaration_fails_before_stdout(tmp_path: Path, codepoint: int) -> None:
    payload = {
        "schema_version": 1,
        "coverage": "partial",
        "project": "bad" + chr(codepoint),
        "surfaces": [],
        "unknowns": [{"category": "all", "reason": "Uninspected"}],
    }
    source = tmp_path / "input.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = CliRunner().invoke(app, ["export", "external-io", str(tmp_path), "--input", str(source)])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert "UTF-8" in result.stderr
