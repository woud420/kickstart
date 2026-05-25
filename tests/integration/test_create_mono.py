import json
import tempfile
from pathlib import Path
from typing import Callable

import pytest


@pytest.fixture
def _run_create_mono(kickstart_run) -> Callable[..., Path]:
    """Return a helper that runs `kickstart create mono <args>` and returns the generated project root."""

    def _runner(tmp: Path, *args: str) -> Path:
        project_name = args[0]
        root = Path(args[args.index("--root") + 1]) if "--root" in args else tmp
        kickstart_run("create", "mono", *args, cwd=tmp, check=True)
        return root / project_name

    return _runner


@pytest.fixture
def _run_create_system(kickstart_run) -> Callable[..., Path]:
    """Return a helper that runs `kickstart create system <args>` and returns the generated project root."""

    def _runner(tmp: Path, *args: str) -> Path:
        project_name = args[0]
        root = Path(args[args.index("--root") + 1]) if "--root" in args else tmp
        kickstart_run("create", "system", *args, cwd=tmp, check=True)
        return root / project_name

    return _runner


def test_create_monorepo_kustomize(_run_create_mono):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        _run_create_mono(tmp, "infra-stack", "--root", str(tmp))

        base = tmp / "infra-stack"
        assert (base / "infra/k8s/base/deployment.yaml").exists()
        assert (base / "Makefile").exists()


def test_create_system_is_workspace_neutral_by_default(_run_create_system):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        base = _run_create_system(tmp, "platform", "--root", str(tmp), "--cloud", "aws")

        manifest = json.loads((base / ".kickstart/scaffold.json").read_text())
        readme = (base / "README.md").read_text()

        assert manifest["project"] == {
            "name": "platform",
            "kind": "system",
            "repo_layout": "monorepo",
        }
        assert manifest["composition"]["workspace_tooling"] == "none"
        assert not (base / "package.json").exists()
        assert not (base / "turbo.json").exists()
        assert not (base / "config/tsconfig/base.json").exists()
        assert (base / "tools").exists()
        assert "Workspace tooling: None" in readme


def test_create_system_can_emit_bun_turbo_workspace_tooling(_run_create_system):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        base = _run_create_system(
            tmp,
            "platform",
            "--root",
            str(tmp),
            "--workspace-tooling",
            "bun-turbo",
        )

        manifest = json.loads((base / ".kickstart/scaffold.json").read_text())

        assert manifest["composition"]["workspace_tooling"] == "bun-turbo"
        assert (base / "package.json").exists()
        assert (base / "turbo.json").exists()
        assert (base / "config/tsconfig/base.json").exists()


def test_create_monorepo_kustomize_with_root(_run_create_mono):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Create a custom root directory
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        _run_create_mono(tmp, "infra-stack", "--root", str(custom_root))

        base = custom_root / "infra-stack"
        assert (base / "infra/k8s/base/deployment.yaml").exists()
        assert (base / "Makefile").exists()


def test_create_aws_kubernetes_docs_match_selected_profile(_run_create_mono):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        base = _run_create_mono(
            tmp,
            "aws-stack",
            "--root",
            str(tmp),
            "--cloud",
            "aws",
            "--runtime",
            "kubernetes",
            "--knowledge",
            "none",
        )

        readme = (base / "README.md").read_text()
        adr = (base / "docs/decisions/0001-stack-profile.md").read_text()
        knowledge = (base / "knowledge/README.md").read_text()
        build_workflow = (base / ".github/workflows/build.yml").read_text()
        test_workflow = (base / ".github/workflows/test.yml").read_text()
        deploy_workflow = (base / ".github/workflows/deploy.yml").read_text()

        assert (base / "docs/agents/recommended-agents.md").exists()
        assert (base / "AGENTS.md").exists()
        assert (base / ".kickstart/scaffold.json").exists()
        manifest = json.loads((base / ".kickstart/scaffold.json").read_text())
        assert manifest["project"] == {
            "name": "aws-stack",
            "kind": "system",
            "repo_layout": "monorepo",
        }
        assert manifest["execution"] == {"models": ["container"], "platforms": ["kubernetes"]}
        assert manifest["artifacts"]["kubernetes"] == "kustomize"
        assert manifest["provider"] == {"targets": ["aws"]}
        assert (base / "config/tsconfig/base.json").exists()
        assert "CLOUDFLARE_API_TOKEN" not in readme
        assert "Cloudflare support covers" not in adr
        assert "Kubernetes manifests" in adr
        assert "Kubernetes packaging" in adr
        assert "scratch reports to review before intentionally committing" in readme
        assert "scratch reports to review before intentionally committing" in knowledge
        assert "docker/build-push-action" not in build_workflow
        assert "make build" in build_workflow
        assert "make k8s-render ENV=dev" in test_workflow
        assert "make k8s-render ENV=${{ inputs.environment }}" in deploy_workflow


def test_create_cloudflare_workers_docs_match_runtime_profile(_run_create_mono):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        base = _run_create_mono(
            tmp,
            "edge-stack",
            "--root",
            str(tmp),
            "--cloud",
            "cloudflare",
            "--runtime",
            "cloudflare-workers",
        )

        readme = (base / "README.md").read_text()
        adr = (base / "docs/decisions/0001-stack-profile.md").read_text()
        architecture = (base / "docs/architecture/context.md").read_text()
        test_workflow = (base / ".github/workflows/test.yml").read_text()
        deploy_workflow = (base / ".github/workflows/deploy.yml").read_text()

        assert (base / "infra/cloudflare/workers/README.md").exists()
        assert not (base / "infra/k8s/base/deployment.yaml").exists()
        manifest = json.loads((base / ".kickstart/scaffold.json").read_text())
        assert manifest["project"]["kind"] == "system"
        assert manifest["execution"] == {
            "models": ["cloudflare-worker"],
            "platforms": ["cloudflare-workers"],
        }
        assert manifest["artifacts"]["worker"] == "wrangler"
        assert manifest["provider"] == {"targets": ["cloudflare"]}
        assert "CLOUDFLARE_API_TOKEN" in readme
        assert "Kubernetes manifests" not in adr
        assert "Kubernetes packaging" not in adr
        assert "Cloudflare Worker runtime notes" in adr
        assert "K8s[Kubernetes]" not in architecture
        assert "Cloudflare Worker" in architecture
        assert "make k8s-render" not in test_workflow
        assert "make k8s-render" not in deploy_workflow
        assert "make cf-worker-notes" in test_workflow
