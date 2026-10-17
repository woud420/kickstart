"""Focused updater checks."""

from __future__ import annotations
from unittest.mock import patch
import pytest
from src.model.dto.telemetry import (
    CliUpgradeChecksumStatus,
    CliUpgradeErrorCategory,
    CliUpgradeOutcome,
)
from src.utils import handoff, updater

from tests.unit.utils.updater_helpers import managed_install, mock_current_release, nested_install, private_tempdir


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_same_version_healthy_layout_is_already_current(mock_print, tmp_path, monkeypatch):
    launcher, _ = managed_install(tmp_path)
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])
    mock_current_release(monkeypatch)

    result = updater.check_for_update()

    assert result.outcome is CliUpgradeOutcome.ALREADY_CURRENT
    assert launcher.resolve().read_text() == "#!/bin/sh\necho healthy\n"


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.handoff.print")
@patch("src.utils.updater.print")
def test_upgrade_same_version_repairs_nested_layout(
    mock_print, mock_handoff_print, tmp_path, monkeypatch, handoff_chain
):
    """ENG-205: an already-current binary must not return before repairing a nested payload."""
    private_tmp = private_tempdir(tmp_path, monkeypatch)
    launcher, app_root = nested_install(tmp_path)
    bundle_dest = app_root / updater.APP_DIR_NAME
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])
    mock_current_release(monkeypatch)

    with pytest.raises(handoff_chain.replaced) as replaced:
        updater.check_for_update()

    result = replaced.value.result
    assert result.outcome is CliUpgradeOutcome.REPAIRED
    assert result.target_version == "1.0.0"
    assert result.error_category is CliUpgradeErrorCategory.NONE
    assert result.checksum_status is CliUpgradeChecksumStatus.NOT_REACHED

    # The public launcher path is preserved and resolves straight to the canonical payload.
    assert launcher.is_symlink()
    assert launcher.readlink() == bundle_dest / updater.BINARY_NAME
    canonical = bundle_dest / updater.BINARY_NAME
    assert launcher.resolve() == canonical.resolve()
    assert not canonical.is_symlink()
    # The payload that was running (not the stale original) is what got promoted.
    assert canonical.read_text() == "#!/bin/sh\necho running\n"
    assert (bundle_dest / "_internal" / "marker").read_text() == "running\n"
    assert not (bundle_dest / ".kickstart").exists()
    assert sorted(entry.name for entry in app_root.iterdir()) == [updater.APP_DIR_NAME]

    # Repair ran from a staged copy under the OS temp dir, then the canonical launcher cleaned it up.
    assert [call.phase.value for call in handoff_chain.calls] == ["activate", "finalize"]
    activate_call, finalize_call = handoff_chain.calls
    assert activate_call.launcher.parent.parent.parent == private_tmp
    assert activate_call.launcher.parent.parent.name.startswith(handoff.STAGE_PREFIX_REPAIR)
    assert finalize_call.launcher == canonical
    assert not activate_call.stage_dir.exists()
    assert list(private_tmp.iterdir()) == []

    messages = [c.args[0] for c in mock_print.call_args_list]
    assert not any("already up to date" in m for m in messages)
    assert any("repairing the install layout" in m for m in messages)
    handoff_messages = [c.args[0] for c in mock_handoff_print.call_args_list]
    assert any("Repaired the managed install layout" in m for m in handoff_messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.handoff.print")
@patch("src.utils.updater.print")
def test_upgrade_repairs_wrapper_launched_nested_payload(
    mock_print, mock_handoff_print, tmp_path, monkeypatch, handoff_chain
):
    """A wrapper install repairs in place; the wrapper keeps pointing at <app_root>/current/kickstart."""
    private_tempdir(tmp_path, monkeypatch)
    _, app_root = nested_install(tmp_path)
    bundle_dest = app_root / updater.APP_DIR_NAME
    canonical = bundle_dest / updater.BINARY_NAME
    wrapper = tmp_path / "wrapper-bin" / updater.BINARY_NAME
    wrapper.parent.mkdir()
    wrapper.write_text(f'#!/bin/sh\nexec "{canonical}" "$@"\n')
    monkeypatch.setattr(updater.sys, "argv", [str(canonical)])
    mock_current_release(monkeypatch)

    with pytest.raises(handoff_chain.replaced) as replaced:
        updater.check_for_update()

    assert replaced.value.result.outcome is CliUpgradeOutcome.REPAIRED
    assert not canonical.is_symlink()
    assert canonical.read_text() == "#!/bin/sh\necho running\n"
    assert not (bundle_dest / ".kickstart").exists()
    assert wrapper.read_text() == f'#!/bin/sh\nexec "{canonical}" "$@"\n'
    assert [call.phase.value for call in handoff_chain.calls] == ["activate", "finalize"]


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_repair_staging_failure_leaves_install_untouched(mock_print, tmp_path, monkeypatch):
    private_tmp = private_tempdir(tmp_path, monkeypatch)
    launcher, app_root = nested_install(tmp_path)
    running = launcher.resolve()
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])
    mock_current_release(monkeypatch)

    def fail_copytree(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("src.utils.handoff.shutil.copytree", fail_copytree)

    result = updater.check_for_update()

    assert result.outcome is CliUpgradeOutcome.FAILED
    assert result.error_category is CliUpgradeErrorCategory.INSTALLATION
    assert result.checksum_status is CliUpgradeChecksumStatus.NOT_REACHED
    assert launcher.resolve() == running
    assert (app_root / updater.APP_DIR_NAME / ".kickstart").is_dir()
    assert list(private_tmp.iterdir()) == []
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("could not stage the running payload" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_repair_exec_failure_is_a_clean_installation_failure(mock_print, tmp_path, monkeypatch):
    """When the staged launcher cannot start (e.g. noexec temp), nothing is modified."""
    private_tmp = private_tempdir(tmp_path, monkeypatch)
    launcher, app_root = nested_install(tmp_path)
    running = launcher.resolve()
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])
    mock_current_release(monkeypatch)

    def refuse_exec(launcher_path, args, env):
        raise PermissionError(13, "Permission denied", str(launcher_path))

    monkeypatch.setattr("src.utils.handoff.exec_launcher", refuse_exec)

    result = updater.check_for_update()

    assert result.outcome is CliUpgradeOutcome.FAILED
    assert result.error_category is CliUpgradeErrorCategory.INSTALLATION
    assert launcher.resolve() == running
    assert (app_root / updater.APP_DIR_NAME / ".kickstart").is_dir()
    assert list(private_tmp.iterdir()) == []
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("could not start the staged payload" in m for m in messages)
    assert any("TMPDIR" in m for m in messages)
