"""Verify package artifacts contain a configured public PostHog capture token."""

from __future__ import annotations

import argparse
import ast
import os
import tarfile
import zipfile
from pathlib import Path
from typing import Final

from scripts.embed_posthog_token import is_public_project_token


BUILD_CONFIG_SUFFIX: Final[str] = "src/telemetry/_build_config.py"
TOKEN_NAME: Final[str] = "EMBEDDED_POSTHOG_PROJECT_TOKEN"


def _source_from_wheel(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(BUILD_CONFIG_SUFFIX)]
        if len(names) != 1:
            raise ValueError("wheel must contain exactly one telemetry build configuration")
        return archive.read(names[0]).decode("utf-8")


def _source_from_sdist(path: Path) -> str:
    with tarfile.open(path, mode="r:gz") as archive:
        members = [member for member in archive.getmembers() if member.name.endswith(BUILD_CONFIG_SUFFIX)]
        if len(members) != 1:
            raise ValueError("sdist must contain exactly one telemetry build configuration")
        extracted = archive.extractfile(members[0])
        if extracted is None:
            raise ValueError("could not read telemetry build configuration from sdist")
        return extracted.read().decode("utf-8")


def embedded_token_from_artifact(path: Path) -> str:
    """Read the embedded token from a wheel or gzipped source distribution."""
    if path.suffix == ".whl":
        source = _source_from_wheel(path)
    elif path.name.endswith(".tar.gz"):
        source = _source_from_sdist(path)
    else:
        raise ValueError("expected a .whl or .tar.gz package artifact")

    module = ast.parse(source)
    for node in module.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == TOKEN_NAME
            and node.value is not None
        ):
            value = ast.literal_eval(node.value)
            if not isinstance(value, str):
                break
            return value
    raise ValueError("telemetry build configuration does not define the embedded token")


def verify_artifact(path: Path, *, expected_project_token: str | None = None) -> None:
    """Fail when an artifact lacks a non-empty public capture token."""
    embedded_project_token = embedded_token_from_artifact(path)
    if not is_public_project_token(embedded_project_token):
        raise ValueError("artifact does not contain a non-empty public phc_ project token")
    if expected_project_token is not None and embedded_project_token != expected_project_token:
        raise ValueError("artifact capture token does not match the configured PostHog project")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expected-token-env",
        help="Environment variable containing the expected token; values are compared but never printed.",
    )
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args()
    expected_project_token = None
    if args.expected_token_env is not None:
        expected_project_token = os.environ.get(args.expected_token_env, "").strip()
        if not is_public_project_token(expected_project_token):
            raise SystemExit(f"{args.expected_token_env} must contain a non-empty public phc_ project token")
    for artifact in args.artifacts:
        verify_artifact(artifact, expected_project_token=expected_project_token)
        print(f"{artifact.name}: embedded public PostHog configuration verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
