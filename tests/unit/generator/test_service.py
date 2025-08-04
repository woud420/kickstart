import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from src.generator.service import ServiceGenerator


@pytest.fixture
def service_generator():
    return ServiceGenerator("test-service", "python", False, {"key": "value"})


@pytest.fixture
def service_generator_with_helm():
    return ServiceGenerator("test-service", "python", False, {"key": "value"}, helm=True)


@pytest.fixture
def service_generator_with_gh():
    return ServiceGenerator("test-service", "python", True, {"key": "value"})


@pytest.fixture
def service_generator_with_root():
    return ServiceGenerator("test-service", "python", False, {"key": "value"}, root="/tmp")


def test_service_generator_initialization(service_generator):
    assert service_generator.name == "test-service"
    assert service_generator.lang == "python"
    assert service_generator.gh is False
    assert service_generator.helm is False
    assert service_generator.config == {"key": "value"}
    assert service_generator.lang_template_dir == service_generator.template_dir / "python"


def test_service_generator_initialization_with_helm(service_generator_with_helm):
    assert service_generator_with_helm.helm is True


def test_service_generator_initialization_with_gh(service_generator_with_gh):
    assert service_generator_with_gh.gh is True


def test_service_generator_initialization_with_root(service_generator_with_root):
    assert service_generator_with_root.project == Path("/tmp/test-service")


@patch('src.generator.service.create_repo')
@patch.object(ServiceGenerator, '_create_helm_chart')
@patch.object(ServiceGenerator, '_create_python_structure')
@patch.object(ServiceGenerator, 'write_content')
@patch.object(ServiceGenerator, 'create_architecture_docs')
@patch.object(ServiceGenerator, 'write_template')
@patch.object(ServiceGenerator, 'init_basic_structure')
@patch.object(ServiceGenerator, 'create_project')
@patch.object(ServiceGenerator, 'log_success')
def test_create_success_python_with_helm_and_gh(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_write_template, mock_create_architecture_docs, mock_write_content,
    mock_create_python_structure, mock_create_helm_chart, mock_create_repo,
    tmp_path
):
    # Setup
    generator = ServiceGenerator("test-service", "python", True, {"key": "value"}, helm=True)
    mock_create_project.return_value = True
    generator.lang_template_dir = tmp_path / "python"
    generator.lang_template_dir.mkdir()

    # Execute
    generator.create()

    # Verify
    mock_create_project.assert_called_once()
    mock_init_basic_structure.assert_called_once_with([
        "src", "src/api", "src/model", "tests", "tests/api", "tests/model", "architecture"
    ])
    
    # Verify template files are written
    expected_template_calls = [
        call("README.md", "python/README.md.tpl"),
        call(".gitignore", "python/gitignore.tpl"),
        call("Dockerfile", "python/Dockerfile.tpl"),
        call("Makefile", "python/Makefile.tpl")
    ]
    mock_write_template.assert_has_calls(expected_template_calls)
    
    mock_create_architecture_docs.assert_called_once_with("test-service Architecture Notes")
    mock_write_content.assert_called_once_with(".env.example", "EXAMPLE_ENV_VAR=value\n")
    mock_create_python_structure.assert_called_once()
    mock_create_helm_chart.assert_called_once()
    mock_log_success.assert_called_once_with("Python service 'test-service' created successfully in 'test-service'!")
    mock_create_repo.assert_called_once_with("test-service")


@patch.object(ServiceGenerator, 'create_project')
def test_create_fails_when_create_project_fails(mock_create_project, service_generator):
    mock_create_project.return_value = False
    
    service_generator.create()
    
    mock_create_project.assert_called_once()


@patch('src.generator.service.warn')
@patch.object(ServiceGenerator, 'create_project')
def test_create_warns_when_language_template_missing(mock_create_project, mock_warn, tmp_path):
    generator = ServiceGenerator("test-service", "nonexistent", False, {})
    mock_create_project.return_value = True
    generator.lang_template_dir = tmp_path / "nonexistent"  # Directory doesn't exist
    
    generator.create()
    
    mock_warn.assert_called_once_with("No templates for language: nonexistent")


@patch.object(ServiceGenerator, 'write_content')
def test_create_python_structure(mock_write_content, service_generator):
    service_generator._create_python_structure()
    
    # Verify __init__.py files are created
    expected_init_calls = [
        call("src/__init__.py", ""),
        call("src/api/__init__.py", ""),
        call("src/model/__init__.py", ""),
        call("tests/__init__.py", ""),
        call("tests/api/__init__.py", ""),
        call("tests/model/__init__.py", "")
    ]
    
    # Verify main.py is created
    expected_main_content = "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'message': 'Hello World'}\n"
    expected_main_call = call("src/main.py", expected_main_content)
    
    mock_write_content.assert_has_calls(expected_init_calls + [expected_main_call], any_order=True)


@patch.object(ServiceGenerator, 'write_template')
def test_create_python_structure_writes_requirements(mock_write_template, service_generator):
    service_generator._create_python_structure()
    
    mock_write_template.assert_called_once_with("requirements.txt", "python/requirements.txt.tpl")


@patch.object(ServiceGenerator, 'write_content')
def test_create_rust_structure(mock_write_content, service_generator):
    generator = ServiceGenerator("test-service", "rust", False, {})
    generator._create_rust_structure()
    
    # Verify mod.rs files are created
    expected_mod_calls = [
        call("src/api/mod.rs", "// Module definitions\n"),
        call("src/model/mod.rs", "// Module definitions\n"),
        call("tests/api/mod.rs", "// Module definitions\n"),
        call("tests/model/mod.rs", "// Module definitions\n")
    ]
    
    # Verify main.rs is created
    expected_main_content = "use actix_web::{web, App, HttpResponse, HttpServer};\n\n#[actix_web::main]\nasync fn main() -> std::io::Result<()> {\n    HttpServer::new(|| {\n        App::new()\n            .route(\"/\", web::get().to(|| async { HttpResponse::Ok().json(\"Hello World\") }))\n    })\n    .bind(\"127.0.0.1:8080\")?\n    .run()\n    .await\n}\n"
    expected_main_call = call("src/main.rs", expected_main_content)
    
    mock_write_content.assert_has_calls(expected_mod_calls + [expected_main_call], any_order=True)


@patch.object(ServiceGenerator, 'write_template')
def test_create_rust_structure_writes_cargo_toml(mock_write_template, service_generator):
    generator = ServiceGenerator("test-service", "rust", False, {})
    generator._create_rust_structure()
    
    mock_write_template.assert_called_once_with("Cargo.toml", "rust/Cargo.toml.tpl")


@patch.object(ServiceGenerator, 'write_content')
def test_create_cpp_structure(mock_write_content, service_generator):
    generator = ServiceGenerator("test-service", "cpp", False, {})
    generator._create_cpp_structure()
    
    expected_calls = [
        call("src/api/routes.hpp", "#pragma once\n\nnamespace api {\n    class Routes {\n    public:\n        Routes() = default;\n    };\n}\n"),
        call("src/model/user.hpp", "#pragma once\n\nnamespace model {\n    // Add your models here\n}\n"),
        call("src/main.cpp", "#include <iostream>\n\nint main() {\n    std::cout << \"Hello World\" << std::endl;\n    return 0;\n}\n")
    ]
    
    mock_write_content.assert_has_calls(expected_calls, any_order=True)


@patch.object(ServiceGenerator, 'write_template')
def test_create_cpp_structure_writes_cmake(mock_write_template, service_generator):
    generator = ServiceGenerator("test-service", "cpp", False, {})
    generator._create_cpp_structure()
    
    mock_write_template.assert_called_once_with("CMakeLists.txt", "cpp/CMakeLists.txt.tpl")


@patch.object(ServiceGenerator, 'write_content')
def test_create_go_structure(mock_write_content, service_generator):
    generator = ServiceGenerator("test-service", "go", False, {})
    generator._create_go_structure()
    
    expected_go_main = """package main

import (
    "fmt"
    "net/http"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintln(w, `{"message": "Hello World"}`)
    })
    fmt.Println("Listening on :8080...")
    http.ListenAndServe(":8080", nil)
}
"""
    
    expected_calls = [
        call("src/api/.gitkeep", ""),
        call("src/model/.gitkeep", ""),
        call("tests/api/.gitkeep", ""),
        call("tests/model/.gitkeep", ""),
        call("src/main.go", expected_go_main)
    ]
    
    mock_write_content.assert_has_calls(expected_calls, any_order=True)


@patch.object(ServiceGenerator, 'write_template')
def test_create_go_structure_writes_go_mod(mock_write_template, service_generator):
    generator = ServiceGenerator("test-service", "go", False, {})
    generator._create_go_structure()
    
    mock_write_template.assert_called_once_with("go.mod", "go/go.mod.tpl")


@patch('src.generator.service.success')
@patch.object(ServiceGenerator, 'write_template')
@patch.object(ServiceGenerator, 'create_directories')
def test_create_helm_chart(mock_create_directories, mock_write_template, mock_success, tmp_path):
    generator = ServiceGenerator("test-service", "python", False, {})
    generator.project = tmp_path
    
    generator._create_helm_chart()
    
    # Verify helm directory structure is created
    expected_helm_path = tmp_path / "helm" / "test-service" / "templates"
    mock_create_directories.assert_called_once_with([str(expected_helm_path)])
    
    # Verify helm template files are written
    expected_template_calls = [
        call("helm/test-service/Chart.yaml", "monorepo/helm/Chart.yaml"),
        call("helm/test-service/values.yaml", "monorepo/helm/values.yaml"),
        call("helm/test-service/templates/deployment.yaml", "monorepo/helm/deployment.yaml")
    ]
    mock_write_template.assert_has_calls(expected_template_calls, any_order=True)
    
    mock_success.assert_called_once_with("Helm chart scaffolded")


@patch('src.generator.service.create_repo')
@patch.object(ServiceGenerator, '_create_rust_structure')
@patch.object(ServiceGenerator, 'write_content')
@patch.object(ServiceGenerator, 'create_architecture_docs')
@patch.object(ServiceGenerator, 'write_template')
@patch.object(ServiceGenerator, 'init_basic_structure')
@patch.object(ServiceGenerator, 'create_project')
@patch.object(ServiceGenerator, 'log_success')
def test_create_with_different_languages(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_write_template, mock_create_architecture_docs, mock_write_content,
    mock_create_rust_structure, mock_create_repo, tmp_path
):
    # Test rust language selection
    generator = ServiceGenerator("test-service", "rust", False, {})
    mock_create_project.return_value = True
    generator.lang_template_dir = tmp_path / "rust"
    generator.lang_template_dir.mkdir()

    generator.create()

    mock_create_rust_structure.assert_called_once()
    mock_log_success.assert_called_once_with("Rust service 'test-service' created successfully in 'test-service'!")


@patch.object(ServiceGenerator, '_create_cpp_structure')
@patch.object(ServiceGenerator, 'write_content')
@patch.object(ServiceGenerator, 'create_architecture_docs')
@patch.object(ServiceGenerator, 'write_template')
@patch.object(ServiceGenerator, 'init_basic_structure')
@patch.object(ServiceGenerator, 'create_project')
@patch.object(ServiceGenerator, 'log_success')
def test_create_cpp_language_selection(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_write_template, mock_create_architecture_docs, mock_write_content,
    mock_create_cpp_structure, tmp_path
):
    generator = ServiceGenerator("test-service", "cpp", False, {})
    mock_create_project.return_value = True
    generator.lang_template_dir = tmp_path / "cpp"
    generator.lang_template_dir.mkdir()

    generator.create()

    mock_create_cpp_structure.assert_called_once()
    mock_log_success.assert_called_once_with("Cpp service 'test-service' created successfully in 'test-service'!")


@patch.object(ServiceGenerator, '_create_go_structure')
@patch.object(ServiceGenerator, 'write_content')
@patch.object(ServiceGenerator, 'create_architecture_docs')
@patch.object(ServiceGenerator, 'write_template')
@patch.object(ServiceGenerator, 'init_basic_structure')
@patch.object(ServiceGenerator, 'create_project')
@patch.object(ServiceGenerator, 'log_success')
def test_create_go_language_selection(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_write_template, mock_create_architecture_docs, mock_write_content,
    mock_create_go_structure, tmp_path
):
    generator = ServiceGenerator("test-service", "go", False, {})
    mock_create_project.return_value = True
    generator.lang_template_dir = tmp_path / "go"
    generator.lang_template_dir.mkdir()

    generator.create()

    mock_create_go_structure.assert_called_once()
    mock_log_success.assert_called_once_with("Go service 'test-service' created successfully in 'test-service'!")


def test_unsupported_language_does_not_call_structure_method(tmp_path):
    """Test that unsupported languages don't call any language-specific structure method."""
    with patch.object(ServiceGenerator, 'create_project', return_value=True), \
         patch.object(ServiceGenerator, 'init_basic_structure'), \
         patch.object(ServiceGenerator, 'write_template'), \
         patch.object(ServiceGenerator, 'create_architecture_docs'), \
         patch.object(ServiceGenerator, 'write_content'), \
         patch.object(ServiceGenerator, 'log_success'), \
         patch.object(ServiceGenerator, '_create_python_structure') as mock_python, \
         patch.object(ServiceGenerator, '_create_rust_structure') as mock_rust, \
         patch.object(ServiceGenerator, '_create_cpp_structure') as mock_cpp, \
         patch.object(ServiceGenerator, '_create_go_structure') as mock_go:
        
        generator = ServiceGenerator("test-service", "unsupported", False, {})
        generator.lang_template_dir = tmp_path / "unsupported"
        generator.lang_template_dir.mkdir()
        
        generator.create()
        
        mock_python.assert_not_called()
        mock_rust.assert_not_called()
        mock_cpp.assert_not_called()
        mock_go.assert_not_called()