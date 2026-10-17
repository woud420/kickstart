import errno
import json
from pathlib import Path
import sys

import pytest

from scripts import generated_make_test_eval as runner


def _report(root: Path):
    from scripts.generated_eval_report import GeneratedEvalReport, MakeTestResult, RunProvenance

    provenance = RunProvenance(
        run_id="fixture-run",
        started_at_utc="2026-10-17T07:00:00+00:00",
        finished_at_utc="2026-10-17T07:01:00+00:00",
        source_revision="abc123",
        source_dirty=False,
        execution_context="test host",
        command=("python", "scripts/generated_make_test_eval.py", "--prewarm"),
        tools={"python": "3.14", "bun": "1.3.5"},
        workers=12,
        timeout_seconds=90,
    )
    passed = MakeTestResult(root / "good", "service", "container", "{}", 0, 0.1, "pass", "")
    failed = MakeTestResult(root / "bad", "frontend", "", "{}", 2, 0.2, "dependency unavailable", "missing package")
    return GeneratedEvalReport(
        report_path=root / "results.md",
        output_root=root / "matrix",
        target="test",
        dependency_mode="cached",
        cache_root=root / "cache",
        provenance=provenance,
        results=(passed, failed),
        prewarm_requested=True,
        prewarm_workers=2,
        prewarm_results=(failed,),
    )


def test_report_retains_dated_context_and_consistent_runtime_and_prewarm_counts(tmp_path: Path) -> None:
    from dataclasses import asdict
    from scripts.generated_eval_report import write_report

    report = _report(tmp_path)
    summary = write_report(report)
    payload = json.loads(Path(summary.json_report).read_text())
    markdown = report.report_path.read_text()

    assert payload["schema_version"] == 1
    assert payload["summary"] == json.loads(json.dumps(asdict(summary)))
    assert summary.makefiles == 2 and summary.passed == 1 and summary.failed == 1
    assert summary.prewarm.targets == 1 and summary.prewarm.failed == 1
    assert payload["results"][1]["returncode"] == 2
    assert "fixture-run" in markdown and "2026-10-17T07:00:00+00:00" in markdown
    assert "abc123" in markdown and "test host" in markdown and "bun: 1.3.5" in markdown
    assert "## Prewarm Failures" in markdown and "missing package" in markdown
    assert "- Passed: 1" in markdown and "- Failed: 1" in markdown


def test_failed_report_replace_preserves_previous_proof_and_removes_temporary_file(tmp_path: Path, monkeypatch) -> None:
    from scripts import generated_eval_report as reporting

    report = _report(tmp_path)
    report.report_path.write_text("previous markdown")
    sidecar = Path(str(report.report_path) + ".json")
    sidecar.write_text("previous structured proof")

    def full_disk(*_args):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(reporting.os, "replace", full_disk)
    with pytest.raises(OSError, match="No space left"):
        reporting.write_report(report)

    assert report.report_path.read_text() == "previous markdown"
    assert sidecar.read_text() == "previous structured proof"
    assert not list(tmp_path.glob("*.tmp"))


def test_empty_matrix_is_a_usage_error_without_a_zero_test_report(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "report.md"
    monkeypatch.setattr(
        sys, "argv", ["generated_make_test_eval.py", "--output-root", str(tmp_path), "--report", str(path)]
    )
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2
    assert not path.exists() and not Path(str(path) + ".json").exists()


def test_report_failure_emits_no_completed_console_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    from scripts import generated_eval_report as reporting

    report = _report(tmp_path)
    (tmp_path / "Makefile").write_text("test:\n\t@true\n")
    (tmp_path / ".kickstart").mkdir()
    (tmp_path / ".kickstart/scaffold.json").write_text("{}\n")
    report.report_path.write_text("previous markdown")
    monkeypatch.setattr(
        sys,
        "argv",
        ["generated_make_test_eval.py", "--output-root", str(tmp_path), "--report", str(report.report_path)],
    )
    monkeypatch.setattr(runner, "run_make_tests", lambda *_args, **_kwargs: report.results)
    monkeypatch.setattr(runner, "_capture_provenance", lambda *_args, **_kwargs: report.provenance)

    replace = reporting.os.replace

    def full_disk(source, destination):
        if Path(destination) == report.report_path:
            raise OSError(errno.ENOSPC, "No space left on device")
        return replace(source, destination)

    monkeypatch.setattr(reporting.os, "replace", full_disk)
    with pytest.raises(OSError, match="No space left"):
        runner.main()
    assert capsys.readouterr().out == ""
    assert report.report_path.read_text() == "previous markdown"
    payload = json.loads(Path(str(report.report_path) + ".json").read_text())
    assert payload["summary"]["provenance"]["run_id"] == "fixture-run"


def test_provenance_captures_allowlisted_tools_without_environment_values(monkeypatch) -> None:
    import subprocess

    monkeypatch.setenv("PRIVATE_TOKEN", "fixture-private-value")
    monkeypatch.setattr(runner.platform, "platform", lambda: "fixture host")

    def command(args, **_kwargs):
        if args[:2] == ("git", "rev-parse"):
            return subprocess.CompletedProcess(args, 0, "abc123\n", "")
        if args[:2] == ("git", "status"):
            return subprocess.CompletedProcess(args, 0, " M scripts/example.py\n", "")
        if args[0] == "cargo":
            raise subprocess.TimeoutExpired(args, 10)
        assert args[0] in {"bun", "node", "rustc", "go", "cmake", "poetry", "make"}
        return subprocess.CompletedProcess(args, 0, "fixture version\nmore detail\n", "")

    monkeypatch.setattr(runner.subprocess, "run", command)
    provenance = runner._capture_provenance("start", "finish", workers=12, timeout_seconds=90)

    assert provenance.source_revision == "abc123" and provenance.source_dirty is True
    assert provenance.execution_context == "fixture host"
    assert provenance.tools["cargo"] == "unavailable"
    assert provenance.tools["bun"] == "fixture version"
    assert "fixture-private-value" not in repr(provenance)


def test_provenance_marks_unavailable_source_state_as_unknown(monkeypatch) -> None:
    def unavailable(*_args, **_kwargs):
        raise FileNotFoundError("tool unavailable")

    monkeypatch.setattr(runner.subprocess, "run", unavailable)
    provenance = runner._capture_provenance("start", "finish", workers=1, timeout_seconds=90)

    assert provenance.source_revision == "unknown" and provenance.source_dirty is None
    assert provenance.tools["bun"] == "unavailable"


def test_report_records_opt_in_cleanup_and_affected_component_count(tmp_path: Path) -> None:
    from dataclasses import replace
    from scripts.generated_eval_report import write_report

    report = _report(tmp_path)
    result = replace(report.results[0], cleaned_artifacts=(".venv",))
    summary = write_report(replace(report, results=(result,), clean_completed=True))

    payload = json.loads(Path(summary.json_report).read_text())
    assert payload["summary"]["clean_completed"] is True
    assert payload["summary"]["cleaned_components"] == 1
    assert payload["results"][0]["cleaned_artifacts"] == [".venv"]
    assert "Clean completed dependency/cache directories: True" in report.report_path.read_text()


def test_cleanup_warnings_are_persisted_without_changing_completed_test_counts(tmp_path: Path) -> None:
    from dataclasses import replace
    from scripts.generated_eval_report import write_report

    report = _report(tmp_path)
    result = replace(report.results[0], cleanup_errors=("node_modules: OSError errno=66",))
    summary = write_report(replace(report, results=(result,), clean_completed=True))

    payload = json.loads(Path(summary.json_report).read_text())
    assert summary.passed == 1 and summary.failed == 0
    assert summary.cleanup_failed_components == 1 and summary.cleaned_components == 0
    assert payload["results"][0]["cleanup_errors"] == ["node_modules: OSError errno=66"]
    assert "Components with cleanup warnings: 1" in report.report_path.read_text()
    assert "node_modules: OSError errno=66" in report.report_path.read_text()
