from __future__ import annotations

import difflib
from pathlib import Path
from typing import Iterable


def _collect_tree_entries(root: Path) -> tuple[set[str], set[str]]:
    directories: set[str] = set()
    files: set[str] = set()

    for path in sorted(root.rglob("*")):
        rel_path = path.relative_to(root).as_posix()
        if path.is_dir():
            directories.add(f"{rel_path}/")
        elif path.is_file():
            files.add(rel_path)

    return directories, files


def _render_file_diff(relative_path: str, expected_bytes: bytes, actual_bytes: bytes) -> str:
    try:
        expected_text = expected_bytes.decode("utf-8")
        actual_text = actual_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return (
            f"--- fixture/{relative_path}\n"
            f"+++ generated/{relative_path}\n"
            "@@ binary @@\n"
            f"- {len(expected_bytes)} bytes\n"
            f"+ {len(actual_bytes)} bytes"
        )

    diff_lines = list(
        difflib.unified_diff(
            expected_text.splitlines(),
            actual_text.splitlines(),
            fromfile=f"fixture/{relative_path}",
            tofile=f"generated/{relative_path}",
            lineterm="",
        )
    )

    if not diff_lines:
        return (
            f"--- fixture/{relative_path}\n"
            f"+++ generated/{relative_path}\n"
            "@@ text @@\n"
            "- content differs"
        )

    return "\n".join(diff_lines)


def assert_matches_golden_scaffold(
    generated_root: Path,
    fixture_root: Path,
    *,
    required_key_files: Iterable[str],
) -> None:
    fixture_dirs, fixture_files = _collect_tree_entries(fixture_root)
    generated_dirs, generated_files = _collect_tree_entries(generated_root)

    required_files = set(required_key_files)
    fixture_missing_required = sorted(required_files - fixture_files)
    generated_missing_required = sorted(required_files - generated_files)

    fixture_entries = fixture_dirs | fixture_files
    generated_entries = generated_dirs | generated_files

    missing_entries = sorted(fixture_entries - generated_entries)
    extra_entries = sorted(generated_entries - fixture_entries)

    changed_files: list[str] = []
    diff_blocks: list[str] = []

    for relative_path in sorted(fixture_files & generated_files):
        expected_file = fixture_root / relative_path
        generated_file = generated_root / relative_path

        expected_bytes = expected_file.read_bytes()
        actual_bytes = generated_file.read_bytes()

        if expected_bytes == actual_bytes:
            continue

        changed_files.append(relative_path)
        diff_blocks.append(_render_file_diff(relative_path, expected_bytes, actual_bytes))

    if not (
        fixture_missing_required
        or generated_missing_required
        or missing_entries
        or extra_entries
        or changed_files
    ):
        return

    lines = ["Golden scaffold drift detected (TypeScript Cloudflare Worker)."]

    if fixture_missing_required:
        lines.extend(
            [
                "",
                "Fixture is missing required key files:",
                *[f"- {path}" for path in fixture_missing_required],
            ]
        )

    if generated_missing_required:
        lines.extend(
            [
                "",
                "Generated output is missing required key files:",
                *[f"- {path}" for path in generated_missing_required],
            ]
        )

    if missing_entries:
        lines.extend(
            [
                "",
                "Missing paths (present in fixture, absent in generated output):",
                *[f"- {path}" for path in missing_entries],
            ]
        )

    if extra_entries:
        lines.extend(
            [
                "",
                "Extra paths (present in generated output, absent in fixture):",
                *[f"- {path}" for path in extra_entries],
            ]
        )

    if changed_files:
        lines.extend(
            [
                "",
                "Changed files:",
                *[f"- {path}" for path in changed_files],
                "",
                "Unified diffs:",
            ]
        )

        for diff_block in diff_blocks:
            lines.extend(["", diff_block])

    raise AssertionError("\n".join(lines))
