"""Service capability validation for language/runtime extension options."""

from dataclasses import dataclass

from src.utils.error_handling import ExtensionError


@dataclass(frozen=True)
class ServiceExtensionSelection:
    """Selected service extensions after validation."""

    database: str | None = None
    cache: str | None = None
    auth: str | None = None

    def has_extensions(self) -> bool:
        """Return whether any extension option was selected."""
        return self.database is not None or self.cache is not None or self.auth is not None


@dataclass(frozen=True)
class ServiceExtensionSupport:
    """Implemented extensions for a language/runtime/framework combination."""

    databases: tuple[str, ...] = ()
    caches: tuple[str, ...] = ()
    auth: tuple[str, ...] = ()


IMPLEMENTED_DATABASE_EXTENSIONS = ("postgres",)
IMPLEMENTED_CACHE_EXTENSIONS = ("redis",)
IMPLEMENTED_AUTH_EXTENSIONS = ("jwt",)

_SERVICE_EXTENSION_SUPPORT: dict[tuple[str, str, str], ServiceExtensionSupport] = {
    ("python", "container", "fastapi"): ServiceExtensionSupport(
        databases=IMPLEMENTED_DATABASE_EXTENSIONS,
        caches=IMPLEMENTED_CACHE_EXTENSIONS,
        auth=IMPLEMENTED_AUTH_EXTENSIONS,
    ),
    ("rust", "container", "default"): ServiceExtensionSupport(
        caches=IMPLEMENTED_CACHE_EXTENSIONS,
        auth=IMPLEMENTED_AUTH_EXTENSIONS,
    ),
    ("typescript", "container", "default"): ServiceExtensionSupport(
        databases=IMPLEMENTED_DATABASE_EXTENSIONS,
    ),
}


def normalize_framework(*, language: str, framework: str | None) -> str:
    """Return the canonical framework capability id for validation messages."""
    if language != "python":
        return framework or "default"
    if framework is None or framework == "fastapi":
        return "fastapi"
    return framework


def validate_service_extensions(
    *,
    language: str,
    runtime: str,
    framework: str | None,
    database: str | None,
    cache: str | None,
    auth: str | None,
) -> ServiceExtensionSelection:
    """Validate selected service extensions for a language/runtime/framework."""
    selection = ServiceExtensionSelection(
        database=_normalize_optional(database),
        cache=_normalize_optional(cache),
        auth=_normalize_optional(auth),
    )
    framework_id = normalize_framework(language=language, framework=framework)
    support = _SERVICE_EXTENSION_SUPPORT.get((language, runtime, framework_id), ServiceExtensionSupport())

    _validate_category(
        category="database",
        selected=selection.database,
        supported=support.databases,
        implemented=IMPLEMENTED_DATABASE_EXTENSIONS,
        language=language,
        runtime=runtime,
        framework=framework_id,
    )
    _validate_category(
        category="cache",
        selected=selection.cache,
        supported=support.caches,
        implemented=IMPLEMENTED_CACHE_EXTENSIONS,
        language=language,
        runtime=runtime,
        framework=framework_id,
    )
    _validate_category(
        category="auth",
        selected=selection.auth,
        supported=support.auth,
        implemented=IMPLEMENTED_AUTH_EXTENSIONS,
        language=language,
        runtime=runtime,
        framework=framework_id,
    )
    return selection


def _normalize_optional(value: str | None) -> str | None:
    """Normalize absent option spellings."""
    if value is None or value == "none":
        return None
    return value


def _validate_category(
    *,
    category: str,
    selected: str | None,
    supported: tuple[str, ...],
    implemented: tuple[str, ...],
    language: str,
    runtime: str,
    framework: str,
) -> None:
    """Validate one extension category."""
    if selected is None:
        return

    if selected not in implemented:
        raise ExtensionError(
            "{category} extension '{selected}' is not implemented. Implemented {category} extensions: {implemented}.".format(
                category=category,
                selected=selected,
                implemented=", ".join(implemented) or "none",
            )
        )

    if selected not in supported:
        raise ExtensionError(
            "{category} extension '{selected}' is not supported for {language}/{runtime}/{framework} services. "
            "Currently supported for this combination: {supported}.".format(
                category=category,
                selected=selected,
                language=language,
                runtime=runtime,
                framework=framework,
                supported=", ".join(supported) or "none",
            )
        )
