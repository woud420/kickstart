from types import SimpleNamespace

import pytest
from unittest.mock import patch, call
from src.generator.system import SystemGenerator
from src.utils.errors import ProjectCreationError


def _template_written(mock_write_template, target, template):
    return any(
        template_call.args[:2] == (target, template)
        for template_call in mock_write_template.call_args_list
    )


def _expected_monorepo_dirs():
    return [
        "apps",
        "packages",
        "config/eslint",
        "config/tsconfig",
        "infra/docker",
        "infra/terraform/modules/example_module",
        "infra/terraform/modules/service_runtime",
        "infra/terraform/env/dev",
        "infra/terraform/env/staging",
        "infra/terraform/env/prod",
        ".github/workflows",
        "frontend",
        "libs",
        "services",
        "tools",
        "data/postgres",
        "knowledge",
        ".kickstart",
        ".agents/skills",
        "docs/architecture",
        "docs/contracts",
        "docs/operations",
        "docs/decisions",
        "docs/agents",
        "docs/data",
        "docs/knowledge",
        "docs/runbooks",
        "reports",
        "scripts",
    ]


@pytest.fixture
def monorepo_generator():
    return SystemGenerator("test-monorepo", False, {"key": "value"}, workspace_tooling="bun-turbo")


@pytest.fixture(autouse=True)
def mock_scaffold_contract_docs():
    with patch.object(SystemGenerator, "create_scaffold_contract_docs", return_value=True):
        yield


@pytest.fixture
def create_mocks():
    with (
        patch.object(SystemGenerator, "create_project", return_value=True) as create_project,
        patch.object(SystemGenerator, "init_basic_structure") as init_basic_structure,
        patch.object(SystemGenerator, "write_template") as write_template,
        patch.object(SystemGenerator, "create_architecture_docs") as create_architecture_docs,
        patch.object(SystemGenerator, "log_success") as log_success,
    ):
        yield SimpleNamespace(
            create_project=create_project,
            init_basic_structure=init_basic_structure,
            write_template=write_template,
            create_architecture_docs=create_architecture_docs,
            log_success=log_success,
        )


def test_monorepo_cloud_selection():
    generator = SystemGenerator("test", False, {}, cloud="gcp", knowledge="obsidian", workspace_tooling="bun-turbo")

    assert generator._clouds() == ["gcp"]
    assert generator._include_obsidian() is True
    assert generator._include_backstage() is False


def test_monorepo_multi_cloud_includes_cloudflare():
    generator = SystemGenerator("test", False, {}, cloud="multi", workspace_tooling="bun-turbo")

    assert generator._clouds() == ["aws", "gcp", "cloudflare"]
    assert generator._template_vars()["include_cloudflare"] is True
    assert generator._template_vars()["cloud_label"] == "AWS, GCP, CLOUDFLARE"
    assert generator._template_vars()["uses_bun_turbo"] is True


def test_monorepo_cloudflare_only_selection():
    generator = SystemGenerator("test", False, {}, cloud="cloudflare", workspace_tooling="bun-turbo")

    assert generator._clouds() == ["cloudflare"]
    assert generator._template_vars()["include_aws"] is False
    assert generator._template_vars()["include_gcp"] is False
    assert generator._template_vars()["include_cloudflare"] is True


def test_monorepo_cloudflare_workers_runtime_selection():
    generator = SystemGenerator("test", False, {}, cloud="cloudflare", runtime="cloudflare-workers", workspace_tooling="bun-turbo")

    assert generator._uses_kubernetes() is False
    assert generator._uses_cloudflare_workers() is True
    assert generator._template_vars()["runtime_label"] == "Cloudflare Workers"


def test_monorepo_hybrid_runtime_selection():
    generator = SystemGenerator("test", False, {}, runtime="hybrid", workspace_tooling="bun-turbo")

    assert generator._uses_kubernetes() is True
    assert generator._uses_cloudflare_workers() is True


def test_monorepo_rejects_invalid_profile_options():
    with pytest.raises(ValueError):
        SystemGenerator("test", False, {}, cloud="azure", workspace_tooling="bun-turbo").create()

    with pytest.raises(ValueError):
        SystemGenerator("test", False, {}, knowledge="wiki", workspace_tooling="bun-turbo").create()

    with pytest.raises(ValueError):
        SystemGenerator("test", False, {}, runtime="lambda", workspace_tooling="bun-turbo").create()


@patch("src.generator.monorepo.create_repo")
@patch.object(SystemGenerator, "_create_kustomize_structure")
def test_create_success_with_kustomize_and_gh(mock_create_kustomize_structure, mock_create_repo, create_mocks):
    mock_log_success = create_mocks.log_success
    mock_create_project = create_mocks.create_project
    mock_init_basic_structure = create_mocks.init_basic_structure
    mock_create_architecture_docs = create_mocks.create_architecture_docs
    mock_write_template = create_mocks.write_template

    generator = SystemGenerator("test-monorepo", True, {"key": "value"}, workspace_tooling="bun-turbo")

    generator.create()

    mock_create_project.assert_called_once()
    mock_init_basic_structure.assert_called_once_with(_expected_monorepo_dirs())

    mock_create_kustomize_structure.assert_called_once()

    expected_templates = [
        ("infra/docker/docker-compose.yml", "docker-compose.yml"),
        ("infra/terraform/env/dev/main.tf", "terraform_env_main.tf"),
        ("infra/terraform/env/dev/variables.tf", "variables.tf"),
        ("infra/terraform/env/dev/terraform.tfvars.example", "terraform.tfvars.example"),
        ("infra/terraform/env/staging/main.tf", "terraform_env_main.tf"),
        ("infra/terraform/env/staging/variables.tf", "variables.tf"),
        ("infra/terraform/env/prod/main.tf", "terraform_env_main.tf"),
        ("infra/terraform/env/prod/variables.tf", "variables.tf"),
        (".github/workflows/build.yml", "build.yml"),
        (".github/workflows/test.yml", "test.yml"),
        (".github/workflows/deploy.yml", "deploy.yml"),
        ("docs/decisions/0001-stack-profile.md", "adr_stack_profile.md"),
        ("docs/agents/recommended-agents.md", "agents_recommended.md"),
        ("knowledge/README.md", "knowledge_root_readme.md"),
        ("package.json", "package.json.tpl"),
        ("turbo.json", "turbo.json.tpl"),
        ("bunfig.toml", "bunfig.toml.tpl"),
        ("config/tsconfig/base.json", "tsconfig_base.json.tpl"),
    ]

    for target, template in expected_templates:
        assert _template_written(mock_write_template, target, template)

    mock_create_architecture_docs.assert_called_once()
    assert mock_create_architecture_docs.call_args.args[0] == "test-monorepo System Docs"
    mock_log_success.assert_called_once_with(
        "System 'test-monorepo' scaffolded as a monorepo for Kubernetes with Kustomize artifacts in 'test-monorepo'."
    )
    mock_create_repo.assert_called_once_with("test-monorepo")


@patch("src.generator.monorepo.create_repo")
@patch.object(SystemGenerator, "_create_helm_structure")
def test_create_success_with_helm(mock_create_helm_structure, mock_create_repo, create_mocks):
    mock_log_success = create_mocks.log_success

    generator = SystemGenerator("test-monorepo", False, {"key": "value"}, helm=True, workspace_tooling="bun-turbo")

    generator.create()

    mock_create_helm_structure.assert_called_once()
    mock_log_success.assert_called_once_with(
        "System 'test-monorepo' scaffolded as a monorepo for Kubernetes with Helm artifacts in 'test-monorepo'."
    )
    mock_create_repo.assert_not_called()


@patch.object(SystemGenerator, "_create_kustomize_structure")
def test_create_success_with_cloudflare_workers_runtime(mock_create_kustomize_structure, create_mocks):
    mock_log_success = create_mocks.log_success
    mock_init_basic_structure = create_mocks.init_basic_structure
    mock_write_template = create_mocks.write_template

    generator = SystemGenerator("edge-stack", False, {}, cloud="cloudflare", runtime="cloudflare-workers", workspace_tooling="bun-turbo")

    generator.create()

    dirs = mock_init_basic_structure.call_args.args[0]
    assert "infra/cloudflare/workers" in dirs
    assert _template_written(mock_write_template, "infra/cloudflare/workers/README.md", "cloudflare_workers_readme.md")
    assert _template_written(
        mock_write_template,
        "infra/cloudflare/workers/wrangler.example.toml",
        "cloudflare_workers_wrangler.toml",
    )
    mock_create_kustomize_structure.assert_not_called()
    mock_log_success.assert_called_once_with(
        "System 'edge-stack' scaffolded as a monorepo for Cloudflare Workers with Wrangler artifacts in 'edge-stack'."
    )


@patch.object(SystemGenerator, 'create_project')
def test_create_fails_when_create_project_fails(mock_create_project, monorepo_generator):
    mock_create_project.return_value = False

    with pytest.raises(ProjectCreationError, match="was not created"):
        monorepo_generator.create()

    mock_create_project.assert_called_once()


@patch.object(SystemGenerator, 'write_template')
@patch.object(SystemGenerator, 'create_directories')
def test_create_helm_structure(mock_create_directories, mock_write_template, monorepo_generator):
    monorepo_generator._create_helm_structure()
    
    mock_create_directories.assert_called_once_with(["infra/helm/example-service/templates"])
    
    expected_helm_calls = [
        call("infra/helm/example-service/Chart.yaml", "helm/Chart.yaml"),
        call("infra/helm/example-service/values.yaml", "helm/values.yaml"),
        call("infra/helm/example-service/templates/deployment.yaml", "helm/deployment.yaml"),
        call("infra/helm/example-service/templates/service.yaml", "helm/service.yaml"),
        call("infra/helm/example-service/templates/configmap.yaml", "helm/configmap.yaml"),
        call("infra/helm/example-service/templates/_helpers.tpl", "helm/_helpers.tpl"),
    ]

    for expected_call in expected_helm_calls:
        assert _template_written(mock_write_template, *expected_call.args)


@patch.object(SystemGenerator, 'write_template')
@patch.object(SystemGenerator, 'create_directories')
def test_create_kustomize_structure(mock_create_directories, mock_write_template, monorepo_generator):
    monorepo_generator._create_kustomize_structure()
    
    expected_directories = [
        "infra/k8s/base",
        "infra/k8s/overlays/dev",
        "infra/k8s/overlays/staging", 
        "infra/k8s/overlays/prod"
    ]
    mock_create_directories.assert_called_once_with(expected_directories)
    
    expected_kustomize_calls = [
        call("infra/k8s/base/kustomization.yaml", "kustomize/kustomization.yaml"),
        call("infra/k8s/base/deployment.yaml", "kustomize/deployment.yaml"),
        call("infra/k8s/base/service.yaml", "kustomize/service.yaml"),
        call("infra/k8s/base/configmap.yaml", "kustomize/configmap.yaml"),
        call("infra/k8s/base/secret.yaml", "kustomize/secret.yaml"),
        call("infra/k8s/base/hpa.yaml", "kustomize/hpa.yaml"),
        call("infra/k8s/base/networkpolicy.yaml", "kustomize/networkpolicy.yaml"),
        call("infra/k8s/overlays/dev/kustomization.yaml", "kustomize/overlay-kustomization.yaml"),
    ]

    for expected_call in expected_kustomize_calls:
        assert _template_written(mock_write_template, *expected_call.args)


def test_terraform_environments_coverage(create_mocks):
    """Test that all expected environments are covered in terraform file generation."""
    expected_envs = ["dev", "staging", "prod"]

    with patch.object(SystemGenerator, "_create_kustomize_structure"):
        mock_write_template = create_mocks.write_template
        generator = SystemGenerator("test", False, {}, workspace_tooling="bun-turbo")
        generator.create()

        # Check that terraform files are created for each environment
        terraform_calls = [
            call
            for call in mock_write_template.call_args_list
            if any(f"infra/terraform/env/{env}" in str(call) for env in expected_envs)
        ]

        # Should have 3 files per environment (main.tf, variables.tf, tfvars example)
        assert len(terraform_calls) == len(expected_envs) * 3

        # Check specific calls exist
        for env in expected_envs:
            main_tf_call = call(f"infra/terraform/env/{env}/main.tf", "terraform_env_main.tf")
            variables_tf_call = call(f"infra/terraform/env/{env}/variables.tf", "variables.tf")
            tfvars_call = call(f"infra/terraform/env/{env}/terraform.tfvars.example", "terraform.tfvars.example")
            assert _template_written(mock_write_template, *main_tf_call.args)
            assert _template_written(mock_write_template, *variables_tf_call.args)
            assert _template_written(mock_write_template, *tfvars_call.args)


def test_monorepo_name_passed_to_templates(create_mocks):
    """Test that monorepo name is correctly passed to Makefile and README templates."""
    with patch.object(SystemGenerator, "_create_kustomize_structure"):
        mock_write_template = create_mocks.write_template
        generator = SystemGenerator("my-awesome-repo", False, {}, workspace_tooling="bun-turbo")
        generator.create()

        # Check that monorepo name is passed to templates
        makefile_call = next(
            template_call
            for template_call in mock_write_template.call_args_list
            if template_call.args[:2] == ("Makefile", "Makefile.tpl")
        )
        readme_call = next(
            template_call
            for template_call in mock_write_template.call_args_list
            if template_call.args[:2] == ("README.md", "README.md.tpl")
        )

        assert makefile_call.kwargs["monorepo_name"] == "my-awesome-repo"
        assert makefile_call.kwargs["system_name"] == "my-awesome-repo"
        assert makefile_call.kwargs["workspace_tooling"] == "bun-turbo"
        assert readme_call.kwargs["monorepo_name"] == "my-awesome-repo"
        assert readme_call.kwargs["system_name"] == "my-awesome-repo"
