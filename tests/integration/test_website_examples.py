"""The website's command examples must match real generator output.

`website/src/site/content.ts` shows each example command next to the file
tree it claims to generate. Those lists are curated by hand, so this test
regenerates every example and verifies each advertised path really exists —
the website cannot drift from the generator without failing CI.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

from tests.integration.conftest import REPO_ROOT, KickstartRunner

CONTENT_PATH = REPO_ROOT / "website" / "src" / "site" / "content.ts"
EXAMPLE_PATTERN = re.compile(r'command:\s*"([^"]+)",.*?output:\s*\[(.*?)\]', re.DOTALL)
OUTPUT_ENTRY_PATTERN = re.compile(r'"([^"]+)"')


def website_examples() -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Parse (command, advertised output paths) pairs from the website content."""
    source = CONTENT_PATH.read_text(encoding="utf-8")
    examples = tuple(
        (command, tuple(OUTPUT_ENTRY_PATTERN.findall(block)))
        for command, block in EXAMPLE_PATTERN.findall(source)
    )
    assert examples, f"no command examples parsed from {CONTENT_PATH}"
    command_count = len(re.findall(r'command:\s*"', source))
    assert len(examples) == command_count, (
        f"parsed {len(examples)} command/output pairs but found {command_count} command literals; "
        "the regex mis-paired an example - keep command and output adjacent per entry"
    )
    return examples


@pytest.mark.parametrize(
    ("command", "advertised"),
    website_examples(),
    ids=[shlex.split(command)[2] for command, _ in website_examples()],
)
def test_website_example_output_matches_generation(
    command: str,
    advertised: tuple[str, ...],
    kickstart_run: KickstartRunner,
    tmp_path: Path,
) -> None:
    args = shlex.split(command)
    assert args[0] == "kickstart", f"unexpected example command: {command}"

    completed = kickstart_run(*args[1:], "--root", str(tmp_path), cwd=REPO_ROOT, capture_output=True, text=True)
    assert completed.returncode == 0, f"example generation failed: {completed.stdout}{completed.stderr}"

    project_dirs = [path for path in tmp_path.iterdir() if path.is_dir()]
    assert len(project_dirs) == 1
    project = project_dirs[0]

    missing = [
        entry
        for entry in advertised
        if not ((project / entry).is_dir() if entry.endswith("/") else (project / entry).is_file())
    ]
    assert missing == [], f"website advertises paths the generator does not produce: {missing}"
