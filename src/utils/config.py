import toml
from pathlib import Path
from typing import cast

from src.utils.types import ConfigValue


def load_config() -> dict[str, ConfigValue]:
    config: dict[str, ConfigValue] = {}
    paths = [
        Path.cwd() / ".kickstart.toml",
        Path.home() / ".kickstartrc",
        Path.home() / ".config/kickstart/config.toml"
    ]
    for path in paths:
        if path.exists():
            config.update(cast(dict[str, ConfigValue], toml.load(path)))
    return config
