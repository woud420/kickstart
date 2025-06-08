from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1"}


@dataclass
class Component:
    type: str
    name: str
    lang: Optional[str] = None
    root: Optional[str] = None
    helm: bool = False


def parse(path: Path | str) -> List[Component]:
    """Parse a Markdown specification file into a list of Components."""
    lines = Path(path).read_text().splitlines()
    table_lines = [line.strip() for line in lines if line.strip().startswith("|") and line.strip().endswith("|")]
    if not table_lines:
        return []

    headers = [h.strip().lower() for h in table_lines[0].strip("|").split("|")]
    # skip header and separator line if present
    data_lines = [line for line in table_lines[1:] if not set(line.strip()) <= {"|", "-", " "}]

    components: List[Component] = []
    for line in data_lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        comp = Component(
            type=row.get("type", ""),
            name=row.get("name", ""),
            lang=row.get("lang") or None,
            root=row.get("root") or None,
            helm=_parse_bool(row.get("helm", "")),
        )
        components.append(comp)
    return components
