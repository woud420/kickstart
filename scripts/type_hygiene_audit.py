"""Audit loose type annotations in source and active generated templates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from template_wiring_audit import TEMPLATE_ROOT, _active_templates, _referenced_templates, _template_files


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = ("src", "scripts", "tests")
ANY_NAME = "A" "ny"
LOOSE_PYTHON_TYPE_PATTERN = re.compile(
    rf"\b{ANY_NAME}\b"
    rf"|\bDict\s*\[\s*str\s*,\s*{ANY_NAME}\s*\]"
    rf"|\bdict\s*\[\s*str\s*,\s*object\s*\]"
    rf"|\bMapping\s*\[\s*str\s*,\s*object\s*\]"
    rf"|\bCallable\s*\[[^\n]*\b{ANY_NAME}\b"
)
LOOSE_TEMPLATE_TYPE_PATTERN = re.compile(
    LOOSE_PYTHON_TYPE_PATTERN.pattern
    + r"|\bRecord\s*<\s*string\s*,\s*any\s*>"
    + r"|:\s*any\b"
)


@dataclass(frozen=True)
class TypeHygieneIssue:
    """One loose type annotation match."""

    path: Path
    line_number: int
    line: str

    def render(self) -> str:
        """Return a compact command-line issue string."""
        relative_path = self.path.relative_to(REPO_ROOT)
        return f"{relative_path}:{self.line_number}: {self.line.strip()}"


def main() -> int:
    """Run the type hygiene audit."""
    source_files = _python_source_files()
    active_templates = _active_template_files()
    issues = (
        *_scan_files(source_files, LOOSE_PYTHON_TYPE_PATTERN),
        *_scan_files(active_templates, LOOSE_TEMPLATE_TYPE_PATTERN),
    )

    print(f"type hygiene source files: {len(source_files)}")
    print(f"type hygiene active templates: {len(active_templates)}")
    print(f"type hygiene issues: {len(issues)}")
    for issue in issues:
        print(issue.render())

    return 1 if issues else 0


def _python_source_files() -> tuple[Path, ...]:
    """Return Python source, script, and test files checked by the hygiene audit."""
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
    return tuple(sorted(files))


def _active_template_files() -> tuple[Path, ...]:
    """Return template files that are wired into active scaffold output."""
    active = _active_templates()
    active.update(_referenced_templates(active))
    template_files = _template_files()
    return tuple(sorted(TEMPLATE_ROOT / path for path in active & template_files))


def _scan_files(files: tuple[Path, ...], pattern: re.Pattern[str]) -> tuple[TypeHygieneIssue, ...]:
    """Return all loose type matches for the given files."""
    issues: list[TypeHygieneIssue] = []
    for path in files:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if pattern.search(line):
                issues.append(TypeHygieneIssue(path=path, line_number=line_number, line=line))
    return tuple(issues)


if __name__ == "__main__":
    raise SystemExit(main())
