from __future__ import annotations

from src.config import load_config
from src.operations import check
from src.output import write_line


def check_command() -> None:
    result = check(load_config())
    write_line(f"{result.status}: {result.endpoint}")
