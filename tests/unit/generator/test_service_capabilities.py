"""Tests for service extension capability validation."""

import pytest

from src.generator.service_capabilities import validate_service_extensions
from src.utils.error_handling import ExtensionError


@pytest.mark.parametrize("language", ["python", "rust", "typescript"])
def test_container_services_accept_implemented_extensions(language: str) -> None:
    selection = validate_service_extensions(
        language=language,
        runtime="container",
        framework=None,
        database="postgres",
        cache="redis",
        auth="jwt",
    )

    assert selection.database == "postgres"
    assert selection.cache == "redis"
    assert selection.auth == "jwt"


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
