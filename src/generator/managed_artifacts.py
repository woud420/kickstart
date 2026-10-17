"""Approved managed markdown targets shared by generation and read-only checks."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ManagedArtifact:
    id: str
    target: str
    comparison: Literal["content", "presence"] = "content"


MANAGED_DOCS = (
    ManagedArtifact("agent-map", "AGENTS.md"),
    ManagedArtifact("claude-pointer", "CLAUDE.md"),
    ManagedArtifact("agents-skills-readme", ".agents/skills/README.md"),
    ManagedArtifact("contracts-readme", "docs/contracts/README.md"),
    ManagedArtifact("operations-readme", "docs/operations/README.md"),
    ManagedArtifact("decisions-readme", "docs/decisions/README.md"),
)
ARCHITECTURE_ARTIFACT = ManagedArtifact("architecture-readme", "docs/architecture/README.md", "presence")
ALL_MANAGED_DOCS = (*MANAGED_DOCS, ARCHITECTURE_ARTIFACT)
WORKFLOW_PATTERN = r"^\.github/workflows/[A-Za-z0-9_.-]+\.(?:yml|yaml)$"
OWNERSHIP_PATH_PATTERN = r"^(?!\.{1,2}(?:/|$))(?!.*\/\.{1,2}(?:/|$))[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$"
