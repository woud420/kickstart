"""Assert every scaffold emits a working .github/workflows/ci.yml.

Generated projects rely on the per-language CI workflows in
src/templates/_shared/github/ to enforce make check on push/PR. Without
this test, a future change that drops the workflow wiring for a single
language (or that points it at the wrong language template) would only
surface when a downstream user pushes a generated repo.

The test invokes `kickstart create` as a subprocess for each (project_kind,
language) combination and asserts that the resulting project ships a
ci.yml that runs `make check`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

CI_WORKFLOW_PATH = ".github/workflows/ci.yml"

SCAFFOLDS_THAT_EMIT_CI = (
    pytest.param(("service", "python"), id="service-python"),
    pytest.param(("service", "rust"), id="service-rust"),
    pytest.param(("service", "typescript"), id="service-typescript"),
    pytest.param(("service", "go"), id="service-go"),
    pytest.param(("service", "cpp"), id="service-cpp"),
    pytest.param(("cli", "python"), id="cli-python"),
    pytest.param(("cli", "rust"), id="cli-rust"),
    pytest.param(("cli", "typescript"), id="cli-typescript"),
    pytest.param(("lib", "python"), id="lib-python"),
    pytest.param(("lib", "rust"), id="lib-rust"),
    pytest.param(("frontend", None), id="frontend"),
)


def _project_name(project_kind: str, language: str | None) -> str:
    suffix = language[:2] if language else "fe"
    return f"{project_kind}-{suffix}-ci"


def _create_args(project_kind: str, language: str | None, name: str, root: Path) -> list[str]:
    args = ["create", project_kind, name, "--root", str(root)]
    if language is not None:
        args.extend(["--lang", language])
    return args


@pytest.mark.parametrize("project_kind_language", SCAFFOLDS_THAT_EMIT_CI)
def test_scaffold_emits_ci_workflow(kickstart_run, project_kind_language: tuple[str, str | None]) -> None:
    project_kind, language = project_kind_language
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        name = _project_name(project_kind, language)
        completed = kickstart_run(
            *_create_args(project_kind, language, name, root),
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, (
            f"kickstart create failed for {project_kind}/{language}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}"
        )

        ci_file = root / name / CI_WORKFLOW_PATH
        assert ci_file.exists(), (
            f"{project_kind}/{language} did not emit {CI_WORKFLOW_PATH}. "
            f"Directory contents: {sorted(p.relative_to(root / name) for p in (root / name).rglob('*') if p.is_file())}"
        )

        ci_content = ci_file.read_text()
        assert "make check" in ci_content, (
            f"{project_kind}/{language} CI workflow does not invoke `make check`:\n{ci_content}"
        )
