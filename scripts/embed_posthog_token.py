"""Validate, stage, or clear the public PostHog token used in release artifacts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Final


POSTHOG_PROJECT_TOKEN_ENV: Final[str] = "POSTHOG_PUBLIC_CUSTOMER_API_TOKEN"
DEFAULT_TARGET: Final[Path] = Path(__file__).parents[1] / "src" / "telemetry" / "_build_config.py"


def is_public_project_token(value: str) -> bool:
    """Return whether a value is a non-empty public PostHog capture token."""
    return value.startswith("phc_") and len(value) > len("phc_")


def render_build_config(project_token: str) -> str:
    """Render a Python module without interpolating unescaped configuration."""
    if not is_public_project_token(project_token):
        raise ValueError("expected a non-empty public PostHog phc_ project token")
    return (
        '"""Public telemetry configuration populated only while building release artifacts."""\n\n'
        "from typing import Final\n\n\n"
        f"EMBEDDED_POSTHOG_PROJECT_TOKEN: Final[str] = {json.dumps(project_token)}\n"
    )


def write_build_config(target: Path, project_token: str) -> None:
    """Write the validated public token into the module packaged by Poetry and PyInstaller."""
    target.write_text(render_build_config(project_token), encoding="utf-8")


def clear_build_config(target: Path) -> None:
    """Restore the checked-in tokenless build configuration."""
    target.write_text(
        '"""Public telemetry configuration populated only while building release artifacts."""\n\n'
        "from typing import Final\n\n\n"
        'EMBEDDED_POSTHOG_PROJECT_TOKEN: Final[str] = ""\n',
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate the process environment without writing.")
    mode.add_argument("--write", action="store_true", help="Stage the token in the packaged build module.")
    mode.add_argument("--clear", action="store_true", help="Restore the tokenless build module.")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument(
        "--allow-local",
        action="store_true",
        help="Permit --write outside GitHub Actions for an explicit local artifact test.",
    )
    return parser


def main() -> int:
    """Run the selected build-configuration operation without printing the token."""
    args = _parser().parse_args()
    if args.clear:
        clear_build_config(args.target)
        print("Cleared staged public PostHog build configuration.")
        return 0

    if args.write and os.environ.get("GITHUB_ACTIONS") != "true" and not args.allow_local:
        raise SystemExit("--write is restricted to GitHub Actions; pass --allow-local for an explicit local build")

    project_token = os.environ.get(POSTHOG_PROJECT_TOKEN_ENV, "").strip()
    if not is_public_project_token(project_token):
        raise SystemExit(f"{POSTHOG_PROJECT_TOKEN_ENV} must contain a non-empty public phc_ project token")
    if args.write:
        write_build_config(args.target, project_token)
        print("Staged public PostHog configuration for artifact builds.")
    else:
        print("Public PostHog artifact-build configuration is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
