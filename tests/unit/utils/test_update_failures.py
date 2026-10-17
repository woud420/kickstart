"""Focused updater checks."""

from __future__ import annotations
import json
from unittest.mock import MagicMock, patch
import requests
from src.utils import updater

from tests.unit.utils.updater_helpers import release_archive, release_payload


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_already_up_to_date(mock_print):
    payload = release_payload("v1.0.0", "kickstart-linux-x64-py3.14.tar.gz")
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    with patch("src.utils.updater.requests.get", return_value=response):
        result = updater.check_for_update()
    assert result.target_version == "1.0.0"
    assert result.outcome.value == "already_current"
    assert result.error_category.value == "none"
    assert result.checksum_status.value == "not_reached"
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("You're already up to date" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_missing_archive_for_host(mock_print, monkeypatch):
    # Latest release publishes the linux archive but we report ourselves as macos arm64.
    monkeypatch.setattr(updater.sys, "platform", "darwin")
    monkeypatch.setattr(updater.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(updater, "host_python_minor", lambda: "3.14")
    payload = release_payload("v1.1.0", "kickstart-linux-x64-py3.14.tar.gz")
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    with patch("src.utils.updater.requests.get", return_value=response):
        result = updater.check_for_update()
    assert result.target_version == "1.1.0"
    assert result.outcome.value == "failed"
    assert result.error_category.value == "archive_missing"
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("no asset named kickstart-macos-arm64-py3.14.tar.gz" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_release_lookup_failure(mock_print):
    with patch("src.utils.updater.requests.get", side_effect=requests.ConnectionError("offline")):
        result = updater.check_for_update()
    assert result.target_version == "unknown"
    assert result.outcome.value == "failed"
    assert result.error_category.value == "release_lookup"
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("Update failed: could not query the latest release" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_invalid_json(mock_print):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.side_effect = json.JSONDecodeError("bad", "", 0)
    with patch("src.utils.updater.requests.get", return_value=response):
        updater.check_for_update()
    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("Update failed" in m for m in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_invalid_release_metadata_is_categorized(mock_print):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {}

    with patch("src.utils.updater.requests.get", return_value=response):
        result = updater.check_for_update()

    assert result.target_version == "unknown"
    assert result.outcome.value == "failed"
    assert result.error_category.value == "invalid_release_metadata"
    assert result.checksum_status.value == "not_reached"
    messages = [call.args[0] for call in mock_print.call_args_list]
    assert any("release metadata is invalid" in message for message in messages)


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_unsupported_platform_is_categorized(mock_print):
    payload = release_payload("v1.1.0", "kickstart-linux-x64-py3.14.tar.gz")

    with (
        patch("src.utils.updater.fetch_release_info", return_value=payload),
        patch("src.utils.updater.expected_archive_name", side_effect=RuntimeError("private detail")),
    ):
        result = updater.check_for_update()

    assert result.error_category.value == "unsupported_platform"
    assert result.target_version == "1.1.0"


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_download_failure_is_categorized(mock_print, tmp_path):
    archive_name = "kickstart-linux-x64-py3.14.tar.gz"
    payload = release_payload("v1.1.0", archive_name, with_sha=False)

    with (
        patch("src.utils.updater.fetch_release_info", return_value=payload),
        patch("src.utils.updater.expected_archive_name", return_value=archive_name),
        patch("src.utils.updater.resolve_current_install_layout", return_value=(tmp_path, None)),
        patch("src.utils.updater.download_to", side_effect=requests.ConnectionError("private detail")),
    ):
        result = updater.check_for_update()

    assert result.error_category.value == "download"
    assert result.checksum_status.value == "not_reached"


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_checksum_fetch_failure_is_categorized(mock_print, tmp_path):
    archive_name = "kickstart-linux-x64-py3.14.tar.gz"
    payload = release_payload("v1.1.0", archive_name)

    with (
        patch("src.utils.updater.fetch_release_info", return_value=payload),
        patch("src.utils.updater.expected_archive_name", return_value=archive_name),
        patch("src.utils.updater.resolve_current_install_layout", return_value=(tmp_path, None)),
        patch("src.utils.updater.download_to"),
        patch("src.utils.updater.requests.get", side_effect=requests.ConnectionError("private detail")),
    ):
        result = updater.check_for_update()

    assert result.error_category.value == "checksum_fetch"
    assert result.checksum_status.value == "failed"


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_extraction_failure_preserves_missing_checksum_status(mock_print, tmp_path):
    archive_name = "kickstart-linux-x64-py3.14.tar.gz"
    payload = release_payload("v1.1.0", archive_name, with_sha=False)

    with (
        patch("src.utils.updater.fetch_release_info", return_value=payload),
        patch("src.utils.updater.expected_archive_name", return_value=archive_name),
        patch("src.utils.updater.resolve_current_install_layout", return_value=(tmp_path, None)),
        patch("src.utils.updater.download_to"),
        patch("src.utils.updater._extract_archive_launcher", side_effect=RuntimeError("private detail")),
    ):
        result = updater.check_for_update()

    assert result.error_category.value == "archive_extraction"
    assert result.checksum_status.value == "not_published"


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_install_failure_is_categorized(mock_print, tmp_path):
    archive_name = "kickstart-linux-x64-py3.14.tar.gz"
    payload = release_payload("v1.1.0", archive_name, with_sha=False)

    with (
        patch("src.utils.updater.fetch_release_info", return_value=payload),
        patch("src.utils.updater.expected_archive_name", return_value=archive_name),
        patch("src.utils.updater.resolve_current_install_layout", return_value=(tmp_path, None)),
        patch("src.utils.updater.download_to"),
        patch("src.utils.updater._extract_archive_launcher", return_value=tmp_path / "kickstart"),
        patch("src.utils.updater.install_binary", side_effect=OSError("private detail")),
    ):
        result = updater.check_for_update()

    assert result.error_category.value == "installation"
    assert result.checksum_status.value == "not_published"


@patch("src.utils.updater.__version__", "1.0.0")
@patch("src.utils.updater.print")
def test_upgrade_checksum_mismatch_aborts(mock_print, tmp_path, monkeypatch):
    """Bad .sha256 content -> we bail without installing."""
    monkeypatch.setattr(updater.sys, "platform", "linux")
    monkeypatch.setattr(updater.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(updater, "host_python_minor", lambda: "3.14")

    bundle_name = "kickstart-linux-x64-py3.14"
    archive_name = f"{bundle_name}.tar.gz"
    archive_path = release_archive(tmp_path, bundle_name=bundle_name)
    archive_bytes = archive_path.read_bytes()

    payload = release_payload("v1.1.0", archive_name, with_sha=True)

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

    monkeypatch.setattr(updater, "current_entrypoint_path", lambda: tmp_path / "bin" / "kickstart")
    with patch("src.utils.updater.requests.get", side_effect=fake_get):
        result = updater.check_for_update()

    assert result.target_version == "1.1.0"
    assert result.outcome.value == "failed"
    assert result.error_category.value == "checksum_mismatch"
    assert result.checksum_status.value == "failed"

    messages = [c.args[0] for c in mock_print.call_args_list]
    assert any("could not verify checksum" in m for m in messages)
    assert not any("Updated to" in m for m in messages)
