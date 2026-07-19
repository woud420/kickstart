from pathlib import Path

import pytest

from src.telemetry.config import POSTHOG_US_CAPTURE_ENDPOINT, PostHogSettings, posthog_settings_from_environment


def test_environment_config_accepts_only_public_capture_token() -> None:
    settings = posthog_settings_from_environment(
        {
            "POSTHOG_PUBLIC_CUSTOMER_API_TOKEN": "phc_public_test_token",
            "POSTHOG_PROJECT_ID": "123456",
        }
    )

    assert settings is not None
    assert settings.project_token == "phc_public_test_token"
    assert settings.endpoint == POSTHOG_US_CAPTURE_ENDPOINT


def test_project_id_alone_does_not_configure_capture() -> None:
    assert posthog_settings_from_environment({"POSTHOG_PROJECT_ID": "123456"}) is None


def test_personal_api_key_is_rejected() -> None:
    assert posthog_settings_from_environment({"POSTHOG_PUBLIC_CUSTOMER_API_TOKEN": "phx_secret"}) is None


def test_empty_public_token_body_is_rejected() -> None:
    assert posthog_settings_from_environment({"POSTHOG_PUBLIC_CUSTOMER_API_TOKEN": "phc_"}) is None


def test_settings_repr_never_contains_project_token() -> None:
    settings = PostHogSettings("phc_do_not_print")

    assert "phc_do_not_print" not in repr(settings)


def test_configuration_never_auto_loads_cwd_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text("POSTHOG_PUBLIC_CUSTOMER_API_TOKEN=phc_untrusted_project_value\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert posthog_settings_from_environment({}) is None
