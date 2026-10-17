from copy import deepcopy

import pytest
from unittest.mock import patch, MagicMock
from src.api import create_service, create_frontend, create_lib, create_cli, create_system, create_monorepo


@patch("src.api.ServiceGenerator")
def test_create_service_basic(mock_service_generator):
    mock_generator_instance = MagicMock()
    mock_service_generator.return_value = mock_generator_instance

    create_service("test-service", "python", True, {"key": "value"})

    mock_service_generator.assert_called_once_with(
        "test-service",
        "python",
        True,
        {"key": "value"},
        helm=False,
        root=None,
        database=None,
        cache=None,
        auth=None,
        framework=None,
        runtime="container",
    )
    mock_generator_instance.create.assert_called_once()


@patch("src.api.ServiceGenerator")
def test_create_service_with_helm_and_root(mock_service_generator):
    mock_generator_instance = MagicMock()
    mock_service_generator.return_value = mock_generator_instance

    create_service("test-service", "rust", False, {"config": "test"}, helm=True, root="/tmp")

    mock_service_generator.assert_called_once_with(
        "test-service",
        "rust",
        False,
        {"config": "test"},
        helm=True,
        root="/tmp",
        database=None,
        cache=None,
        auth=None,
        framework=None,
        runtime="container",
    )
    mock_generator_instance.create.assert_called_once()


@patch("src.api.ServiceGenerator")
def test_create_service_with_keyword_only_args(mock_service_generator):
    mock_generator_instance = MagicMock()
    mock_service_generator.return_value = mock_generator_instance

    # Test that helm and root are keyword-only arguments
    create_service("test", "go", True, {}, helm=True)
    create_service("test", "go", True, {}, root="/path")
    create_service("test", "go", True, {}, helm=False, root="/path")

    assert mock_service_generator.call_count == 3


@pytest.mark.parametrize(
    ("create", "generator_name", "arguments", "root"),
    [
        (create_frontend, "FrontendGenerator", ("test-frontend", False, {"framework": "react"}), None),
        (create_frontend, "FrontendGenerator", ("test-frontend", True, {"config": "test"}), "/custom/path"),
        (create_lib, "LibraryGenerator", ("test-lib", "python", True, {"license": "MIT"}), None),
        (create_lib, "LibraryGenerator", ("test-lib", "rust", False, {"version": "0.1.0"}), "/lib/path"),
        (create_cli, "CLIGenerator", ("test-cli", "go", False, {"description": "A CLI tool"}), None),
        (create_cli, "CLIGenerator", ("test-cli", "rust", True, {"config": "test"}), "/cli/path"),
    ],
    ids=["frontend-default", "frontend-root", "lib-default", "lib-root", "cli-default", "cli-root"],
)
def test_create_forwards_constructor(create, generator_name, arguments, root):
    expected_arguments = deepcopy(arguments)
    with patch(f"src.api.{generator_name}") as generator:
        if root is None:
            create(*arguments)
        else:
            create(*arguments, root=root)

    generator.assert_called_once_with(*expected_arguments, root)
    generator.return_value.create.assert_called_once()


@patch("src.api.MonorepoGenerator")
def test_create_monorepo_basic(mock_monorepo_generator):
    mock_generator_instance = MagicMock()
    mock_monorepo_generator.return_value = mock_generator_instance

    create_monorepo("test-monorepo", True, {"infrastructure": "k8s"})

    mock_monorepo_generator.assert_called_once_with(
        "test-monorepo",
        True,
        {"infrastructure": "k8s"},
        helm=False,
        root=None,
        cloud="multi",
        knowledge="none",
        runtime="kubernetes",
        workspace_tooling="bun-turbo",
    )
    mock_generator_instance.create.assert_called_once()


@patch("src.api.SystemGenerator")
def test_create_system_basic(mock_system_generator):
    mock_generator_instance = MagicMock()
    mock_system_generator.return_value = mock_generator_instance

    create_system("test-system", True, {"infrastructure": "k8s"})

    mock_system_generator.assert_called_once_with(
        "test-system",
        True,
        {"infrastructure": "k8s"},
        helm=False,
        root=None,
        cloud="multi",
        knowledge="none",
        runtime="kubernetes",
        workspace_tooling="none",
    )
    mock_generator_instance.create.assert_called_once()


@patch("src.api.MonorepoGenerator")
def test_create_monorepo_with_helm_and_root(mock_monorepo_generator):
    mock_generator_instance = MagicMock()
    mock_monorepo_generator.return_value = mock_generator_instance

    create_monorepo("test-monorepo", False, {"config": "test"}, helm=True, root="/monorepo/path")

    mock_monorepo_generator.assert_called_once_with(
        "test-monorepo",
        False,
        {"config": "test"},
        helm=True,
        root="/monorepo/path",
        cloud="multi",
        knowledge="none",
        runtime="kubernetes",
        workspace_tooling="bun-turbo",
    )
    mock_generator_instance.create.assert_called_once()


@patch("src.api.MonorepoGenerator")
def test_create_monorepo_with_cloud_and_knowledge(mock_monorepo_generator):
    mock_generator_instance = MagicMock()
    mock_monorepo_generator.return_value = mock_generator_instance

    create_monorepo(
        "test-monorepo",
        False,
        {"config": "test"},
        cloud="gcp",
        knowledge="obsidian",
    )

    mock_monorepo_generator.assert_called_once_with(
        "test-monorepo",
        False,
        {"config": "test"},
        helm=False,
        root=None,
        cloud="gcp",
        knowledge="obsidian",
        runtime="kubernetes",
        workspace_tooling="bun-turbo",
    )
    mock_generator_instance.create.assert_called_once()


@patch("src.api.ServiceGenerator")
def test_create_service_with_runtime(mock_service_generator):
    mock_generator_instance = MagicMock()
    mock_service_generator.return_value = mock_generator_instance

    create_service("edge-api", "typescript", False, {}, runtime="cloudflare-workers")

    mock_service_generator.assert_called_once_with(
        "edge-api",
        "typescript",
        False,
        {},
        helm=False,
        root=None,
        database=None,
        cache=None,
        auth=None,
        framework=None,
        runtime="cloudflare-workers",
    )
    mock_generator_instance.create.assert_called_once()


@patch("src.api.MonorepoGenerator")
def test_create_monorepo_with_runtime(mock_monorepo_generator):
    mock_generator_instance = MagicMock()
    mock_monorepo_generator.return_value = mock_generator_instance

    create_monorepo("edge-stack", False, {}, cloud="cloudflare", runtime="cloudflare-workers")

    mock_monorepo_generator.assert_called_once_with(
        "edge-stack",
        False,
        {},
        helm=False,
        root=None,
        cloud="cloudflare",
        knowledge="none",
        runtime="cloudflare-workers",
        workspace_tooling="bun-turbo",
    )
    mock_generator_instance.create.assert_called_once()


@pytest.mark.parametrize(
    ("create", "generator_name", "arguments", "error_type", "message"),
    [
        (create_service, "ServiceGenerator", ("test", "python", True, {}), ValueError, "Test error"),
        (create_frontend, "FrontendGenerator", ("test", True, {}), RuntimeError, "Frontend error"),
        (create_lib, "LibraryGenerator", ("test", "python", True, {}), OSError, "File system error"),
        (create_cli, "CLIGenerator", ("test", "go", False, {}), KeyError, "Missing key"),
        (create_monorepo, "MonorepoGenerator", ("test", True, {}), ImportError, "Module not found"),
    ],
    ids=["service", "frontend", "lib", "cli", "monorepo"],
)
def test_create_generator_error(create, generator_name, arguments, error_type, message):
    with patch(f"src.api.{generator_name}") as generator:
        generator.return_value.create.side_effect = error_type(message)
        with pytest.raises(error_type, match=message):
            create(*arguments)


def test_api_exports():
    """Test that all expected functions are exported in __all__."""
    from src.api import __all__

    expected_exports = [
        "create_service",
        "create_frontend",
        "create_lib",
        "create_cli",
        "create_system",
        "create_monorepo",
    ]

    assert set(__all__) == set(expected_exports)


def test_parameter_validation_types():
    """Test that functions accept correct parameter types."""
    # These should not raise type errors during runtime
    # (static type checking would catch these at development time)

    with patch("src.api.ServiceGenerator") as mock_gen:
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

    with (
        patch("src.api.ServiceGenerator") as mock_service_gen,
        patch("src.api.FrontendGenerator") as mock_frontend_gen,
        patch("src.api.LibraryGenerator") as mock_lib_gen,
        patch("src.api.CLIGenerator") as mock_cli_gen,
        patch("src.api.SystemGenerator") as mock_system_gen,
        patch("src.api.MonorepoGenerator") as mock_monorepo_gen,
    ):
        # Setup mocks
        for mock_gen in [
            mock_service_gen,
            mock_frontend_gen,
            mock_lib_gen,
            mock_cli_gen,
            mock_system_gen,
            mock_monorepo_gen,
        ]:
            mock_gen.return_value.create = MagicMock()

        # Test default values
        create_service("test", "python", True, {})
        mock_service_gen.assert_called_with(
            "test",
            "python",
            True,
            {},
            helm=False,
            root=None,
            database=None,
            cache=None,
            auth=None,
            framework=None,
            runtime="container",
        )

        create_frontend("test", True, {})
        mock_frontend_gen.assert_called_with("test", True, {}, None)

        create_lib("test", "python", True, {})
        mock_lib_gen.assert_called_with("test", "python", True, {}, None)

        create_cli("test", "python", True, {})
        mock_cli_gen.assert_called_with("test", "python", True, {}, None)

        create_system("test", True, {})
        mock_system_gen.assert_called_with(
            "test",
            True,
            {},
            helm=False,
            root=None,
            cloud="multi",
            knowledge="none",
            runtime="kubernetes",
            workspace_tooling="none",
        )

        create_monorepo("test", True, {})
        mock_monorepo_gen.assert_called_with(
            "test",
            True,
            {},
            helm=False,
            root=None,
            cloud="multi",
            knowledge="none",
            runtime="kubernetes",
            workspace_tooling="bun-turbo",
        )
