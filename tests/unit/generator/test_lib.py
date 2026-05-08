import pytest
from pathlib import Path
from unittest.mock import patch, call
from src.generator.lib import LibraryGenerator, CLIGenerator
from src.utils.error_handling import LanguageNotSupportedError


@pytest.fixture
def library_generator():
    return LibraryGenerator("test-lib", "python", False, {"key": "value"})


@pytest.fixture
def library_generator_rust():
    return LibraryGenerator("test-lib", "rust", False, {"key": "value"})


@pytest.fixture
def library_generator_with_gh():
    return LibraryGenerator("test-lib", "python", True, {"key": "value"})


@pytest.fixture
def library_generator_with_root():
    return LibraryGenerator("test-lib", "python", False, {"key": "value"}, root="/tmp")


@pytest.fixture
def cli_generator():
    return CLIGenerator("test-cli", "python", False, {"key": "value"})

@pytest.fixture(autouse=True)
def mock_scaffold_contract_docs():
    with patch.object(LibraryGenerator, "create_scaffold_contract_docs", return_value=True), \
         patch.object(CLIGenerator, "create_scaffold_contract_docs", return_value=True):
        yield


@pytest.fixture
def cli_generator_rust():
    return CLIGenerator("test-cli", "rust", False, {"key": "value"})


@pytest.fixture
def cli_generator_typescript():
    return CLIGenerator("test-cli", "typescript", False, {"key": "value"})


@pytest.fixture
def cli_generator_with_gh():
    return CLIGenerator("test-cli", "python", True, {"key": "value"})


def test_library_generator_initialization(library_generator):
    assert library_generator.name == "test-lib"
    assert library_generator.lang == "python"
    assert library_generator.gh is False
    assert library_generator.config == {"key": "value"}
    assert library_generator.lang_template_dir == library_generator.template_dir / "python"


def test_library_generator_initialization_with_gh(library_generator_with_gh):
    assert library_generator_with_gh.gh is True


def test_library_generator_initialization_with_root(library_generator_with_root):
    assert library_generator_with_root.project == Path("/tmp/test-lib")


def test_cli_generator_inherits_from_library_generator():
    """Test that CLIGenerator inherits from LibraryGenerator."""
    cli_gen = CLIGenerator("test", "python", False, {})
    assert isinstance(cli_gen, LibraryGenerator)
    assert cli_gen.name == "test"
    assert cli_gen.lang == "python"
    assert cli_gen.gh is False


@patch('src.generator.lib.create_repo')
@patch.object(LibraryGenerator, 'write_content_files')
@patch.object(LibraryGenerator, 'write_template')
@patch.object(LibraryGenerator, 'create_architecture_docs')
@patch.object(LibraryGenerator, 'init_basic_structure')
@patch.object(LibraryGenerator, 'create_project')
@patch.object(LibraryGenerator, 'log_success')
def test_library_create_python_success_with_gh(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_create_architecture_docs, mock_write_template, mock_write_content_files, mock_create_repo
):
    generator = LibraryGenerator("test-lib", "python", True, {"key": "value"})
    mock_create_project.return_value = True

    generator.create()

    mock_create_project.assert_called_once()
    mock_init_basic_structure.assert_called_once_with([
        "src", "tests", ".kickstart", "docs/architecture",
        "docs/contracts", "docs/operations", "docs/decisions"
    ])
    
    # Verify common template files are written
    expected_common_calls = [
        call(".gitignore", "python/gitignore.tpl"),
        call("Makefile", "python/Makefile.tpl"),
        call("README.md", "python/README.md.tpl")
    ]
    
    # Verify Python-specific file
    expected_python_call = call("pyproject.toml", "python/pyproject.toml.tpl")
    
    all_expected_calls = expected_common_calls + [expected_python_call]
    mock_write_template.assert_has_calls(all_expected_calls, any_order=True)
    
    mock_create_architecture_docs.assert_called_once_with("test-lib Library Docs")
    mock_log_success.assert_called_once_with("Python library 'test-lib' created successfully in 'test-lib'!")
    mock_create_repo.assert_called_once_with("test-lib")


@patch('src.generator.lib.create_repo')
@patch.object(LibraryGenerator, 'write_content_files')
@patch.object(LibraryGenerator, 'write_template')
@patch.object(LibraryGenerator, 'create_architecture_docs')
@patch.object(LibraryGenerator, 'init_basic_structure')
@patch.object(LibraryGenerator, 'create_project')
@patch.object(LibraryGenerator, 'log_success')
def test_library_create_rust_success(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_create_architecture_docs, mock_write_template, mock_write_content_files, mock_create_repo
):
    generator = LibraryGenerator("test-lib", "rust", False, {"key": "value"})
    mock_create_project.return_value = True

    generator.create()

    # Verify common template files are written
    expected_common_calls = [
        call(".gitignore", "rust/gitignore.tpl"),
        call("Makefile", "rust/Makefile.tpl"),
        call("README.md", "rust/README.md.tpl")
    ]
    
    # Verify Rust-specific file
    expected_rust_call = call("Cargo.toml", "rust/Cargo.lib.toml.tpl")
    
    all_expected_calls = expected_common_calls + [expected_rust_call]
    mock_write_template.assert_has_calls(all_expected_calls, any_order=True)
    
    mock_create_architecture_docs.assert_called_once_with("test-lib Library Docs")
    mock_log_success.assert_called_once_with("Rust library 'test-lib' created successfully in 'test-lib'!")
    mock_create_repo.assert_not_called()


@patch.object(LibraryGenerator, 'create_project')
def test_library_create_fails_when_create_project_fails(mock_create_project, library_generator):
    mock_create_project.return_value = False
    
    library_generator.create()
    
    mock_create_project.assert_called_once()


@patch('src.generator.lib.create_repo')
@patch.object(CLIGenerator, 'write_content')
@patch.object(CLIGenerator, 'write_template')
@patch.object(CLIGenerator, 'create_architecture_docs')
@patch.object(CLIGenerator, 'init_basic_structure')
@patch.object(CLIGenerator, 'create_project')
@patch.object(CLIGenerator, 'log_success')
def test_cli_create_python_success_with_gh(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_create_architecture_docs, mock_write_template, mock_write_content, mock_create_repo
):
    generator = CLIGenerator("test-cli", "python", True, {"key": "value"})
    mock_create_project.return_value = True

    generator.create()

    mock_create_project.assert_called_once()
    mock_init_basic_structure.assert_called_once_with([
        "src/cli", "src/cli/commands", "src/config", "src/clients", "src/model", "src/operations",
        "src/output", "src/error", "tests", ".kickstart", "docs/architecture",
        "docs/contracts", "docs/operations", "docs/decisions"
    ])
    
    # Verify common template files are written
    expected_template_calls = [
        call(".gitignore", "python/gitignore.tpl"),
        call("Makefile", "cli/python/Makefile.tpl"),
        call("README.md", "cli/python/README.md.tpl"),
        call("pyproject.toml", "python/pyproject.cli.toml.tpl"),
        call("src/main.py", "cli/python/src/main.py.tpl"),
        call("src/cli/app.py", "cli/python/src/cli/app.py.tpl"),
        call("src/cli/commands/check.py", "cli/python/src/cli/commands/check.py.tpl"),
        call("src/model/dto.py", "cli/python/src/model/dto.py.tpl"),
        call("tests/test_cli_smoke.py", "cli/python/tests/test_cli_smoke.py.tpl"),
    ]
    mock_write_template.assert_has_calls(expected_template_calls, any_order=True)
    mock_write_content.assert_called_once_with("src/__init__.py", '__version__ = "0.1.0"\n')
    
    mock_create_architecture_docs.assert_called_once_with("test-cli CLI Docs")
    mock_log_success.assert_called_once_with("Python CLI 'test-cli' created successfully in 'test-cli'!")
    mock_create_repo.assert_called_once_with("test-cli")


@patch('src.generator.lib.create_repo')
@patch.object(CLIGenerator, 'write_content')
@patch.object(CLIGenerator, 'write_template')
@patch.object(CLIGenerator, 'create_architecture_docs')
@patch.object(CLIGenerator, 'init_basic_structure')
@patch.object(CLIGenerator, 'create_project')
@patch.object(CLIGenerator, 'log_success')
def test_cli_create_rust_success(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_create_architecture_docs, mock_write_template, mock_write_content, mock_create_repo
):
    generator = CLIGenerator("test-cli", "rust", False, {"key": "value"})
    mock_create_project.return_value = True

    generator.create()

    # Verify common template files are written
    expected_template_calls = [
        call(".gitignore", "rust/gitignore.tpl"),
        call("Makefile", "cli/rust/Makefile.tpl"),
        call("README.md", "cli/rust/README.md.tpl"),
        call("Cargo.toml", "rust/Cargo.cli.toml.tpl"),
        call("src/main.rs", "cli/rust/src/main.rs.tpl"),
        call("src/cli/args.rs", "cli/rust/src/cli/args.rs.tpl"),
        call("src/cli/dispatch.rs", "cli/rust/src/cli/dispatch.rs.tpl"),
        call("src/model/dto.rs", "cli/rust/src/model/dto.rs.tpl"),
        call("tests/cli_smoke.rs", "cli/rust/tests/cli_smoke.rs.tpl"),
    ]
    mock_write_template.assert_has_calls(expected_template_calls, any_order=True)
    mock_write_content.assert_not_called()
    
    mock_create_architecture_docs.assert_called_once_with("test-cli CLI Docs")
    mock_log_success.assert_called_once_with("Rust CLI 'test-cli' created successfully in 'test-cli'!")
    mock_create_repo.assert_not_called()


@patch('src.generator.lib.create_repo')
@patch.object(CLIGenerator, 'write_content')
@patch.object(CLIGenerator, 'write_template')
@patch.object(CLIGenerator, 'create_architecture_docs')
@patch.object(CLIGenerator, 'init_basic_structure')
@patch.object(CLIGenerator, 'create_project')
@patch.object(CLIGenerator, 'log_success')
def test_cli_create_typescript_success(
    mock_log_success, mock_create_project, mock_init_basic_structure,
    mock_create_architecture_docs, mock_write_template, mock_write_content, mock_create_repo
):
    generator = CLIGenerator("test-cli", "typescript", False, {"key": "value"})
    mock_create_project.return_value = True

    generator.create()

    expected_template_calls = [
        call(".gitignore", "typescript/gitignore.tpl"),
        call("Makefile", "cli/typescript/Makefile.tpl"),
        call("README.md", "cli/typescript/README.md.tpl"),
        call("package.json", "cli/typescript/package.json.tpl"),
        call("tsconfig.json", "cli/typescript/tsconfig.json.tpl"),
        call("vitest.config.ts", "cli/typescript/vitest.config.ts.tpl"),
        call("bin/dev.js", "cli/typescript/bin/dev.js.tpl"),
        call("bin/run.js", "cli/typescript/bin/run.js.tpl"),
        call("src/base-command.ts", "cli/typescript/src/base-command.ts.tpl"),
        call("src/commands/check.ts", "cli/typescript/src/commands/check.ts.tpl"),
        call("src/model/dto.ts", "cli/typescript/src/model/dto.ts.tpl"),
        call("tests/cli-smoke.test.ts", "cli/typescript/tests/cli-smoke.test.ts.tpl"),
    ]
    mock_write_template.assert_has_calls(expected_template_calls, any_order=True)
    mock_write_content.assert_not_called()
    mock_create_architecture_docs.assert_called_once_with("test-cli CLI Docs")
    mock_log_success.assert_called_once_with("Typescript CLI 'test-cli' created successfully in 'test-cli'!")
    mock_create_repo.assert_not_called()


@patch.object(CLIGenerator, 'create_project')
def test_cli_create_fails_when_create_project_fails(mock_create_project, cli_generator):
    mock_create_project.return_value = False
    
    cli_generator.create()
    
    mock_create_project.assert_called_once()


def test_library_unsupported_language_fails_loudly():
    """Test that unsupported library languages fail before partial generation."""
    with patch.object(LibraryGenerator, 'create_project', return_value=True), \
         patch.object(LibraryGenerator, 'init_basic_structure'), \
         patch.object(LibraryGenerator, 'create_architecture_docs'), \
         patch.object(LibraryGenerator, 'log_success'), \
         patch.object(LibraryGenerator, 'write_template') as mock_write_template:
        
        generator = LibraryGenerator("test", "unsupported", False, {})
        with pytest.raises(LanguageNotSupportedError, match="Supported library languages: python, rust"):
            generator.create()

        mock_write_template.assert_not_called()


def test_cli_unsupported_language_fails_loudly():
    """Test that unsupported CLI languages fail before partial generation."""
    with patch.object(CLIGenerator, 'create_project', return_value=True), \
         patch.object(CLIGenerator, 'init_basic_structure'), \
         patch.object(CLIGenerator, 'create_architecture_docs'), \
         patch.object(CLIGenerator, 'log_success'), \
         patch.object(CLIGenerator, 'write_template') as mock_write_template, \
         patch.object(CLIGenerator, 'write_content') as mock_write_content:
        
        generator = CLIGenerator("test", "unsupported", False, {})
        with pytest.raises(LanguageNotSupportedError, match="Supported cli languages: python, rust, typescript"):
            generator.create()

        mock_write_template.assert_not_called()
        mock_write_content.assert_not_called()


def test_library_python_vs_rust_differences():
    """Test the differences between Python and Rust library generation."""
    test_cases = [
        ("python", "pyproject.toml", "python/pyproject.toml.tpl"),
        ("rust", "Cargo.toml", "rust/Cargo.lib.toml.tpl")
    ]
    
    for lang, expected_config_filename, expected_config_template in test_cases:
        with patch.object(LibraryGenerator, 'create_project', return_value=True), \
             patch.object(LibraryGenerator, 'init_basic_structure'), \
             patch.object(LibraryGenerator, 'create_architecture_docs'), \
             patch.object(LibraryGenerator, 'log_success'), \
             patch.object(LibraryGenerator, 'write_content_files'), \
             patch.object(LibraryGenerator, 'write_template') as mock_write_template:
            
            generator = LibraryGenerator("test", lang, False, {})
            generator.create()
            
            # Check that the correct language-specific config file is written
            config_call = call(expected_config_filename, expected_config_template)
            assert config_call in mock_write_template.call_args_list


def test_cli_language_differences():
    """Test the language-specific package files for CLI generation."""
    test_cases = [
        ("python", "pyproject.toml", "python/pyproject.cli.toml.tpl", "src/main.py", "cli/python/src/main.py.tpl"),
        ("rust", "Cargo.toml", "rust/Cargo.cli.toml.tpl", "src/main.rs", "cli/rust/src/main.rs.tpl"),
        ("typescript", "package.json", "cli/typescript/package.json.tpl", "src/base-command.ts", "cli/typescript/src/base-command.ts.tpl"),
    ]
    
    for lang, expected_filename, config_template, main_file, main_template in test_cases:
        with patch.object(CLIGenerator, 'create_project', return_value=True), \
             patch.object(CLIGenerator, 'init_basic_structure'), \
             patch.object(CLIGenerator, 'create_architecture_docs'), \
             patch.object(CLIGenerator, 'log_success'), \
             patch.object(CLIGenerator, 'write_template') as mock_write_template, \
             patch.object(CLIGenerator, 'write_content') as mock_write_content:
            
            generator = CLIGenerator("test", lang, False, {})
            generator.create()
            
            # Check that the correct language-specific config file is written
            config_call = call(expected_filename, config_template)
            assert config_call in mock_write_template.call_args_list

            assert call(main_file, main_template) in mock_write_template.call_args_list
            if lang == "python":
                assert call("src/__init__.py", '__version__ = "0.1.0"\n') in mock_write_content.call_args_list
            else:
                mock_write_content.assert_not_called()


def test_library_vs_cli_architecture_docs_difference():
    """Test that library and CLI generators create different architecture docs."""
    # Test library
    with patch.object(LibraryGenerator, 'create_project', return_value=True), \
         patch.object(LibraryGenerator, 'init_basic_structure'), \
         patch.object(LibraryGenerator, 'write_template'), \
         patch.object(LibraryGenerator, 'write_content_files'), \
         patch.object(LibraryGenerator, 'log_success'), \
         patch.object(LibraryGenerator, 'create_architecture_docs') as mock_lib_arch_docs:
        
        lib_generator = LibraryGenerator("my-lib", "python", False, {})
        lib_generator.create()
        
        mock_lib_arch_docs.assert_called_once_with("my-lib Library Docs")
    
    # Test CLI
    with patch.object(CLIGenerator, 'create_project', return_value=True), \
         patch.object(CLIGenerator, 'init_basic_structure'), \
         patch.object(CLIGenerator, 'write_template'), \
         patch.object(CLIGenerator, 'write_content'), \
         patch.object(CLIGenerator, 'log_success'), \
         patch.object(CLIGenerator, 'create_architecture_docs') as mock_cli_arch_docs:
        
        cli_generator = CLIGenerator("my-cli", "python", False, {})
        cli_generator.create()
        
        mock_cli_arch_docs.assert_called_once_with("my-cli CLI Docs")


def test_library_vs_cli_success_message_difference():
    """Test that library and CLI generators have different success messages."""
    # Test library
    with patch.object(LibraryGenerator, 'create_project', return_value=True), \
         patch.object(LibraryGenerator, 'init_basic_structure'), \
         patch.object(LibraryGenerator, 'write_template'), \
         patch.object(LibraryGenerator, 'write_content_files'), \
         patch.object(LibraryGenerator, 'create_architecture_docs'), \
         patch.object(LibraryGenerator, 'log_success') as mock_lib_success:
        
        lib_generator = LibraryGenerator("my-lib", "python", False, {})
        lib_generator.create()
        
        mock_lib_success.assert_called_once_with("Python library 'my-lib' created successfully in 'my-lib'!")
    
    # Test CLI
    with patch.object(CLIGenerator, 'create_project', return_value=True), \
         patch.object(CLIGenerator, 'init_basic_structure'), \
         patch.object(CLIGenerator, 'write_template'), \
         patch.object(CLIGenerator, 'write_content'), \
         patch.object(CLIGenerator, 'log_success') as mock_cli_success:
        
        cli_generator = CLIGenerator("my-cli", "python", False, {})
        cli_generator.create()
        
        mock_cli_success.assert_called_once_with("Python CLI 'my-cli' created successfully in 'my-cli'!")


def test_library_and_cli_directory_structures():
    """Test library stays minimal while CLI gets the modular command layout."""
    library_directories = [
        "src", "tests", ".kickstart", "docs/architecture",
        "docs/contracts", "docs/operations", "docs/decisions"
    ]
    cli_directories = [
        "src/cli", "src/cli/commands", "src/config", "src/clients", "src/model", "src/operations",
        "src/output", "src/error", "tests", ".kickstart", "docs/architecture",
        "docs/contracts", "docs/operations", "docs/decisions"
    ]
    
    # Test library
    with patch.object(LibraryGenerator, 'create_project', return_value=True), \
         patch.object(LibraryGenerator, 'write_template'), \
         patch.object(LibraryGenerator, 'create_architecture_docs'), \
         patch.object(LibraryGenerator, 'write_content_files'), \
         patch.object(LibraryGenerator, 'log_success'), \
         patch.object(LibraryGenerator, 'init_basic_structure') as mock_lib_init:
        
        lib_generator = LibraryGenerator("test", "python", False, {})
        lib_generator.create()
        
        mock_lib_init.assert_called_once_with(library_directories)
    
    # Test CLI
    with patch.object(CLIGenerator, 'create_project', return_value=True), \
         patch.object(CLIGenerator, 'write_template'), \
         patch.object(CLIGenerator, 'write_content'), \
         patch.object(CLIGenerator, 'create_architecture_docs'), \
         patch.object(CLIGenerator, 'log_success'), \
         patch.object(CLIGenerator, 'init_basic_structure') as mock_cli_init:
        
        cli_generator = CLIGenerator("test", "python", False, {})
        cli_generator.create()
        
        mock_cli_init.assert_called_once_with(cli_directories)
