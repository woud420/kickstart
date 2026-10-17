"""Run make targets across generated scaffold components."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
import os
import platform
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from typing import cast
from uuid import uuid4


from scripts.generated_eval_report import (
    DependencyMode,
    GeneratedEvalReport,
    MakeTestResult,
    RunProvenance,
    write_report,
)


@dataclass(frozen=True)
class CommandResult:
    """Result from one subprocess command."""

    stdout: str
    stderr: str
    returncode: int
    timed_out: bool


def run_make_tests(
    output_root: Path,
    *,
    timeout_seconds: int,
    workers: int,
    target: str,
    env: dict[str, str],
    clean_completed: bool = False,
) -> tuple[MakeTestResult, ...]:
    """Run a make target under every generated Makefile."""
    makefiles = _generated_makefiles(output_root)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                _run_one,
                makefile.parent,
                target=target,
                timeout_seconds=timeout_seconds,
                env=env,
                clean_completed=clean_completed,
            )
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
        "PY_CACHE_DIR": cache_root / "python",
        "PIP_CACHE_DIR": cache_root / "pip",
        "POETRY_CACHE_DIR": cache_root / "poetry",
        "POETRY_VIRTUALENVS_PATH": cache_root / "poetry-venvs",
        "CARGO_HOME": cache_root / "cargo",
        "CARGO_TARGET_DIR": cache_root / "cargo-targets",
        "GOCACHE": cache_root / "go-build",
        "GOMODCACHE": cache_root / "go-mod",
        "BUN_CACHE_DIR": cache_root / "bun",
        "BUN_INSTALL_CACHE_DIR": cache_root / "bun" / "install",
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


def _run_one(
    path: Path, *, target: str, timeout_seconds: int, env: dict[str, str], clean_completed: bool = False
) -> MakeTestResult:
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
        cleaned_artifacts=_cleanup_component_dependencies(path, kind) if clean_completed else (),
    )


def _cleanup_component_dependencies(path: Path, kind: str) -> tuple[str, ...]:
    """Remove only local install directories after a leaf target has exited."""
    if kind not in {"service", "worker", "frontend", "library", "lib", "cli"}:
        return ()
    try:
        ownership = json.loads((path / ".kickstart/scaffold.json").read_text()).get("ownership", {})
    except (OSError, json.JSONDecodeError):
        return ()
    if not isinstance(ownership, dict):
        return ()
    removed = []
    for name in (".venv", "node_modules", ".cache"):
        if any(isinstance(source, str) and (source == name or source.startswith(name + "/")) for source in ownership):
            continue
        directory = path / name
        if directory.is_symlink() or not directory.is_dir():
            continue
        shutil.rmtree(directory)
        removed.append(name)
    return tuple(removed)


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


def _generated_makefiles(output_root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path.parent.parent / "Makefile"
            for path in output_root.rglob(".kickstart/scaffold.json")
            if (path.parent.parent / "Makefile").is_file()
        )
    )


def _prewarm_targets(output_root: Path) -> tuple[Path, ...]:
    selected: dict[str, Path] = {}
    for makefile in _generated_makefiles(output_root):
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


def _capture_provenance(started_at: str, finished_at: str, *, workers: int, timeout_seconds: int) -> RunProvenance:
    repo = Path(__file__).resolve().parents[1]

    def read_command(command: tuple[str, ...]) -> tuple[str, int]:
        try:
            completed = subprocess.run(command, cwd=repo, text=True, capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return ("unavailable", 1)
        return (completed.stdout.strip(), completed.returncode)

    revision, revision_exit = read_command(("git", "rev-parse", "HEAD"))
    status, status_exit = read_command(("git", "status", "--porcelain"))
    tools = {"python": sys.version.splitlines()[0]}
    for name, command in (
        ("bun", ("bun", "--version")),
        ("node", ("node", "--version")),
        ("cargo", ("cargo", "--version")),
        ("rustc", ("rustc", "--version")),
        ("go", ("go", "version")),
        ("cmake", ("cmake", "--version")),
        ("poetry", ("poetry", "--version")),
        ("make", ("make", "--version")),
    ):
        version, exit_code = read_command(command)
        tools[name] = version.splitlines()[0] if exit_code == 0 and version else "unavailable"
    return RunProvenance(
        run_id=str(uuid4()),
        started_at_utc=started_at,
        finished_at_utc=finished_at,
        source_revision=revision if revision_exit == 0 else "unknown",
        source_dirty=bool(status) if status_exit == 0 else None,
        execution_context=platform.platform(),
        command=(sys.executable, *sys.argv),
        tools=tools,
        workers=workers,
        timeout_seconds=timeout_seconds,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run make targets across generated scaffolds.")
    scratch = Path(tempfile.gettempdir())
    parser.add_argument("--output-root", type=Path, default=scratch / "kickstart-scaffold-matrix")
    parser.add_argument("--report", type=Path, default=scratch / "kickstart-generated-make-test-eval.md")
    parser.add_argument("--timeout-seconds", type=int, default=35)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--target", default="test")
    parser.add_argument("--dependency-mode", choices=("network", "cached", "offline"), default="cached")
    parser.add_argument("--cache-root", type=Path, default=scratch / "kickstart-eval-cache")
    parser.add_argument("--prewarm", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--prewarm-workers", type=int, default=2)
    parser.add_argument(
        "--clean-completed",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Remove completed leaf .venv/node_modules/.cache directories; preserve recorded source and shared caches.",
    )
    args = parser.parse_args()

    if not _generated_makefiles(args.output_root):
        parser.error(f"no generated Makefiles found under {args.output_root}")
    started_at = datetime.now(UTC).isoformat()
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
        clean_completed=args.clean_completed,
    )
    report = GeneratedEvalReport(
        report_path=args.report,
        output_root=args.output_root,
        target=args.target,
        dependency_mode=dependency_mode,
        cache_root=args.cache_root,
        provenance=_capture_provenance(
            started_at,
            datetime.now(UTC).isoformat(),
            workers=args.workers,
            timeout_seconds=args.timeout_seconds,
        ),
        results=results,
        clean_completed=args.clean_completed,
        prewarm_requested=args.prewarm,
        prewarm_workers=args.prewarm_workers,
        prewarm_results=prewarm_results,
    )
    summary = write_report(report)
    print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
