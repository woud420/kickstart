from pathlib import Path

import pytest

from ci.release_policy import project_version, runtime_version, validate_release, validate_version_sync


def write_pyproject(path: Path, version: str) -> Path:
    pyproject = path / "pyproject.toml"
    pyproject.write_text(f'[project]\nname = "kickstart"\nversion = "{version}"\n', encoding="utf-8")
    return pyproject


def write_init(path: Path, body: str) -> Path:
    init_file = path / "__init__.py"
    init_file.write_text(body, encoding="utf-8")
    return init_file


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


def test_runtime_version_reads_dunder_version(tmp_path: Path) -> None:
    assert runtime_version(write_init(tmp_path, '__version__ = "0.4.2"\n')) == "0.4.2"


def test_runtime_version_requires_dunder_version(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="does not define __version__"):
        runtime_version(write_init(tmp_path, "VERSION = '0.4.2'\n"))


def test_validate_version_sync_accepts_matching_versions() -> None:
    validate_version_sync("0.4.2", "0.4.2")


def test_validate_version_sync_rejects_desynced_versions() -> None:
    with pytest.raises(ValueError, match="does not match runtime __version__"):
        validate_version_sync("0.4.2", "0.4.0")
