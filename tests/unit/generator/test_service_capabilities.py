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


@pytest.mark.parametrize("language", ["rust", "typescript"])
def test_non_python_services_reject_current_python_only_extensions(language: str) -> None:
    with pytest.raises(ExtensionError, match=rf"{language}/container/default"):
        validate_service_extensions(
            language=language,
            runtime="container",
            framework=None,
            database=None,
            cache="redis",
            auth=None,
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


@pytest.mark.parametrize(
    ("category", "value", "kwargs"),
    [
        ("database", "mysql", {"database": "mysql", "cache": None, "auth": None}),
        ("database", "sqlite", {"database": "sqlite", "cache": None, "auth": None}),
        ("cache", "memcached", {"database": None, "cache": "memcached", "auth": None}),
        ("auth", "oauth", {"database": None, "cache": None, "auth": "oauth"}),
    ],
)
def test_unimplemented_extension_values_reject(category: str, value: str, kwargs: dict[str, str | None]) -> None:
    with pytest.raises(ExtensionError, match=f"{category} extension '{value}' is not implemented"):
        validate_service_extensions(
            language="python",
            runtime="container",
            framework=None,
            **kwargs,
        )
