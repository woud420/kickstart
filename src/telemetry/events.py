"""Build and record closed, provider-neutral product events."""

import platform as runtime_platform

from src.model.dto.telemetry import (
    ScaffoldCreateContext,
    ScaffoldCreateErrorCategory,
    ScaffoldCreateOutcome,
    ScaffoldCreateProperties,
    TelemetryDurationBucket,
    TelemetryEvent,
    TelemetryEventName,
)
from src.stack.profile import stack_registry
from src.telemetry.reporter import TelemetryReporter, default_telemetry_reporter
from src.utils.errors import (
    DirectoryCreationError,
    ExtensionError,
    FileOperationError,
    InvalidProjectNameError,
    KickstartError,
    LanguageNotSupportedError,
    ManifestShapeError,
    MarkerError,
    MissingCreateArgumentsError,
    ProjectCreationError,
    TemplateError,
    UnsupportedOptionError,
    UnsupportedProjectTypeError,
)


_PROJECT_TYPES = {"service", "frontend", "lib", "cli", "system"}
_LEGACY_SYSTEM_PROJECT_TYPES = {"mono", "monorepo"}
_FRAMEWORKS = {"fastapi", "minimal"}
_DATABASES = {"none", "postgres"}
_CACHES = {"none", "redis"}
_AUTH = {"none", "jwt"}
_CONFIGURATION_ERRORS = (
    ExtensionError,
    InvalidProjectNameError,
    LanguageNotSupportedError,
    MissingCreateArgumentsError,
)
_PROJECT_CREATION_ERRORS = (
    DirectoryCreationError,
    FileOperationError,
    ManifestShapeError,
    MarkerError,
    ProjectCreationError,
    TemplateError,
)


def build_scaffold_create_event(
    context: ScaffoldCreateContext,
    outcome: ScaffoldCreateOutcome,
    error_category: ScaffoldCreateErrorCategory,
    duration_seconds: float,
    *,
    cli_version: str,
    platform_name: str | None = None,
    architecture: str | None = None,
) -> TelemetryEvent:
    """Normalize one terminal create result into the closed property DTO."""
    project_type = _project_type(context.project_type)
    language = _language(context.language, project_type)
    return TelemetryEvent(
        name=TelemetryEventName.SCAFFOLD_CREATE_COMPLETED,
        properties=ScaffoldCreateProperties(
            cli_version=cli_version,
            project_type=project_type,
            language=language,
            runtime=_runtime(context.runtime, project_type),
            cloud=_cloud(context.cloud, project_type),
            framework=_framework(context.framework, project_type, language),
            database=_extension(context.database, project_type, _DATABASES),
            cache=_extension(context.cache, project_type, _CACHES),
            auth=_extension(context.auth, project_type, _AUTH),
            knowledge=_knowledge(context.knowledge, project_type),
            workspace_tooling=_workspace_tooling(
                context.workspace_tooling,
                context.project_type,
                project_type,
            ),
            helm=context.helm,
            github_requested=context.github_requested,
            interactive=context.interactive,
            outcome=outcome,
            error_category=error_category,
            duration_bucket=_duration_bucket(duration_seconds),
            platform=_platform(platform_name or runtime_platform.system()),
            architecture=_architecture(architecture or runtime_platform.machine()),
        ),
    )


def capture_scaffold_create_terminal(
    context: ScaffoldCreateContext,
    outcome: ScaffoldCreateOutcome,
    error_category: ScaffoldCreateErrorCategory,
    duration_seconds: float,
    *,
    cli_version: str,
    reporter: TelemetryReporter | None = None,
) -> None:
    """Attempt one terminal capture while containing mapping and reporter failures."""
    try:
        event = build_scaffold_create_event(
            context,
            outcome,
            error_category,
            duration_seconds,
            cli_version=cli_version,
        )
        target_reporter = default_telemetry_reporter() if reporter is None else reporter
        target_reporter.record(event)
    except Exception:
        return


def classify_scaffold_create_exception(
    error: Exception,
) -> tuple[ScaffoldCreateOutcome, ScaffoldCreateErrorCategory]:
    """Reduce handled exceptions to fixed categories without serializing details."""
    if isinstance(error, UnsupportedProjectTypeError):
        return ScaffoldCreateOutcome.EXPECTED_ERROR, ScaffoldCreateErrorCategory.UNSUPPORTED_PROJECT_TYPE
    if isinstance(error, UnsupportedOptionError):
        return ScaffoldCreateOutcome.EXPECTED_ERROR, ScaffoldCreateErrorCategory.UNSUPPORTED_OPTION
    if isinstance(error, _CONFIGURATION_ERRORS):
        return ScaffoldCreateOutcome.EXPECTED_ERROR, ScaffoldCreateErrorCategory.INVALID_CONFIGURATION
    if isinstance(error, _PROJECT_CREATION_ERRORS):
        return ScaffoldCreateOutcome.EXPECTED_ERROR, ScaffoldCreateErrorCategory.PROJECT_CREATION_ERROR
    if isinstance(error, KickstartError):
        return ScaffoldCreateOutcome.EXPECTED_ERROR, ScaffoldCreateErrorCategory.EXPECTED_ERROR
    if isinstance(error, ValueError):
        return ScaffoldCreateOutcome.INVALID_CONFIGURATION, ScaffoldCreateErrorCategory.INVALID_CONFIGURATION
    return ScaffoldCreateOutcome.UNEXPECTED_ERROR, ScaffoldCreateErrorCategory.UNEXPECTED_ERROR


def _project_type(value: str | None) -> str:
    candidate = "" if value is None else value.strip().lower()
    if candidate in _LEGACY_SYSTEM_PROJECT_TYPES:
        return "system"
    return candidate if candidate in _PROJECT_TYPES else "unknown"


def _language(value: str, project_type: str) -> str:
    if project_type in {"frontend", "system"}:
        return "none"
    normalized = stack_registry.normalize_language(value)
    return normalized if normalized in stack_registry.languages else "unknown"


def _runtime(value: str | None, project_type: str) -> str:
    if project_type == "service":
        normalized = stack_registry.normalize_service_runtime(value or "container")
        return normalized if normalized in stack_registry.service_runtimes else "unknown"
    if project_type == "system":
        normalized = stack_registry.normalize_system_runtime(value or "kubernetes")
        return normalized if normalized in stack_registry.system_runtimes else "unknown"
    return "none"


def _cloud(value: str, project_type: str) -> str:
    if project_type != "system":
        return "none"
    normalized = stack_registry.normalize_cloud(value)
    return normalized if normalized in stack_registry.clouds else "unknown"


def _framework(value: str | None, project_type: str, language: str) -> str:
    if project_type != "service":
        return "none"
    if language == "python" and value is None:
        return "fastapi"
    if value is None or value == "none":
        return "none"
    candidate = value.strip().lower()
    return candidate if candidate in _FRAMEWORKS else "unknown"


def _extension(value: str | None, project_type: str, known: set[str]) -> str:
    if project_type != "service" or value is None:
        return "none"
    candidate = value.strip().lower()
    return candidate if candidate in known else "unknown"


def _knowledge(value: str, project_type: str) -> str:
    if project_type != "system":
        return "none"
    normalized = stack_registry.normalize_knowledge(value)
    return normalized if normalized in stack_registry.knowledge else "unknown"


def _workspace_tooling(value: str | None, raw_project_type: str | None, project_type: str) -> str:
    if project_type != "system":
        return "none"
    raw_type = "" if raw_project_type is None else raw_project_type.strip().lower()
    default = "bun-turbo" if raw_type in _LEGACY_SYSTEM_PROJECT_TYPES else "none"
    normalized = stack_registry.normalize_workspace_tooling(value or default)
    return normalized if normalized in stack_registry.workspace_tooling else "unknown"


def _duration_bucket(duration_seconds: float) -> TelemetryDurationBucket:
    if duration_seconds < 1:
        return TelemetryDurationBucket.UNDER_ONE_SECOND
    if duration_seconds < 5:
        return TelemetryDurationBucket.ONE_TO_FIVE_SECONDS
    if duration_seconds < 30:
        return TelemetryDurationBucket.FIVE_TO_THIRTY_SECONDS
    return TelemetryDurationBucket.THIRTY_SECONDS_OR_MORE


def _platform(value: str) -> str:
    candidate = value.strip().lower()
    return {"darwin": "macos", "linux": "linux", "windows": "windows"}.get(candidate, "other")


def _architecture(value: str) -> str:
    candidate = value.strip().lower()
    if candidate in {"arm64", "aarch64"}:
        return "arm64"
    if candidate in {"x86_64", "amd64"}:
        return "x86_64"
    return "other"
