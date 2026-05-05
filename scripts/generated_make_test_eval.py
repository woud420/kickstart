"""Run make targets across generated scaffold components."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Literal, cast


DependencyMode = Literal["network", "cached", "offline"]


@dataclass(frozen=True)
class CommandResult:
    """Result from one subprocess command."""

    stdout: str
    stderr: str
    returncode: int
    timed_out: bool


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


def run_make_tests(
    output_root: Path,
    *,
    timeout_seconds: int,
    workers: int,
    target: str,
    env: dict[str, str],
) -> tuple[MakeTestResult, ...]:
    """Run a make target under every generated Makefile."""
    makefiles = sorted(output_root.rglob("Makefile"))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_run_one, makefile.parent, target=target, timeout_seconds=timeout_seconds, env=env)
            for makefile in makefiles
        ]
        results = [future.result() for future in as_completed(futures)]
    return tuple(sorted(results, key=lambda result: str(result.path)))


def prewarm_dependencies(
    output_root: Path,
    *,
    timeout_seconds: int,
    workers: int,
    env: dict[str, str],
) -> tuple[MakeTestResult, ...]:
    """Run `make install` once per dependency family to seed package caches."""
    targets = _prewarm_targets(output_root)
    if not targets:
        return ()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_run_one, target_path, target="install", timeout_seconds=timeout_seconds, env=env)
            for target_path in targets
        ]
        results = [future.result() for future in as_completed(futures)]
    return tuple(sorted(results, key=lambda result: str(result.path)))


def eval_environment(dependency_mode: DependencyMode, cache_root: Path) -> dict[str, str]:
    """Return an environment for dependency-backed generated evals."""
    env = os.environ.copy()
    if dependency_mode == "network":
        return env

    cache_paths = {
        "XDG_CACHE_HOME": cache_root / "xdg",
        "PIP_CACHE_DIR": cache_root / "pip",
        "POETRY_CACHE_DIR": cache_root / "poetry",
        "POETRY_VIRTUALENVS_PATH": cache_root / "poetry-venvs",
        "CARGO_HOME": cache_root / "cargo",
        "CARGO_TARGET_DIR": cache_root / "cargo-targets",
        "GOCACHE": cache_root / "go-build",
        "GOMODCACHE": cache_root / "go-mod",
        "BUN_INSTALL_CACHE_DIR": cache_root / "bun",
        "npm_config_cache": cache_root / "npm",
    }
    for path in cache_paths.values():
        path.mkdir(parents=True, exist_ok=True)
    env.update({key: str(path) for key, path in cache_paths.items()})

    if dependency_mode == "offline":
        env.update(
            {
                "CARGO_NET_OFFLINE": "true",
                "GOPROXY": "off",
                "PIP_NO_INDEX": "1",
                "npm_config_offline": "true",
            }
        )

    return env


def _run_one(path: Path, *, target: str, timeout_seconds: int, env: dict[str, str]) -> MakeTestResult:
    kind, platform, artifacts = _manifest_summary(path)
    started = time.monotonic()
    completed = _run_command(["make", target], cwd=path, timeout_seconds=timeout_seconds, env=env)
    output = f"{completed.stdout}\n{completed.stderr}".strip()
    returncode = completed.returncode

    duration = time.monotonic() - started
    return MakeTestResult(
        path=path,
        kind=kind,
        platform=platform,
        artifacts=artifacts,
        returncode=returncode,
        duration_seconds=duration,
        reason=_classify_output(output, returncode, completed.timed_out, target=target),
        output_tail=_tail(output),
    )


def _run_command(command: list[str], *, cwd: Path, timeout_seconds: int, env: dict[str, str]) -> CommandResult:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        returncode = process.returncode if process.returncode is not None else 0
        return CommandResult(stdout=stdout, stderr=stderr, returncode=returncode, timed_out=False)
    except subprocess.TimeoutExpired:
        _stop_process_group(process, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            _stop_process_group(process, signal.SIGKILL)
            stdout, stderr = process.communicate()
        return CommandResult(stdout=stdout, stderr=stderr, returncode=124, timed_out=True)


def _stop_process_group(process: subprocess.Popen[str], sig: signal.Signals) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        return


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


def _prewarm_targets(output_root: Path) -> tuple[Path, ...]:
    selected: dict[str, Path] = {}
    for makefile in sorted(output_root.rglob("Makefile")):
        path = makefile.parent
        key = _dependency_family(path)
        if key is None or key in selected:
            continue
        selected[key] = path
    return tuple(selected[key] for key in sorted(selected))


def _dependency_family(path: Path) -> str | None:
    kind, platform, artifacts = _manifest_summary(path)
    if (path / "package.json").exists():
        return f"node:{kind}:{platform}:{artifacts}"
    if (path / "pyproject.toml").exists() or (path / "requirements.txt").exists():
        return f"python:{kind}:{platform}:{artifacts}"
    if (path / "Cargo.toml").exists():
        return f"rust:{kind}:{platform}:{artifacts}"
    if (path / "go.mod").exists():
        return f"go:{kind}:{platform}:{artifacts}"
    if (path / "CMakeLists.txt").exists():
        return f"cpp:{kind}:{platform}:{artifacts}"
    return None


def _classify_output(output: str, returncode: int, timed_out: bool, *, target: str = "test") -> str:
    text = output.lower()
    if timed_out:
        if target == "install" or "install" in text:
            return "timeout during dependency install"
        return "timeout"
    if returncode == 0:
        return "pass"
    if "no rule to make target" in text and target in text:
        return f"make {target} target missing"
    if "exec format error" in text and "pytest" in text:
        return "python pytest wrapper broken"
    if "vitest: command not found" in text:
        return "node test dependency missing"
    if "turbo: command not found" in text:
        return "node workspace dependency missing"
    if "bun is unable to write files to tempdir" in text:
        return "bun tempdir permission denied"
    if "operation not permitted" in text and ("go-build" in text or "cache" in text):
        return "cache permission denied"
    if "poetry could not find a pyproject.toml" in text:
        return "python missing pyproject"
    if "command not found" in text and "pytest" in text:
        return "python missing pytest command"
    if "no test specified" in text or "missing script" in text:
        return "node missing test script"
    if 'name = "ops cli"' in text:
        return "rust cargo package name invalid"
    if "no targets specified in the manifest" in text:
        return "rust library target missing"
    if "error: failed to parse manifest" in text or "invalid type: map" in text:
        return "rust cargo manifest invalid"
    if (
        "hostname cannot be resolved" in text
        or "network is not connected" in text
        or "could not resolve host" in text
        or "failedtoopensocket" in text
        or "connectionrefused downloading" in text
        or "temporary failure in name resolution" in text
    ):
        return "network unavailable"
    if "failed to get" in text and "as a dependency" in text:
        return "rust dependency unavailable"
    if "could not resolve" in text or "failed to resolve" in text:
        return "package registry unavailable"
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


def write_report(
    path: Path,
    results: tuple[MakeTestResult, ...],
    output_root: Path,
    *,
    target: str,
    dependency_mode: DependencyMode,
    cache_root: Path,
    prewarm_workers: int = 0,
    prewarm_results: tuple[MakeTestResult, ...] = (),
) -> None:
    """Write a Markdown report for generated make-target results."""
    by_reason = Counter(result.reason for result in results)
    by_kind = Counter(result.kind for result in results)
    by_kind_reason = Counter((result.kind, result.reason) for result in results)
    prewarm_by_reason = Counter(result.reason for result in prewarm_results)

    lines = [
        "# Generated Make Test Eval",
        "",
        f"- Output root: `{output_root}`",
        f"- Target: `make {target}`",
        f"- Dependency mode: `{dependency_mode}`",
        f"- Cache root: `{cache_root if dependency_mode != 'network' else 'default tool caches'}`",
        f"- Makefiles tested: {len(results)}",
        f"- Passed: {by_reason.get('pass', 0)}",
        f"- Failed: {len(results) - by_reason.get('pass', 0)}",
        "",
    ]
    if prewarm_results:
        lines.extend(
            [
                "## Prewarm",
                "",
                f"- Targets: {len(prewarm_results)}",
                f"- Workers: {prewarm_workers}",
                f"- Passed: {prewarm_by_reason.get('pass', 0)}",
                f"- Failed: {len(prewarm_results) - prewarm_by_reason.get('pass', 0)}",
                "",
            ]
        )
    lines.extend(["## By Kind", ""])
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(by_kind.items()))
    lines.extend(["", "## By Result", ""])
    lines.extend(f"- {reason}: {count}" for reason, count in by_reason.most_common())
    lines.extend(["", "## By Kind And Result", ""])
    lines.extend(f"- {kind} / {reason}: {count}" for (kind, reason), count in sorted(by_kind_reason.items()))
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
    parser = argparse.ArgumentParser(description="Run make targets across generated scaffolds.")
    parser.add_argument("--output-root", type=Path, default=Path("/private/tmp/kickstart-scaffold-matrix"))
    parser.add_argument("--report", type=Path, default=Path("reports/generated-make-test-eval.md"))
    parser.add_argument("--timeout-seconds", type=int, default=35)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--target", default="test")
    parser.add_argument("--dependency-mode", choices=("network", "cached", "offline"), default="cached")
    parser.add_argument("--cache-root", type=Path, default=Path("/private/tmp/kickstart-eval-cache"))
    parser.add_argument("--prewarm", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--prewarm-workers", type=int, default=2)
    args = parser.parse_args()

    dependency_mode = cast(DependencyMode, args.dependency_mode)
    env = eval_environment(dependency_mode, args.cache_root)
    prewarm_results: tuple[MakeTestResult, ...] = ()
    if args.prewarm:
        prewarm_results = prewarm_dependencies(
            args.output_root,
            timeout_seconds=args.timeout_seconds,
            workers=args.prewarm_workers,
            env=env,
        )

    results = run_make_tests(
        args.output_root,
        timeout_seconds=args.timeout_seconds,
        workers=args.workers,
        target=args.target,
        env=env,
    )
    write_report(
        args.report,
        results,
        args.output_root,
        target=args.target,
        dependency_mode=dependency_mode,
        cache_root=args.cache_root,
        prewarm_workers=args.prewarm_workers,
        prewarm_results=prewarm_results,
    )

    by_reason = Counter(result.reason for result in results)
    prewarm_by_reason = Counter(result.reason for result in prewarm_results)
    print(
        json.dumps(
            {
                "target": args.target,
                "dependency_mode": dependency_mode,
                "cache_root": str(args.cache_root if dependency_mode != "network" else "default tool caches"),
                "prewarm": {
                    "targets": len(prewarm_results),
                    "workers": args.prewarm_workers,
                    "passed": prewarm_by_reason.get("pass", 0),
                    "failed": len(prewarm_results) - prewarm_by_reason.get("pass", 0),
                    "by_reason": dict(prewarm_by_reason),
                },
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
