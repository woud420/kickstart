"""Focused updater checks."""

from __future__ import annotations
import runpy
from unittest.mock import MagicMock, patch
import pytest
import requests
from src.utils import updater


@pytest.mark.parametrize("repository", [None, "other/project"])
def test_repository_setting(monkeypatch: pytest.MonkeyPatch, repository: str | None) -> None:
    if repository is None:
        monkeypatch.delenv("KICKSTART_REPO", raising=False)
    else:
        monkeypatch.setenv("KICKSTART_REPO", repository)
    values = runpy.run_path(updater.__file__)
    assert values["REPO"] == (repository or "woud420/kickstart")


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
    assert updater.expected_archive_name("macos-arm64", "3.13") == "kickstart-macos-arm64-py3.13.tar.gz"


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
