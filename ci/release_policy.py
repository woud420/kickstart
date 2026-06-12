"""Validate release tags against package metadata."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import tomllib


STABLE_SEMVER_TAG = re.compile(r"^v(?P<version>(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))$")
RUNTIME_VERSION = re.compile(r'^__version__ = "(?P<version>[^"]+)"$', re.MULTILINE)


@dataclass(frozen=True)
class ReleasePolicyResult:
    """Validated release policy data."""

    tag: str
    version: str


def project_version(version_file: Path) -> str:
    """Return the package version from PEP 621 project metadata."""
    data = tomllib.loads(version_file.read_text(encoding="utf-8"))
    project = data.get("project")
    if not isinstance(project, dict):
        raise ValueError(f"{version_file} does not contain a [project] table")

    version = project.get("version")
    if not isinstance(version, str) or version == "":
        raise ValueError(f"{version_file} does not contain project.version")

    return version


def runtime_version(init_file: Path) -> str:
    """Return the runtime __version__ constant from the package init module."""
    match = RUNTIME_VERSION.search(init_file.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"{init_file} does not define __version__")

    return match.group("version")


def validate_version_sync(package_version: str, module_version: str) -> None:
    """Require project metadata and the runtime __version__ to agree."""
    if package_version != module_version:
        raise ValueError(
            f"project.version '{package_version}' does not match runtime __version__ '{module_version}'. "
            "Update pyproject.toml and src/__init__.py together."
        )


def validate_release(tag: str, package_version: str) -> ReleasePolicyResult:
    """Validate that a tag is a stable semver tag matching the package version."""
    match = STABLE_SEMVER_TAG.fullmatch(tag)
    if match is None:
        raise ValueError(f"Release tag '{tag}' is not supported. Use stable semantic version tags like v0.4.1.")

    tag_version = match.group("version")
    if tag_version != package_version:
        raise ValueError(
            f"Release tag '{tag}' does not match project.version '{package_version}'. "
            f"Update pyproject.toml or tag v{package_version}."
        )

    return ReleasePolicyResult(tag=tag, version=tag_version)


def main() -> int:
    """Run release policy validation from the command line."""
    parser = argparse.ArgumentParser(description="Validate a kickstart release tag.")
    parser.add_argument("--tag", required=True, help="Git tag name, for example v0.4.1")
    parser.add_argument("--version-file", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--init-file", type=Path, default=Path("src/__init__.py"))
    args = parser.parse_args()

    package_version = project_version(args.version_file)
    validate_version_sync(package_version, runtime_version(args.init_file))
    result = validate_release(args.tag, package_version)
    print(f"Release policy passed for {result.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
