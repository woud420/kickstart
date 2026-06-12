from pathlib import Path

import pytest

from scripts.bootstrap_eval import (
    ANY_NAME,
    DEFAULT_CASES,
    DEFAULT_MAX_FILE_LINES,
    BootstrapCase,
    CaseResult,
    UnknownCaseError,
    audit_capability_tests,
    audit_depth,
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


def test_default_line_cap_is_enforced_at_its_real_value(tmp_path: Path) -> None:
    assert DEFAULT_MAX_FILE_LINES == 200
    at_cap = write(tmp_path / "src" / "at_cap.py", "x = 1\n" * DEFAULT_MAX_FILE_LINES)
    over_cap = write(tmp_path / "src" / "over_cap.py", "x = 1\n" * (DEFAULT_MAX_FILE_LINES + 1))

    assert audit_file(at_cap, tmp_path, max_lines=DEFAULT_MAX_FILE_LINES) == ()
    rules = [violation.rule for violation in audit_file(over_cap, tmp_path, max_lines=DEFAULT_MAX_FILE_LINES)]
    assert rules == ["max-file-lines"]


def test_audit_file_flags_typescript_any_and_rust_panics(tmp_path: Path) -> None:
    ts = write(tmp_path / "src" / "index.ts", "const x: any = 1;\n")
    rs = write(tmp_path / "src" / "main.rs", "let v = result.unwrap();\n")

    assert [violation.rule for violation in audit_file(ts, tmp_path, max_lines=300)] == ["typescript-no-any"]
    assert [violation.rule for violation in audit_file(rs, tmp_path, max_lines=300)] == ["rust-no-panic-paths"]


def test_audit_file_catches_dotted_any_and_nested_object(tmp_path: Path) -> None:
    object_name = "obj" "ect"
    path = write(
        tmp_path / "src" / "sneaky.py",
        f"import typing\n\ndef f(x: typing.{ANY_NAME}) -> dict[str, {object_name}]:\n    return {{}}\n",
    )

    rules = {violation.rule for violation in audit_file(path, tmp_path, max_lines=300)}

    assert rules == {"python-no-any", "python-no-object-type"}


def test_audit_file_ignores_forbidden_tokens_in_comments(tmp_path: Path) -> None:
    py = write(tmp_path / "src" / "noted.py", f"x = 1  # never use {ANY_NAME} here\n")
    ts = write(tmp_path / "src" / "noted.ts", "const x = 1; // if it has any flaws, fix them\n")

    assert audit_file(py, tmp_path, max_lines=300) == ()
    assert audit_file(ts, tmp_path, max_lines=300) == ()


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


def test_audit_depth_allows_three_levels_and_flags_four(tmp_path: Path) -> None:
    fine = write(tmp_path / "src" / "cli" / "commands" / "check.py", "x = 1\n")
    deep = write(tmp_path / "src" / "cli" / "commands" / "nested" / "extra.py", "x = 1\n")

    assert audit_depth(fine, tmp_path) is None
    violation = audit_depth(deep, tmp_path)
    assert violation is not None and violation.rule == "max-src-depth"
    assert audit_depth(write(tmp_path / "docs" / "a" / "b" / "c" / "d.py", "x = 1\n"), tmp_path) is None


def test_audit_tree_includes_depth_violations(tmp_path: Path) -> None:
    write(tmp_path / "src" / "a" / "b" / "c" / "deep.py", "x = 1\n")

    rules = [violation.rule for violation in audit_tree(tmp_path, max_lines=300)]

    assert rules == ["max-src-depth"]


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


def test_capability_tests_rule_requires_a_test_per_extension(tmp_path: Path) -> None:
    (tmp_path / ".kickstart").mkdir()
    (tmp_path / ".kickstart" / "scaffold.json").write_text(
        '{"capabilities": {"service_extensions": {"auth": "jwt", "cache": "redis"}}}',
        encoding="utf-8",
    )
    write(tmp_path / "tests" / "unit" / "handler" / "test_auth.py", "from src.handler.auth import JWTAuth\n")

    violations = audit_capability_tests(tmp_path)

    assert [violation.rule for violation in violations] == ["capability-tests"]
    assert "cache=redis" in violations[0].detail


def test_capability_tests_rule_accepts_covered_extensions(tmp_path: Path) -> None:
    (tmp_path / ".kickstart").mkdir()
    (tmp_path / ".kickstart" / "scaffold.json").write_text(
        '{"capabilities": {"service_extensions": {"auth": "jwt"}}}',
        encoding="utf-8",
    )
    write(tmp_path / "src" / "handler" / "auth.rs", "#[cfg(test)]\nmod tests { use jsonwebtoken as jwt; }\n")

    assert audit_capability_tests(tmp_path) == ()


def test_capability_tests_rule_passes_without_extensions(tmp_path: Path) -> None:
    (tmp_path / ".kickstart").mkdir()
    (tmp_path / ".kickstart" / "scaffold.json").write_text('{"capabilities": {}}', encoding="utf-8")

    assert audit_capability_tests(tmp_path) == ()
