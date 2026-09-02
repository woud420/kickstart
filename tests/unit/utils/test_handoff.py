"""Tests for src.utils.handoff (ENG-205 staged activation chain)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.model.dto.telemetry import (
    CliUpgradeChecksumStatus,
    CliUpgradeErrorCategory,
    CliUpgradeOutcome,
)
from src.utils import handoff
from src.utils.errors import HandoffError


def _fake_bundle(root: Path, *, body: str = "#!/bin/sh\necho staged\n") -> Path:
    """Create an onedir-shaped payload under `root` and return its launcher."""
    (root / "_internal").mkdir(parents=True)
    (root / "_internal" / "marker").write_text(body)
    launcher = root / handoff.BINARY_NAME
    launcher.write_text(body)
    launcher.chmod(0o755)
    return launcher


def _handoff(tmp_path: Path, *, mode: handoff.HandoffMode = handoff.HandoffMode.REPAIR) -> handoff.Handoff:
    return handoff.Handoff(
        mode=mode,
        launcher_dir=tmp_path / "bin",
        app_root=tmp_path / "share" / "kickstart",
        bundle_launcher=tmp_path / "stage" / "bundle" / handoff.BINARY_NAME,
        target_version="1.2.3",
        checksum_status=CliUpgradeChecksumStatus.VERIFIED,
        started_at=1234.5,
    )


# --- manifest -------------------------------------------------------------


def test_handoff_manifest_round_trips(tmp_path):
    stage_dir = tmp_path / "stage"
    stage_dir.mkdir()
    original = _handoff(tmp_path, mode=handoff.HandoffMode.UPGRADE)

    manifest = original.write(stage_dir)

    assert manifest == stage_dir / handoff.HANDOFF_FILENAME
    assert json.loads(manifest.read_text())["version"] == handoff.HANDOFF_VERSION
    assert handoff.load_handoff(stage_dir) == original


@pytest.mark.parametrize(
    "content, match",
    [
        ("not json", "cannot read handoff manifest"),
        ("[]", "is not an object"),
        ('{"version": 99}', "unsupported handoff manifest version"),
        ('{"version": 1, "mode": "repair"}', "is malformed"),
        (
            '{"version": 1, "mode": "sideways", "launcher_dir": "/b", "app_root": "/a", '
            '"bundle_launcher": "/s/kickstart", "target_version": "1.0.0", '
            '"checksum_status": "verified", "started_at": 1}',
            "is malformed",
        ),
    ],
)
def test_load_handoff_rejects_bad_manifests(tmp_path, content, match):
    (tmp_path / handoff.HANDOFF_FILENAME).write_text(content)
    with pytest.raises(HandoffError, match=match):
        handoff.load_handoff(tmp_path)


def test_load_handoff_missing_manifest(tmp_path):
    with pytest.raises(HandoffError, match="cannot read handoff manifest"):
        handoff.load_handoff(tmp_path)


def test_handoff_results_follow_mode(tmp_path):
    repair = _handoff(tmp_path, mode=handoff.HandoffMode.REPAIR)
    upgrade = _handoff(tmp_path, mode=handoff.HandoffMode.UPGRADE)

    assert repair.success().outcome is CliUpgradeOutcome.REPAIRED
    assert upgrade.success().outcome is CliUpgradeOutcome.UPDATED
    assert repair.success().checksum_status is CliUpgradeChecksumStatus.VERIFIED
    failure = repair.failure(CliUpgradeErrorCategory.INSTALLATION)
    assert failure.outcome is CliUpgradeOutcome.FAILED
    assert failure.error_category is CliUpgradeErrorCategory.INSTALLATION
    assert failure.target_version == "1.2.3"
    unknown = handoff.unknown_failure(CliUpgradeErrorCategory.UNEXPECTED_ERROR)
    assert unknown.target_version == "unknown"
    assert unknown.checksum_status is CliUpgradeChecksumStatus.NOT_REACHED


def test_handoff_paths(tmp_path):
    current = _handoff(tmp_path)
    assert current.canonical_launcher == tmp_path / "share" / "kickstart" / "current" / "kickstart"
    assert current.public_launcher == tmp_path / "bin" / "kickstart"


# --- environment scrubbing ----------------------------------------------


def test_handoff_environment_drops_bootloader_state_and_restores_saved_library_path(tmp_path):
    env = {
        "PATH": "/usr/bin",
        "_PYI_ARCHIVE_FILE": "/old/kickstart",
        "_PYI_PARENT_PROCESS_LEVEL": "1",
        "_MEIPASS2": "/old/_internal",
        "LD_LIBRARY_PATH": "/old/_internal:/usr/lib",
        "LD_LIBRARY_PATH_ORIG": "/usr/lib",
        "DYLD_LIBRARY_PATH": "/old/_internal",
        "DYLD_LIBRARY_PATH_ORIG": "",
    }

    child = handoff.handoff_environment(env, bundle_root=tmp_path)

    assert child == {"PATH": "/usr/bin", "LD_LIBRARY_PATH": "/usr/lib"}


def test_handoff_environment_strips_payload_entries_without_saved_value(tmp_path):
    payload = tmp_path / "payload"
    (payload / "_internal").mkdir(parents=True)
    env = {
        "LD_LIBRARY_PATH": f"{payload / '_internal'}:/opt/lib::{payload}",
        "DYLD_LIBRARY_PATH": str(payload / "_internal"),
        "HOME": "/home/user",
    }

    child = handoff.handoff_environment(env, bundle_root=payload)

    assert child == {"LD_LIBRARY_PATH": "/opt/lib", "HOME": "/home/user"}


def test_handoff_environment_leaves_unrelated_library_paths_alone_without_bundle():
    env = {"LD_LIBRARY_PATH": "/opt/lib", "USER": "jm"}
    assert handoff.handoff_environment(env, bundle_root=None) == env


def test_handoff_environment_defaults_to_process_environment(monkeypatch):
    monkeypatch.setenv("_PYI_TEST_ONLY", "1")
    monkeypatch.setenv("KICKSTART_TEST_ONLY", "kept")
    child = handoff.handoff_environment()
    assert "_PYI_TEST_ONLY" not in child
    assert child["KICKSTART_TEST_ONLY"] == "kept"


# --- staging --------------------------------------------------------------


def test_stage_running_bundle_copies_the_running_payload(tmp_path, monkeypatch):
    running = _fake_bundle(tmp_path / "nested" / "current", body="#!/bin/sh\necho running\n")
    monkeypatch.setattr("sys.argv", [str(running)])
    stage_dir = tmp_path / "stage"
    stage_dir.mkdir()

    staged = handoff.stage_running_bundle(stage_dir)

    assert staged == stage_dir / "current" / handoff.BINARY_NAME
    assert staged.read_text() == "#!/bin/sh\necho running\n"
    assert (staged.parent / "_internal" / "marker").read_text() == "#!/bin/sh\necho running\n"
    assert os.access(staged, os.X_OK)


def test_stage_running_bundle_refuses_non_bundle(tmp_path, monkeypatch):
    script = tmp_path / "kickstart"
    script.write_text("#!/bin/sh\n")
    script.chmod(0o755)
    monkeypatch.setattr("sys.argv", [str(script)])
    with pytest.raises(HandoffError, match="not a kickstart onedir payload"):
        handoff.stage_running_bundle(tmp_path / "stage")


def test_create_stage_dir_uses_mode_prefix(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    repair = handoff.create_stage_dir(handoff.HandoffMode.REPAIR)
    upgrade = handoff.create_stage_dir(handoff.HandoffMode.UPGRADE)
    assert repair.parent == tmp_path and repair.name.startswith(handoff.STAGE_PREFIX_REPAIR)
    assert upgrade.parent == tmp_path and upgrade.name.startswith(handoff.STAGE_PREFIX_UPGRADE)


def test_handoff_to_staged_writes_manifest_then_execs_activate_phase(tmp_path, monkeypatch):
    stage_dir = tmp_path / "stage"
    staged = _fake_bundle(stage_dir / "bundle")
    current = _handoff(tmp_path)
    calls: list[tuple[Path, list[str], dict[str, str]]] = []

    def record(launcher, args, env):
        calls.append((launcher, args, env))
        raise SystemExit(0)

    monkeypatch.setattr(handoff, "exec_launcher", record)
    monkeypatch.setenv("_PYI_ARCHIVE_FILE", "/old")

    with pytest.raises(SystemExit):
        handoff.handoff_to_staged(current, stage_dir)

    assert handoff.load_handoff(stage_dir) == current
    assert calls == [
        (
            staged,
            [handoff.HANDOFF_COMMAND, "--stage-dir", str(stage_dir), "--phase", "activate"],
            calls[0][2],
        )
    ]
    assert "_PYI_ARCHIVE_FILE" not in calls[0][2]


def test_exec_launcher_flushes_and_replaces_process(tmp_path, monkeypatch, real_exec_launcher):
    launcher = tmp_path / "kickstart"
    launcher.write_text("#!/bin/sh\n")
    seen: list[tuple[str, list[str], dict[str, str]]] = []

    def fake_execve(path, argv, env):
        seen.append((path, argv, env))

    monkeypatch.setattr(handoff.os, "execve", fake_execve)
    with patch("src.utils.handoff.sys.stdout.flush") as out_flush, patch("src.utils.handoff.sys.stderr.flush"):
        real_exec_launcher(launcher, ["a", "b"], {"X": "1"})
    out_flush.assert_called_once()
    assert seen == [(str(launcher), [str(launcher), "a", "b"], {"X": "1"})]


# --- activate / finalize --------------------------------------------------


def _nested_install(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Return ``(public_launcher, app_root, running_executable)`` for a nested layout."""
    app_root = tmp_path / "share" / "kickstart"
    bundle_dest = app_root / "current"
    _fake_bundle(bundle_dest, body="#!/bin/sh\necho stale\n")
    (bundle_dest / handoff.BINARY_NAME).unlink()
    running = _fake_bundle(bundle_dest / ".kickstart" / "current", body="#!/bin/sh\necho running\n")
    (bundle_dest / handoff.BINARY_NAME).symlink_to(running)
    launcher_dir = tmp_path / "bin"
    launcher_dir.mkdir()
    launcher = launcher_dir / handoff.BINARY_NAME
    launcher.symlink_to(bundle_dest / handoff.BINARY_NAME)
    return launcher, app_root, running


@patch("src.utils.handoff.print")
def test_activate_replaces_payload_verifies_and_hands_off_to_canonical(mock_print, tmp_path, monkeypatch):
    launcher, app_root, _ = _nested_install(tmp_path)
    stage_dir = tmp_path / "stage"
    staged = _fake_bundle(stage_dir / "bundle", body="#!/bin/sh\necho staged\n")
    current = handoff.Handoff(
        mode=handoff.HandoffMode.REPAIR,
        launcher_dir=launcher.parent,
        app_root=app_root,
        bundle_launcher=staged,
        target_version="1.0.0",
        checksum_status=CliUpgradeChecksumStatus.NOT_REACHED,
        started_at=0.0,
    )
    calls: list[tuple[Path, list[str]]] = []

    def record(launcher_path, args, env):
        calls.append((launcher_path, args))
        raise SystemExit(0)

    monkeypatch.setattr(handoff, "exec_launcher", record)

    with pytest.raises(SystemExit):
        handoff.activate(current, stage_dir)

    canonical = app_root / "current" / handoff.BINARY_NAME
    assert launcher.resolve() == canonical.resolve()
    assert not canonical.is_symlink()
    assert canonical.read_text() == "#!/bin/sh\necho staged\n"
    assert not (app_root / "current" / ".kickstart").exists()
    assert stage_dir.is_dir(), "activate must leave cleanup to the finalize hop"
    assert calls == [(canonical, [handoff.HANDOFF_COMMAND, "--stage-dir", str(stage_dir), "--phase", "finalize"])]


@patch("src.utils.handoff.print")
def test_activate_refuses_staged_payload_inside_app_root(mock_print, tmp_path):
    launcher, app_root, running = _nested_install(tmp_path)
    current = handoff.Handoff(
        mode=handoff.HandoffMode.REPAIR,
        launcher_dir=launcher.parent,
        app_root=app_root,
        bundle_launcher=running,
        target_version="1.0.0",
        checksum_status=CliUpgradeChecksumStatus.NOT_REACHED,
        started_at=0.0,
    )
    with pytest.raises(HandoffError, match="inside the managed app root"):
        handoff.activate(current, tmp_path / "stage")
    assert launcher.resolve() == running


@patch("src.utils.handoff.print")
def test_activate_failure_rolls_back_and_propagates(mock_print, tmp_path, monkeypatch):
    launcher, app_root, running = _nested_install(tmp_path)
    stage_dir = tmp_path / "stage"
    staged = _fake_bundle(stage_dir / "bundle")
    current = handoff.Handoff(
        mode=handoff.HandoffMode.REPAIR,
        launcher_dir=launcher.parent,
        app_root=app_root,
        bundle_launcher=staged,
        target_version="1.0.0",
        checksum_status=CliUpgradeChecksumStatus.NOT_REACHED,
        started_at=0.0,
    )
    original_rename = Path.rename

    def fail_activation(self: Path, target: Path) -> Path:
        if self.name.startswith(".current.tmp-"):
            raise OSError("activation failed")
        return original_rename(self, target)

    monkeypatch.setattr(Path, "rename", fail_activation)

    with pytest.raises(OSError, match="activation failed"):
        handoff.activate(current, stage_dir)

    assert launcher.resolve() == running
    assert running.read_text() == "#!/bin/sh\necho running\n"
    assert (app_root / "current" / ".kickstart").is_dir()


@patch("src.utils.handoff.print")
def test_activate_returns_success_when_final_handoff_cannot_start(mock_print, tmp_path, monkeypatch):
    launcher, app_root, _ = _nested_install(tmp_path)
    stage_dir = tmp_path / "stage"
    staged = _fake_bundle(stage_dir / "bundle")
    current = handoff.Handoff(
        mode=handoff.HandoffMode.UPGRADE,
        launcher_dir=launcher.parent,
        app_root=app_root,
        bundle_launcher=staged,
        target_version="1.1.0",
        checksum_status=CliUpgradeChecksumStatus.VERIFIED,
        started_at=0.0,
    )

    def refuse(launcher_path, args, env):
        raise OSError("exec format error")

    monkeypatch.setattr(handoff, "exec_launcher", refuse)

    result = handoff.activate(current, stage_dir)

    assert result.outcome is CliUpgradeOutcome.UPDATED
    assert launcher.resolve() == (app_root / "current" / handoff.BINARY_NAME).resolve()
    assert stage_dir.is_dir()
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("Remove the staging directory manually" in m and str(stage_dir) in m for m in messages)


def test_verify_activated_layout_rejects_survivors(tmp_path):
    launcher, app_root, _ = _nested_install(tmp_path)
    current = handoff.Handoff(
        mode=handoff.HandoffMode.REPAIR,
        launcher_dir=launcher.parent,
        app_root=app_root,
        bundle_launcher=tmp_path / "stage" / handoff.BINARY_NAME,
        target_version="1.0.0",
        checksum_status=CliUpgradeChecksumStatus.NOT_REACHED,
        started_at=0.0,
    )
    # Still nested: the launcher resolves into .kickstart/current.
    with pytest.raises(HandoffError, match="resolves to"):
        handoff.verify_activated_layout(current)

    # Collapse the symlink but leave the nested directory behind.
    canonical = app_root / "current" / handoff.BINARY_NAME
    canonical.unlink()
    canonical.write_text("#!/bin/sh\n")
    with pytest.raises(HandoffError, match="survived activation"):
        handoff.verify_activated_layout(current)


@patch("src.utils.handoff.print")
def test_finalize_removes_stage_dir_and_reports(mock_print, tmp_path):
    stage_dir = tmp_path / "stage"
    _fake_bundle(stage_dir / "bundle")
    current = _handoff(tmp_path, mode=handoff.HandoffMode.REPAIR)
    current.write(stage_dir)

    result = handoff.finalize(current, stage_dir)

    assert not stage_dir.exists()
    assert result == current.success()
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("Repaired the managed install layout" in m for m in messages)
    assert any(str(current.public_launcher) in m for m in messages)


@patch("src.utils.handoff.print")
def test_finalize_upgrade_message_names_the_version(mock_print, tmp_path):
    stage_dir = tmp_path / "stage"
    stage_dir.mkdir()
    current = _handoff(tmp_path, mode=handoff.HandoffMode.UPGRADE)

    result = handoff.finalize(current, stage_dir)

    assert result.outcome is CliUpgradeOutcome.UPDATED
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("Updated to 1.2.3" in m for m in messages)
