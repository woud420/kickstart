"""Execute the public docs' create examples against the repository CLI."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import pytest

from tests.integration.conftest import REPO_ROOT, KickstartRunner


def docs_create_commands() -> tuple[str, ...]:
    source = (REPO_ROOT / "website/src/docs/content.ts").read_text(encoding="utf-8")
    strings = (json.loads(match.group()) for match in re.finditer(r'"(?:[^"\\]|\\.)*"', source))
    commands = tuple(
        dict.fromkeys(
            line
            for value in strings
            for line in value.splitlines()
            if line.startswith("kickstart create ") and "--help" not in shlex.split(line)
        )
    )
    assert len(commands) >= 5, "expected examples for each project type"
    return commands


@pytest.mark.parametrize("command", docs_create_commands())
def test_documentation_create_example(command: str, kickstart_run: KickstartRunner, tmp_path: Path) -> None:
    args = shlex.split(command)[1:]
    if "--root" in args:
        index = args.index("--root")
        del args[index : index + 2]
    result = kickstart_run(*args, "--root", str(tmp_path), cwd=REPO_ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    project = tmp_path / args[2]
    for artifact in ("README.md", "AGENTS.md", ".kickstart/scaffold.json", "Makefile"):
        assert (project / artifact).is_file(), f"{command}: missing {artifact}"

    if "cloudflare-workers" in args and "typescript" in args:
        makefile = (project / "Makefile").read_text()
        assert "check: lint typecheck test" in makefile
        assert "dev:" in makefile
        worker = (project / "src/index.ts").read_text()
        assert 'url.pathname === "/healthz"' in worker
