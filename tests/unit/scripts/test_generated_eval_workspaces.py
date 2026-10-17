import json
import os
from pathlib import Path
import shlex
import sys
from threading import Barrier, Event

import pytest

from scripts import generated_make_test_eval as evaluator


def _workspace(root: Path, *, legacy: bool = False) -> Path:
    root.mkdir(parents=True)
    packages = ["apps/*", "packages/*"]
    (root / "package.json").write_text(
        json.dumps({"packageManager": "bun@1.3.0", "workspaces": {"packages": packages} if legacy else packages})
    )
    return root


def _component(root: Path, name: str, *, kind: str = "frontend", slot: str = "apps") -> Path:
    path = root / slot / name
    (path / ".kickstart").mkdir(parents=True)
    (path / ".kickstart/scaffold.json").write_text(json.dumps({"project": {"kind": kind}}))
    (path / "package.json").write_text(json.dumps({"name": name, "packageManager": "bun@1.3.0"}))
    (path / "Makefile").write_text("test install:\n\t@true\n")
    return path


@pytest.mark.parametrize("prewarm", [False, True])
@pytest.mark.parametrize("legacy", [False, True])
def test_workspace_dependency_commands_do_not_overlap(tmp_path: Path, prewarm: bool, legacy: bool) -> None:
    workspace = _workspace(tmp_path / "system", legacy=legacy)
    first = _component(workspace, "edge", kind="worker")
    second = _component(workspace, "web")
    (workspace / ".kickstart").mkdir()
    (workspace / ".kickstart/scaffold.json").write_text(json.dumps({"project": {"kind": "system"}}))
    probe = tmp_path / "install_probe.py"
    probe.write_text(
        "import pathlib, sys, time\n"
        "lock = pathlib.Path(sys.argv[1])\n"
        "try:\n"
        "    lock.mkdir()\n"
        "except FileExistsError:\n"
        "    raise SystemExit('another install is changing shared dependencies')\n"
        "try:\n"
        "    time.sleep(0.25)\n"
        "finally:\n"
        "    lock.rmdir()\n"
    )
    command = " ".join(shlex.quote(str(value)) for value in (sys.executable, probe, workspace / ".install-lock"))
    for path in (workspace, first, second):
        (path / "Makefile").write_text(f"test install:\n\t@{command}\n")
    options = {"timeout_seconds": 5, "workers": 2, "env": os.environ.copy()}

    if prewarm:
        results = evaluator.prewarm_dependencies(tmp_path, **options)
    else:
        results = evaluator.run_make_tests(tmp_path, target="test", **options)

    assert len(results) == 3
    assert all(result.returncode == 0 for result in results), [result.output_tail for result in results]


def test_workspace_cleanup_finishes_before_the_next_target(tmp_path: Path, monkeypatch) -> None:
    workspace = _workspace(tmp_path / "system")
    first = _component(workspace, "edge", kind="worker")
    _component(workspace, "web")
    cleanup_started = Event()
    next_started = Event()
    cleaning = Event()

    def command(command, *, cwd, timeout_seconds, env):
        if cwd != first:
            next_started.set()
            assert cleanup_started.wait(timeout=2)
        return evaluator.CommandResult("", "", 1 if cleaning.is_set() else 0, False)

    def cleanup(path, kind):
        if path == first:
            cleaning.set()
            cleanup_started.set()
            next_started.wait(timeout=0.25)
            cleaning.clear()
        return evaluator.CleanupResult()

    monkeypatch.setattr(evaluator, "_run_command", command)
    monkeypatch.setattr(evaluator, "_cleanup_component_dependencies", cleanup)

    results = evaluator.run_make_tests(
        tmp_path, timeout_seconds=5, workers=2, target="test", env=os.environ.copy(), clean_completed=True
    )

    assert len(results) == 2 and all(result.returncode == 0 for result in results)


@pytest.mark.parametrize("layout", ["independent-workspaces", "standalone", "nonmember", "nested"])
def test_unrelated_dependency_targets_remain_parallel(tmp_path: Path, monkeypatch, layout: str) -> None:
    if layout == "independent-workspaces":
        _component(_workspace(tmp_path / "one"), "edge")
        _component(_workspace(tmp_path / "two"), "web")
    elif layout == "standalone":
        _component(tmp_path, "edge")
        _component(tmp_path, "web")
    elif layout == "nonmember":
        root = _workspace(tmp_path / "system")
        _component(root, "edge")
        _component(root, "web", slot="services")
    else:
        root = _workspace(tmp_path / "system")
        _component(root, "edge")
        _component(_workspace(root / "apps/nested"), "web")
    simultaneous = Barrier(2)

    def command(command, *, cwd, timeout_seconds, env):
        simultaneous.wait(timeout=2)
        return evaluator.CommandResult("", "", 0, False)

    monkeypatch.setattr(evaluator, "_run_command", command)

    results = evaluator.run_make_tests(tmp_path, timeout_seconds=5, workers=2, target="test", env=os.environ.copy())

    assert len(results) == 2 and all(result.returncode == 0 for result in results)


@pytest.mark.parametrize(
    "metadata",
    [
        "[]",
        '{"packageManager": "bun@1.3.0", "workspaces": "apps/*"}',
        '{"packageManager": "bun@1.3.0", "workspaces": ["", "/outside"]}',
    ],
)
def test_unusable_workspace_metadata_does_not_stop_other_targets(tmp_path: Path, monkeypatch, metadata: str) -> None:
    (tmp_path / "package.json").write_text(metadata)
    _component(tmp_path, "edge")
    _component(tmp_path, "web")
    simultaneous = Barrier(2)

    def command(command, *, cwd, timeout_seconds, env):
        simultaneous.wait(timeout=2)
        return evaluator.CommandResult("", "", 0, False)

    monkeypatch.setattr(evaluator, "_run_command", command)
    results = evaluator.run_make_tests(tmp_path, timeout_seconds=5, workers=2, target="test", env=os.environ.copy())
    assert len(results) == 2 and all(result.returncode == 0 for result in results)
