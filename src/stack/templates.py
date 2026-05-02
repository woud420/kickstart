"""Stack template mapping helpers."""

from src.stack.agent_workflows import agent_workflow_template_configs
from src.stack.types import KnowledgeProfile, RuntimeProfile, TemplateConfig


def service_templates(language: str, runtime: str) -> tuple[TemplateConfig, ...]:
    """Return service template mappings for a language/runtime pair."""
    if runtime == "cloudflare-workers":
        return _cloudflare_worker_service_templates(language)

    common = (
        TemplateConfig("README.md", f"{language}/README.md.tpl"),
        TemplateConfig(".gitignore", f"{language}/gitignore.tpl"),
        TemplateConfig("Dockerfile", f"{language}/Dockerfile.tpl"),
        TemplateConfig("Makefile", f"{language}/Makefile.tpl"),
    )
    language_specific = {
        "python": (
            TemplateConfig("requirements.txt", "python/requirements.txt.tpl"),
            TemplateConfig("pyproject.toml", "python/pyproject.toml.tpl"),
        ),
        "rust": (TemplateConfig("Cargo.toml", "rust/Cargo.toml.tpl"),),
        "go": (TemplateConfig("go.mod", "go/go.mod.tpl"),),
        "typescript": (
            TemplateConfig("package.json", "typescript/package.json.tpl"),
            TemplateConfig("tsconfig.json", "typescript/tsconfig.json.tpl"),
            TemplateConfig("tsconfig.build.json", "typescript/tsconfig.build.json.tpl"),
            TemplateConfig("bunfig.toml", "typescript/bunfig.toml.tpl"),
        ),
        "cpp": (TemplateConfig("CMakeLists.txt", "cpp/CMakeLists.txt.tpl"),),
    }
    return common + language_specific.get(language, ())


def monorepo_templates(
    environments: tuple[str, ...],
    knowledge_profile: KnowledgeProfile,
    runtime_profile: RuntimeProfile,
) -> tuple[TemplateConfig, ...]:
    """Return monorepo template mappings for selected stack profiles."""
    templates = [
        TemplateConfig("infra/docker/docker-compose.yml", "docker-compose.yml"),
        TemplateConfig("infra/terraform/versions.tf", "terraform_versions.tf"),
        TemplateConfig("infra/terraform/providers.tf", "terraform_providers.tf"),
        TemplateConfig("infra/terraform/modules/service_runtime/main.tf", "terraform_module_service_runtime.tf"),
        TemplateConfig("data/postgres/schema.sql", "postgres_schema.sql"),
        TemplateConfig("docs/decisions/0001-stack-profile.md", "adr_stack_profile.md"),
        *agent_workflow_template_configs(),
        TemplateConfig("docs/architecture/context.md", "architecture_context.md"),
        TemplateConfig("docs/data/README.md", "data_readme.md"),
        TemplateConfig("docs/knowledge/README.md", "knowledge_readme.md"),
        TemplateConfig("knowledge/README.md", "knowledge_root_readme.md"),
        TemplateConfig("package.json", "package.json.tpl"),
        TemplateConfig("turbo.json", "turbo.json.tpl"),
        TemplateConfig("bunfig.toml", "bunfig.toml.tpl"),
        TemplateConfig("config/tsconfig/base.json", "tsconfig_base.json.tpl"),
    ]

    for env in environments:
        templates.extend(
            [
                TemplateConfig(f"infra/terraform/env/{env}/main.tf", "terraform_env_main.tf", {"environment": env}),
                TemplateConfig(
                    f"infra/terraform/env/{env}/variables.tf",
                    "variables.tf",
                    {"environment": env},
                ),
                TemplateConfig(
                    f"infra/terraform/env/{env}/terraform.tfvars.example",
                    "terraform.tfvars.example",
                    {"environment": env},
                ),
            ]
        )

    templates.extend(
        [
            TemplateConfig(".github/workflows/build.yml", "build.yml"),
            TemplateConfig(".github/workflows/test.yml", "test.yml"),
            TemplateConfig(".github/workflows/deploy.yml", "deploy.yml"),
        ]
    )

    if knowledge_profile.include_backstage:
        templates.extend(
            [
                TemplateConfig("catalog-info.yaml", "catalog-info.yaml"),
                TemplateConfig("templates/backstage/template.yaml", "backstage_template.yaml"),
            ]
        )

    if knowledge_profile.include_obsidian:
        templates.extend(
            [
                TemplateConfig(".obsidian/app.json", "obsidian_app.json"),
                TemplateConfig(".obsidian/graph.json", "obsidian_graph.json"),
            ]
        )

    if runtime_profile.uses_cloudflare_workers:
        templates.extend(
            [
                TemplateConfig("infra/cloudflare/workers/README.md", "cloudflare_workers_readme.md"),
                TemplateConfig("infra/cloudflare/workers/wrangler.example.toml", "cloudflare_workers_wrangler.toml"),
            ]
        )

    return tuple(templates)


def kustomize_template_configs() -> tuple[TemplateConfig, ...]:
    """Return Kubernetes Kustomize template mappings."""
    return (
        TemplateConfig("infra/k8s/base/kustomization.yaml", "kustomize/kustomization.yaml"),
        TemplateConfig("infra/k8s/base/deployment.yaml", "kustomize/deployment.yaml"),
        TemplateConfig("infra/k8s/base/service.yaml", "kustomize/service.yaml"),
        TemplateConfig("infra/k8s/base/configmap.yaml", "kustomize/configmap.yaml"),
        TemplateConfig("infra/k8s/base/secret.yaml", "kustomize/secret.yaml"),
        TemplateConfig("infra/k8s/base/hpa.yaml", "kustomize/hpa.yaml"),
        TemplateConfig("infra/k8s/base/networkpolicy.yaml", "kustomize/networkpolicy.yaml"),
    )


def helm_template_configs() -> tuple[TemplateConfig, ...]:
    """Return Helm chart template mappings."""
    return (
        TemplateConfig("infra/helm/example-service/Chart.yaml", "helm/Chart.yaml"),
        TemplateConfig("infra/helm/example-service/values.yaml", "helm/values.yaml"),
        TemplateConfig("infra/helm/example-service/templates/deployment.yaml", "helm/deployment.yaml"),
        TemplateConfig("infra/helm/example-service/templates/service.yaml", "helm/service.yaml"),
        TemplateConfig("infra/helm/example-service/templates/configmap.yaml", "helm/configmap.yaml"),
        TemplateConfig("infra/helm/example-service/templates/_helpers.tpl", "helm/_helpers.tpl"),
    )


def _cloudflare_worker_service_templates(language: str) -> tuple[TemplateConfig, ...]:
    base = f"cloudflare-workers/{language}"
    common = (
        TemplateConfig("README.md", f"{base}/README.md.tpl"),
        TemplateConfig(".gitignore", f"{base}/gitignore.tpl"),
        TemplateConfig("Makefile", f"{base}/Makefile.tpl"),
        TemplateConfig("wrangler.toml", f"{base}/wrangler.toml.tpl"),
        TemplateConfig(".dev.vars.example", f"{base}/dev.vars.example.tpl"),
    )
    worker_specific = {
        "typescript": (
            TemplateConfig("package.json", f"{base}/package.json.tpl"),
            TemplateConfig("tsconfig.json", f"{base}/tsconfig.json.tpl"),
            TemplateConfig("src/index.ts", f"{base}/src/index.ts.tpl"),
            TemplateConfig("tests/worker.test.ts", f"{base}/tests/worker.test.ts.tpl"),
        ),
        "rust": (
            TemplateConfig("Cargo.toml", f"{base}/Cargo.toml.tpl"),
            TemplateConfig("package.json", f"{base}/package.json.tpl"),
            TemplateConfig("src/lib.rs", f"{base}/src/lib.rs.tpl"),
            TemplateConfig("tests/README.md", f"{base}/tests/README.md.tpl"),
        ),
    }
    return common + worker_specific[language]
