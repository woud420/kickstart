"""Focused updater checks."""

from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from src.model.dto.telemetry import (
    CliUpgradeChecksumStatus,
    CliUpgradeOutcome,
)
from src.utils import handoff, updater

from tests.unit.utils.updater_helpers import (
    managed_install,
    nested_install,
    private_tempdir,
    release_archive,
    release_payload,
)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.handoff.print")
@patch("src.utils.updater.print")
def test_upgrade_repairs_nested_layout(mock_print, mock_handoff_print, tmp_path, monkeypatch, handoff_chain):
    """ENG-204 regression: two upgrades repair nesting and keep one stable managed root.

    ENG-205: both upgrades activate the new payload through the staged process
    handoff instead of replacing ``<app_root>/current`` from inside it.
    """
    private_tempdir(tmp_path, monkeypatch)
    monkeypatch.setattr(updater.sys, "platform", "linux")
    monkeypatch.setattr(updater.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(updater, "host_python_minor", lambda: "3.14")

    bundle_name = "kickstart-linux-x64-py3.14"
    archive_name = f"{bundle_name}.tar.gz"

    # Pre-build a real onedir-shaped archive on disk we can hand back via requests.
    archive_path = release_archive(tmp_path, bundle_name=bundle_name)
    archive_bytes = archive_path.read_bytes()
    # Compute the matching sha256.
    import hashlib

    archive_sha = hashlib.sha256(archive_bytes).hexdigest()

    payload = release_payload("v1.1.0", archive_name, with_sha=True)

    def fake_get(url, **kwargs):
        response = MagicMock()
        response.raise_for_status.return_value = None
        if url.endswith("/releases/latest"):
            response.json.return_value = payload
        elif url.endswith(".sha256"):
            response.text = f"{archive_sha}  {archive_name}\n"
        else:
            response.content = archive_bytes
            response.__enter__.return_value = response
            response.__exit__.return_value = False
        return response

    # Reproduce the broken layout created by an older upgrade: the public launcher
    # still points at the canonical managed executable, but that executable became
    # another symlink to a nested payload.
    launcher, app_root = nested_install(tmp_path)
    bundle_dest = app_root / updater.APP_DIR_NAME
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])

    with patch("src.utils.updater.requests.get", side_effect=fake_get):
        with pytest.raises(handoff_chain.replaced) as first:
            updater.check_for_update()
        assert launcher.resolve().parent == bundle_dest
        assert not (bundle_dest / ".kickstart").exists()

        with pytest.raises(handoff_chain.replaced) as second:
            updater.check_for_update()

    for result in (first.value.result, second.value.result):
        assert result.target_version == "1.1.0"
        assert result.outcome.value == "updated"
        assert result.error_category.value == "none"
        assert result.checksum_status.value == "verified"

    # Both upgrades converge on the same public launcher and canonical payload.
    assert launcher.is_symlink()
    assert launcher.readlink() == bundle_dest / updater.BINARY_NAME
    target = launcher.resolve()
    assert target.parent == bundle_dest
    assert target.read_text().startswith("#!/bin/sh\necho ok")
    assert not (bundle_dest / ".kickstart").exists()

    # Each upgrade activated from a staged copy outside the app root, then handed
    # off to the canonical launcher, which removed its staging directory.
    assert [call.phase.value for call in handoff_chain.calls] == ["activate", "finalize", "activate", "finalize"]
    for activate_call in handoff_chain.calls[::2]:
        assert activate_call.launcher.name == updater.BINARY_NAME
        assert not activate_call.launcher.resolve().is_relative_to(app_root.resolve())
        assert activate_call.launcher.parent.parent.parent.name.startswith(handoff.STAGE_PREFIX_UPGRADE)
        assert not activate_call.stage_dir.exists()
    for finalize_call in handoff_chain.calls[1::2]:
        assert finalize_call.launcher == bundle_dest / updater.BINARY_NAME

    messages = [c.args[0] for c in mock_print.call_args_list]
    assert sum("Checksum verified" in m for m in messages) == 2
    assert sum("also repairs the layout" in m for m in messages) == 1
    handoff_messages = [c.args[0] for c in mock_handoff_print.call_args_list]
    assert sum("Updated to 1.1.0" in m for m in handoff_messages) == 2


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.handoff.print")
@patch("src.utils.updater.print")
def test_managed_upgrade_uses_handoff(mock_print, mock_handoff_print, tmp_path, monkeypatch, handoff_chain):
    """A healthy managed install never replaces <app_root>/current from inside it."""
    private_tempdir(tmp_path, monkeypatch)
    monkeypatch.setattr(updater.sys, "platform", "linux")
    monkeypatch.setattr(updater.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(updater, "host_python_minor", lambda: "3.14")
    bundle_name = "kickstart-linux-x64-py3.14"
    archive_bytes = release_archive(tmp_path, bundle_name=bundle_name).read_bytes()
    payload = release_payload("v1.1.0", f"{bundle_name}.tar.gz", with_sha=False)

    def fake_get(url, **kwargs):
        response = MagicMock()
        response.raise_for_status.return_value = None
        if url.endswith("/releases/latest"):
            response.json.return_value = payload
        else:
            response.content = archive_bytes
            response.__enter__.return_value = response
            response.__exit__.return_value = False
        return response

    launcher, app_root = managed_install(tmp_path)
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])

    with patch("src.utils.updater.requests.get", side_effect=fake_get):
        with pytest.raises(handoff_chain.replaced) as replaced:
            updater.check_for_update()

    result = replaced.value.result
    assert result.outcome is CliUpgradeOutcome.UPDATED
    assert result.target_version == "1.1.0"
    assert result.checksum_status is CliUpgradeChecksumStatus.NOT_PUBLISHED
    canonical = app_root / updater.APP_DIR_NAME / updater.BINARY_NAME
    assert launcher.resolve() == canonical.resolve()
    assert canonical.read_text().startswith("#!/bin/sh\necho ok")
    assert [call.phase.value for call in handoff_chain.calls] == ["activate", "finalize"]
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert not any("also repairs the layout" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_single_file_install_upgrades_in_process(mock_print, tmp_path, monkeypatch, handoff_chain):
    """Legacy single-file launchers have no app root to protect and keep the in-process install."""
    private_tempdir(tmp_path, monkeypatch)
    monkeypatch.setattr(updater.sys, "platform", "linux")
    monkeypatch.setattr(updater.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(updater, "host_python_minor", lambda: "3.14")
    bundle_name = "kickstart-linux-x64-py3.14"
    archive_bytes = release_archive(tmp_path, bundle_name=bundle_name).read_bytes()
    payload = release_payload("v1.1.0", f"{bundle_name}.tar.gz", with_sha=False)

    def fake_get(url, **kwargs):
        response = MagicMock()
        response.raise_for_status.return_value = None
        if url.endswith("/releases/latest"):
            response.json.return_value = payload
        else:
            response.content = archive_bytes
            response.__enter__.return_value = response
            response.__exit__.return_value = False
        return response

    launcher = tmp_path / "bin" / updater.BINARY_NAME
    launcher.parent.mkdir()
    launcher.write_text("#!/bin/sh\necho single-file\n")
    launcher.chmod(0o755)
    monkeypatch.setattr(updater.sys, "argv", [str(launcher)])

    with patch("src.utils.updater.requests.get", side_effect=fake_get):
        result = updater.check_for_update()

    assert result.outcome is CliUpgradeOutcome.UPDATED
    assert handoff_chain.calls == []
    assert launcher.is_symlink()
    assert launcher.resolve().read_text().startswith("#!/bin/sh\necho ok")
