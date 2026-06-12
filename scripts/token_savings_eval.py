"""Measure how many output tokens a scaffold saves an agent.

kickstart's pitch includes minimizing the tokens an agent spends bootstrapping
a project: one short `kickstart create` command replaces authoring every
starter file by hand. This eval makes that claim measurable. For each
representative scaffold it generates the project, counts the text content an
agent would otherwise have had to emit, estimates tokens with a documented
heuristic, and compares that to the token cost of the command itself.

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


# Rough heuristic for code-heavy text: ~4 bytes per token. The exact tokenizer
# varies by model; the eval reports bytes alongside tokens so the raw data
# stays model-agnostic.
BYTES_PER_TOKEN = 4


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

    @property
    def command_tokens(self) -> int:
        return estimate_tokens(self.command_text)

    @property
    def output_tokens(self) -> int:
        return max(1, round(self.content_bytes / BYTES_PER_TOKEN))

    @property
    def savings_ratio(self) -> float:
        return self.output_tokens / self.command_tokens


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


def measure_tree(root: Path) -> tuple[int, int]:
    """Return (text file count, total UTF-8 content bytes) under a directory."""
    file_count = 0
    content_bytes = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not is_text_file(path):
            continue
        file_count += 1
        content_bytes += len(path.read_bytes())
    return file_count, content_bytes


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

    file_count, content_bytes = measure_tree(case_root)
    return CaseResult(
        case=case,
        command_text=user_facing_command(case),
        file_count=file_count,
        content_bytes=content_bytes,
    )


def render_report(results: tuple[CaseResult, ...]) -> str:
    """Render a markdown report for the measured cases."""
    lines = [
        "# kickstart token savings eval",
        "",
        f"Token estimate heuristic: ~{BYTES_PER_TOKEN} UTF-8 bytes per token for code-heavy text.",
        "Output tokens approximate what an agent would emit authoring every generated file by hand;",
        "command tokens are the cost of the `kickstart create` invocation that replaces that work.",
        "",
        "| scaffold | files | bytes | output tokens (est) | command tokens (est) | savings |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            f"| {result.case.slug} | {result.file_count} | {result.content_bytes} "
            f"| {result.output_tokens} | {result.command_tokens} | {result.savings_ratio:,.0f}x |"
        )

    total_output = sum(result.output_tokens for result in results)
    total_command = sum(result.command_tokens for result in results)
    lines.extend(
        [
            f"| total | | | {total_output} | {total_command} | {total_output / total_command:,.0f}x |",
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
            "output_tokens_estimate": result.output_tokens,
            "command_tokens_estimate": result.command_tokens,
            "savings_ratio": round(result.savings_ratio, 1),
        }
        for result in results
    ]
    return json.dumps(payload, indent=2)


def main() -> int:
    """Run the token savings eval from the command line."""
    parser = argparse.ArgumentParser(description="Measure agent token savings per kickstart scaffold.")
    parser.add_argument("--output-root", type=Path, default=Path("/private/tmp/kickstart-token-savings"))
    parser.add_argument("--report", type=Path, default=Path("/private/tmp/kickstart-token-savings.md"))
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
