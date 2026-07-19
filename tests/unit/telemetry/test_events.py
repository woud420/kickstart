from pathlib import Path
from unittest.mock import Mock

import pytest

from src.model.dto.telemetry import (
    ScaffoldCreateContext,
    ScaffoldCreateErrorCategory,
    ScaffoldCreateOutcome,
    TelemetryDurationBucket,
)
from src.telemetry.events import (
    build_scaffold_create_event,
    capture_scaffold_create_terminal,
    classify_scaffold_create_exception,
)
from src.telemetry.reporter import TelemetryReporter
from src.telemetry.sink import InMemoryTelemetrySink
from src.telemetry.state import TelemetryStateStore
from src.utils.errors import (
    ExtensionError,
    KickstartError,
    ProjectCreationError,
    UnsupportedOptionError,
    UnsupportedProjectTypeError,
)


def _service_context() -> ScaffoldCreateContext:
    return ScaffoldCreateContext(
        project_type="service",
        language="ts",
        runtime="docker",
        cloud="private-cloud-value",
        framework=None,
        database="POSTGRES",
        cache="redis",
        auth="jwt",
        knowledge="private-knowledge-value",
        workspace_tooling="private-workspace-value",
        helm=True,
        github_requested=True,
        interactive=False,
    )


def test_service_event_canonicalizes_aliases_and_ignores_inapplicable_values() -> None:
    event = build_scaffold_create_event(
        _service_context(),
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        2.5,
        cli_version="0.4.3",
        platform_name="Darwin",
        architecture="aarch64",
    )

    assert event.properties.as_mapping() == {
        "architecture": "arm64",
        "auth": "jwt",
        "cache": "redis",
        "cli_version": "0.4.3",
        "cloud": "none",
        "database": "postgres",
        "duration_bucket": "1_to_5s",
        "error_category": "none",
        "framework": "none",
        "github_requested": True,
        "helm": True,
        "interactive": False,
        "knowledge": "none",
        "language": "typescript",
        "outcome": "success",
        "platform": "macos",
        "project_type": "service",
        "runtime": "container",
        "workspace_tooling": "none",
    }


def test_legacy_monorepo_event_uses_system_defaults() -> None:
    context = ScaffoldCreateContext(
        project_type="monorepo",
        language="private-language-value",
        runtime="k8s",
        cloud="google",
        framework="private-framework-value",
        database="private-database-value",
        cache="private-cache-value",
        auth="private-auth-value",
        knowledge="both",
        workspace_tooling=None,
        helm=False,
        github_requested=False,
        interactive=True,
    )

    properties = build_scaffold_create_event(
        context,
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        10,
        cli_version="0.4.3",
        platform_name="Linux",
        architecture="amd64",
    ).properties

    assert properties.project_type == "system"
    assert properties.language == "none"
    assert properties.runtime == "kubernetes"
    assert properties.cloud == "gcp"
    assert properties.knowledge == "both"
    assert properties.workspace_tooling == "bun-turbo"
    assert properties.framework == "none"
    assert properties.database == "none"
    assert properties.duration_bucket is TelemetryDurationBucket.FIVE_TO_THIRTY_SECONDS


def test_canonical_system_defaults_to_vendor_neutral_workspace() -> None:
    context = ScaffoldCreateContext(
        project_type="system",
        language="python",
        runtime=None,
        cloud="multi",
        framework=None,
        database=None,
        cache=None,
        auth=None,
        knowledge="none",
        workspace_tooling=None,
        helm=False,
        github_requested=False,
        interactive=False,
    )

    properties = build_scaffold_create_event(
        context,
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        0.5,
        cli_version="0.4.3",
        platform_name="Windows",
        architecture="unknown-cpu",
    ).properties

    assert properties.workspace_tooling == "none"
    assert properties.runtime == "kubernetes"
    assert properties.platform == "windows"
    assert properties.architecture == "other"


def test_unknown_inputs_are_reduced_to_fixed_values_without_raw_data() -> None:
    raw_values = {
        "private-project-type",
        "private-language",
        "private-runtime",
        "private-cloud",
        "private-framework",
        "private-database",
        "private-cache",
        "private-auth",
        "private-knowledge",
        "private-workspace",
    }
    context = ScaffoldCreateContext(
        project_type="private-project-type",
        language="private-language",
        runtime="private-runtime",
        cloud="private-cloud",
        framework="private-framework",
        database="private-database",
        cache="private-cache",
        auth="private-auth",
        knowledge="private-knowledge",
        workspace_tooling="private-workspace",
        helm=False,
        github_requested=False,
        interactive=False,
    )

    mapping = build_scaffold_create_event(
        context,
        ScaffoldCreateOutcome.INVALID_CONFIGURATION,
        ScaffoldCreateErrorCategory.INVALID_CONFIGURATION,
        30,
        cli_version="0.4.3",
        platform_name="private-platform",
        architecture="private-architecture",
    ).properties.as_mapping()

    assert mapping["project_type"] == "unknown"
    assert mapping["language"] == "unknown"
    assert mapping["platform"] == "other"
    assert mapping["architecture"] == "other"
    assert raw_values.isdisjoint(set(str(value) for value in mapping.values()))
    assert {"name", "root", "path", "error", "exception"}.isdisjoint(mapping)


@pytest.mark.parametrize(
    ("error", "outcome", "category"),
    [
        (
            UnsupportedProjectTypeError("private detail"),
            ScaffoldCreateOutcome.EXPECTED_ERROR,
            ScaffoldCreateErrorCategory.UNSUPPORTED_PROJECT_TYPE,
        ),
        (
            UnsupportedOptionError("private detail"),
            ScaffoldCreateOutcome.EXPECTED_ERROR,
            ScaffoldCreateErrorCategory.UNSUPPORTED_OPTION,
        ),
        (
            ExtensionError("private detail"),
            ScaffoldCreateOutcome.EXPECTED_ERROR,
            ScaffoldCreateErrorCategory.INVALID_CONFIGURATION,
        ),
        (
            ProjectCreationError("private detail"),
            ScaffoldCreateOutcome.EXPECTED_ERROR,
            ScaffoldCreateErrorCategory.PROJECT_CREATION_ERROR,
        ),
        (
            KickstartError("private detail"),
            ScaffoldCreateOutcome.EXPECTED_ERROR,
            ScaffoldCreateErrorCategory.EXPECTED_ERROR,
        ),
        (
            ValueError("private detail"),
            ScaffoldCreateOutcome.INVALID_CONFIGURATION,
            ScaffoldCreateErrorCategory.INVALID_CONFIGURATION,
        ),
        (
            RuntimeError("private detail"),
            ScaffoldCreateOutcome.UNEXPECTED_ERROR,
            ScaffoldCreateErrorCategory.UNEXPECTED_ERROR,
        ),
    ],
)
def test_exception_classification_never_uses_exception_text(
    error: Exception,
    outcome: ScaffoldCreateOutcome,
    category: ScaffoldCreateErrorCategory,
) -> None:
    assert classify_scaffold_create_exception(error) == (outcome, category)


@pytest.mark.parametrize(
    ("duration", "bucket"),
    [
        (0.999, TelemetryDurationBucket.UNDER_ONE_SECOND),
        (1.0, TelemetryDurationBucket.ONE_TO_FIVE_SECONDS),
        (5.0, TelemetryDurationBucket.FIVE_TO_THIRTY_SECONDS),
        (30.0, TelemetryDurationBucket.THIRTY_SECONDS_OR_MORE),
    ],
)
def test_duration_boundaries_use_coarse_buckets(duration: float, bucket: TelemetryDurationBucket) -> None:
    event = build_scaffold_create_event(
        _service_context(),
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        duration,
        cli_version="0.4.3",
        platform_name="Linux",
        architecture="x86_64",
    )

    assert event.properties.duration_bucket is bucket


def test_capture_helper_records_exactly_one_event_for_enabled_reporter(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    store.enable()
    sink = InMemoryTelemetrySink()
    reporter = TelemetryReporter(store, sink, {}, development=False)

    capture_scaffold_create_terminal(
        _service_context(),
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        0.25,
        cli_version="0.4.3",
        reporter=reporter,
    )

    assert len(sink.envelopes) == 1
    assert sink.envelopes[0].event.properties.outcome is ScaffoldCreateOutcome.SUCCESS


def test_capture_helper_contains_unexpected_reporter_failures() -> None:
    reporter = Mock(spec=TelemetryReporter)
    reporter.record.side_effect = RuntimeError("synthetic reporter failure")

    capture_scaffold_create_terminal(
        _service_context(),
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        0.25,
        cli_version="0.4.3",
        reporter=reporter,
    )

    reporter.record.assert_called_once()
