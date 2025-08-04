import toml
from pathlib import Path
from typing import Any


def load_config() -> dict[str, Any]:
    config: dict[str, Any] = {}
    paths = [
        Path.cwd() / ".kickstart.toml",
        Path.home() / ".kickstartrc",
        Path.home() / ".config/kickstart/config.toml"
    ]
    for path in paths:
        if path.exists():
            config.update(toml.load(path))
    return config
