import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.embed_posthog_token import clear_build_config, render_build_config, write_build_config


def test_render_build_config_rejects_non_capture_credentials() -> None:
    with pytest.raises(ValueError, match="public PostHog phc_"):
        render_build_config("phx_personal_key")


def test_write_and_clear_build_config(tmp_path: Path) -> None:
    target = tmp_path / "_build_config.py"

    write_build_config(target, 'phc_public_token_with_"quotes"')

    written = target.read_text(encoding="utf-8")
    assert 'phc_public_token_with_\\"quotes\\"' in written
    clear_build_config(target)
    assert 'EMBEDDED_POSTHOG_PROJECT_TOKEN: Final[str] = ""' in target.read_text(encoding="utf-8")


def test_cli_does_not_print_the_token(tmp_path: Path) -> None:
    token = "phc_do_not_print_this_value"
    target = tmp_path / "_build_config.py"
    environment = os.environ.copy()
    environment["POSTHOG_PUBLIC_CUSTOMER_API_TOKEN"] = token

    result = subprocess.run(
        [sys.executable, "scripts/embed_posthog_token.py", "--write", "--allow-local", "--target", str(target)],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 0
    assert token not in result.stdout
    assert token not in result.stderr
    assert token in target.read_text(encoding="utf-8")


def test_cli_refuses_to_stage_into_a_local_checkout_without_explicit_override(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment.pop("GITHUB_ACTIONS", None)
    environment["POSTHOG_PUBLIC_CUSTOMER_API_TOKEN"] = "phc_local_test_token"

    result = subprocess.run(
        [sys.executable, "scripts/embed_posthog_token.py", "--write", "--target", str(tmp_path / "config.py")],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode != 0
    assert "pass --allow-local" in result.stderr
