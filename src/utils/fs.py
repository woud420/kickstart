from pathlib import Path
from typing import Any


def write_file(path: Path, template: Path | str, **vars: Any) -> None:
    if isinstance(template, Path):
        content = template.read_text()
    else:
        content = template

    for key, value in vars.items():
        content = content.replace(f"{{{{{key.upper()}}}}}", str(value))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

