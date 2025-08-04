import pytest
from pathlib import Path
from src.generator.base import BaseGenerator
from unittest.mock import patch

@pytest.fixture
def base_generator():
    return BaseGenerator("test-project", {"key": "value"})

@pytest.fixture
def base_generator_with_root():
    return BaseGenerator("test-project", {"key": "value"}, root="/tmp")

def test_base_generator_initialization(base_generator):
    assert base_generator.name == "test-project"
    assert base_generator.config == {"key": "value"}
    assert base_generator.project == Path("test-project")
    assert base_generator.template_dir == Path(__file__).parent.parent.parent.parent / "src" / "templates"

def test_base_generator_initialization_with_root(base_generator_with_root):
    assert base_generator_with_root.project == Path("/tmp/test-project")

def test_create_project_success(base_generator, tmp_path):
    with patch.object(base_generator, 'project', tmp_path / "new-project"):
        assert base_generator.create_project() is True

def test_create_project_failure(base_generator, tmp_path):
    existing_dir = tmp_path / "existing-project"
    existing_dir.mkdir()
    with patch.object(base_generator, 'project', existing_dir):
        assert base_generator.create_project() is False

def test_create_directories(base_generator, tmp_path):
    with patch.object(base_generator, 'project', tmp_path):
        directories = ["dir1", "dir2/subdir"]
        base_generator.create_directories(directories)
        assert (tmp_path / "dir1").exists()
        assert (tmp_path / "dir2/subdir").exists()

def test_init_basic_structure(base_generator, tmp_path):
    with patch.object(base_generator, 'project', tmp_path):
        base_generator.init_basic_structure(["foo", "bar"])
        assert (tmp_path / "foo").exists()
        assert (tmp_path / "bar").exists()

def test_create_architecture_docs(base_generator, tmp_path):
    with patch.object(base_generator, 'project', tmp_path):
        base_generator.create_architecture_docs("My Docs")
        arch = tmp_path / "architecture/README.md"
        assert arch.exists()
        assert arch.read_text() == "# My Docs\n"

@patch('src.generator.base.write_file')
def test_write_template(mock_write_file, base_generator, tmp_path):
    template_path = tmp_path / "template.txt"
    template_path.write_text("Hello {{NAME}}")
    target = "output.txt"
    vars = {"name": "World"}
    base_generator.write_template(target, str(template_path), **vars)
    mock_write_file.assert_called_once_with(
        base_generator.project / target,
        str(template_path),
        service_name="test-project",
        name="World"
    )

@patch('src.generator.base.write_file')
def test_write_content(mock_write_file, base_generator):
    target = "output.txt"
    content = "test content"
    base_generator.write_content(target, content)
    mock_write_file.assert_called_once_with(
        base_generator.project / target,
        content
    )

@patch('src.generator.base.success')
def test_log_success(mock_success, base_generator):
    message = "Test success message"
    base_generator.log_success(message)
    mock_success.assert_called_once_with(message)

def test_get_common_vars(base_generator):
    vars = base_generator.get_common_vars()
    assert vars == {"service_name": "test-project"} 