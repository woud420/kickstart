"""Audit import provenance for the split error model.

Exception classes live in `src.utils.errors`; `src.utils.error_handling`
owns only the handling API (decorators, ErrorCollector, safe_* helpers).
Because error_handling re-imports a few classes for its own use, importing
an error class from it half-works: some names resolve, others raise
ImportError only at import time. PR #81 merged green with exactly that
mixed import and broke master. This audit turns the mistake into a lint
failure: any name ending in ``Error`` imported from
``src.utils.error_handling`` is flagged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = ("src", "scripts", "ci", "tests")

# Matches single-line and parenthesized multi-line import statements.
IMPORT_STATEMENT_PATTERN = re.compile(
    r"from\s+src\.utils\.error_handling\s+import\s+(\([^)]*\)|[^\n]*)",
    re.MULTILINE,
)
ERROR_NAME_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*Error)\b")


@dataclass(frozen=True)
class ImportHygieneIssue:
    """One error-class import from the wrong module."""

    path: Path
    line_number: int
    name: str

    def render(self) -> str:
        """Return a compact command-line issue string."""
        relative_path = self.path.relative_to(REPO_ROOT)
        return (
            f"{relative_path}:{self.line_number}: imports {self.name} from"
            " src.utils.error_handling — error classes live in src.utils.errors"
        )


def main() -> int:
    """Run the import hygiene audit."""
    source_files = _python_source_files()
    issues = _scan_files(source_files)

    print(f"import hygiene source files: {len(source_files)}")
    print(f"import hygiene issues: {len(issues)}")
    for issue in issues:
        print(issue.render())

    return 1 if issues else 0


def _python_source_files() -> tuple[Path, ...]:
    """Return Python source, script, CI, and test files to audit."""
    files: list[Path] = []
    for root_name in SOURCE_ROOTS:
        root = REPO_ROOT / root_name
        if not root.exists():
            continue
        files.extend(
            path
            for path in root.rglob("*.py")
            if "__pycache__" not in path.parts and not path.name.endswith(".tpl")
        )
    return tuple(sorted(path for path in files if path.name != "import_hygiene_audit.py"))


def find_issues(source: str, path: Path) -> tuple[ImportHygieneIssue, ...]:
    """Return every error-class name imported from error_handling in ``source``."""
    issues: list[ImportHygieneIssue] = []
    for match in IMPORT_STATEMENT_PATTERN.finditer(source):
        line_number = source.count("\n", 0, match.start()) + 1
        for name_match in ERROR_NAME_PATTERN.finditer(match.group(1)):
            issues.append(
                ImportHygieneIssue(path=path, line_number=line_number, name=name_match.group(1))
            )
    return tuple(issues)


def _scan_files(files: tuple[Path, ...]) -> tuple[ImportHygieneIssue, ...]:
    """Return all wrong-module error imports for the given files."""
    issues: list[ImportHygieneIssue] = []
    for path in files:
        issues.extend(find_issues(path.read_text(encoding="utf-8"), path))
    return tuple(issues)


if __name__ == "__main__":
    raise SystemExit(main())
