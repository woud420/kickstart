"""Persist one typed generated-project evaluation as Markdown and JSON."""

from collections import Counter
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shlex
import tempfile
from typing import Literal

DependencyMode = Literal["network", "cached", "offline"]


@dataclass(frozen=True)
class MakeTestResult:
    """Result from one generated component Makefile."""

    path: Path
    kind: str
    platform: str
    artifacts: str
    returncode: int
    duration_seconds: float
    reason: str
    output_tail: str
    cleaned_artifacts: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunProvenance:
    """Allowlisted execution facts; never capture the process environment."""

    run_id: str
    started_at_utc: str
    finished_at_utc: str
    source_revision: str
    source_dirty: bool | None
    execution_context: str
    command: tuple[str, ...]
    tools: dict[str, str]
    workers: int
    timeout_seconds: int


@dataclass(frozen=True)
class PrewarmSummary:
    requested: bool
    targets: int
    workers: int
    passed: int
    failed: int
    by_reason: dict[str, int]


@dataclass(frozen=True)
class EvaluationSummary:
    target: str
    dependency_mode: DependencyMode
    cache_root: str
    output_root: str
    prewarm: PrewarmSummary
    makefiles: int
    passed: int
    failed: int
    by_reason: dict[str, int]
    clean_completed: bool
    cleaned_components: int
    provenance: RunProvenance
    report: str
    json_report: str


@dataclass(frozen=True)
class GeneratedEvalReport:
    report_path: Path
    output_root: Path
    target: str
    dependency_mode: DependencyMode
    cache_root: Path
    provenance: RunProvenance
    results: tuple[MakeTestResult, ...]
    clean_completed: bool = False
    prewarm_requested: bool = False
    prewarm_workers: int = 0
    prewarm_results: tuple[MakeTestResult, ...] = ()

    def summary(self) -> EvaluationSummary:
        results = Counter(result.reason for result in self.results)
        prewarm = Counter(result.reason for result in self.prewarm_results)
        return EvaluationSummary(
            target=self.target,
            dependency_mode=self.dependency_mode,
            cache_root=str(self.cache_root) if self.dependency_mode != "network" else "default tool caches",
            output_root=str(self.output_root),
            prewarm=PrewarmSummary(
                requested=self.prewarm_requested,
                targets=len(self.prewarm_results),
                workers=self.prewarm_workers,
                passed=prewarm.get("pass", 0),
                failed=len(self.prewarm_results) - prewarm.get("pass", 0),
                by_reason=dict(sorted(prewarm.items())),
            ),
            makefiles=len(self.results),
            passed=results.get("pass", 0),
            failed=len(self.results) - results.get("pass", 0),
            by_reason=dict(sorted(results.items())),
            clean_completed=self.clean_completed,
            cleaned_components=sum(bool(result.cleaned_artifacts) for result in self.results),
            provenance=self.provenance,
            report=str(self.report_path),
            json_report=str(self.report_path) + ".json",
        )


def write_report(report: GeneratedEvalReport) -> EvaluationSummary:
    """Return console totals only after both proof files have been persisted."""
    summary = report.summary()
    payload = {
        "schema_version": 1,
        "summary": asdict(summary),
        "results": [asdict(result) for result in report.results],
        "prewarm_results": [asdict(result) for result in report.prewarm_results],
    }
    _atomic_write(Path(summary.json_report), json.dumps(payload, default=str, indent=2, sort_keys=True) + "\n")
    _atomic_write(report.report_path, _markdown(report, summary))
    return summary


def _markdown(report: GeneratedEvalReport, summary: EvaluationSummary) -> str:
    provenance = summary.provenance
    lines = [
        "# Generated Make Test Eval",
        "",
        f"- Run ID: `{provenance.run_id}`",
        f"- Started (UTC): {provenance.started_at_utc}",
        f"- Finished (UTC): {provenance.finished_at_utc}",
        f"- Source revision: `{provenance.source_revision}` (dirty: {provenance.source_dirty})",
        f"- Execution context: {provenance.execution_context}",
        f"- Command: `{shlex.join(provenance.command)}`",
        f"- Workers / timeout: {provenance.workers} / {provenance.timeout_seconds}s",
        f"- Structured report: `{summary.json_report}`",
        f"- Output root: `{summary.output_root}`",
        f"- Target: `make {summary.target}`",
        f"- Dependency mode: `{summary.dependency_mode}`",
        f"- Cache root: `{summary.cache_root}`",
        f"- Clean completed dependency/cache directories: {summary.clean_completed}",
        f"- Components cleaned: {summary.cleaned_components}",
        f"- Makefiles tested: {summary.makefiles}",
        f"- Passed: {summary.passed}",
        f"- Failed: {summary.failed}",
        "",
        "## Tool Versions",
        "",
        *(f"- {name}: {version}" for name, version in sorted(provenance.tools.items())),
    ]
    prewarm = summary.prewarm
    lines.extend(
        [
            "",
            "## Prewarm",
            "",
            f"- Requested: {prewarm.requested}",
            f"- Targets: {prewarm.targets}",
            f"- Workers: {prewarm.workers}",
            f"- Passed: {prewarm.passed}",
            f"- Failed: {prewarm.failed}",
        ]
    )
    lines.extend(f"- {reason}: {count}" for reason, count in prewarm.by_reason.items())
    for title, counts in (
        ("By Kind", Counter(result.kind for result in report.results)),
        ("By Result", summary.by_reason),
        ("By Kind And Result", Counter(f"{r.kind} / {r.reason}" for r in report.results)),
    ):
        lines.extend(["", f"## {title}", ""])
        lines.extend(f"- {label}: {count}" for label, count in sorted(counts.items()))
    for title, results in (("Prewarm Failures", report.prewarm_results), ("Failures", report.results)):
        lines.extend(["", f"## {title}", ""])
        for result in results:
            if result.reason == "pass":
                continue
            lines.extend(
                [
                    f"### {result.kind} - {result.reason}",
                    f"- Path: `{result.path}`",
                    f"- Platform: `{result.platform}`",
                    f"- Artifacts: `{result.artifacts}`",
                    f"- Exit: `{result.returncode}` in {result.duration_seconds:.2f}s",
                    f"- Output: `{result.output_tail}`",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
