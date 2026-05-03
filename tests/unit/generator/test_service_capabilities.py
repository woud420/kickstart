"""Tests for service extension capability validation."""

import pytest

from src.generator.service_capabilities import validate_service_extensions
from src.utils.error_handling import ExtensionError


def test_python_fastapi_container_accepts_implemented_extensions() -> None:
    selection = validate_service_extensions(
        language="python",
        runtime="container",
        framework=None,
        database="postgres",
        cache="redis",
        auth="jwt",
    )

    assert selection.database == "postgres"
    assert selection.cache == "redis"
    assert selection.auth == "jwt"


def test_rust_container_accepts_implemented_extensions() -> None:
    selection = validate_service_extensions(
        language="rust",
        runtime="container",
        framework=None,
        database="postgres",
        cache="redis",
        auth="jwt",
    )

    assert selection.database == "postgres"
    assert selection.cache == "redis"
    assert selection.auth == "jwt"


def test_typescript_container_accepts_database_and_cache_extensions() -> None:
    selection = validate_service_extensions(
        language="typescript",
        runtime="container",
        framework=None,
        database="postgres",
        cache="redis",
        auth=None,
    )

    assert selection.database == "postgres"
    assert selection.cache == "redis"
    assert selection.auth is None


def test_typescript_services_reject_jwt_until_templates_exist() -> None:
    with pytest.raises(ExtensionError, match="typescript/container/default"):
        validate_service_extensions(
            language="typescript",
            runtime="container",
            framework=None,
            database=None,
            cache=None,
            auth="jwt",
        )


def test_cloudflare_worker_services_reject_extensions() -> None:
    with pytest.raises(ExtensionError, match="auth extension 'jwt' is not supported"):
        validate_service_extensions(
            language="typescript",
            runtime="cloudflare-workers",
            framework=None,
            database=None,
            cache=None,
            auth="jwt",
        )


def test_python_minimal_services_reject_extensions() -> None:
    with pytest.raises(ExtensionError, match="database extension 'postgres' is not supported"):
        validate_service_extensions(
            language="python",
            runtime="container",
            framework="minimal",
            database="postgres",
            cache=None,
            auth=None,
        )
