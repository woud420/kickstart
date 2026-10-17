"""Noninteractive create command options and creator dispatch."""

from unittest.mock import patch


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


@patch("src.cli.create.create_monorepo")
@patch("src.cli.create.load_config")
def test_create_monorepo_with_args(mock_load_config, mock_create_monorepo, runner, mock_config):
    """Test creating a monorepo with command line arguments."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(app, ["create", "mono", "test-mono", "--helm", "--gh", "--root", "/tmp"])

    assert result.exit_code == 0
    mock_create_monorepo.assert_called_once_with("test-mono", True, mock_config, helm=True, root="/tmp")


@patch("src.cli.create.create_monorepo")
@patch("src.cli.create.load_config")
def test_create_monorepo_with_cloud_and_knowledge(mock_load_config, mock_create_monorepo, runner, mock_config):
    """Test creating a monorepo with workflow profile options."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(
        app,
        [
            "create",
            "mono",
            "test-mono",
            "--root",
            "/tmp",
            "--cloud",
            "cloudflare",
            "--knowledge",
            "obsidian",
        ],
    )

    assert result.exit_code == 0
    mock_create_monorepo.assert_called_once_with(
        "test-mono",
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


@patch("src.cli.create.create_monorepo")
@patch("src.cli.create.load_config")
def test_create_monorepo_with_runtime(mock_load_config, mock_create_monorepo, runner, mock_config):
    """Test creating a system monorepo with an explicit platform profile."""
    mock_load_config.return_value = mock_config

    result = runner.invoke(
        app,
        [
            "create",
            "mono",
            "edge-stack",
            "--cloud",
            "cloudflare",
            "--runtime",
            "cloudflare-workers",
            "--root",
            "/tmp",
        ],
    )

    assert result.exit_code == 0
    mock_create_monorepo.assert_called_once_with(
        "edge-stack",
        False,
        mock_config,
        helm=False,
        root="/tmp",
        cloud="cloudflare",
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
