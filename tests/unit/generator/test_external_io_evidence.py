"""Real citation paths and line ranges, without semantic surface inference."""

from pathlib import Path
from typing import NoReturn

import pytest

from src.generator.external_io_contract import (
    ExternalIOContract,
    ExternalIOContractError,
    HttpSurface,
    SourceEvidence,
    SurfaceObservation,
    SurfaceUnknown,
)
from src.generator.external_io_evidence import verify_external_io_sources


def _contract(path: str = "app.py", start: int = 1, end: int | None = None) -> ExternalIOContract:
    return ExternalIOContract(
        "sample", (SurfaceObservation(HttpSurface("GET", "/declared"), (SourceEvidence(path, start, end),)),), ()
    )


@pytest.mark.parametrize(
    ("content", "start", "end"),
    [
        ("one\n", 1, None),
        ("one", 1, 1),
        ("one\r\ntwo\r\n", 1, 2),
        ("one\rtwo\r", 2, None),
        ("\n", 1, 1),
    ],
)
def test_existing_ranges_cover_standard_line_endings(tmp_path: Path, content: str, start: int, end: int | None) -> None:
    source = tmp_path / "app.py"
    source.write_bytes(content.encode("utf-8"))
    before = source.read_bytes()
    verify_external_io_sources(_contract(start=start, end=end), tmp_path)
    assert source.read_bytes() == before


@pytest.mark.parametrize(
    ("content", "start", "end"),
    [
        ("", 1, None),
        ("one\n", 2, None),
        ("one\ntwo\n", 1, 3),
    ],
)
def test_absent_lines_are_rejected(tmp_path: Path, content: str, start: int, end: int | None) -> None:
    (tmp_path / "app.py").write_text(content)
    with pytest.raises(ExternalIOContractError, match="exceeds"):
        verify_external_io_sources(_contract(start=start, end=end), tmp_path)


def test_missing_or_nonfile_sources_are_rejected(tmp_path: Path) -> None:
    for name in ("missing", "directory"):
        if name == "directory":
            (tmp_path / name).mkdir()
        with pytest.raises(ExternalIOContractError, match="not a file"):
            verify_external_io_sources(_contract(name), tmp_path)


def test_invalid_utf8_source_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_bytes(b"\xff\n")
    with pytest.raises(ExternalIOContractError, match="cannot read cited"):
        verify_external_io_sources(_contract(), tmp_path)


def test_unreadable_source_is_a_domain_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "app.py").write_text("line\n")

    def denied(self: Path, encoding: str) -> NoReturn:
        raise PermissionError("test denied")

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(ExternalIOContractError, match="cannot read cited"):
        verify_external_io_sources(_contract(), tmp_path)


@pytest.mark.parametrize("directory", [False, True])
def test_symlinks_cannot_cite_outside_the_selected_root(tmp_path: Path, directory: bool) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "app.py").write_text("outside\n")
    if directory:
        (root / "linked").symlink_to(outside, target_is_directory=True)
        path = "linked/app.py"
    else:
        (root / "linked").symlink_to(outside / "app.py")
        path = "linked"
    with pytest.raises(ExternalIOContractError, match="escapes repository"):
        verify_external_io_sources(_contract(path), root)


def test_internal_symlinks_and_repeated_citations_are_supported(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("one\ntwo\n")
    (tmp_path / "linked.py").symlink_to("app.py")
    contract = ExternalIOContract(
        "sample",
        (
            SurfaceObservation(
                HttpSurface("GET", "/"),
                (
                    SourceEvidence("linked.py", 1),
                    SourceEvidence("linked.py", 2),
                ),
            ),
        ),
        (),
    )
    verify_external_io_sources(contract, tmp_path)


def test_symlink_loop_is_a_domain_error(tmp_path: Path) -> None:
    (tmp_path / "loop").symlink_to("loop")
    with pytest.raises(ExternalIOContractError, match="cited source"):
        verify_external_io_sources(_contract("loop"), tmp_path)


def test_invalid_repository_root_is_a_domain_error(tmp_path: Path) -> None:
    with pytest.raises(ExternalIOContractError, match="cannot inspect"):
        verify_external_io_sources(_contract(), tmp_path / "missing")
    file = tmp_path / "file"
    file.write_text("file\n")
    with pytest.raises(ExternalIOContractError, match="directory"):
        verify_external_io_sources(_contract(), file)


def test_explicit_unknowns_need_no_source_or_manifest(tmp_path: Path) -> None:
    contract = ExternalIOContract("sample", (), (SurfaceUnknown("all", "Not inspected"),))
    verify_external_io_sources(contract, tmp_path)
    assert list(tmp_path.iterdir()) == []
