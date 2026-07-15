"""The import hygiene audit catches error-class imports from the wrong module.

PR #81 merged green while importing TemplateError from
src.utils.error_handling (it lives in src.utils.errors) and broke master.
These tests pin that failure class as a lint error.

The banned import statement is always built by concatenation here so that
this test file itself stays clean under the audit (the same trick
type_hygiene_audit uses for its own patterns).
"""

from __future__ import annotations

from pathlib import Path

from scripts.import_hygiene_audit import find_issues

FAKE_PATH = Path("/repo/src/example.py")
BANNED_IMPORT = "from src.utils." + "error_handling import "


def test_flags_error_class_from_error_handling() -> None:
    source = BANNED_IMPORT + "TemplateError\n"
    issues = find_issues(source, FAKE_PATH)
    assert [issue.name for issue in issues] == ["TemplateError"]
    assert issues[0].line_number == 1


def test_flags_mixed_import_exactly_like_pr_81() -> None:
    source = BANNED_IMPORT + "KickstartError, TemplateError\n"
    issues = find_issues(source, FAKE_PATH)
    assert sorted(issue.name for issue in issues) == ["KickstartError", "TemplateError"]


def test_flags_parenthesized_multiline_import() -> None:
    source = BANNED_IMPORT + "(\n    ErrorCollector,\n    FileOperationError,\n)\n"
    issues = find_issues(source, FAKE_PATH)
    assert [issue.name for issue in issues] == ["FileOperationError"]
    assert issues[0].line_number == 1


def test_allows_handling_api_imports() -> None:
    source = BANNED_IMPORT + "ErrorCollector, safe_file_write\nfrom src.utils.errors import TemplateError\n"
    assert find_issues(source, FAKE_PATH) == ()


def test_reports_line_numbers_for_later_imports() -> None:
    source = "import os\n\n" + BANNED_IMPORT + "DirectoryCreationError\n"
    issues = find_issues(source, FAKE_PATH)
    assert issues[0].line_number == 3


def test_repo_is_currently_clean() -> None:
    from scripts.import_hygiene_audit import _python_source_files, _scan_files

    assert _scan_files(_python_source_files()) == ()
