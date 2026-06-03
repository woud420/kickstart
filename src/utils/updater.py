"""Self-update for the kickstart installation.

`kickstart upgrade` queries the GitHub Releases API for the latest tag, picks
the binary archive matching this host's platform and Python minor, verifies its
SHA-256, extracts it to a temp directory, and re-uses `installer.install_binary`
to overwrite the running launcher and (when this is an onedir install) refresh
the binary payload directory.
"""

from __future__ import annotations

import hashlib
import os
import platform
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Optional, TypedDict, cast

import requests

from src import __version__
from src.utils.installer import (
    APP_DIR_NAME,
    BINARY_NAME,
    InstallResult,
    current_binary_path,
    default_app_root,
    install_binary,
)


REPO: str = os.environ.get("KICKSTART_REPO") or "woud420/kickstart"
RELEASE_URL: str = f"https://api.github.com/repos/{REPO}/releases/latest"


class ReleaseAsset(TypedDict):
    """Relevant GitHub release asset fields."""

    name: str
    browser_download_url: str


class ReleaseInfo(TypedDict):
    """Relevant GitHub release response fields."""

    tag_name: str
    assets: list[ReleaseAsset]


def host_platform_tag() -> str:
    """Return the platform tag used in release asset names (e.g. ``linux-x64``)."""
    if sys.platform.startswith("linux"):
        os_tag = "linux"
    elif sys.platform == "darwin":
        os_tag = "macos"
    else:
        raise RuntimeError(f"Unsupported platform for self-update: {sys.platform}")

    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        arch_tag = "x64"
    elif machine in {"arm64", "aarch64"}:
        arch_tag = "arm64"
    else:
        raise RuntimeError(f"Unsupported architecture for self-update: {machine}")

    return f"{os_tag}-{arch_tag}"


def host_python_minor() -> str:
    """Return the Python minor used in release asset names (e.g. ``3.14``)."""
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def expected_archive_name(
    platform_tag: Optional[str] = None,
    python_minor: Optional[str] = None,
) -> str:
    """Return the archive asset name for this host (or for explicit overrides)."""
    return f"kickstart-{platform_tag or host_platform_tag()}-py{python_minor or host_python_minor()}.tar.gz"


def find_asset(assets: list[ReleaseAsset], name: str) -> Optional[ReleaseAsset]:
    """Return the asset with exactly this name, or None."""
    return next((asset for asset in assets if asset["name"] == name), None)


def resolve_current_install_layout() -> tuple[Path, Optional[Path]]:
    """Return ``(launcher_dir, app_root_or_None)`` for the currently running install.

    When the launcher is a symlink (the onedir install shape), we can recover
    the app root from the symlink target. For legacy single-file installs the
    launcher is a regular file and we return ``None`` so callers fall back to
    `default_app_root` (or skip app-root handling entirely).
    """
    launcher = current_binary_path()
    launcher_dir = launcher.parent

    if launcher.is_symlink():
        try:
            executable = launcher.resolve()
        except OSError:
            return launcher_dir, None
        # Expected layout: <app_root>/<APP_DIR_NAME>/<BINARY_NAME>
        if executable.parent.name == APP_DIR_NAME:
            return launcher_dir, executable.parent.parent

    return launcher_dir, None


def fetch_release_info(url: str = RELEASE_URL) -> ReleaseInfo:
    """Return the GitHub Releases payload for the latest release."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return cast(ReleaseInfo, response.json())


def download_to(url: str, destination: Path) -> None:
    """Stream `url` to `destination`. Raises on network/HTTP error."""
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        destination.write_bytes(response.content)


def verify_sha256(archive_path: Path, expected_hash: str) -> None:
    """Verify `archive_path` has the given hex-encoded SHA-256."""
    actual = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if actual != expected_hash:
        raise RuntimeError(f"checksum mismatch (expected {expected_hash}, got {actual})")


def _extract_archive_launcher(archive_path: Path, dest_root: Path) -> Path:
    """Extract a release tarball and return the launcher path inside the bundle."""
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(dest_root)
    bundle_dirs = [entry for entry in dest_root.iterdir() if entry.is_dir()]
    if len(bundle_dirs) != 1:
        names = sorted(entry.name for entry in dest_root.iterdir())
        raise RuntimeError(f"unexpected archive layout (top-level entries: {names})")
    launcher = bundle_dirs[0] / BINARY_NAME
    if not launcher.exists():
        raise RuntimeError(f"archive does not contain a {BINARY_NAME} executable at {launcher}")
    return launcher


def check_for_update() -> None:
    """Check for updates and install the newest release in-place."""
    print(f"[cyan]Checking for updates (current version: {__version__})...")

    try:
        info = fetch_release_info()
    except Exception as exc:
        print(f"[red]✖ Update failed: could not query the latest release: {exc}")
        return

    latest = info["tag_name"].lstrip("v")
    if latest == __version__:
        print("[green]✅ You're already up to date.")
        return

    try:
        archive_name = expected_archive_name()
    except RuntimeError as exc:
        print(f"[red]✖ Update failed: {exc}")
        return

    archive_asset = find_asset(info["assets"], archive_name)
    if archive_asset is None:
        print(
            f"[red]✖ Update failed: no asset named {archive_name} on release {info['tag_name']}. "
            "Wait for the release to publish the matching binary archive."
        )
        return

    hash_asset = find_asset(info["assets"], f"{archive_name}.sha256")
    launcher_dir, app_root = resolve_current_install_layout()

    print(f"[yellow]⬆ New version available: {latest} — downloading {archive_name}...")
    print(f"  launcher dir: {launcher_dir}")
    print(f"  app root:     {app_root or default_app_root(launcher_dir)}")

    with tempfile.TemporaryDirectory(prefix="kickstart-upgrade-") as raw_dir:
        tmp = Path(raw_dir)
        archive_path = tmp / archive_name

        try:
            download_to(archive_asset["browser_download_url"], archive_path)
        except Exception as exc:
            print(f"[red]✖ Update failed: could not download {archive_name}: {exc}")
            return

        if hash_asset is not None:
            try:
                hash_response = requests.get(hash_asset["browser_download_url"], timeout=10)
                hash_response.raise_for_status()
                expected_hash = hash_response.text.strip().split()[0]
                verify_sha256(archive_path, expected_hash)
                print(f"[green]🔒 Checksum verified ({expected_hash}).")
            except Exception as exc:
                print(f"[red]✖ Update failed: could not verify checksum: {exc}")
                return
        else:
            print("[yellow]⚠ No matching .sha256 asset; skipping checksum verification.")

        extract_root = tmp / "extracted"
        extract_root.mkdir()
        try:
            launcher = _extract_archive_launcher(archive_path, extract_root)
        except Exception as exc:
            print(f"[red]✖ Update failed: could not extract archive: {exc}")
            return

        try:
            result: InstallResult = install_binary(
                launcher,
                target_dir=launcher_dir,
                overwrite=True,
                app_root=app_root,
            )
        except Exception as exc:
            print(f"[red]✖ Update failed: could not install the new app bundle: {exc}")
            return

    print(f"[green]✔ Updated to {latest}.")
    print(f"  launcher: {result.destination}")
    if result.app_path is not None:
        print(f"  app:      {result.app_path}")
