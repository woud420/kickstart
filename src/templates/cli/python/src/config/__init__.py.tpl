from __future__ import annotations

from src.clients import default_endpoint
from src.model.dto import CliConfig


def load_config() -> CliConfig:
    return CliConfig(endpoint=default_endpoint())
