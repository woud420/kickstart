import pytest
from unittest.mock import patch, MagicMock
from src.api import (
    create_service,
    create_frontend,
    create_lib,
    create_cli,
    create_monorepo
)


@patch('src.api.ServiceGenerator')
def test_create_service_basic(mock_service_generator):
    mock_generator_instance = MagicMock()
    mock_service_generator.return_value = mock_generator_instance
    
    create_service("test-service", "python", True, {"key": "value"})
    
    mock_service_generator.assert_called_once_with("test-service", "python", True, {"key": "value"}, False, None)
    mock_generator_instance.create.assert_called_once()


@patch('src.api.ServiceGenerator')
def test_create_service_with_helm_and_root(mock_service_generator):
    mock_generator_instance = MagicMock()
    mock_service_generator.return_value = mock_generator_instance
    
    create_service("test-service", "rust", False, {"config": "test"}, helm=True, root="/tmp")
    
    mock_service_generator.assert_called_once_with("test-service", "rust", False, {"config": "test"}, True, "/tmp")
    mock_generator_instance.create.assert_called_once()


@patch('src.api.ServiceGenerator')
def test_create_service_with_keyword_only_args(mock_service_generator):
    mock_generator_instance = MagicMock()
    mock_service_generator.return_value = mock_generator_instance
    
    # Test that helm and root are keyword-only arguments
    create_service("test", "go", True, {}, helm=True)
    create_service("test", "go", True, {}, root="/path")
    create_service("test", "go", True, {}, helm=False, root="/path")
    
    assert mock_service_generator.call_count == 3


@patch('src.api.FrontendGenerator')
def test_create_frontend_basic(mock_frontend_generator):
    mock_generator_instance = MagicMock()
    mock_frontend_generator.return_value = mock_generator_instance
    
    create_frontend("test-frontend", False, {"framework": "react"})
    
    mock_frontend_generator.assert_called_once_with("test-frontend", False, {"framework": "react"}, None)
    mock_generator_instance.create.assert_called_once()


@patch('src.api.FrontendGenerator')
def test_create_frontend_with_root(mock_frontend_generator):
    mock_generator_instance = MagicMock()
    mock_frontend_generator.return_value = mock_generator_instance
    
    create_frontend("test-frontend", True, {"config": "test"}, root="/custom/path")
    
    mock_frontend_generator.assert_called_once_with("test-frontend", True, {"config": "test"}, "/custom/path")
    mock_generator_instance.create.assert_called_once()


@patch('src.api.LibraryGenerator')
def test_create_lib_basic(mock_lib_generator):
    mock_generator_instance = MagicMock()
    mock_lib_generator.return_value = mock_generator_instance
    
    create_lib("test-lib", "python", True, {"license": "MIT"})
    
    mock_lib_generator.assert_called_once_with("test-lib", "python", True, {"license": "MIT"}, None)
    mock_generator_instance.create.assert_called_once()


@patch('src.api.LibraryGenerator')
def test_create_lib_with_root(mock_lib_generator):
    mock_generator_instance = MagicMock()
    mock_lib_generator.return_value = mock_generator_instance
    
    create_lib("test-lib", "rust", False, {"version": "0.1.0"}, root="/lib/path")
    
    mock_lib_generator.assert_called_once_with("test-lib", "rust", False, {"version": "0.1.0"}, "/lib/path")
    mock_generator_instance.create.assert_called_once()


@patch('src.api.CLIGenerator')
def test_create_cli_basic(mock_cli_generator):
    mock_generator_instance = MagicMock()
    mock_cli_generator.return_value = mock_generator_instance
    
    create_cli("test-cli", "go", False, {"description": "A CLI tool"})
    
    mock_cli_generator.assert_called_once_with("test-cli", "go", False, {"description": "A CLI tool"}, None)
    mock_generator_instance.create.assert_called_once()


@patch('src.api.CLIGenerator')
def test_create_cli_with_root(mock_cli_generator):
    mock_generator_instance = MagicMock()
    mock_cli_generator.return_value = mock_generator_instance
    
    create_cli("test-cli", "java", True, {"config": "test"}, root="/cli/path")
    
    mock_cli_generator.assert_called_once_with("test-cli", "java", True, {"config": "test"}, "/cli/path")
    mock_generator_instance.create.assert_called_once()


@patch('src.api.MonorepoGenerator')
def test_create_monorepo_basic(mock_monorepo_generator):
    mock_generator_instance = MagicMock()
    mock_monorepo_generator.return_value = mock_generator_instance
    
    create_monorepo("test-monorepo", True, {"infrastructure": "k8s"})
    
    mock_monorepo_generator.assert_called_once_with("test-monorepo", True, {"infrastructure": "k8s"}, False, None)
    mock_generator_instance.create.assert_called_once()


@patch('src.api.MonorepoGenerator')
def test_create_monorepo_with_helm_and_root(mock_monorepo_generator):
    mock_generator_instance = MagicMock()
    mock_monorepo_generator.return_value = mock_generator_instance
    
    create_monorepo("test-monorepo", False, {"config": "test"}, helm=True, root="/monorepo/path")
    
    mock_monorepo_generator.assert_called_once_with("test-monorepo", False, {"config": "test"}, True, "/monorepo/path")
    mock_generator_instance.create.assert_called_once()


@patch('src.api.ServiceGenerator')
def test_create_service_generator_exception_propagates(mock_service_generator):
    mock_generator_instance = MagicMock()
    mock_generator_instance.create.side_effect = ValueError("Test error")
    mock_service_generator.return_value = mock_generator_instance
    
    with pytest.raises(ValueError, match="Test error"):
        create_service("test", "python", True, {})


@patch('src.api.FrontendGenerator')
def test_create_frontend_generator_exception_propagates(mock_frontend_generator):
    mock_generator_instance = MagicMock()
    mock_generator_instance.create.side_effect = RuntimeError("Frontend error")
    mock_frontend_generator.return_value = mock_generator_instance
    
    with pytest.raises(RuntimeError, match="Frontend error"):
        create_frontend("test", True, {})


@patch('src.api.LibraryGenerator')
def test_create_lib_generator_exception_propagates(mock_lib_generator):
    mock_generator_instance = MagicMock()
    mock_generator_instance.create.side_effect = OSError("File system error")
    mock_lib_generator.return_value = mock_generator_instance
    
    with pytest.raises(OSError, match="File system error"):
        create_lib("test", "python", True, {})


@patch('src.api.CLIGenerator')
def test_create_cli_generator_exception_propagates(mock_cli_generator):
    mock_generator_instance = MagicMock()
    mock_generator_instance.create.side_effect = KeyError("Missing key")
    mock_cli_generator.return_value = mock_generator_instance
    
    with pytest.raises(KeyError, match="Missing key"):
        create_cli("test", "go", False, {})


@patch('src.api.MonorepoGenerator')
def test_create_monorepo_generator_exception_propagates(mock_monorepo_generator):
    mock_generator_instance = MagicMock()
    mock_generator_instance.create.side_effect = ImportError("Module not found")
    mock_monorepo_generator.return_value = mock_generator_instance
    
    with pytest.raises(ImportError, match="Module not found"):
        create_monorepo("test", True, {})


def test_api_exports():
    """Test that all expected functions are exported in __all__."""
    from src.api import __all__
    
    expected_exports = [
        "create_service",
        "create_frontend", 
        "create_lib",
        "create_cli",
        "create_monorepo"
    ]
    
    assert set(__all__) == set(expected_exports)


def test_parameter_validation_types():
    """Test that functions accept correct parameter types."""
    # These should not raise type errors during runtime
    # (static type checking would catch these at development time)
    
    with patch('src.api.ServiceGenerator') as mock_gen:
        mock_gen.return_value.create = MagicMock()
        
        # Test string parameters
        create_service("test", "python", True, {"key": "value"})
        
        # Test boolean parameters
        create_service("test", "python", False, {})
        
        # Test dict parameter (empty)
        create_service("test", "python", True, {})
        
        # Test dict parameter (with content)
        create_service("test", "python", True, {"complex": {"nested": "value"}})


def test_optional_parameters_default_behavior():
    """Test that optional parameters have correct default behavior."""
    
    with patch('src.api.ServiceGenerator') as mock_service_gen, \
         patch('src.api.FrontendGenerator') as mock_frontend_gen, \
         patch('src.api.LibraryGenerator') as mock_lib_gen, \
         patch('src.api.CLIGenerator') as mock_cli_gen, \
         patch('src.api.MonorepoGenerator') as mock_monorepo_gen:
        
        # Setup mocks
        for mock_gen in [mock_service_gen, mock_frontend_gen, mock_lib_gen, mock_cli_gen, mock_monorepo_gen]:
            mock_gen.return_value.create = MagicMock()
        
        # Test default values
        create_service("test", "python", True, {})
        mock_service_gen.assert_called_with("test", "python", True, {}, False, None)
        
        create_frontend("test", True, {})
        mock_frontend_gen.assert_called_with("test", True, {}, None)
        
        create_lib("test", "python", True, {})
        mock_lib_gen.assert_called_with("test", "python", True, {}, None)
        
        create_cli("test", "python", True, {})
        mock_cli_gen.assert_called_with("test", "python", True, {}, None)
        
        create_monorepo("test", True, {})
        mock_monorepo_gen.assert_called_with("test", True, {}, False, None)