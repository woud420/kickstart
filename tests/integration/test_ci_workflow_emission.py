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
from dataclasses import dataclass, field
from pathlib import Path

import pytest

CI_WORKFLOW_PATH = ".github/workflows/ci.yml"


@dataclass(frozen=True)
class ScaffoldSpec:
    project_kind: str
    language: str | None
    extra_args: tuple[str, ...] = field(default_factory=tuple)

    @property
    def label(self) -> str:
        parts: list[str] = [self.project_kind]
        if self.language:
            parts.append(self.language)
        if self.extra_args:
            parts.append("-".join(self.extra_args).replace("--", "").replace(" ", ""))
        return "-".join(parts)


SCAFFOLDS_THAT_EMIT_CI = (
    pytest.param(ScaffoldSpec("service", "python"), id="service-python"),
    pytest.param(ScaffoldSpec("service", "rust"), id="service-rust"),
    pytest.param(ScaffoldSpec("service", "typescript"), id="service-typescript"),
    pytest.param(ScaffoldSpec("service", "go"), id="service-go"),
    pytest.param(ScaffoldSpec("service", "cpp"), id="service-cpp"),
    pytest.param(
        ScaffoldSpec("service", "typescript", ("--runtime", "cloudflare-workers")),
        id="service-typescript-cf",
    ),
    pytest.param(
        ScaffoldSpec("service", "rust", ("--runtime", "cloudflare-workers")),
        id="service-rust-cf",
    ),
    pytest.param(ScaffoldSpec("cli", "python"), id="cli-python"),
    pytest.param(ScaffoldSpec("cli", "rust"), id="cli-rust"),
    pytest.param(ScaffoldSpec("cli", "typescript"), id="cli-typescript"),
    pytest.param(ScaffoldSpec("lib", "python"), id="lib-python"),
    pytest.param(ScaffoldSpec("lib", "rust"), id="lib-rust"),
    pytest.param(ScaffoldSpec("frontend", None), id="frontend"),
)


def _project_name(spec: ScaffoldSpec) -> str:
    suffix = spec.language[:2] if spec.language else "fe"
    cf_tag = "-cf" if "cloudflare-workers" in spec.extra_args else ""
    return f"{spec.project_kind}-{suffix}{cf_tag}-ci"


def _create_args(spec: ScaffoldSpec, name: str, root: Path) -> list[str]:
    args = ["create", spec.project_kind, name, "--root", str(root)]
    if spec.language is not None:
        args.extend(["--lang", spec.language])
    args.extend(spec.extra_args)
    return args


def _generate(kickstart_run, spec: ScaffoldSpec, root: Path) -> Path:
    name = _project_name(spec)
    completed = kickstart_run(
        *_create_args(spec, name, root),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        f"kickstart create failed for {spec.label}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}"
    )
    return root / name


@pytest.mark.parametrize("spec", SCAFFOLDS_THAT_EMIT_CI)
def test_scaffold_emits_ci_workflow(kickstart_run, spec: ScaffoldSpec) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = _generate(kickstart_run, spec, Path(tmpdir))

        ci_file = project_root / CI_WORKFLOW_PATH
        assert ci_file.exists(), (
            f"{spec.label} did not emit {CI_WORKFLOW_PATH}. "
            f"Directory contents: {sorted(p.relative_to(project_root) for p in project_root.rglob('*') if p.is_file())}"
        )

        ci_content = ci_file.read_text()
        assert "make check" in ci_content, (
            f"{spec.label} CI workflow does not invoke `make check`:\n{ci_content}"
        )


@pytest.mark.parametrize("spec", SCAFFOLDS_THAT_EMIT_CI)
def test_dockerfile_and_docker_build_target_agree(kickstart_run, spec: ScaffoldSpec) -> None:
    """If a scaffold ships a Dockerfile, its Makefile must expose docker-build;
    if it does not ship a Dockerfile, the Makefile must not expose docker-build.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = _generate(kickstart_run, spec, Path(tmpdir))

        makefile = project_root / "Makefile"
        if not makefile.exists():
            pytest.skip(f"{spec.label} does not emit a Makefile")

        has_dockerfile = (project_root / "Dockerfile").exists()
        makefile_content = makefile.read_text()
        has_docker_build = "\ndocker-build:" in makefile_content or makefile_content.startswith(
            "docker-build:"
        )

        assert has_dockerfile == has_docker_build, (
            f"{spec.label}: Dockerfile present={has_dockerfile}, "
            f"docker-build target present={has_docker_build}. "
            "These must agree."
        )
