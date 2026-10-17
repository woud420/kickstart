"""Shared release archives and managed-install fixtures for updater tests."""

from __future__ import annotations
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from src.utils import updater


def release_archive(tmp_path: Path, *, bundle_name: str) -> Path:
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


def release_payload(tag: str, archive_name: str, *, with_sha: bool = True) -> dict:
    assets = [
        {"name": archive_name, "browser_download_url": f"https://x/{archive_name}"},
    ]
    if with_sha:
        assets.append({"name": f"{archive_name}.sha256", "browser_download_url": f"https://x/{archive_name}.sha256"})
    return {"tag_name": tag, "assets": assets}


def private_tempdir(tmp_path: Path, monkeypatch) -> Path:
    """Point tempfile at a per-test directory so staged payloads never touch the real /tmp."""
    private = tmp_path / "tmp"
    private.mkdir(exist_ok=True)
    monkeypatch.setattr(tempfile, "tempdir", str(private))
    return private


def managed_install(tmp_path: Path, *, launcher_body: str = "#!/bin/sh\necho healthy\n") -> tuple[Path, Path]:
    """Build a healthy managed install and return ``(public_launcher, app_root)``."""
    app_root = tmp_path / "share" / "kickstart"
    bundle_dest = app_root / updater.APP_DIR_NAME
    (bundle_dest / "_internal").mkdir(parents=True)
    (bundle_dest / "_internal" / "marker").write_text("healthy\n")
    executable = bundle_dest / updater.BINARY_NAME
    executable.write_text(launcher_body)
    executable.chmod(0o755)
    launcher_dir = tmp_path / "bin"
    launcher_dir.mkdir(exist_ok=True)
    launcher = launcher_dir / updater.BINARY_NAME
    launcher.symlink_to(executable)
    return launcher, app_root


def nested_install(tmp_path: Path, *, depth: int = 1) -> tuple[Path, Path]:
    """Model the layout an older updater left behind and return ``(public_launcher, app_root)``.

    ``<app_root>/current`` keeps the stale original payload, but its launcher
    became a symlink into ``.kickstart/current`` (``depth`` levels deep), which
    holds the payload that actually runs.
    """
    app_root = tmp_path / "share" / "kickstart"
    bundle_dest = app_root / updater.APP_DIR_NAME
    (bundle_dest / "_internal").mkdir(parents=True)
    (bundle_dest / "_internal" / "marker").write_text("stale\n")

    nested_bundle = bundle_dest
    for _ in range(depth):
        nested_bundle = nested_bundle / ".kickstart" / updater.APP_DIR_NAME
    (nested_bundle / "_internal").mkdir(parents=True)
    (nested_bundle / "_internal" / "marker").write_text("running\n")
    nested_executable = nested_bundle / updater.BINARY_NAME
    nested_executable.write_text("#!/bin/sh\necho running\n")
    nested_executable.chmod(0o755)

    managed_executable = bundle_dest / updater.BINARY_NAME
    managed_executable.symlink_to(nested_executable)
    launcher_dir = tmp_path / "bin"
    launcher_dir.mkdir(exist_ok=True)
    launcher = launcher_dir / updater.BINARY_NAME
    launcher.symlink_to(managed_executable)
    return launcher, app_root


def mock_current_release(monkeypatch, version: str = "1.0.0") -> None:
    payload = release_payload(f"v{version}", "kickstart-linux-x64-py3.14.tar.gz")
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    monkeypatch.setattr(updater.requests, "get", lambda *args, **kwargs: response)
