import pytest
from pathlib import Path
from unittest.mock import patch, call
from src.generator.monorepo import MonorepoGenerator


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
        "architecture",
        "frontend",
        "libs",
        "services",
        "data/postgres",
        "knowledge",
        "docs/adr",
        "docs/agents",
        "docs/architecture",
        "docs/data",
        "docs/knowledge",
        "docs/runbooks",
        "reports",
        "scripts",
    ]


@pytest.fixture
def monorepo_generator():
    return MonorepoGenerator("test-monorepo", False, {"key": "value"})


@pytest.fixture
def monorepo_generator_with_helm():
    return MonorepoGenerator("test-monorepo", False, {"key": "value"}, helm=True)


@pytest.fixture
def monorepo_generator_with_gh():
    return MonorepoGenerator("test-monorepo", True, {"key": "value"})


@pytest.fixture
def monorepo_generator_with_root():
    return MonorepoGenerator("test-monorepo", False, {"key": "value"}, root="/tmp")


def test_monorepo_generator_initialization(monorepo_generator):
    assert monorepo_generator.name == "test-monorepo"
    assert monorepo_generator.helm is False
    assert monorepo_generator.gh is False
    assert monorepo_generator.cloud == "multi"
    assert monorepo_generator.knowledge == "both"
    assert monorepo_generator.runtime == "kubernetes"
    assert monorepo_generator.config == {"key": "value"}
    assert monorepo_generator.template_dir.name == "monorepo"


def test_monorepo_generator_initialization_with_helm(monorepo_generator_with_helm):
    assert monorepo_generator_with_helm.helm is True


def test_monorepo_generator_initialization_with_gh(monorepo_generator_with_gh):
    assert monorepo_generator_with_gh.gh is True


def test_monorepo_generator_initialization_with_root(monorepo_generator_with_root):
    assert monorepo_generator_with_root.project == Path("/tmp/test-monorepo")


def test_monorepo_cloud_selection():
    generator = MonorepoGenerator("test", False, {}, cloud="gcp", knowledge="obsidian")

    assert generator._clouds() == ["gcp"]
    assert generator._include_obsidian() is True
    assert generator._include_backstage() is False


def test_monorepo_multi_cloud_includes_cloudflare():
    generator = MonorepoGenerator("test", False, {}, cloud="multi")

    assert generator._clouds() == ["aws", "gcp", "cloudflare"]
    assert generator._template_vars()["include_cloudflare"] is True
    assert generator._template_vars()["cloud_label"] == "AWS, GCP, CLOUDFLARE"


def test_monorepo_cloudflare_only_selection():
    generator = MonorepoGenerator("test", False, {}, cloud="cloudflare")

    assert generator._clouds() == ["cloudflare"]
    assert generator._template_vars()["include_aws"] is False
    assert generator._template_vars()["include_gcp"] is False
    assert generator._template_vars()["include_cloudflare"] is True


def test_monorepo_cloudflare_workers_runtime_selection():
    generator = MonorepoGenerator("test", False, {}, cloud="cloudflare", runtime="cloudflare-workers")

    assert generator._uses_kubernetes() is False
    assert generator._uses_cloudflare_workers() is True
    assert generator._template_vars()["runtime_label"] == "Cloudflare Workers"


def test_monorepo_hybrid_runtime_selection():
    generator = MonorepoGenerator("test", False, {}, runtime="hybrid")

    assert generator._uses_kubernetes() is True
    assert generator._uses_cloudflare_workers() is True


def test_monorepo_rejects_invalid_profile_options():
    with pytest.raises(ValueError):
        MonorepoGenerator("test", False, {}, cloud="azure").create()

    with pytest.raises(ValueError):
        MonorepoGenerator("test", False, {}, knowledge="wiki").create()

    with pytest.raises(ValueError):
        MonorepoGenerator("test", False, {}, runtime="lambda").create()


@patch('src.generator.monorepo.create_repo')
@patch.object(MonorepoGenerator, '_create_kustomize_structure')
@patch.object(MonorepoGenerator, 'write_template')
@patch.object(MonorepoGenerator, 'create_architecture_docs')
@patch.object(MonorepoGenerator, 'init_basic_structure')
@patch.object(MonorepoGenerator, 'create_project')
@patch.object(MonorepoGenerator, 'log_success')
def test_create_success_with_kustomize_and_gh(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_create_architecture_docs, mock_write_template, 
    mock_create_kustomize_structure, mock_create_repo
):
    generator = MonorepoGenerator("test-monorepo", True, {"key": "value"})
    mock_create_project.return_value = True

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
        ("docs/adr/0001-stack-profile.md", "adr_stack_profile.md"),
        ("docs/agents/recommended-agents.md", "agents_recommended.md"),
        ("knowledge/README.md", "knowledge_root_readme.md"),
        ("package.json", "package.json.tpl"),
        ("turbo.json", "turbo.json.tpl"),
        ("bunfig.toml", "bunfig.toml.tpl"),
        ("config/tsconfig/base.json", "tsconfig_base.json.tpl"),
        ("catalog-info.yaml", "catalog-info.yaml"),
    ]

    for target, template in expected_templates:
        assert _template_written(mock_write_template, target, template)
    
    mock_create_architecture_docs.assert_called_once_with("test-monorepo Deployment Infra Docs")
    mock_log_success.assert_called_once_with(
        "Monorepo 'test-monorepo' scaffolded for Kubernetes with Kustomize support in 'test-monorepo'."
    )
    mock_create_repo.assert_called_once_with("test-monorepo")


@patch('src.generator.monorepo.create_repo')
@patch.object(MonorepoGenerator, '_create_helm_structure')
@patch.object(MonorepoGenerator, 'write_template')
@patch.object(MonorepoGenerator, 'create_architecture_docs')
@patch.object(MonorepoGenerator, 'init_basic_structure')
@patch.object(MonorepoGenerator, 'create_project')
@patch.object(MonorepoGenerator, 'log_success')
def test_create_success_with_helm(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_create_architecture_docs, mock_write_template, 
    mock_create_helm_structure, mock_create_repo
):
    generator = MonorepoGenerator("test-monorepo", False, {"key": "value"}, helm=True)
    mock_create_project.return_value = True

    generator.create()

    mock_create_helm_structure.assert_called_once()
    mock_log_success.assert_called_once_with(
        "Monorepo 'test-monorepo' scaffolded for Kubernetes with Helm support in 'test-monorepo'."
    )
    mock_create_repo.assert_not_called()


@patch.object(MonorepoGenerator, '_create_kustomize_structure')
@patch.object(MonorepoGenerator, 'write_template')
@patch.object(MonorepoGenerator, 'create_architecture_docs')
@patch.object(MonorepoGenerator, 'init_basic_structure')
@patch.object(MonorepoGenerator, 'create_project')
@patch.object(MonorepoGenerator, 'log_success')
def test_create_success_with_cloudflare_workers_runtime(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_create_architecture_docs, mock_write_template, mock_create_kustomize_structure
):
    generator = MonorepoGenerator("edge-stack", False, {}, cloud="cloudflare", runtime="cloudflare-workers")
    mock_create_project.return_value = True

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
        "Monorepo 'edge-stack' scaffolded for Cloudflare Workers with Wrangler support in 'edge-stack'."
    )


@patch.object(MonorepoGenerator, 'create_project')
def test_create_fails_when_create_project_fails(mock_create_project, monorepo_generator):
    mock_create_project.return_value = False
    
    monorepo_generator.create()
    
    mock_create_project.assert_called_once()


@patch.object(MonorepoGenerator, 'write_template')
@patch.object(MonorepoGenerator, 'create_directories')
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


@patch.object(MonorepoGenerator, 'write_template')
@patch.object(MonorepoGenerator, 'create_directories')
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


def test_terraform_environments_coverage():
    """Test that all expected environments are covered in terraform file generation."""
    expected_envs = ["dev", "staging", "prod"]
    
    with patch.object(MonorepoGenerator, 'create_project', return_value=True), \
         patch.object(MonorepoGenerator, 'init_basic_structure'), \
         patch.object(MonorepoGenerator, '_create_kustomize_structure'), \
         patch.object(MonorepoGenerator, 'create_architecture_docs'), \
         patch.object(MonorepoGenerator, 'log_success'), \
         patch.object(MonorepoGenerator, 'write_template') as mock_write_template:
        
        generator = MonorepoGenerator("test", False, {})
        generator.create()
        
        # Check that terraform files are created for each environment
        terraform_calls = [call for call in mock_write_template.call_args_list 
                          if any(f"infra/terraform/env/{env}" in str(call) for env in expected_envs)]
        
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


def test_github_workflows_coverage():
    """Test that all expected GitHub workflow files are created."""
    expected_workflows = ["build.yml", "test.yml", "deploy.yml"]
    
    with patch.object(MonorepoGenerator, 'create_project', return_value=True), \
         patch.object(MonorepoGenerator, 'init_basic_structure'), \
         patch.object(MonorepoGenerator, '_create_kustomize_structure'), \
         patch.object(MonorepoGenerator, 'create_architecture_docs'), \
         patch.object(MonorepoGenerator, 'log_success'), \
         patch.object(MonorepoGenerator, 'write_template') as mock_write_template:
        
        generator = MonorepoGenerator("test", False, {})
        generator.create()
        
        # Check that workflow files are created
        for workflow in expected_workflows:
            assert _template_written(mock_write_template, f".github/workflows/{workflow}", workflow)


def test_monorepo_name_passed_to_templates():
    """Test that monorepo name is correctly passed to Makefile and README templates."""
    with patch.object(MonorepoGenerator, 'create_project', return_value=True), \
         patch.object(MonorepoGenerator, 'init_basic_structure'), \
         patch.object(MonorepoGenerator, '_create_kustomize_structure'), \
         patch.object(MonorepoGenerator, 'create_architecture_docs'), \
         patch.object(MonorepoGenerator, 'log_success'), \
         patch.object(MonorepoGenerator, 'write_template') as mock_write_template:
        
        generator = MonorepoGenerator("my-awesome-repo", False, {})
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
        assert readme_call.kwargs["monorepo_name"] == "my-awesome-repo"


def test_basic_structure_includes_all_required_directories():
    """Test that init_basic_structure is called with all required directories."""
    with patch.object(MonorepoGenerator, 'create_project', return_value=True), \
         patch.object(MonorepoGenerator, '_create_kustomize_structure'), \
         patch.object(MonorepoGenerator, 'write_template'), \
         patch.object(MonorepoGenerator, 'create_architecture_docs'), \
         patch.object(MonorepoGenerator, 'log_success'), \
         patch.object(MonorepoGenerator, 'init_basic_structure') as mock_init_structure:
        
        generator = MonorepoGenerator("test", False, {})
        generator.create()
        
        mock_init_structure.assert_called_once_with(_expected_monorepo_dirs())
