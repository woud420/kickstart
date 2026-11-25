"""Noninteractive create command options and creator dispatch."""

from unittest.mock import patch

import pytest

from src.cli.main import app


@patch("src.cli.create.create_service")
@patch("src.cli.create.load_config")
def test_create_service_with_args(mock_load_config, mock_create_service, runner, mock_config):
    """Test creating a service with command line arguments."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(
        app, ["create", "service", "test-service", "--lang", "rust", "--gh", "--helm", "--root", "/tmp"]
    )

    assert result.exit_code == 0
    mock_create_service.assert_called_once_with("test-service", "rust", True, mock_config, helm=True, root="/tmp")


@patch("src.cli.create.create_frontend")
@patch("src.cli.create.load_config")
def test_create_frontend_with_args(mock_load_config, mock_create_frontend, runner, mock_config):
    """Test creating a frontend with command line arguments."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, ["create", "frontend", "test-frontend", "--gh", "--root", "/tmp"])

    assert result.exit_code == 0
    mock_create_frontend.assert_called_once_with("test-frontend", True, mock_config, root="/tmp")


@patch("src.cli.create.create_lib")
@patch("src.cli.create.load_config")
def test_create_lib_with_args(mock_load_config, mock_create_lib, runner, mock_config):
    """Test creating a library with command line arguments."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, ["create", "lib", "test-lib", "--lang", "go", "--root", "/tmp"])

    assert result.exit_code == 0
    mock_create_lib.assert_called_once_with("test-lib", "go", False, mock_config, root="/tmp")


@patch("src.cli.create.create_cli")
@patch("src.cli.create.load_config")
def test_create_cli_with_args(mock_load_config, mock_create_cli, runner, mock_config):
    """Test creating a CLI with command line arguments."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, ["create", "cli", "test-cli", "--lang", "rust", "--root", "/tmp"])

    assert result.exit_code == 0
    mock_create_cli.assert_called_once_with("test-cli", "rust", False, mock_config, root="/tmp")


@pytest.mark.parametrize("alias", ["mono", "monorepo"])
@patch("src.cli.create.create_system")
@patch("src.cli.create.load_config")
def test_removed_monorepo_aliases_point_to_system(mock_load_config, mock_create_system, alias, runner, mock_config):
    """The removed mono/monorepo types fail with the replacement command."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, ["create", alias, "test-mono", "--root", "/tmp"])

    assert result.exit_code == 1
    output = " ".join(result.stdout.split())
    assert f"Type '{alias}' was removed" in output
    assert "kickstart create system test-mono --workspace-tooling bun-turbo" in output
    mock_create_system.assert_not_called()


@patch("src.cli.create.create_system")
@patch("src.cli.create.load_config")
def test_create_system_with_cloud_and_knowledge(mock_load_config, mock_create_system, runner, mock_config):
    """Test creating a system with workflow profile options."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(
        app,
        [
            "create",
            "system",
            "test-system",
            "--root",
            "/tmp",
            "--cloud",
            "cloudflare",
            "--knowledge",
            "obsidian",
        ],
    )

    assert result.exit_code == 0
    mock_create_system.assert_called_once_with(
        "test-system",
        False,
        mock_config,
        helm=False,
        root="/tmp",
        cloud="cloudflare",
        knowledge="obsidian",
    )


@patch("src.cli.create.create_service")
@patch("src.cli.create.load_config")
def test_create_service_with_runtime(mock_load_config, mock_create_service, runner, mock_config):
    """Test creating a service with an explicit execution profile."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(
        app,
        [
            "create",
            "service",
            "edge-api",
            "--lang",
            "typescript",
            "--runtime",
            "cloudflare-workers",
            "--root",
            "/tmp",
        ],
    )

    assert result.exit_code == 0
    mock_create_service.assert_called_once_with(
        "edge-api",
        "typescript",
        False,
        mock_config,
        helm=False,
        root="/tmp",
        runtime="cloudflare-workers",
    )


@patch("src.cli.create.create_system")
@patch("src.cli.create.load_config")
def test_create_system_with_runtime(mock_load_config, mock_create_system, runner, mock_config):
    """Test creating a system with the canonical public project type."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(
        app,
        [
            "create",
            "system",
            "platform",
            "--cloud",
            "aws",
            "--runtime",
            "kubernetes",
            "--knowledge",
            "none",
            "--root",
            "/tmp",
        ],
    )

    assert result.exit_code == 0
    mock_create_system.assert_called_once_with(
        "platform",
        False,
        mock_config,
        helm=False,
        root="/tmp",
        cloud="aws",
        runtime="kubernetes",
    )


@patch("src.cli.create.create_system")
@patch("src.cli.create.load_config")
def test_create_system_with_bun_turbo_workspace_tooling(mock_load_config, mock_create_system, runner, mock_config):
    """Test creating a system with explicit Bun + Turbo workspace tooling."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(
        app,
        [
            "create",
            "system",
            "platform",
            "--workspace-tooling",
            "bun-turbo",
            "--root",
            "/tmp",
        ],
    )

    assert result.exit_code == 0
    mock_create_system.assert_called_once_with(
        "platform",
        False,
        mock_config,
        helm=False,
        root="/tmp",
        workspace_tooling="bun-turbo",
    )
