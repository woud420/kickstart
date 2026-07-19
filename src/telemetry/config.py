"""Runtime-only configuration for telemetry delivery."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from src.telemetry._build_config import EMBEDDED_POSTHOG_PROJECT_TOKEN


POSTHOG_PROJECT_TOKEN_ENV = "POSTHOG_PUBLIC_CUSTOMER_API_TOKEN"
POSTHOG_US_CAPTURE_ENDPOINT = "https://us.i.posthog.com/i/v0/e/"
POSTHOG_TIMEOUT_SECONDS = 2.0


@dataclass(frozen=True)
class PostHogSettings:
    """Validated PostHog delivery settings; the public token stays out of reprs."""

    project_token: str = field(repr=False)
    endpoint: str = POSTHOG_US_CAPTURE_ENDPOINT
    timeout_seconds: float = POSTHOG_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        if not self.project_token.startswith("phc_") or len(self.project_token) == len("phc_"):
            raise ValueError("PostHog capture requires a public phc_ project token")
        if self.timeout_seconds <= 0:
            raise ValueError("PostHog timeout must be positive")


def posthog_settings_from_configuration(
    environ: Mapping[str, str] | None = None,
    *,
    embedded_project_token: str = EMBEDDED_POSTHOG_PROJECT_TOKEN,
) -> PostHogSettings | None:
    """Resolve an explicit runtime override or the token embedded in release artifacts."""
    process_environment = os.environ if environ is None else environ
    runtime_project_token = process_environment.get(POSTHOG_PROJECT_TOKEN_ENV)
    project_token = embedded_project_token.strip() if runtime_project_token is None else runtime_project_token.strip()
    if not project_token.startswith("phc_") or len(project_token) == len("phc_"):
        return None
    return PostHogSettings(project_token=project_token)
