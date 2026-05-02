import pytest

from src.stack.profile import stack_registry
from src.utils.error_handling import LanguageNotSupportedError


def test_language_and_runtime_aliases_normalize_to_canonical_ids():
    assert stack_registry.normalize_language("ts") == "typescript"
    assert stack_registry.normalize_language("c++") == "cpp"
    assert stack_registry.normalize_service_runtime("cf-worker") == "cloudflare-workers"
    assert stack_registry.normalize_monorepo_runtime("k8s") == "kubernetes"
    assert stack_registry.normalize_cloud("cf") == "cloudflare"


def test_container_service_selection_includes_templates_and_smoke_commands():
    selection = stack_registry.service_selection("typescript", "container")

    assert selection.language == "typescript"
    assert selection.runtime == "container"
    assert selection.deployment_tool == "docker"
    assert "make typecheck" in selection.smoke_commands
    assert {"target": "package.json", "template": "typescript/package.json.tpl"} in selection.template_configs()


def test_cloudflare_worker_service_selection_is_language_limited():
    selection = stack_registry.service_selection("rust", "cloudflare-workers")

    assert selection.deployment_tool == "wrangler"
    assert "make check" in selection.smoke_commands
    assert {"target": "src/lib.rs", "template": "cloudflare-workers/rust/src/lib.rs.tpl"} in selection.template_configs()

    with pytest.raises(LanguageNotSupportedError):
        stack_registry.service_selection("cpp", "cloudflare-workers")


def test_cloudflare_worker_service_selection_rejects_helm():
    with pytest.raises(ValueError, match="does not support Helm"):
        stack_registry.service_selection("typescript", "cloudflare-workers", helm=True)


def test_monorepo_selection_resolves_cloud_knowledge_runtime_and_templates():
    selection = stack_registry.monorepo_selection(
        cloud="multi",
        knowledge="both",
        runtime="cloudflare-workers",
    )

    assert selection.clouds == ("aws", "gcp", "cloudflare")
    assert selection.cloud_label == "AWS, GCP, CLOUDFLARE"
    assert selection.include_backstage is True
    assert selection.include_obsidian is True
    assert selection.uses_kubernetes is False
    assert selection.uses_cloudflare_workers is True
    assert selection.deployment_label == "Wrangler"
    assert "make cf-worker-notes" in selection.smoke_commands

    template_pairs = {(template.target, template.template) for template in selection.templates}
    assert ("infra/cloudflare/workers/README.md", "cloudflare_workers_readme.md") in template_pairs
    assert ("catalog-info.yaml", "catalog-info.yaml") in template_pairs
    assert (".obsidian/app.json", "obsidian_app.json") in template_pairs


def test_hybrid_monorepo_selection_reports_both_deployment_tools():
    selection = stack_registry.monorepo_selection(runtime="hybrid")

    assert selection.uses_kubernetes is True
    assert selection.uses_cloudflare_workers is True
    assert selection.deployment_tool == "kustomize+wrangler"
    assert selection.deployment_label == "Kustomize and Wrangler"
    assert "make k8s-render ENV=dev" in selection.smoke_commands
    assert "make cf-worker-notes" in selection.smoke_commands
