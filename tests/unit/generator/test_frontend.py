import pytest
from pathlib import Path
from unittest.mock import patch, call
from src.generator.frontend import FrontendGenerator


@pytest.fixture
def frontend_generator():
    return FrontendGenerator("test-frontend", False, {"key": "value"})


@pytest.fixture
def frontend_generator_with_gh():
    return FrontendGenerator("test-frontend", True, {"key": "value"})


@pytest.fixture
def frontend_generator_with_root():
    return FrontendGenerator("test-frontend", False, {"key": "value"}, root="/tmp")


def test_frontend_generator_initialization(frontend_generator):
    assert frontend_generator.name == "test-frontend"
    assert frontend_generator.gh is False
    assert frontend_generator.config == {"key": "value"}
    assert frontend_generator.template_dir.name == "react"


def test_frontend_generator_initialization_with_gh(frontend_generator_with_gh):
    assert frontend_generator_with_gh.gh is True


def test_frontend_generator_initialization_with_root(frontend_generator_with_root):
    assert frontend_generator_with_root.project == Path("/tmp/test-frontend")


@patch('src.generator.frontend.create_repo')
@patch.object(FrontendGenerator, 'write_template')
@patch.object(FrontendGenerator, 'create_architecture_docs')
@patch.object(FrontendGenerator, 'init_basic_structure')
@patch.object(FrontendGenerator, 'create_project')
@patch.object(FrontendGenerator, 'log_success')
def test_create_success_with_gh(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_create_architecture_docs, mock_write_template, mock_create_repo
):
    generator = FrontendGenerator("test-frontend", True, {"key": "value"})
    mock_create_project.return_value = True

    generator.create()

    mock_create_project.assert_called_once()
    mock_init_basic_structure.assert_called_once_with([
        "src", "public", "tests", "architecture"
    ])
    
    # Verify template files are written
    expected_template_calls = [
        call(".gitignore", "gitignore.tpl"),
        call("Dockerfile", "Dockerfile.tpl"),
        call("Makefile", "Makefile.tpl"),
        call("README.md", "README.md.tpl"),
        call("package.json", "package.json.tpl")
    ]
    mock_write_template.assert_has_calls(expected_template_calls, any_order=True)
    
    mock_create_architecture_docs.assert_called_once_with("test-frontend Frontend Docs")
    mock_log_success.assert_called_once_with("Frontend app 'test-frontend' created successfully in 'test-frontend'!")
    mock_create_repo.assert_called_once_with("test-frontend")


@patch('src.generator.frontend.create_repo')
@patch.object(FrontendGenerator, 'write_template')
@patch.object(FrontendGenerator, 'create_architecture_docs')
@patch.object(FrontendGenerator, 'init_basic_structure')
@patch.object(FrontendGenerator, 'create_project')
@patch.object(FrontendGenerator, 'log_success')
def test_create_success_without_gh(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_create_architecture_docs, mock_write_template, mock_create_repo
):
    generator = FrontendGenerator("test-frontend", False, {"key": "value"})
    mock_create_project.return_value = True

    generator.create()

    mock_create_project.assert_called_once()
    mock_init_basic_structure.assert_called_once_with([
        "src", "public", "tests", "architecture"
    ])
    
    # Verify template files are written
    expected_template_calls = [
        call(".gitignore", "gitignore.tpl"),
        call("Dockerfile", "Dockerfile.tpl"),
        call("Makefile", "Makefile.tpl"),
        call("README.md", "README.md.tpl"),
        call("package.json", "package.json.tpl")
    ]
    mock_write_template.assert_has_calls(expected_template_calls, any_order=True)
    
    mock_create_architecture_docs.assert_called_once_with("test-frontend Frontend Docs")
    mock_log_success.assert_called_once_with("Frontend app 'test-frontend' created successfully in 'test-frontend'!")
    mock_create_repo.assert_not_called()


@patch.object(FrontendGenerator, 'create_project')
def test_create_fails_when_create_project_fails(mock_create_project, frontend_generator):
    mock_create_project.return_value = False
    
    frontend_generator.create()
    
    mock_create_project.assert_called_once()


def test_template_directory_is_react():
    """Test that the template directory is correctly set to react."""
    generator = FrontendGenerator("test", False, {})
    assert generator.template_dir.name == "react"
    # Ensure it's the react subdirectory of the base template directory
    assert "react" in str(generator.template_dir)


def test_project_structure_directories():
    """Test that the correct directory structure is created."""
    expected_directories = ["src", "public", "tests", "architecture"]
    
    with patch.object(FrontendGenerator, 'create_project', return_value=True), \
         patch.object(FrontendGenerator, 'write_template'), \
         patch.object(FrontendGenerator, 'create_architecture_docs'), \
         patch.object(FrontendGenerator, 'log_success'), \
         patch.object(FrontendGenerator, 'init_basic_structure') as mock_init_structure:
        
        generator = FrontendGenerator("test", False, {})
        generator.create()
        
        mock_init_structure.assert_called_once_with(expected_directories)


def test_all_template_files_are_written():
    """Test that all expected template files are written."""
    expected_template_files = [
        (".gitignore", "gitignore.tpl"),
        ("Dockerfile", "Dockerfile.tpl"),
        ("Makefile", "Makefile.tpl"),
        ("README.md", "README.md.tpl"),
        ("package.json", "package.json.tpl")
    ]
    
    with patch.object(FrontendGenerator, 'create_project', return_value=True), \
         patch.object(FrontendGenerator, 'init_basic_structure'), \
         patch.object(FrontendGenerator, 'create_architecture_docs'), \
         patch.object(FrontendGenerator, 'log_success'), \
         patch.object(FrontendGenerator, 'write_template') as mock_write_template:
        
        generator = FrontendGenerator("test", False, {})
        generator.create()
        
        for file_path, template_name in expected_template_files:
            expected_call = call(file_path, template_name)
            assert expected_call in mock_write_template.call_args_list


def test_architecture_docs_content():
    """Test that architecture docs are created with correct title."""
    with patch.object(FrontendGenerator, 'create_project', return_value=True), \
         patch.object(FrontendGenerator, 'init_basic_structure'), \
         patch.object(FrontendGenerator, 'write_template'), \
         patch.object(FrontendGenerator, 'log_success'), \
         patch.object(FrontendGenerator, 'create_architecture_docs') as mock_create_arch_docs:
        
        generator = FrontendGenerator("my-awesome-app", False, {})
        generator.create()
        
        mock_create_arch_docs.assert_called_once_with("my-awesome-app Frontend Docs")


def test_success_message_format():
    """Test that the success message has the correct format."""
    with patch.object(FrontendGenerator, 'create_project', return_value=True), \
         patch.object(FrontendGenerator, 'init_basic_structure'), \
         patch.object(FrontendGenerator, 'write_template'), \
         patch.object(FrontendGenerator, 'create_architecture_docs'), \
         patch.object(FrontendGenerator, 'log_success') as mock_log_success:
        
        generator = FrontendGenerator("my-react-app", False, {})
        generator.create()
        
        expected_message = "Frontend app 'my-react-app' created successfully in 'my-react-app'!"
        mock_log_success.assert_called_once_with(expected_message)


def test_github_repo_creation_conditional():
    """Test that GitHub repo creation only happens when gh=True."""
    test_cases = [
        (True, True),   # gh=True should call create_repo
        (False, False), # gh=False should not call create_repo
    ]
    
    for gh_flag, should_create_repo in test_cases:
        with patch.object(FrontendGenerator, 'create_project', return_value=True), \
             patch.object(FrontendGenerator, 'init_basic_structure'), \
             patch.object(FrontendGenerator, 'write_template'), \
             patch.object(FrontendGenerator, 'create_architecture_docs'), \
             patch.object(FrontendGenerator, 'log_success'), \
             patch('src.generator.frontend.create_repo') as mock_create_repo:
            
            generator = FrontendGenerator("test", gh_flag, {})
            generator.create()
            
            if should_create_repo:
                mock_create_repo.assert_called_once_with("test")
            else:
                mock_create_repo.assert_not_called()


def test_template_files_count():
    """Test that exactly 5 template files are written."""
    with patch.object(FrontendGenerator, 'create_project', return_value=True), \
         patch.object(FrontendGenerator, 'init_basic_structure'), \
         patch.object(FrontendGenerator, 'create_architecture_docs'), \
         patch.object(FrontendGenerator, 'log_success'), \
         patch.object(FrontendGenerator, 'write_template') as mock_write_template:
        
        generator = FrontendGenerator("test", False, {})
        generator.create()
        
        # Should write exactly 5 template files
        assert mock_write_template.call_count == 5


def test_no_language_specific_logic():
    """Test that FrontendGenerator doesn't have language-specific methods like ServiceGenerator."""
    generator = FrontendGenerator("test", False, {})
    
    # Frontend generator should not have language-specific methods
    assert not hasattr(generator, '_create_python_structure')
    assert not hasattr(generator, '_create_rust_structure')
    assert not hasattr(generator, '_create_go_structure')
    
    # But should have the base create method
    assert hasattr(generator, 'create')


def test_inheritance_from_base_generator():
    """Test that FrontendGenerator properly inherits from BaseGenerator."""
    from src.generator.base import BaseGenerator
    
    generator = FrontendGenerator("test", False, {})
    assert isinstance(generator, BaseGenerator)
    
    # Should have inherited methods
    assert hasattr(generator, 'create_project')
    assert hasattr(generator, 'init_basic_structure')
    assert hasattr(generator, 'write_template')
    assert hasattr(generator, 'create_architecture_docs')
    assert hasattr(generator, 'log_success')