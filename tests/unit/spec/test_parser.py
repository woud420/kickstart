from pathlib import Path
from src.spec.parser import parse, Component


def test_parse_markdown_table(tmp_path: Path):
    md = tmp_path / "spec.md"
    md.write_text(
        """
| type | name | lang | root | helm |
| ---- | ---- | ---- | ---- | ---- |
| service | auth | python | services | true |
| lib | utils | rust | libs | false |
| frontend | web | react | apps | |
"""
    )
    comps = parse(md)
    assert comps == [
        Component(type="service", name="auth", lang="python", root="services", helm=True),
        Component(type="lib", name="utils", lang="rust", root="libs", helm=False),
        Component(type="frontend", name="web", lang="react", root="apps", helm=False),
    ]


def test_parse_no_table(tmp_path: Path):
    md = tmp_path / "empty.md"
    md.write_text("# Nothing here")
    assert parse(md) == []
