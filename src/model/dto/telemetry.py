"""Provider-neutral telemetry data-transfer objects."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TypeAlias, TypedDict
from uuid import UUID


TELEMETRY_STATE_SCHEMA_VERSION = 1
TelemetryPropertyValue: TypeAlias = str | int | float | bool


class TelemetryConsent(StrEnum):
    """The user's persisted telemetry preference."""

    UNSET = "unset"
    ENABLED = "enabled"
    DISABLED = "disabled"


class TelemetryEventName(StrEnum):
    """Closed event-name allowlist for the initial telemetry contract."""

    SCAFFOLD_CREATE_COMPLETED = "scaffold_create_completed"


class ScaffoldCreateOutcome(StrEnum):
    """Closed terminal outcomes for a create invocation."""

    SUCCESS = "success"
    CANCELLED = "cancelled"
    INPUT_ENDED = "input_ended"
    EXPECTED_ERROR = "expected_error"
    INVALID_CONFIGURATION = "invalid_configuration"
    UNEXPECTED_ERROR = "unexpected_error"


class ScaffoldCreateErrorCategory(StrEnum):
    """Coarse error categories that never contain raw exception data."""

    NONE = "none"
    INTERRUPTED = "interrupted"
    INPUT_ENDED = "input_ended"
    UNSUPPORTED_PROJECT_TYPE = "unsupported_project_type"
    UNSUPPORTED_OPTION = "unsupported_option"
    PROJECT_CREATION_ERROR = "project_creation_error"
    INVALID_CONFIGURATION = "invalid_configuration"
    EXPECTED_ERROR = "expected_error"
    UNEXPECTED_ERROR = "unexpected_error"


class TelemetryDurationBucket(StrEnum):
    """Fixed duration buckets rather than identifying precise timings."""

    UNDER_ONE_SECOND = "under_1s"
    ONE_TO_FIVE_SECONDS = "1_to_5s"
    FIVE_TO_THIRTY_SECONDS = "5_to_30s"
    THIRTY_SECONDS_OR_MORE = "30s_or_more"


class TelemetrySuppressionReason(StrEnum):
    """Why telemetry is not effective for the current process."""

    ENABLED = "enabled"
    NOT_OPTED_IN = "not_opted_in"
    USER_DISABLED = "user_disabled"
    DO_NOT_TRACK = "do_not_track"
    ENVIRONMENT_DISABLED = "environment_disabled"
    CI = "ci"
    TEST = "test"
    DEVELOPMENT = "development"
    EVALUATION = "evaluation"
    INVALID_STATE = "invalid_state"


@dataclass(frozen=True)
class ScaffoldCreateProperties:
    """Closed property DTO for the initial scaffold completion event."""

    cli_version: str
    project_type: str
    language: str
    runtime: str
    cloud: str
    framework: str
    database: str
    cache: str
    auth: str
    knowledge: str
    workspace_tooling: str
    helm: bool
    github_requested: bool
    interactive: bool
    outcome: ScaffoldCreateOutcome
    error_category: ScaffoldCreateErrorCategory
    duration_bucket: TelemetryDurationBucket
    platform: str
    architecture: str

    def as_mapping(self) -> dict[str, TelemetryPropertyValue]:
        """Return the exact provider-neutral property allowlist."""
        return {
            "architecture": self.architecture,
            "auth": self.auth,
            "cache": self.cache,
            "cli_version": self.cli_version,
            "cloud": self.cloud,
            "database": self.database,
            "duration_bucket": self.duration_bucket.value,
            "error_category": self.error_category.value,
            "framework": self.framework,
            "github_requested": self.github_requested,
            "helm": self.helm,
            "interactive": self.interactive,
            "knowledge": self.knowledge,
            "language": self.language,
            "outcome": self.outcome.value,
            "platform": self.platform,
            "project_type": self.project_type,
            "runtime": self.runtime,
            "workspace_tooling": self.workspace_tooling,
        }


@dataclass(frozen=True)
class ScaffoldCreateContext:
    """Safe create inputs retained for terminal event normalization.

    Project names and roots are intentionally absent from this DTO.
    """

    project_type: str | None
    language: str
    runtime: str | None
    cloud: str
    framework: str | None
    database: str | None
    cache: str | None
    auth: str | None
    knowledge: str
    workspace_tooling: str | None
    helm: bool
    github_requested: bool
    interactive: bool


@dataclass(frozen=True)
class TelemetryEvent:
    """A typed product event before identity and delivery metadata are added."""

    name: TelemetryEventName
    properties: ScaffoldCreateProperties


@dataclass(frozen=True)
class TelemetryEnvelope:
    """The vendor-neutral envelope delivered to a telemetry sink."""

    event_id: UUID
    anonymous_id: UUID
    occurred_at: datetime
    event: TelemetryEvent


@dataclass(frozen=True)
class TelemetryState:
    """Versioned user consent and pseudonymous identity state."""

    consent: TelemetryConsent = TelemetryConsent.UNSET
    anonymous_id: UUID | None = None
    schema_version: int = TELEMETRY_STATE_SCHEMA_VERSION


class TelemetryStateDocument(TypedDict, total=False):
    """JSON representation persisted in the user configuration directory."""

    schema_version: int
    consent: str
    anonymous_id: str


@dataclass(frozen=True)
class EffectiveTelemetry:
    """The current process-level telemetry decision."""

    enabled: bool
    reason: TelemetrySuppressionReason
    anonymous_id: UUID | None


@dataclass(frozen=True)
class TelemetryIdentityReset:
    """The result of an explicit identity rotation request."""

    previous_id: UUID | None
    current_id: UUID | None
