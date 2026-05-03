from pathlib import Path

import pytest

from ci.release_policy import project_version, validate_release


def write_pyproject(path: Path, version: str) -> Path:
    pyproject = path / "pyproject.toml"
    pyproject.write_text(f'[project]\nname = "kickstart"\nversion = "{version}"\n', encoding="utf-8")
    return pyproject


def test_project_version_reads_project_metadata(tmp_path: Path) -> None:
    assert project_version(write_pyproject(tmp_path, "0.4.1")) == "0.4.1"


def test_validate_release_accepts_stable_semver_matching_package_version() -> None:
    result = validate_release("v0.4.1", "0.4.1")

    assert result.tag == "v0.4.1"
    assert result.version == "0.4.1"


@pytest.mark.parametrize("tag", ["0.4.1", "v0.4", "v0.4.1-rc.1", "v0.4.1+build.1", "vx.y.z"])
def test_validate_release_rejects_non_stable_release_tags(tag: str) -> None:
    with pytest.raises(ValueError, match="stable semantic version tags"):
        validate_release(tag, "0.4.1")


def test_validate_release_requires_tag_to_match_package_version() -> None:
    with pytest.raises(ValueError, match="does not match project.version"):
        validate_release("v0.4.2", "0.4.1")
