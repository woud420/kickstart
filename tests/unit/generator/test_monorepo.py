import pytest
from pathlib import Path
from unittest.mock import patch, call
from src.generator.monorepo import MonorepoGenerator


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
    assert monorepo_generator.config == {"key": "value"}
    assert monorepo_generator.template_dir.name == "monorepo"


def test_monorepo_generator_initialization_with_helm(monorepo_generator_with_helm):
    assert monorepo_generator_with_helm.helm is True


def test_monorepo_generator_initialization_with_gh(monorepo_generator_with_gh):
    assert monorepo_generator_with_gh.gh is True


def test_monorepo_generator_initialization_with_root(monorepo_generator_with_root):
    assert monorepo_generator_with_root.project == Path("/tmp/test-monorepo")


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
    mock_init_basic_structure.assert_called_once_with([
        "infra/docker",
        "infra/terraform/modules/example_module",
        "infra/terraform/env/dev",
        "infra/terraform/env/staging", 
        "infra/terraform/env/prod",
        ".github/workflows",
        "architecture"
    ])
    
    mock_create_kustomize_structure.assert_called_once()
    
    # Verify Docker template
    expected_docker_call = call("infra/docker/docker-compose.yml", "docker-compose.yml")
    
    # Verify Terraform environment templates
    expected_terraform_calls = [
        call("infra/terraform/env/dev/main.tf", "terraform_env_main.tf"),
        call("infra/terraform/env/dev/variables.tf", "variables.tf"),
        call("infra/terraform/env/staging/main.tf", "terraform_env_main.tf"),
        call("infra/terraform/env/staging/variables.tf", "variables.tf"),
        call("infra/terraform/env/prod/main.tf", "terraform_env_main.tf"),
        call("infra/terraform/env/prod/variables.tf", "variables.tf")
    ]
    
    # Verify GitHub workflow templates
    expected_workflow_calls = [
        call(".github/workflows/build.yml", "build.yml"),
        call(".github/workflows/test.yml", "test.yml"),
        call(".github/workflows/deploy.yml", "deploy.yml")
    ]
    
    # Verify documentation templates
    expected_doc_calls = [
        call("Makefile", "Makefile.tpl", monorepo_name="test-monorepo"),
        call("README.md", "README.md.tpl", monorepo_name="test-monorepo")
    ]
    
    all_expected_calls = [expected_docker_call] + expected_terraform_calls + expected_workflow_calls + expected_doc_calls
    mock_write_template.assert_has_calls(all_expected_calls, any_order=True)
    
    mock_create_architecture_docs.assert_called_once_with("test-monorepo Deployment Infra Docs")
    mock_log_success.assert_called_once_with("Monorepo 'test-monorepo' scaffolded with Kustomize support in 'test-monorepo'.")
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
    mock_log_success.assert_called_once_with("Monorepo 'test-monorepo' scaffolded with Helm support in 'test-monorepo'.")
    mock_create_repo.assert_not_called()


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
        call("infra/helm/example-service/templates/deployment.yaml", "helm/deployment.yaml")
    ]
    
    mock_write_template.assert_has_calls(expected_helm_calls, any_order=True)


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
        call("infra/k8s/base/service.yaml", "kustomize/service.yaml")
    ]
    
    mock_write_template.assert_has_calls(expected_kustomize_calls, any_order=True)


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
        
        # Should have 2 files per environment (main.tf and variables.tf)
        assert len(terraform_calls) == len(expected_envs) * 2
        
        # Check specific calls exist
        for env in expected_envs:
            main_tf_call = call(f"infra/terraform/env/{env}/main.tf", "terraform_env_main.tf")
            variables_tf_call = call(f"infra/terraform/env/{env}/variables.tf", "variables.tf")
            assert main_tf_call in mock_write_template.call_args_list
            assert variables_tf_call in mock_write_template.call_args_list


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
            workflow_call = call(f".github/workflows/{workflow}", workflow)
            assert workflow_call in mock_write_template.call_args_list


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
        makefile_call = call("Makefile", "Makefile.tpl", monorepo_name="my-awesome-repo")
        readme_call = call("README.md", "README.md.tpl", monorepo_name="my-awesome-repo")
        
        assert makefile_call in mock_write_template.call_args_list
        assert readme_call in mock_write_template.call_args_list


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
        
        expected_dirs = [
            "infra/docker",
            "infra/terraform/modules/example_module",
            "infra/terraform/env/dev",
            "infra/terraform/env/staging",
            "infra/terraform/env/prod",
            ".github/workflows",
            "architecture"
        ]
        
        mock_init_structure.assert_called_once_with(expected_dirs)