"""Run `make test` across generated scaffold components."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import time


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


def run_make_tests(output_root: Path, *, timeout_seconds: int, workers: int) -> tuple[MakeTestResult, ...]:
    """Run `make test` under every generated Makefile."""
    makefiles = sorted(output_root.rglob("Makefile"))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_run_one, makefile.parent, timeout_seconds=timeout_seconds)
            for makefile in makefiles
        ]
        results = [future.result() for future in as_completed(futures)]
    return tuple(sorted(results, key=lambda result: str(result.path)))


def _run_one(path: Path, *, timeout_seconds: int) -> MakeTestResult:
    kind, platform, artifacts = _manifest_summary(path)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            ["make", "test"],
            cwd=path,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        output = f"{completed.stdout}\n{completed.stderr}".strip()
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        output = f"{exc.stdout or ''}\n{exc.stderr or ''}".strip()
        returncode = 124
        timed_out = True

    duration = time.monotonic() - started
    return MakeTestResult(
        path=path,
        kind=kind,
        platform=platform,
        artifacts=artifacts,
        returncode=returncode,
        duration_seconds=duration,
        reason=_classify_output(output, returncode, timed_out),
        output_tail=_tail(output),
    )


def _manifest_summary(path: Path) -> tuple[str, str, str]:
    manifest_path = path / ".kickstart/scaffold.json"
    if not manifest_path.exists():
        return ("unknown", "", "")

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        return (f"manifest-error:{exc}", "", "")

    project = manifest.get("project", {})
    execution = manifest.get("execution", {})
    return (
        str(project.get("kind", "unknown")),
        ",".join(execution.get("platforms", [])),
        json.dumps(manifest.get("artifacts", {}), sort_keys=True),
    )


def _classify_output(output: str, returncode: int, timed_out: bool) -> str:
    text = output.lower()
    if timed_out:
        return "timeout"
    if returncode == 0:
        return "pass"
    if "no rule to make target" in text and "test" in text:
        return "make test target missing"
    if "exec format error" in text and "pytest" in text:
        return "python pytest wrapper broken"
    if "vitest: command not found" in text:
        return "node test dependency missing"
    if "turbo: command not found" in text:
        return "node workspace dependency missing"
    if "bun is unable to write files to tempdir" in text:
        return "bun tempdir permission denied"
    if "poetry could not find a pyproject.toml" in text:
        return "python missing pyproject"
    if "command not found" in text and "pytest" in text:
        return "python missing pytest command"
    if "no test specified" in text or "missing script" in text:
        return "node missing test script"
    if "name = \"ops cli\"" in text:
        return "rust cargo package name invalid"
    if "no targets specified in the manifest" in text:
        return "rust library target missing"
    if "error: failed to parse manifest" in text or "invalid type: map" in text:
        return "rust cargo manifest invalid"
    if "failed to get" in text and "as a dependency" in text:
        return "rust dependency unavailable"
    if "could not resolve" in text or "failed to resolve" in text:
        return "dependency unavailable"
    if "cannot find package" in text or "module not found" in text:
        return "dependency unavailable"
    if "no tests were found" in text or "no tests found" in text:
        return "no tests present"
    if "no test files" in text:
        return "no tests present"
    if "cmake:" in text and "command not found" in text:
        return "cmake unavailable"
    if "make: go: no such file or directory" in text:
        return "go unavailable"
    if "error: could not compile" in text and ("e0432" in text or "e0433" in text):
        return "rust service compile failure"
    return "other failure"


def _tail(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return " / ".join(lines[-4:])[:400]


def write_report(path: Path, results: tuple[MakeTestResult, ...], output_root: Path) -> None:
    """Write a Markdown report for `make test` results."""
    by_reason = Counter(result.reason for result in results)
    by_kind = Counter(result.kind for result in results)
    by_kind_reason = Counter((result.kind, result.reason) for result in results)

    lines = [
        "# Generated Make Test Eval",
        "",
        f"- Output root: `{output_root}`",
        f"- Makefiles tested: {len(results)}",
        f"- Passed: {by_reason.get('pass', 0)}",
        f"- Failed: {len(results) - by_reason.get('pass', 0)}",
        "",
        "## By Kind",
        "",
    ]
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(by_kind.items()))
    lines.extend(["", "## By Result", ""])
    lines.extend(f"- {reason}: {count}" for reason, count in by_reason.most_common())
    lines.extend(["", "## By Kind And Result", ""])
    lines.extend(
        f"- {kind} / {reason}: {count}"
        for (kind, reason), count in sorted(by_kind_reason.items())
    )
    lines.extend(["", "## Failures", ""])
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

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run make test across generated scaffolds.")
    parser.add_argument("--output-root", type=Path, default=Path("/private/tmp/kickstart-scaffold-matrix"))
    parser.add_argument("--report", type=Path, default=Path("reports/generated-make-test-eval.md"))
    parser.add_argument("--timeout-seconds", type=int, default=35)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    results = run_make_tests(
        args.output_root,
        timeout_seconds=args.timeout_seconds,
        workers=args.workers,
    )
    write_report(args.report, results, args.output_root)

    by_reason = Counter(result.reason for result in results)
    print(
        json.dumps(
            {
                "makefiles": len(results),
                "passed": by_reason.get("pass", 0),
                "failed": len(results) - by_reason.get("pass", 0),
                "by_reason": dict(by_reason),
                "report": str(args.report),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
