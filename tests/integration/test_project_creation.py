"""Integration tests for end-to-end project creation workflows.

These tests validate the complete project creation process from CLI input
to final project structure, ensuring all components work together correctly.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

from src.api import create_service, create_frontend, create_lib, create_cli, create_monorepo
from src.generator.service import ServiceGenerator
from src.generator.frontend import FrontendGenerator
from src.generator.lib import LibGenerator
from src.generator.monorepo import MonorepoGenerator
from src.utils.error_handling import LanguageNotSupportedError


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for test projects."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture  
def mock_config():
    """Mock configuration for testing."""
    return {
        "default_language": "python",
        "github_username": "testuser",
        "github_token": "fake_token"
    }


class TestServiceCreation:
    """Test end-to-end service creation workflows."""
    
    def test_python_service_creation_complete_workflow(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test complete Python service creation workflow.
        
        Validates:
        - Directory structure creation
        - Template file generation
        - Language-specific files
        - Error handling for edge cases
        """
        service_name = "test-python-service"
        
        # Mock GitHub repo creation to avoid external API calls
        with patch('src.utils.github.create_repo') as mock_github:
            mock_github.return_value = True
            
            # Create service
            generator = ServiceGenerator(
                name=service_name,
                lang="python", 
                gh=True,
                config=mock_config,
                helm=False,
                root=str(temp_project_dir)
            )
            generator.create()
        
        project_path = temp_project_dir / service_name
        
        # Verify project directory exists
        assert project_path.exists()
        assert project_path.is_dir()
        
        # Verify directory structure
        expected_dirs = [
            "src", "src/api", "src/model",
            "tests", "tests/unit/api", "tests/unit/model",
            "docs/architecture",
            "docs/contracts",
            "docs/operations",
            "docs/decisions",
            ".kickstart",
        ]
        for expected_dir in expected_dirs:
            assert (project_path / expected_dir).exists(), f"Missing directory: {expected_dir}"
        
        # Verify Python-specific files
        python_files = [
            "src/__init__.py",
            "src/api/__init__.py", 
            "src/model/__init__.py",
            "src/main.py",
            "tests/__init__.py",
            "tests/unit/api/__init__.py",
            "tests/unit/model/__init__.py",
        ]
        for py_file in python_files:
            assert (project_path / py_file).exists(), f"Missing Python file: {py_file}"
        
        # Verify main.py contains FastAPI code
        main_py_content = (project_path / "src/main.py").read_text()
        assert "FastAPI" in main_py_content
        assert "app = create_app()" in main_py_content
        
        # Verify architecture docs
        arch_readme = project_path / "docs/architecture/README.md"
        assert arch_readme.exists()
        assert service_name in arch_readme.read_text()
        assert (project_path / "AGENTS.md").exists()
        assert (project_path / ".kickstart/scaffold.json").exists()
        manifest = json.loads((project_path / ".kickstart/scaffold.json").read_text())
        assert manifest["project"] == {
            "name": service_name,
            "kind": "service",
            "repo_layout": "single-project",
        }
        assert manifest["execution"] == {"models": ["container"], "platforms": ["local"]}
        assert manifest["artifacts"] == {"image": "dockerfile"}
        assert manifest["capabilities"] == {}

    def test_python_service_extension_manifest(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test Python service extensions are recorded in the scaffold manifest."""
        service_name = "test-python-service-extensions"

        generator = ServiceGenerator(
            name=service_name,
            lang="python",
            gh=False,
            config=mock_config,
            root=str(temp_project_dir),
            database="postgres",
            cache="redis",
            auth="jwt",
        )
        generator.create()

        project_path = temp_project_dir / service_name
        manifest = json.loads((project_path / ".kickstart/scaffold.json").read_text())

        assert manifest["capabilities"] == {
            "service_extensions": {
                "auth": "jwt",
                "cache": "redis",
                "database": "postgres",
            }
        }
        assert (project_path / "src/clients/database.py").exists()
        assert (project_path / "src/clients/cache.py").exists()
        assert (project_path / "src/handler/auth.py").exists()
    
    def test_rust_service_creation_with_helm(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test Rust service creation with Helm charts."""
        service_name = "test-rust-service"
        
        with patch('src.utils.github.create_repo'):
            generator = ServiceGenerator(
                name=service_name,
                lang="rust",
                gh=False,
                config=mock_config, 
                helm=True,
                root=str(temp_project_dir)
            )
            generator.create()
        
        project_path = temp_project_dir / service_name
        
        # Verify Rust-specific files
        rust_files = [
            "src/main.rs",
            "src/api/mod.rs",
            "src/model/mod.rs"
        ]
        for rust_file in rust_files:
            assert (project_path / rust_file).exists(), f"Missing Rust file: {rust_file}"
        
        # Verify main.rs contains Actix-web code
        main_rs_content = (project_path / "src/main.rs").read_text()
        assert "actix_web" in main_rs_content
        assert "HttpServer::new" in main_rs_content
        
        # Verify Helm chart structure
        helm_path = project_path / "helm" / service_name
        assert helm_path.exists()
        assert (helm_path / "Chart.yaml").exists()
        assert (helm_path / "values.yaml").exists()
        assert (helm_path / "templates/deployment.yaml").exists()
        assert (helm_path / "templates/service.yaml").exists()
        assert (helm_path / "templates/configmap.yaml").exists()
        assert (helm_path / "templates/_helpers.tpl").exists()

        deployment_yaml = (helm_path / "templates/deployment.yaml").read_text()
        assert 'name: {{ include "example-service.fullname" . }}' in deployment_yaml
        assert "}}  labels" not in deployment_yaml
        assert "}}spec" not in deployment_yaml
        manifest = json.loads((project_path / ".kickstart/scaffold.json").read_text())
        assert manifest["execution"] == {"models": ["container"], "platforms": ["kubernetes"]}
        assert manifest["artifacts"] == {"image": "dockerfile", "kubernetes": "helm"}

    def test_rust_service_redis_cache_extension(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test Rust service generation with Redis cache support."""
        service_name = "test-rust-redis-service"

        generator = ServiceGenerator(
            name=service_name,
            lang="rust",
            gh=False,
            config=mock_config,
            root=str(temp_project_dir),
            cache="redis",
        )
        generator.create()

        project_path = temp_project_dir / service_name
        manifest = json.loads((project_path / ".kickstart/scaffold.json").read_text())

        assert manifest["capabilities"] == {"service_extensions": {"cache": "redis"}}
        assert (project_path / "src/clients/mod.rs").read_text() == "pub mod cache;\n"
        assert (project_path / "src/clients/cache.rs").exists()
        assert "mod clients;" in (project_path / "src/main.rs").read_text()
        assert "redis = " in (project_path / "Cargo.toml").read_text()
        assert "REDIS_URL=redis://127.0.0.1:6379/0" in (project_path / ".env.example").read_text()

    def test_rust_service_jwt_auth_extension(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test Rust service generation with JWT auth support."""
        service_name = "test-rust-jwt-service"

        generator = ServiceGenerator(
            name=service_name,
            lang="rust",
            gh=False,
            config=mock_config,
            root=str(temp_project_dir),
            auth="jwt",
        )
        generator.create()

        project_path = temp_project_dir / service_name
        manifest = json.loads((project_path / ".kickstart/scaffold.json").read_text())

        assert manifest["capabilities"] == {"service_extensions": {"auth": "jwt"}}
        assert (project_path / "src/handler/mod.rs").read_text() == "pub mod auth;\n"
        assert (project_path / "src/handler/auth.rs").exists()
        assert "mod handler;" in (project_path / "src/main.rs").read_text()
        assert "jsonwebtoken = " in (project_path / "Cargo.toml").read_text()
        assert "JWT_SECRET=change-me-change-me" in (project_path / ".env.example").read_text()

    def test_typescript_service_postgres_database_extension(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test TypeScript service generation with Postgres database support."""
        service_name = "test-typescript-postgres-service"

        generator = ServiceGenerator(
            name=service_name,
            lang="typescript",
            gh=False,
            config=mock_config,
            root=str(temp_project_dir),
            database="postgres",
        )
        generator.create()

        project_path = temp_project_dir / service_name
        manifest = json.loads((project_path / ".kickstart/scaffold.json").read_text())

        assert manifest["capabilities"] == {"service_extensions": {"database": "postgres"}}
        assert (project_path / "src/clients/database.ts").exists()
        assert (project_path / "migrations/001_initial.sql").exists()
        assert '"pg": "^8.13.1"' in (project_path / "package.json").read_text()
        assert "DATABASE_URL: z.string().url()" in (project_path / "src/config/env.ts").read_text()
        assert "DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/postgres" in (
            project_path / ".env.example"
        ).read_text()

    def test_typescript_cloudflare_worker_creation(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test TypeScript Cloudflare Worker service creation."""
        service_name = "test-worker-service"

        generator = ServiceGenerator(
            name=service_name,
            lang="typescript",
            gh=False,
            config=mock_config,
            runtime="cloudflare-workers",
            root=str(temp_project_dir),
        )
        generator.create()

        project_path = temp_project_dir / service_name

        assert (project_path / "wrangler.toml").exists()
        assert (project_path / "package.json").exists()
        assert (project_path / "src/index.ts").exists()
        assert (project_path / "tests/worker.test.ts").exists()
        assert not (project_path / "Dockerfile").exists()
        manifest = json.loads((project_path / ".kickstart/scaffold.json").read_text())
        assert manifest["project"]["kind"] == "worker"
        assert manifest["execution"] == {
            "models": ["cloudflare-worker"],
            "platforms": ["cloudflare-workers"],
        }
        assert manifest["artifacts"] == {"worker": "wrangler"}
        assert manifest["provider"] == {"targets": ["cloudflare"]}

        worker_source = (project_path / "src/index.ts").read_text()
        assert "ExportedHandler" in worker_source
        assert "/healthz" in worker_source

    def test_rust_cloudflare_worker_creation(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test Rust Cloudflare Worker service creation."""
        service_name = "test-rust-worker"

        generator = ServiceGenerator(
            name=service_name,
            lang="rust",
            gh=False,
            config=mock_config,
            runtime="cloudflare-workers",
            root=str(temp_project_dir),
        )
        generator.create()

        project_path = temp_project_dir / service_name

        assert (project_path / "wrangler.toml").exists()
        assert (project_path / "Cargo.toml").exists()
        assert (project_path / "src/lib.rs").exists()
        assert not (project_path / "Dockerfile").exists()

        cargo_toml = (project_path / "Cargo.toml").read_text()
        assert 'crate-type = ["cdylib"]' in cargo_toml
        assert 'worker = "0.8"' in cargo_toml
    
    def test_service_creation_error_handling(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test error handling during service creation."""
        service_name = "test-service-errors"
        
        # Test creating service in existing directory
        existing_dir = temp_project_dir / service_name
        existing_dir.mkdir()
        
        generator = ServiceGenerator(
            name=service_name,
            lang="python",
            gh=False,
            config=mock_config,
            root=str(temp_project_dir)
        )
        
        # Should not overwrite existing directory
        generator.create()
        
        # Verify it doesn't overwrite (no src directory should be created)
        assert not (existing_dir / "src").exists()


class TestFrontendCreation:
    """Test end-to-end frontend creation workflows."""
    
    def test_react_frontend_creation(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test React frontend project creation."""
        frontend_name = "test-react-app"
        
        with patch('src.utils.github.create_repo'):
            generator = FrontendGenerator(
                name=frontend_name,
                gh=False,
                config=mock_config,
                root=str(temp_project_dir)
            )
            generator.create()
        
        project_path = temp_project_dir / frontend_name
        
        # Verify frontend directory structure
        assert project_path.exists()
        expected_dirs = [
            "src",
            "public",
            "tests",
            "docs/architecture",
            "docs/contracts",
            "docs/operations",
            "docs/decisions",
            ".kickstart",
        ]
        for expected_dir in expected_dirs:
            assert (project_path / expected_dir).exists()


class TestLibraryCreation:
    """Test end-to-end library creation workflows."""
    
    def test_python_library_creation(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test Python library project creation."""
        lib_name = "test-python-lib"
        
        with patch('src.utils.github.create_repo'):
            generator = LibGenerator(
                name=lib_name,
                lang="python",
                gh=False,
                config=mock_config,
                root=str(temp_project_dir)
            )
            generator.create()
        
        project_path = temp_project_dir / lib_name
        
        # Verify library structure
        assert project_path.exists()
        expected_dirs = [
            "src",
            "tests",
            "docs/architecture",
            "docs/contracts",
            "docs/operations",
            "docs/decisions",
            ".kickstart",
        ]
        for expected_dir in expected_dirs:
            assert (project_path / expected_dir).exists()


class TestMonorepoCreation:
    """Test end-to-end monorepo creation workflows."""
    
    def test_monorepo_creation_with_helm(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test monorepo creation with Helm support."""
        mono_name = "test-monorepo"
        
        with patch('src.utils.github.create_repo'):
            generator = MonorepoGenerator(
                name=mono_name,
                gh=False,
                config=mock_config,
                helm=True,
                root=str(temp_project_dir)
            )
            generator.create()
        
        project_path = temp_project_dir / mono_name
        
        # Verify monorepo structure
        assert project_path.exists()
        expected_dirs = [
            "services",
            "libs",
            "frontend",
            "docs/architecture",
            "docs/contracts",
            "docs/operations",
            "docs/decisions",
            ".kickstart",
            "infra",
        ]
        for expected_dir in expected_dirs:
            assert (project_path / expected_dir).exists()


class TestAPIFunctions:
    """Test the high-level API functions used by CLI."""
    
    def test_create_service_api(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test the create_service API function."""
        service_name = "api-test-service"
        
        with patch('src.utils.github.create_repo'):
            create_service(
                name=service_name,
                lang="python",
                gh=False,
                config=mock_config,
                helm=False,
                root=str(temp_project_dir)
            )
        
        project_path = temp_project_dir / service_name
        assert project_path.exists()
        assert (project_path / "src").exists()
    
    def test_create_frontend_api(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test the create_frontend API function."""
        frontend_name = "api-test-frontend"
        
        with patch('src.utils.github.create_repo'):
            create_frontend(
                name=frontend_name,
                gh=False,
                config=mock_config,
                root=str(temp_project_dir)
            )
        
        project_path = temp_project_dir / frontend_name
        assert project_path.exists()
        assert (project_path / "src").exists()
    
    def test_create_lib_api(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test the create_lib API function."""
        lib_name = "api-test-lib"
        
        with patch('src.utils.github.create_repo'):
            create_lib(
                name=lib_name,
                lang="python",
                gh=False,
                config=mock_config,
                root=str(temp_project_dir)
            )
        
        project_path = temp_project_dir / lib_name
        assert project_path.exists()
        assert (project_path / "src").exists()
    
    def test_create_cli_api(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test the create_cli API function."""
        cli_name = "api-test-cli"
        
        with patch('src.utils.github.create_repo'):
            create_cli(
                name=cli_name,
                lang="python",
                gh=False,
                config=mock_config,
                root=str(temp_project_dir)
            )
        
        project_path = temp_project_dir / cli_name
        assert project_path.exists()
        assert (project_path / "src").exists()
    
    def test_create_monorepo_api(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test the create_monorepo API function."""
        mono_name = "api-test-monorepo"
        
        with patch('src.utils.github.create_repo'):
            create_monorepo(
                name=mono_name,
                gh=False,
                config=mock_config,
                helm=False,
                root=str(temp_project_dir)
            )
        
        project_path = temp_project_dir / mono_name
        assert project_path.exists()
        assert (project_path / "services").exists()
        assert (project_path / "infra/k8s/base/deployment.yaml").exists()

    def test_create_monorepo_api_with_cloudflare(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test that Cloudflare monorepos render Cloudflare Terraform only."""
        mono_name = "api-test-cloudflare-monorepo"

        with patch('src.utils.github.create_repo'):
            create_monorepo(
                name=mono_name,
                gh=False,
                config=mock_config,
                helm=False,
                root=str(temp_project_dir),
                cloud="cloudflare",
                knowledge="none",
            )

        project_path = temp_project_dir / mono_name
        main_tf = (project_path / "infra/terraform/env/dev/main.tf").read_text()
        variables_tf = (project_path / "infra/terraform/env/dev/variables.tf").read_text()
        tfvars = (project_path / "infra/terraform/env/dev/terraform.tfvars.example").read_text()

        assert 'source  = "cloudflare/cloudflare"' in main_tf
        assert 'provider "cloudflare"' in main_tf
        assert 'provider_targets = ["cloudflare"]' in tfvars
        assert "cloudflare_account_id" in variables_tf
        assert "aws_region" not in variables_tf
        assert "gcp_project_id" not in variables_tf

    def test_create_monorepo_api_with_cloudflare_workers_runtime(
        self, temp_project_dir: Path, mock_config: Dict[str, Any]
    ):
        """Test that Cloudflare Workers runtime renders Worker runtime docs."""
        mono_name = "api-test-worker-runtime-monorepo"

        create_monorepo(
            name=mono_name,
            gh=False,
            config=mock_config,
            helm=False,
            root=str(temp_project_dir),
            cloud="cloudflare",
            runtime="cloudflare-workers",
            knowledge="none",
        )

        project_path = temp_project_dir / mono_name

        assert (project_path / "infra/cloudflare/workers/README.md").exists()
        assert (project_path / "infra/cloudflare/workers/wrangler.example.toml").exists()
        assert not (project_path / "infra/k8s/base/deployment.yaml").exists()


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""
    
    def test_template_missing_graceful_failure(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test graceful handling when templates are missing."""
        service_name = "test-missing-templates"
        
        # Create generator with non-existent language
        generator = ServiceGenerator(
            name=service_name,
            lang="nonexistent-lang",
            gh=False,
            config=mock_config,
            root=str(temp_project_dir)
        )
        
        # Unsupported languages fail before creating files.
        with pytest.raises(LanguageNotSupportedError):
            generator.create()
        
        # The method should fail before creating the project directory.
    
    def test_permission_error_handling(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test handling of permission errors during file creation."""
        service_name = "test-permissions"
        
        # Create read-only directory
        readonly_dir = temp_project_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        try:
            generator = ServiceGenerator(
                name=service_name,
                lang="python",
                gh=False,
                config=mock_config,
                root=str(readonly_dir)
            )
            
            # Should handle permission errors gracefully
            generator.create()
            
            # Verify it doesn't crash the application
            assert True  # If we get here, no unhandled exception occurred
            
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)


class TestTemplateRendering:
    """Test template rendering and variable substitution."""
    
    def test_template_variable_substitution(self, temp_project_dir: Path, mock_config: Dict[str, Any]):
        """Test that template variables are correctly substituted."""
        service_name = "variable-test-service"
        
        with patch('src.utils.github.create_repo'):
            generator = ServiceGenerator(
                name=service_name,
                lang="python",
                gh=False,
                config=mock_config,
                root=str(temp_project_dir)
            )
            generator.create()
        
        project_path = temp_project_dir / service_name
        
        # Check that service name appears in architecture docs
        arch_file = project_path / "docs/architecture/README.md"
        if arch_file.exists():
            content = arch_file.read_text()
            assert service_name in content
    
    def test_jinja2_template_features(self, temp_project_dir: Path):
        """Test advanced Jinja2 template features work correctly."""
        from src.utils.fs import write_file
        
        # Test template with conditionals and loops
        template_content = """
Project: {{ name }}
{% if description %}
Description: {{ description }}
{% endif %}
Languages:
{% for lang in languages %}
- {{ lang }}
{% endfor %}
        """.strip()
        
        output_file = temp_project_dir / "jinja_test.txt"
        write_file(
            output_file, 
            template_content,
            name="TestProject",
            description="A test project",
            languages=["Python", "Rust", "Go"]
        )
        
        content = output_file.read_text()
        assert "Project: TestProject" in content
        assert "Description: A test project" in content
        assert "- Python" in content
        assert "- Rust" in content
        assert "- Go" in content
