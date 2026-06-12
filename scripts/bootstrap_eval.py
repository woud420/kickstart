"""Bootstrap eval: kickstart must be able to bootstrap a kickstart-like project.

The dogfood standard for the generator: scaffold a project shaped like
kickstart itself (a typed, modular CLI with docs, tests, and canonical Make
verbs) and prove three things about the result, with no manual fixes:

1. generation succeeds,
2. the generated source honors the project taste rules — bounded file
   length, strict typing with no loose escape-hatch annotations, and
   specific errors instead of blanket ``Exception``/``unwrap()``,
3. the project goes green on its own ``make check`` in a fresh tree.

Like the other evals this validates generated output, writes reports to
scratch paths, and is meant for local design iteration, not release CI.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from scripts.generated_make_test_eval import eval_environment


class BootstrapEvalError(Exception):
    """Base error for bootstrap eval harness misuse."""


class UnknownCaseError(BootstrapEvalError):
    """Raised when a requested case slug does not exist."""

    def __init__(self, slug: str, known: tuple[str, ...]) -> None:
        super().__init__(f"unknown case '{slug}'; known cases: {', '.join(known)}")


SOURCE_SUFFIXES = (".py", ".rs", ".ts")
SKIP_DIR_PARTS = frozenset({".venv", ".cache", "node_modules", "target", ".git", "__pycache__"})

# Split so the repo's own type-hygiene audit does not flag this file for
# naming the loose type it forbids (same idiom as type_hygiene_audit.py).
ANY_NAME = "A" "ny"


@dataclass(frozen=True)
class TasteRule:
    """One forbidden-pattern rule applied to generated source files."""

    name: str
    suffix: str
    pattern: re.Pattern[str]
    explanation: str


TASTE_RULES: tuple[TasteRule, ...] = (
    TasteRule(
        name="python-no-any",
        suffix=".py",
        pattern=re.compile(rf"(?:^|[^.\w]){ANY_NAME}\b(?!\w)|\bimport\s+{ANY_NAME}\b"),
        explanation=f"Python sources must use precise types instead of typing.{ANY_NAME}",
    ),
    TasteRule(
        name="python-no-object-type",
        suffix=".py",
        pattern=re.compile(r":\s*object\b|->\s*object\b|\[\s*object\s*\]"),
        explanation="Python annotations must not fall back to object",
    ),
    TasteRule(
        name="python-specific-errors",
        suffix=".py",
        pattern=re.compile(r"raise\s+Exception\(|except\s+Exception\b|raise\s+BaseException\b"),
        explanation="Python errors must be specific exception types",
    ),
    TasteRule(
        name="python-no-suppressions",
        suffix=".py",
        pattern=re.compile(r"#\s*type:\s*ignore"),
        explanation="Python sources must fix types instead of suppressing the checker",
    ),
    TasteRule(
        name="typescript-no-any",
        suffix=".ts",
        pattern=re.compile(r":\s*any\b|as\s+any\b|<any>|:\s*Object\b"),
        explanation="TypeScript sources must not use any or Object",
    ),
    TasteRule(
        name="typescript-no-suppressions",
        suffix=".ts",
        pattern=re.compile(r"@ts-ignore|@ts-expect-error"),
        explanation="TypeScript sources must fix types instead of suppressing the checker",
    ),
    TasteRule(
        name="rust-no-panic-paths",
        suffix=".rs",
        pattern=re.compile(r"\.unwrap\(\)|\.expect\(|panic!\("),
        explanation="Rust non-test sources must surface specific errors instead of panicking",
    ),
)


@dataclass(frozen=True)
class Violation:
    """One taste violation found in a generated file."""

    rule: str
    file: str
    line: int
    detail: str


@dataclass(frozen=True)
class BootstrapCase:
    """One scaffold to bootstrap and validate."""

    slug: str
    args: tuple[str, ...]


DEFAULT_CASES: tuple[BootstrapCase, ...] = (
    BootstrapCase(slug="python-cli-kickstart-like", args=("create", "cli", "kickstart-clone", "--lang", "python")),
    BootstrapCase(slug="python-lib", args=("create", "lib", "shared-models", "--lang", "python")),
    BootstrapCase(
        slug="python-service",
        args=("create", "service", "api", "--lang", "python", "--database", "postgres"),
    ),
    BootstrapCase(
        slug="typescript-worker",
        args=("create", "service", "edge", "--lang", "typescript", "--runtime", "cloudflare-workers"),
    ),
    BootstrapCase(slug="rust-cli", args=("create", "cli", "ops-tool", "--lang", "rust")),
)


@dataclass(frozen=True)
class CaseResult:
    """Outcome of one bootstrap case."""

    case: BootstrapCase
    generated: bool
    violations: tuple[Violation, ...]
    check_passed: bool
    check_seconds: float
    failure_detail: str

    @property
    def passed(self) -> bool:
        return self.generated and not self.violations and self.check_passed


def is_test_path(path: Path) -> bool:
    """True when a file lives under a tests directory or is a test module."""
    return any(part in {"tests", "test"} for part in path.parts) or path.name.startswith("test_")


def source_files(root: Path) -> tuple[Path, ...]:
    """Generated source files eligible for taste rules, caches excluded."""
    files = (
        path
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and path.suffix in SOURCE_SUFFIXES
        and not SKIP_DIR_PARTS.intersection(path.relative_to(root).parts)
    )
    return tuple(files)


def audit_file(path: Path, root: Path, max_lines: int) -> tuple[Violation, ...]:
    """Apply the line-length cap and taste rules to one source file."""
    relative = str(path.relative_to(root))
    lines = path.read_text(encoding="utf-8").splitlines()
    violations: list[Violation] = []

    if len(lines) > max_lines:
        violations.append(
            Violation(
                rule="max-file-lines",
                file=relative,
                line=len(lines),
                detail=f"{len(lines)} lines exceeds the {max_lines}-line cap; split the module",
            )
        )

    rules = tuple(rule for rule in TASTE_RULES if rule.suffix == path.suffix)
    skip_pattern_rules = path.suffix == ".rs" and is_test_path(path.relative_to(root))
    if skip_pattern_rules:
        return tuple(violations)

    for number, line in enumerate(lines, start=1):
        for rule in rules:
            if rule.pattern.search(line):
                violations.append(
                    Violation(rule=rule.name, file=relative, line=number, detail=rule.explanation)
                )
    return tuple(violations)


def audit_tree(root: Path, max_lines: int) -> tuple[Violation, ...]:
    """Audit every eligible source file under a generated project."""
    found: list[Violation] = []
    for path in source_files(root):
        found.extend(audit_file(path, root, max_lines))
    return tuple(found)


def generate_case(case: BootstrapCase, root: Path, repo_root: Path) -> subprocess.CompletedProcess[str]:
    """Generate one scaffold via the CLI module, mirroring agent usage."""
    command = (sys.executable, "-m", "src.cli.main", *case.args, "--root", str(root))
    return subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)


def run_make_check(project: Path, env: dict[str, str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    """Run the generated project's own canonical verification verb."""
    return subprocess.run(
        ("make", "check"),
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )


def run_case(
    case: BootstrapCase,
    output_root: Path,
    repo_root: Path,
    env: dict[str, str],
    max_lines: int,
    timeout_seconds: int,
) -> CaseResult:
    """Generate, audit, and verify one case."""
    case_root = output_root / case.slug
    if case_root.exists():
        shutil.rmtree(case_root)
    case_root.mkdir(parents=True)

    generated = generate_case(case, case_root, repo_root)
    if generated.returncode != 0:
        detail = (generated.stdout + generated.stderr).strip()[-800:]
        return CaseResult(case, False, (), False, 0.0, f"generation failed: {detail}")

    project_dirs = [path for path in case_root.iterdir() if path.is_dir()]
    project = project_dirs[0]
    violations = audit_tree(project, max_lines)

    started = time.monotonic()
    try:
        checked = run_make_check(project, env, timeout_seconds)
    except subprocess.TimeoutExpired:
        return CaseResult(case, True, violations, False, timeout_seconds, "make check timed out")
    elapsed = time.monotonic() - started

    if checked.returncode != 0:
        detail = (checked.stdout + checked.stderr).strip()[-800:]
        return CaseResult(case, True, violations, False, elapsed, f"make check failed: {detail}")

    return CaseResult(case, True, violations, True, elapsed, "")


def render_report(results: tuple[CaseResult, ...], max_lines: int) -> str:
    """Render a markdown report for the bootstrap run."""
    lines = [
        "# kickstart bootstrap eval",
        "",
        "Generate a kickstart-like project, audit taste rules "
        f"(<= {max_lines} lines/file, no loose types, specific errors), and run its own `make check`.",
        "",
        "| case | generated | taste violations | make check | seconds |",
        "| --- | --- | ---: | --- | ---: |",
    ]
    for result in results:
        lines.append(
            f"| {result.case.slug} | {'yes' if result.generated else 'NO'} | {len(result.violations)} "
            f"| {'green' if result.check_passed else 'RED'} | {result.check_seconds:.1f} |"
        )
    lines.append("")
    for result in results:
        for violation in result.violations:
            lines.append(f"- {result.case.slug}: {violation.rule} {violation.file}:{violation.line} — {violation.detail}")
        if result.failure_detail:
            lines.append(f"- {result.case.slug}: {result.failure_detail}")
    return "\n".join(lines) + "\n"


def select_cases(requested: tuple[str, ...]) -> tuple[BootstrapCase, ...]:
    """Resolve --cases slugs, failing loudly on unknown names."""
    if not requested:
        return DEFAULT_CASES
    by_slug = {case.slug: case for case in DEFAULT_CASES}
    missing = tuple(slug for slug in requested if slug not in by_slug)
    if missing:
        raise UnknownCaseError(missing[0], tuple(by_slug))
    return tuple(by_slug[slug] for slug in requested)


def main() -> int:
    """Run the bootstrap eval from the command line."""
    parser = argparse.ArgumentParser(description="Bootstrap and verify kickstart-like projects.")
    parser.add_argument("--output-root", type=Path, default=Path("/private/tmp/kickstart-bootstrap-eval"))
    parser.add_argument("--cache-root", type=Path, default=Path("/private/tmp/kickstart-eval-cache"))
    parser.add_argument("--report", type=Path, default=Path("/private/tmp/kickstart-bootstrap-eval.md"))
    parser.add_argument("--max-file-lines", type=int, default=200)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--cases", nargs="*", default=[], help="Case slugs to run (default: all)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    args.output_root.mkdir(parents=True, exist_ok=True)
    env = eval_environment("cached", args.cache_root)

    cases = select_cases(tuple(args.cases))
    results = tuple(
        run_case(case, args.output_root, repo_root, env, args.max_file_lines, args.timeout_seconds)
        for case in cases
    )

    report = render_report(results, args.max_file_lines)
    args.report.write_text(report, encoding="utf-8")
    print(report)
    print(f"Report written to {args.report}", file=sys.stderr)
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
