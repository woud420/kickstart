from pathlib import Path

import pytest

from scripts.bootstrap_eval import (
    ANY_NAME,
    DEFAULT_CASES,
    BootstrapCase,
    CaseResult,
    UnknownCaseError,
    audit_file,
    audit_tree,
    is_test_path,
    render_report,
    select_cases,
    source_files,
)


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_source_files_skips_caches_and_non_source(tmp_path: Path) -> None:
    write(tmp_path / "src" / "main.py", "x = 1\n")
    write(tmp_path / ".venv" / "lib.py", "x = 1\n")
    write(tmp_path / "node_modules" / "dep.ts", "x = 1\n")
    write(tmp_path / "README.md", "# hi\n")

    found = source_files(tmp_path)

    assert [str(path.relative_to(tmp_path)) for path in found] == ["src/main.py"]


def test_audit_file_flags_python_any_and_generic_errors(tmp_path: Path) -> None:
    path = write(
        tmp_path / "src" / "bad.py",
        f"from typing import {ANY_NAME}\n\ndef f(x: {ANY_NAME}) -> object:\n    raise Exception('boom')\n",
    )

    rules = {violation.rule for violation in audit_file(path, tmp_path, max_lines=300)}

    assert rules == {"python-no-any", "python-no-object-type", "python-specific-errors"}


def test_audit_file_allows_clean_typed_python(tmp_path: Path) -> None:
    path = write(
        tmp_path / "src" / "good.py",
        'class ConfigError(ValueError):\n    """Specific error."""\n\n\ndef f(x: int) -> str:\n    return str(x)\n',
    )

    assert audit_file(path, tmp_path, max_lines=300) == ()


def test_audit_file_enforces_line_cap(tmp_path: Path) -> None:
    path = write(tmp_path / "src" / "long.py", "x = 1\n" * 301)

    violations = audit_file(path, tmp_path, max_lines=300)

    assert [violation.rule for violation in violations] == ["max-file-lines"]


def test_audit_file_flags_typescript_any_and_rust_panics(tmp_path: Path) -> None:
    ts = write(tmp_path / "src" / "index.ts", "const x: any = 1;\n")
    rs = write(tmp_path / "src" / "main.rs", "let v = result.unwrap();\n")

    assert [violation.rule for violation in audit_file(ts, tmp_path, max_lines=300)] == ["typescript-no-any"]
    assert [violation.rule for violation in audit_file(rs, tmp_path, max_lines=300)] == ["rust-no-panic-paths"]


def test_audit_file_flags_checker_suppressions(tmp_path: Path) -> None:
    py = write(tmp_path / "src" / "shim.py", "value = load()  # type: ignore\n")
    ts = write(tmp_path / "src" / "shim.ts", "// @ts-expect-error legacy\nconst x = load();\n")

    assert [violation.rule for violation in audit_file(py, tmp_path, max_lines=300)] == ["python-no-suppressions"]
    assert [violation.rule for violation in audit_file(ts, tmp_path, max_lines=300)] == ["typescript-no-suppressions"]


def test_rust_tests_may_unwrap(tmp_path: Path) -> None:
    path = write(tmp_path / "tests" / "cli_smoke.rs", "let v = run().unwrap();\n")

    assert audit_file(path, tmp_path, max_lines=300) == ()
    assert is_test_path(Path("tests/cli_smoke.rs"))
    assert not is_test_path(Path("src/main.rs"))


def test_audit_tree_aggregates_all_files(tmp_path: Path) -> None:
    write(tmp_path / "src" / "a.py", f"from typing import {ANY_NAME}\n")
    write(tmp_path / "src" / "b.ts", "const x = 1 as any;\n")

    rules = sorted(violation.rule for violation in audit_tree(tmp_path, max_lines=300))

    assert rules == ["python-no-any", "typescript-no-any"]


def test_select_cases_defaults_and_rejects_unknown() -> None:
    assert select_cases(()) == DEFAULT_CASES
    assert select_cases(("rust-cli",))[0].slug == "rust-cli"
    with pytest.raises(UnknownCaseError, match="unknown case 'nope'"):
        select_cases(("nope",))


def test_render_report_marks_failures() -> None:
    case = BootstrapCase(slug="demo", args=("create", "cli", "tool"))
    results = (
        CaseResult(case, generated=True, violations=(), check_passed=True, check_seconds=2.0, failure_detail=""),
        CaseResult(case, generated=True, violations=(), check_passed=False, check_seconds=1.0, failure_detail="make check failed: boom"),
    )

    report = render_report(results, max_lines=300)

    assert "| demo | yes | 0 | green | 2.0 |" in report
    assert "| demo | yes | 0 | RED | 1.0 |" in report
    assert "make check failed: boom" in report
