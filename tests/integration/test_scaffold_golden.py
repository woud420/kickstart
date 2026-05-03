from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from tests.integration.golden_assertions import assert_matches_golden_scaffold

REQUIRED_KEY_FILES = (
    ".kickstart/scaffold.json",
    "AGENTS.md",
    "Makefile",
    "README.md",
    "docs/architecture/README.md",
    "docs/contracts/README.md",
    "docs/decisions/README.md",
    "docs/operations/README.md",
    "wrangler.toml",
    "package.json",
    "src/index.ts",
    "tests/worker.test.ts",
)


def _run_hello_worker_create_command(output_root: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)

    command = [
        sys.executable,
        str(repo_root / "kickstart.py"),
        "create",
        "service",
        "hello-worker",
        "--lang",
        "typescript",
        "--runtime",
        "cloudflare-worker",
        "--root",
        str(output_root),
    ]

    completed = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    if completed.returncode != 0:
        rendered_command = shlex.join(command)
        raise AssertionError(
            "Failed to generate hello-worker scaffold fixture candidate.\n"
            f"Command: {rendered_command}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}"
        )

    return output_root / "hello-worker"


def test_typescript_cloudflare_worker_scaffold_matches_golden() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    fixture_root = repo_root / "tests/fixtures/golden/service-hello-worker-typescript-cloudflare-worker"

    assert fixture_root.exists(), f"Golden fixture directory does not exist: {fixture_root}"

    with tempfile.TemporaryDirectory() as tmpdir:
        generated_root = _run_hello_worker_create_command(Path(tmpdir))
        assert generated_root.exists(), f"Generated scaffold directory does not exist: {generated_root}"

        assert_matches_golden_scaffold(
            generated_root=generated_root,
            fixture_root=fixture_root,
            required_key_files=REQUIRED_KEY_FILES,
        )
