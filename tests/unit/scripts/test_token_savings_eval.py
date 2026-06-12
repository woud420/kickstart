from pathlib import Path

from scripts.token_savings_eval import (
    DEFAULT_CASES,
    CaseResult,
    ScaffoldCase,
    estimate_tokens,
    is_text_file,
    measure_tree,
    render_report,
    user_facing_command,
)


def test_estimate_tokens_uses_bytes_heuristic() -> None:
    assert estimate_tokens("a" * 40) == 10
    assert estimate_tokens("") == 1


def test_is_text_file_accepts_utf8_and_rejects_binary(tmp_path: Path) -> None:
    text = tmp_path / "main.py"
    text.write_text('print("hi")\n', encoding="utf-8")
    binary = tmp_path / "blob.bin"
    binary.write_bytes(b"\x00\x01\x02")

    assert is_text_file(text)
    assert not is_text_file(binary)


def test_measure_tree_counts_text_files_and_splits_metadata(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# hi\n", encoding="utf-8")
    (tmp_path / ".kickstart").mkdir()
    (tmp_path / ".kickstart" / "scaffold.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# map\n", encoding="utf-8")
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01")

    file_count, content_bytes, app_code_bytes = measure_tree(tmp_path)

    assert file_count == 4
    assert content_bytes == len(b"x = 1\n") + len(b"# hi\n") + len(b"{}\n") + len(b"# map\n")
    assert app_code_bytes == len(b"x = 1\n") + len(b"# hi\n")


def test_user_facing_command_targets_installed_binary() -> None:
    case = ScaffoldCase(slug="demo", args=("create", "cli", "tool", "--lang", "rust"))

    assert user_facing_command(case) == "kickstart create cli tool --lang rust"


def test_case_result_savings_ratios() -> None:
    result = CaseResult(
        case=ScaffoldCase(slug="demo", args=("create", "cli", "tool")),
        command_text="kickstart create cli tool",
        file_count=10,
        content_bytes=40_000,
        app_code_bytes=30_000,
    )

    assert result.output_tokens == 10_000
    assert result.app_code_tokens == 7_500
    assert result.command_tokens == estimate_tokens("kickstart create cli tool")
    assert result.savings_ratio == result.output_tokens / result.command_tokens
    assert result.app_code_ratio == result.app_code_tokens / result.command_tokens


def test_render_report_lists_every_case_and_total() -> None:
    results = tuple(
        CaseResult(
            case=case,
            command_text=user_facing_command(case),
            file_count=5,
            content_bytes=20_000,
            app_code_bytes=15_000,
        )
        for case in DEFAULT_CASES[:2]
    )

    report = render_report(results)

    for result in results:
        assert result.case.slug in report
    assert "| total |" in report
    assert "bytes per token" in report
    assert "upper bound" in report
