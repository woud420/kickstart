"""Focused updater checks."""

from __future__ import annotations
import io
import tarfile
from pathlib import Path
import pytest
from src.utils import updater

from tests.unit.utils.updater_helpers import release_archive


def test_extract_archive_launcher_returns_inside_launcher(tmp_path):
    archive = release_archive(tmp_path, bundle_name="kickstart-linux-x64-py3.14")
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


@pytest.mark.parametrize("kind", ["traversal", "symlink", "hardlink"])
def test_archive_rejects_escaping_members(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    monkeypatch.setattr(tarfile.TarFile, "extraction_filter", staticmethod(tarfile.fully_trusted_filter))
    outside = tmp_path / "keep.txt"
    outside.write_text("keep")
    archive = tmp_path / "escape.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo("../keep.txt" if kind == "traversal" else "bundle/link")
        if kind == "traversal":
            member.size = 9
            tar.addfile(member, io.BytesIO(b"overwrite"))
        else:
            member.type = tarfile.SYMTYPE if kind == "symlink" else tarfile.LNKTYPE
            member.linkname = "../../keep.txt" if kind == "symlink" else "../keep.txt"
            tar.addfile(member)
        launcher = tarfile.TarInfo("bundle/kickstart")
        launcher.size = 8
        tar.addfile(launcher, io.BytesIO(b"launcher"))
    destination = tmp_path / "extracted"
    destination.mkdir()

    with pytest.raises(tarfile.FilterError):
        updater._extract_archive_launcher(archive, destination)

    assert outside.read_text() == "keep"


def test_archive_preserves_internal_symlinks(tmp_path: Path) -> None:
    archive = tmp_path / "valid.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for name, content in [("bundle/kickstart", b"launcher"), ("bundle/_internal/lib.so.1", b"library")]:
            member = tarfile.TarInfo(name)
            member.size = len(content)
            member.mode = 0o755
            tar.addfile(member, io.BytesIO(content))
        link = tarfile.TarInfo("bundle/_internal/lib.so")
        link.type = tarfile.SYMTYPE
        link.linkname = "lib.so.1"
        tar.addfile(link)
    destination = tmp_path / "extracted"
    destination.mkdir()

    launcher = updater._extract_archive_launcher(archive, destination)

    assert launcher.read_bytes() == b"launcher"
    link_path = launcher.parent / "_internal/lib.so"
    assert link_path.is_symlink()
    assert link_path.read_bytes() == b"library"
