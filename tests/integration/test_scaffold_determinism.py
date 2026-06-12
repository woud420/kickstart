"""Same input, same bytes: the reproducibility contract.

kickstart promises deterministic, idempotent scaffolds — an agent or CI run
regenerating a project from the same spec must get byte-identical output.
The golden test pins one scaffold's shape over time; this test pins
run-to-run determinism across project kinds.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.integration.conftest import KickstartRunner

DETERMINISM_CASES = (
    ("python-service", ("create", "service", "api", "--lang", "python", "--database", "postgres")),
    ("typescript-worker", ("create", "service", "edge", "--lang", "typescript", "--runtime", "cloudflare-workers")),
    ("rust-cli", ("create", "cli", "ops-tool", "--lang", "rust")),
)


def _tree_contents(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


@pytest.mark.parametrize(("slug", "args"), DETERMINISM_CASES, ids=[case[0] for case in DETERMINISM_CASES])
def test_same_spec_generates_byte_identical_output(
    slug: str,
    args: tuple[str, ...],
    kickstart_run: KickstartRunner,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    roots = (tmp_path / "first", tmp_path / "second")
    for root in roots:
        root.mkdir()
        completed = kickstart_run(*args, "--root", str(root), cwd=repo_root, capture_output=True, text=True)
        assert completed.returncode == 0, f"{slug} generation failed: {completed.stdout}{completed.stderr}"

    first, second = (_tree_contents(root) for root in roots)

    assert first.keys() == second.keys(), f"{slug} generated different file sets"
    different = [name for name in first if first[name] != second[name]]
    assert different == [], f"{slug} generated non-identical content in: {different}"
