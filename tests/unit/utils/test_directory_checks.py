"""Existing non-directory paths cannot satisfy a directory prerequisite."""

import pytest

from src.utils.error_handling import ensure_directory_exists
from src.utils.errors import DirectoryCreationError


@pytest.mark.parametrize("symlink", [False, True])
def test_non_directory_is_not_reported_as_existing(tmp_path, symlink):
    target = tmp_path / "file"
    target.write_text("keep")
    path = tmp_path / "link" if symlink else target
    if symlink:
        path.symlink_to(target)

    assert ensure_directory_exists(path, create=False) is False
    with pytest.raises(DirectoryCreationError, match="not a directory"):
        ensure_directory_exists(path)
    assert target.read_text() == "keep"


def test_symlink_to_directory_is_supported(tmp_path):
    target = tmp_path / "directory"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    assert ensure_directory_exists(link) is True
    assert ensure_directory_exists(link, create=False) is True
