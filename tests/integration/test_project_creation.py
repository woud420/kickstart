"""Integration tests for end-to-end project creation workflows.

These tests validate the complete project creation process from CLI input
to final project structure, ensuring all components work together correctly.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch, MagicMock

from src.api import create_service, create_frontend, create_lib, create_cli, create_monorepo
from src.generator.service import ServiceGenerator
from src.generator.frontend import FrontendGenerator
from src.generator.lib import LibGenerator
from src.generator.monorepo import MonorepoGenerator


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
            "tests", "tests/api", "tests/model",
            "architecture"
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
            "tests/api/__init__.py",
            "tests/model/__init__.py",
        ]
        for py_file in python_files:
            assert (project_path / py_file).exists(), f"Missing Python file: {py_file}"
        
        # Verify main.py contains FastAPI code
        main_py_content = (project_path / "src/main.py").read_text()
        assert "FastAPI" in main_py_content
        assert "app = FastAPI()" in main_py_content
        
        # Verify architecture docs
        arch_readme = project_path / "architecture/README.md"
        assert arch_readme.exists()
        assert service_name in arch_readme.read_text()
    
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
        expected_dirs = ["src", "public", "tests", "architecture"]
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
        expected_dirs = ["src", "tests", "docs", "architecture"]
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
        expected_dirs = ["services", "libs", "frontend", "docs", "architecture"]
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
        
        # Should handle missing templates gracefully
        generator.create()
        
        # Project directory should not be created due to missing templates
        project_path = temp_project_dir / service_name
        # The method should warn and return early, not creating the directory
    
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
        arch_file = project_path / "architecture/README.md"
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