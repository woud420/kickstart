"""Focused updater checks."""

from __future__ import annotations
from pathlib import Path
import pytest
from src.utils import updater

from tests.unit.utils.updater_helpers import managed_install, nested_install


def test_resolve_onedir(tmp_path, monkeypatch):
    """ENG-204 regression: preserve the managed launcher symlink for layout discovery."""
    app_root = tmp_path / ".local" / "share" / "kickstart"
    bundle = app_root / updater.APP_DIR_NAME
    bundle.mkdir(parents=True)
    executable = bundle / updater.BINARY_NAME
    executable.write_text("#!/bin/sh\n")
    executable.chmod(0o755)

    launcher_dir = tmp_path / ".local" / "bin"
    launcher_dir.mkdir(parents=True)
    launcher = launcher_dir / updater.BINARY_NAME
    launcher.symlink_to(executable)

    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])
    resolved_dir, resolved_root = updater.resolve_current_install_layout()
    assert resolved_dir == launcher_dir
    assert resolved_root == app_root


def test_resolve_recovers_root_from_nested_payload(tmp_path, monkeypatch):
    """An old nested payload still reveals the original managed app root."""
    app_root = tmp_path / ".local" / "share" / "kickstart"
    bundle = app_root / updater.APP_DIR_NAME
    nested_bundle = bundle / ".kickstart" / updater.APP_DIR_NAME
    nested_bundle.mkdir(parents=True)
    nested_executable = nested_bundle / updater.BINARY_NAME
    nested_executable.write_text("#!/bin/sh\n")
    nested_executable.chmod(0o755)

    managed_executable = bundle / updater.BINARY_NAME
    managed_executable.symlink_to(nested_executable)
    launcher_dir = tmp_path / ".local" / "bin"
    launcher_dir.mkdir(parents=True)
    launcher = launcher_dir / updater.BINARY_NAME
    launcher.symlink_to(managed_executable)

    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])
    resolved_dir, resolved_root = updater.resolve_current_install_layout()

    assert resolved_dir == launcher_dir
    assert resolved_root == app_root


def test_resolve_normalizes_relative_launcher_target(tmp_path, monkeypatch):
    """A relative managed launcher target identifies the same canonical roots."""
    app_root = tmp_path / "share" / "kickstart"
    bundle = app_root / updater.APP_DIR_NAME
    (bundle / "_internal").mkdir(parents=True)
    executable = bundle / updater.BINARY_NAME
    executable.write_text("#!/bin/sh\n")
    executable.chmod(0o755)

    launcher_dir = tmp_path / "bin"
    launcher_dir.mkdir()
    launcher = launcher_dir / updater.BINARY_NAME
    launcher.symlink_to(Path("..") / "share" / "kickstart" / updater.APP_DIR_NAME / updater.BINARY_NAME)

    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])
    resolved_dir, resolved_root = updater.resolve_current_install_layout()

    assert resolved_dir == launcher_dir
    assert resolved_root == app_root


def test_resolve_legacy_single_file(tmp_path, monkeypatch):
    """A non-symlink launcher (legacy single-file install) yields app_root=None."""
    launcher = tmp_path / "bin" / updater.BINARY_NAME
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#!/bin/sh\n")
    launcher.chmod(0o755)
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])
    resolved_dir, resolved_root = updater.resolve_current_install_layout()
    assert resolved_dir == launcher.parent
    assert resolved_root is None


def test_resolve_generated_wrapper_payload(tmp_path, monkeypatch):
    """A wrapper-executed managed payload refreshes its stable bundle in place."""
    app_root = tmp_path / "share" / "kickstart"
    bundle = app_root / updater.APP_DIR_NAME
    (bundle / "_internal").mkdir(parents=True)
    executable = bundle / updater.BINARY_NAME
    executable.write_text("#!/bin/sh\n")
    executable.chmod(0o755)

    monkeypatch.setattr(updater.sys, "argv", [str(executable)])
    resolved_dir, resolved_root = updater.resolve_current_install_layout()

    assert resolved_dir == bundle
    assert resolved_root == app_root


def test_resolve_symlink_with_unexpected_layout(tmp_path, monkeypatch):
    """A symlink that doesn't end in `<app_root>/<APP_DIR_NAME>/kickstart` falls back to None."""
    elsewhere = tmp_path / "somewhere" / "kickstart"
    elsewhere.parent.mkdir(parents=True)
    elsewhere.write_text("#!/bin/sh\n")
    elsewhere.chmod(0o755)

    launcher = tmp_path / "bin" / updater.BINARY_NAME
    launcher.parent.mkdir(parents=True)
    launcher.symlink_to(elsewhere)
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])
    resolved_dir, resolved_root = updater.resolve_current_install_layout()
    assert resolved_dir == launcher.parent
    assert resolved_root is None


def test_layout_healthy_symlink_needs_no_repair(tmp_path, monkeypatch):
    launcher, app_root = managed_install(tmp_path)
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])

    layout = updater.inspect_managed_layout()

    assert layout.app_root == app_root
    assert layout.launcher_dir == launcher.parent
    assert layout.canonical_executable == (app_root / updater.APP_DIR_NAME / updater.BINARY_NAME).resolve()
    assert layout.actual_executable == layout.canonical_executable
    assert layout.needs_repair is False


@pytest.mark.parametrize("depth", [1, 2])
def test_layout_detects_nested_payload(tmp_path, monkeypatch, depth):
    launcher, app_root = nested_install(tmp_path, depth=depth)
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])

    layout = updater.inspect_managed_layout()

    assert layout.app_root == app_root
    assert layout.needs_repair is True
    assert layout.actual_executable.parent.name == updater.APP_DIR_NAME
    assert ".kickstart" in layout.actual_executable.parts


def test_layout_wrapper_launched_nested_payload(tmp_path, monkeypatch):
    """A wrapper execs <app_root>/current/kickstart directly; drift is still visible there."""
    launcher, app_root = nested_install(tmp_path)
    managed_executable = app_root / updater.APP_DIR_NAME / updater.BINARY_NAME
    monkeypatch.setattr(updater.sys, "argv", [str(managed_executable)])

    layout = updater.inspect_managed_layout()

    assert layout.app_root == app_root
    assert layout.launcher_dir == managed_executable.parent
    assert layout.needs_repair is True


def test_layout_wrapper_launched_healthy_payload(tmp_path, monkeypatch):
    launcher, app_root = managed_install(tmp_path)
    managed_executable = app_root / updater.APP_DIR_NAME / updater.BINARY_NAME
    monkeypatch.setattr(updater.sys, "argv", [str(managed_executable)])

    assert updater.inspect_managed_layout().needs_repair is False


def test_layout_single_file_install_is_never_repaired(tmp_path, monkeypatch):
    launcher = tmp_path / "bin" / updater.BINARY_NAME
    launcher.parent.mkdir()
    launcher.write_text("#!/bin/sh\n")
    launcher.chmod(0o755)
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])

    layout = updater.inspect_managed_layout()

    assert layout.app_root is None
    assert layout.canonical_executable is None
    assert layout.needs_repair is False
