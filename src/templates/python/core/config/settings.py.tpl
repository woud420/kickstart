"""Runtime settings for {{ service_name }}."""

from functools import lru_cache
{% if database|default('') == 'sqlite' %}
from pathlib import Path
{% endif %}

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "{{ service_name }}"
    environment: str = "local"
    host: str = "0.0.0.0"
    port: int = 8000
{% if database|default('') == 'sqlite' %}
    sqlite_path: Path = Path("data/app.sqlite3")
{% endif %}


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
