"""Every generated scaffold satisfies its own adoption check.

docs/scaffold-contract.md, STANDARD_ARTIFACTS in src/generator/adoption.py,
and what generators actually emit are three descriptions of the same ENG-9
baseline. This test pins the round trip so the three legs cannot drift
apart silently: one scaffold per project kind is generated into a temp
directory and must report `complete: true` from the same read-only check
that `kickstart adopt --check` runs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.generator.adoption import inspect_repo
from tests.integration.conftest import KickstartRunner

ROUNDTRIP_CASES = (
    ("python-service", ("create", "service", "api", "--lang", "python")),
    ("typescript-worker", ("create", "service", "edge", "--lang", "typescript", "--runtime", "cloudflare-workers")),
    ("python-lib", ("create", "lib", "shared-models", "--lang", "python")),
    ("rust-cli", ("create", "cli", "ops-tool", "--lang", "rust")),
    ("frontend", ("create", "frontend", "web-app")),
    ("aws-kubernetes-system", ("create", "system", "platform", "--cloud", "aws", "--runtime", "kubernetes", "--knowledge", "none")),
)


@pytest.mark.parametrize(("slug", "args"), ROUNDTRIP_CASES, ids=[case[0] for case in ROUNDTRIP_CASES])
def test_generated_scaffold_passes_adoption_check(
    slug: str,
    args: tuple[str, ...],
    kickstart_run: KickstartRunner,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    completed = kickstart_run(*args, "--root", str(tmp_path), cwd=repo_root, capture_output=True, text=True)
    assert completed.returncode == 0, f"{slug} generation failed: {completed.stdout}{completed.stderr}"

    project_name = args[2]
    report = inspect_repo(tmp_path / project_name)

    incomplete = [artifact for artifact in report.artifacts if not artifact.ok]
    details = ", ".join(f"{artifact.path}: {artifact.issue or 'missing'}" for artifact in incomplete)
    assert report.complete, f"{slug} scaffold fails its own adoption check: {details}"
