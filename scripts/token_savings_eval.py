"""Measure how many output tokens a scaffold saves an agent.

kickstart's pitch includes minimizing the tokens an agent spends bootstrapping
a project: one short `kickstart create` command replaces authoring starter
files by hand. This eval makes that claim measurable and keeps it honest:

- The headline ratio is an explicit **upper bound**: it assumes the agent
  would otherwise retype kickstart's entire output. Real savings are lower
  because an agent asked for a minimal project would write fewer files.
- Output is split into app code versus scaffold metadata (manifest, agent
  map, docs skeleton, CI) so the app-code-only ratio is visible too.
- The command-token denominator covers only the command string, not skill
  or tool-call overhead; treat ratios as comparative, not absolute.

Like the other evals, this validates generated output rather than generator
internals, writes reports to scratch paths, and is meant for local design
evals, not release CI.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


# Rough heuristic for code-heavy text: ~4 bytes per token. The exact tokenizer
# varies by model; the eval reports bytes alongside tokens so the raw data
# stays model-agnostic.
BYTES_PER_TOKEN = 4

# Paths that are kickstart's scaffold bookkeeping rather than app code an
# agent would have authored anyway when asked for a working project.
METADATA_PREFIXES = (".kickstart", ".github", "docs")
METADATA_NAMES = frozenset({"AGENTS.md"})


def is_scaffold_metadata(relative: Path) -> bool:
    """True when a generated path is scaffold bookkeeping, not app code."""
    return relative.parts[0] in METADATA_PREFIXES or relative.name in METADATA_NAMES


@dataclass(frozen=True)
class ScaffoldCase:
    """One representative scaffold command to measure."""

    slug: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class CaseResult:
    """Token accounting for one generated scaffold."""

    case: ScaffoldCase
    command_text: str
    file_count: int
    content_bytes: int
    app_code_bytes: int

    @property
    def command_tokens(self) -> int:
        return estimate_tokens(self.command_text)

    @property
    def output_tokens(self) -> int:
        return max(1, round(self.content_bytes / BYTES_PER_TOKEN))

    @property
    def app_code_tokens(self) -> int:
        return max(1, round(self.app_code_bytes / BYTES_PER_TOKEN))

    @property
    def savings_ratio(self) -> float:
        return self.output_tokens / self.command_tokens

    @property
    def app_code_ratio(self) -> float:
        return self.app_code_tokens / self.command_tokens


DEFAULT_CASES: tuple[ScaffoldCase, ...] = (
    ScaffoldCase(
        slug="python-service-full",
        args=(
            "create",
            "service",
            "api",
            "--lang",
            "python",
            "--database",
            "postgres",
            "--cache",
            "redis",
            "--auth",
            "jwt",
        ),
    ),
    ScaffoldCase(
        slug="typescript-worker",
        args=("create", "service", "edge-site", "--lang", "typescript", "--runtime", "cloudflare-workers"),
    ),
    ScaffoldCase(
        slug="rust-cli",
        args=("create", "cli", "ops-tool", "--lang", "rust"),
    ),
    ScaffoldCase(
        slug="python-lib",
        args=("create", "lib", "shared-models", "--lang", "python"),
    ),
    ScaffoldCase(
        slug="aws-kubernetes-system",
        args=(
            "create",
            "system",
            "platform",
            "--cloud",
            "aws",
            "--runtime",
            "kubernetes",
            "--knowledge",
            "none",
        ),
    ),
)


def estimate_tokens(text: str) -> int:
    """Estimate tokens for a piece of text using the bytes-per-token heuristic."""
    return max(1, round(len(text.encode("utf-8")) / BYTES_PER_TOKEN))


def is_text_file(path: Path) -> bool:
    """Treat a file as text when it decodes as UTF-8 and has no NUL bytes."""
    try:
        raw = path.read_bytes()
    except OSError:
        return False

    if b"\x00" in raw:
        return False

    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return False

    return True


def measure_tree(root: Path) -> tuple[int, int, int]:
    """Return (text files, total UTF-8 bytes, app-code bytes) under a directory."""
    file_count = 0
    content_bytes = 0
    app_code_bytes = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not is_text_file(path):
            continue
        size = len(path.read_bytes())
        file_count += 1
        content_bytes += size
        if not is_scaffold_metadata(path.relative_to(root)):
            app_code_bytes += size
    return file_count, content_bytes, app_code_bytes


def scaffold_command(case: ScaffoldCase, root: Path) -> tuple[str, ...]:
    """Build the generation command for one case."""
    return (sys.executable, "-m", "src.cli.main", *case.args, "--root", str(root))


def user_facing_command(case: ScaffoldCase) -> str:
    """The command text an agent would emit when using the installed binary."""
    return " ".join(("kickstart", *case.args))


def run_case(case: ScaffoldCase, output_root: Path, repo_root: Path) -> CaseResult:
    """Generate one scaffold and measure its content."""
    case_root = output_root / case.slug
    if case_root.exists():
        shutil.rmtree(case_root)
    case_root.mkdir(parents=True)

    completed = subprocess.run(
        scaffold_command(case, case_root),
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"{case.slug} generation failed:\n{completed.stdout}\n{completed.stderr}")

    project_dirs = [path for path in case_root.iterdir() if path.is_dir()]
    if len(project_dirs) != 1:
        raise RuntimeError(f"{case.slug}: expected exactly one generated directory, got {len(project_dirs)}")

    file_count, content_bytes, app_code_bytes = measure_tree(project_dirs[0])
    return CaseResult(
        case=case,
        command_text=user_facing_command(case),
        file_count=file_count,
        content_bytes=content_bytes,
        app_code_bytes=app_code_bytes,
    )


def render_report(results: tuple[CaseResult, ...]) -> str:
    """Render a markdown report for the measured cases."""
    lines = [
        "# kickstart token savings eval",
        "",
        f"Token estimate heuristic: ~{BYTES_PER_TOKEN} UTF-8 bytes per token for code-heavy text.",
        "The full-output ratio is an upper bound: it assumes retyping every generated file.",
        "The app-code ratio excludes scaffold metadata (manifest, agent map, docs skeleton, CI)",
        "and better approximates savings for a minimal hand-written equivalent.",
        "",
        "| scaffold | files | output tokens | app-code tokens | command tokens | full ratio (upper bound) | app-code ratio |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            f"| {result.case.slug} | {result.file_count} | {result.output_tokens} | {result.app_code_tokens} "
            f"| {result.command_tokens} | {result.savings_ratio:,.0f}x | {result.app_code_ratio:,.0f}x |"
        )

    total_output = sum(result.output_tokens for result in results)
    total_app = sum(result.app_code_tokens for result in results)
    total_command = sum(result.command_tokens for result in results)
    lines.extend(
        [
            f"| total | | {total_output} | {total_app} | {total_command} "
            f"| {total_output / total_command:,.0f}x | {total_app / total_command:,.0f}x |",
            "",
        ]
    )
    return "\n".join(lines)


def results_as_json(results: tuple[CaseResult, ...]) -> str:
    """Render machine-readable results."""
    payload = [
        {
            "slug": result.case.slug,
            "command": result.command_text,
            "files": result.file_count,
            "content_bytes": result.content_bytes,
            "app_code_bytes": result.app_code_bytes,
            "output_tokens_estimate": result.output_tokens,
            "app_code_tokens_estimate": result.app_code_tokens,
            "command_tokens_estimate": result.command_tokens,
            "full_ratio_upper_bound": round(result.savings_ratio, 1),
            "app_code_ratio": round(result.app_code_ratio, 1),
        }
        for result in results
    ]
    return json.dumps(payload, indent=2)


def main() -> int:
    """Run the token savings eval from the command line."""
    parser = argparse.ArgumentParser(description="Measure agent token savings per kickstart scaffold.")
    scratch = Path(tempfile.gettempdir())
    parser.add_argument("--output-root", type=Path, default=scratch / "kickstart-token-savings")
    parser.add_argument("--report", type=Path, default=scratch / "kickstart-token-savings.md")
    parser.add_argument("--json", action="store_true", help="Print machine-readable results to stdout")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    args.output_root.mkdir(parents=True, exist_ok=True)

    results = tuple(run_case(case, args.output_root, repo_root) for case in DEFAULT_CASES)
    report = render_report(results)
    args.report.write_text(report, encoding="utf-8")

    if args.json:
        print(results_as_json(results))
    else:
        print(report)
    print(f"Report written to {args.report}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
