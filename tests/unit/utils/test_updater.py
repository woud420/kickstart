"""Tests for src.utils.updater (post tar.gz / onedir release layout)."""

from __future__ import annotations

import io
import json
import os
import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.utils import updater


# --- Pure helpers ---------------------------------------------------------


def test_repo_default(monkeypatch):
    monkeypatch.delenv("KICKSTART_REPO", raising=False)
    # The module-level constant is captured at import; we re-derive via the
    # `os.environ.get(...) or "woud420/kickstart"` shape to keep the check
    # focused on the production fallback. The constant remains the canonical
    # value when no override is set.
    assert updater.REPO == os.environ.get("KICKSTART_REPO") or "woud420/kickstart"


def test_release_url_tracks_repo():
    assert updater.RELEASE_URL.endswith(f"{updater.REPO}/releases/latest")


@pytest.mark.parametrize(
    "platform_value,machine_value,expected",
    [
        ("linux", "x86_64", "linux-x64"),
        ("linux", "amd64", "linux-x64"),
        ("linux", "aarch64", "linux-arm64"),
        ("linux", "arm64", "linux-arm64"),
        ("darwin", "x86_64", "macos-x64"),
        ("darwin", "arm64", "macos-arm64"),
    ],
)
def test_host_platform_tag_matrix(monkeypatch, platform_value, machine_value, expected):
    monkeypatch.setattr(updater.sys, "platform", platform_value)
    monkeypatch.setattr(updater.platform, "machine", lambda: machine_value)
    assert updater.host_platform_tag() == expected


def test_host_platform_tag_rejects_unknown_os(monkeypatch):
    monkeypatch.setattr(updater.sys, "platform", "win32")
    with pytest.raises(RuntimeError, match="Unsupported platform"):
        updater.host_platform_tag()


def test_host_platform_tag_rejects_unknown_arch(monkeypatch):
    monkeypatch.setattr(updater.sys, "platform", "linux")
    monkeypatch.setattr(updater.platform, "machine", lambda: "riscv64")
    with pytest.raises(RuntimeError, match="Unsupported architecture"):
        updater.host_platform_tag()


def test_host_python_minor_format():
    minor = updater.host_python_minor()
    assert minor.count(".") == 1
    major, minor_part = minor.split(".")
    assert major.isdigit() and minor_part.isdigit()


def test_expected_archive_name_default(monkeypatch):
    monkeypatch.setattr(updater.sys, "platform", "linux")
    monkeypatch.setattr(updater.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(updater, "host_python_minor", lambda: "3.14")
    assert updater.expected_archive_name() == "kickstart-linux-x64-py3.14.tar.gz"


def test_expected_archive_name_overrides():
    assert (
        updater.expected_archive_name("macos-arm64", "3.13")
        == "kickstart-macos-arm64-py3.13.tar.gz"
    )


def test_find_asset_match():
    assets = [
        {"name": "kickstart-linux-x64-py3.14.tar.gz", "browser_download_url": "https://x/a"},
        {"name": "kickstart-linux-x64-py3.14.tar.gz.sha256", "browser_download_url": "https://x/b"},
    ]
    found = updater.find_asset(assets, "kickstart-linux-x64-py3.14.tar.gz")
    assert found is not None
    assert found["browser_download_url"] == "https://x/a"


def test_find_asset_missing():
    assets = [{"name": "other.zip", "browser_download_url": "https://x/c"}]
    assert updater.find_asset(assets, "kickstart-linux-x64-py3.14.tar.gz") is None


# --- resolve_current_install_layout -------------------------------------


def test_resolve_current_install_layout_onedir(tmp_path, monkeypatch):
    """A symlinked launcher reveals the app root via the symlink target."""
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

    monkeypatch.setattr(updater, "current_binary_path", lambda: launcher)
    resolved_dir, resolved_root = updater.resolve_current_install_layout()
    assert resolved_dir == launcher_dir
    assert resolved_root == app_root


def test_resolve_current_install_layout_legacy_single_file(tmp_path, monkeypatch):
    """A non-symlink launcher (legacy single-file install) yields app_root=None."""
    launcher = tmp_path / "bin" / updater.BINARY_NAME
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#!/bin/sh\n")
    launcher.chmod(0o755)
    monkeypatch.setattr(updater, "current_binary_path", lambda: launcher)
    resolved_dir, resolved_root = updater.resolve_current_install_layout()
    assert resolved_dir == launcher.parent
    assert resolved_root is None


def test_resolve_current_install_layout_symlink_with_unexpected_layout(tmp_path, monkeypatch):
    """A symlink that doesn't end in `<app_root>/<APP_DIR_NAME>/kickstart` falls back to None."""
    elsewhere = tmp_path / "somewhere" / "kickstart"
    elsewhere.parent.mkdir(parents=True)
    elsewhere.write_text("#!/bin/sh\n")
    elsewhere.chmod(0o755)

    launcher = tmp_path / "bin" / updater.BINARY_NAME
    launcher.parent.mkdir(parents=True)
    launcher.symlink_to(elsewhere)
    monkeypatch.setattr(updater, "current_binary_path", lambda: launcher)
    resolved_dir, resolved_root = updater.resolve_current_install_layout()
    assert resolved_dir == launcher.parent
    assert resolved_root is None


# --- HTTP helpers --------------------------------------------------------


def test_fetch_release_info_decodes_json():
    payload = {"tag_name": "v9.9.9", "assets": []}
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    with patch("src.utils.updater.requests.get", return_value=response) as mock_get:
        result = updater.fetch_release_info("https://x/api")
    mock_get.assert_called_once_with("https://x/api", timeout=10)
    assert result == payload


def test_fetch_release_info_raises_on_http_error():
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError("nope")
    with patch("src.utils.updater.requests.get", return_value=response):
        with pytest.raises(requests.HTTPError):
            updater.fetch_release_info("https://x/api")


def test_download_to_writes_bytes(tmp_path):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.content = b"payload"
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    dest = tmp_path / "out.bin"
    with patch("src.utils.updater.requests.get", return_value=response):
        updater.download_to("https://x/a", dest)
    assert dest.read_bytes() == b"payload"


def test_verify_sha256_matches(tmp_path):
    archive = tmp_path / "a"
    archive.write_bytes(b"hello")
    # echo -n "hello" | shasum -a 256
    updater.verify_sha256(archive, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")


def test_verify_sha256_mismatch(tmp_path):
    archive = tmp_path / "a"
    archive.write_bytes(b"hello")
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        updater.verify_sha256(archive, "deadbeef")


# --- Archive extraction --------------------------------------------------


def _make_release_archive(tmp_path: Path, *, bundle_name: str) -> Path:
    """Build a minimal onedir-style tarball with a single top-level directory."""
    archive = tmp_path / f"{bundle_name}.tar.gz"
    bundle_root = tmp_path / "bundle-src" / bundle_name
    (bundle_root / "_internal").mkdir(parents=True)
    launcher = bundle_root / updater.BINARY_NAME
    launcher.write_text("#!/bin/sh\necho ok\n")
    launcher.chmod(0o755)
    (bundle_root / "_internal" / "marker").write_text("present\n")
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(bundle_root, arcname=bundle_name)
    return archive


def test_extract_archive_launcher_returns_inside_launcher(tmp_path):
    archive = _make_release_archive(tmp_path, bundle_name="kickstart-linux-x64-py3.14")
    extract_root = tmp_path / "out"
    extract_root.mkdir()
    launcher = updater._extract_archive_launcher(archive, extract_root)
    assert launcher.name == updater.BINARY_NAME
    assert launcher.parent.name == "kickstart-linux-x64-py3.14"
    assert launcher.exists()
    assert (launcher.parent / "_internal" / "marker").read_text() == "present\n"


def test_extract_archive_rejects_unexpected_layout(tmp_path):
    archive = tmp_path / "bad.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        # Create two top-level directories — invalid for our format.
        for n in ("a", "b"):
            data = b"x"
            info = tarfile.TarInfo(name=f"{n}/x")
            info.size = len(data)
            tar.addfile(info, fileobj=io.BytesIO(data))
    extract_root = tmp_path / "out"
    extract_root.mkdir()
    with pytest.raises(RuntimeError, match="unexpected archive layout"):
        updater._extract_archive_launcher(archive, extract_root)


def test_extract_archive_rejects_missing_launcher(tmp_path):
    archive = tmp_path / "no-launcher.tar.gz"
    bundle_root = tmp_path / "src" / "kickstart-linux-x64-py3.14"
    bundle_root.mkdir(parents=True)
    (bundle_root / "_internal").mkdir()
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(bundle_root, arcname="kickstart-linux-x64-py3.14")
    extract_root = tmp_path / "out"
    extract_root.mkdir()
    with pytest.raises(RuntimeError, match="does not contain a kickstart executable"):
        updater._extract_archive_launcher(archive, extract_root)


# --- check_for_update end-to-end paths -----------------------------------


def _release_payload(tag: str, archive_name: str, *, with_sha: bool = True) -> dict:
    assets = [
        {"name": archive_name, "browser_download_url": f"https://x/{archive_name}"},
    ]
    if with_sha:
        assets.append(
            {"name": f"{archive_name}.sha256", "browser_download_url": f"https://x/{archive_name}.sha256"}
        )
    return {"tag_name": tag, "assets": assets}


@patch("src.utils.updater.__version__", "1.0.0")
@patch("builtins.print")
def test_check_for_update_already_up_to_date(mock_print):
    payload = _release_payload("v1.0.0", "kickstart-linux-x64-py3.14.tar.gz")
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    with patch("src.utils.updater.requests.get", return_value=response):
        updater.check_for_update()
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("You're already up to date" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("builtins.print")
def test_check_for_update_missing_archive_for_host(mock_print, monkeypatch):
    # Latest release publishes the linux archive but we report ourselves as macos arm64.
    monkeypatch.setattr(updater.sys, "platform", "darwin")
    monkeypatch.setattr(updater.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(updater, "host_python_minor", lambda: "3.14")
    payload = _release_payload("v1.1.0", "kickstart-linux-x64-py3.14.tar.gz")
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    with patch("src.utils.updater.requests.get", return_value=response):
        updater.check_for_update()
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("no asset named kickstart-macos-arm64-py3.14.tar.gz" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("builtins.print")
def test_check_for_update_release_lookup_failure(mock_print):
    with patch("src.utils.updater.requests.get", side_effect=requests.ConnectionError("offline")):
        updater.check_for_update()
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("Update failed: could not query the latest release" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("builtins.print")
def test_check_for_update_invalid_json(mock_print):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.side_effect = json.JSONDecodeError("bad", "", 0)
    with patch("src.utils.updater.requests.get", return_value=response):
        updater.check_for_update()
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("Update failed" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("builtins.print")
def test_check_for_update_end_to_end_installs_bundle(mock_print, tmp_path, monkeypatch):
    """Happy path: latest release publishes a tarball we can download, verify, and install."""
    monkeypatch.setattr(updater.sys, "platform", "linux")
    monkeypatch.setattr(updater.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(updater, "host_python_minor", lambda: "3.14")

    bundle_name = "kickstart-linux-x64-py3.14"
    archive_name = f"{bundle_name}.tar.gz"

    # Pre-build a real onedir-shaped archive on disk we can hand back via requests.
    archive_path = _make_release_archive(tmp_path, bundle_name=bundle_name)
    archive_bytes = archive_path.read_bytes()
    # Compute the matching sha256.
    import hashlib
    archive_sha = hashlib.sha256(archive_bytes).hexdigest()

    payload = _release_payload("v1.1.0", archive_name, with_sha=True)

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

    # Pretend we are running from a fresh onedir install so resolve_current_install_layout
    # gives us a launcher_dir + app_root pair.
    app_root = tmp_path / "share" / "kickstart"
    bundle_dest = app_root / updater.APP_DIR_NAME
    bundle_dest.mkdir(parents=True)
    (bundle_dest / updater.BINARY_NAME).write_text("#!/bin/sh\nold\n")
    (bundle_dest / updater.BINARY_NAME).chmod(0o755)
    launcher_dir = tmp_path / "bin"
    launcher_dir.mkdir()
    launcher = launcher_dir / updater.BINARY_NAME
    launcher.symlink_to(bundle_dest / updater.BINARY_NAME)
    monkeypatch.setattr(updater, "current_binary_path", lambda: launcher)

    with patch("src.utils.updater.requests.get", side_effect=fake_get):
        updater.check_for_update()

    # Verify the launcher now points at the freshly-extracted bundle.
    assert launcher.is_symlink()
    target = launcher.resolve()
    assert target.parent.name == updater.APP_DIR_NAME
    assert target.read_text().startswith("#!/bin/sh\necho ok")

    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("Updated to 1.1.0" in m for m in messages)
    assert any("Checksum verified" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("builtins.print")
def test_check_for_update_checksum_mismatch_aborts(mock_print, tmp_path, monkeypatch):
    """Bad .sha256 content -> we bail without installing."""
    monkeypatch.setattr(updater.sys, "platform", "linux")
    monkeypatch.setattr(updater.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(updater, "host_python_minor", lambda: "3.14")

    bundle_name = "kickstart-linux-x64-py3.14"
    archive_name = f"{bundle_name}.tar.gz"
    archive_path = _make_release_archive(tmp_path, bundle_name=bundle_name)
    archive_bytes = archive_path.read_bytes()

    payload = _release_payload("v1.1.0", archive_name, with_sha=True)

    def fake_get(url, **kwargs):
        response = MagicMock()
        response.raise_for_status.return_value = None
        if url.endswith("/releases/latest"):
            response.json.return_value = payload
        elif url.endswith(".sha256"):
            response.text = "deadbeef  " + archive_name + "\n"
        else:
            response.content = archive_bytes
            response.__enter__.return_value = response
            response.__exit__.return_value = False
        return response

    monkeypatch.setattr(updater, "current_binary_path", lambda: tmp_path / "bin" / "kickstart")
    with patch("src.utils.updater.requests.get", side_effect=fake_get):
        updater.check_for_update()

    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("could not verify checksum" in m for m in messages)
    assert not any("Updated to" in m for m in messages)
