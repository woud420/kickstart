import toml
from pathlib import Path

def load_config():
    config = {}
    paths = [
        Path.cwd() / ".kickstart.toml",
        Path.home() / ".kickstartrc",
        Path.home() / ".config/kickstart/config.toml"
    ]
    for path in paths:
        if path.exists():
            config.update(toml.load(path))
    return config
