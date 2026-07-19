from unittest.mock import patch

from typer.testing import CliRunner

from src.cli.main import app
from src.model.dto.telemetry import (
    ScaffoldCreateContext,
    ScaffoldCreateErrorCategory,
    ScaffoldCreateOutcome,
)
from src.utils.errors import ProjectCreationError


def test_success_attempts_one_terminal_event_after_creation() -> None:
    order: list[str] = []
    runner = CliRunner()
    with (
        patch("src.cli.main.load_config", return_value={}),
        patch("src.cli.main.create_service", side_effect=lambda *args, **kwargs: order.append("create")),
        patch(
            "src.cli.main.capture_scaffold_create_terminal", side_effect=lambda *args, **kwargs: order.append("capture")
        ) as capture,
        patch("src.cli.main.monotonic", side_effect=[10.0, 12.0]),
    ):
        result = runner.invoke(
            app,
            ["create", "service", "private-project-name", "--root", "/private/project/root", "--lang", "ts"],
        )

    assert result.exit_code == 0
    assert order == ["create", "capture"]
    capture.assert_called_once()
    context, outcome, error_category, duration = capture.call_args.args
    assert isinstance(context, ScaffoldCreateContext)
    assert not hasattr(context, "name")
    assert not hasattr(context, "root")
    assert context.project_type == "service"
    assert context.language == "ts"
    assert outcome is ScaffoldCreateOutcome.SUCCESS
    assert error_category is ScaffoldCreateErrorCategory.NONE
    assert duration == 2.0


def test_expected_creation_failure_preserves_exit_and_attempts_one_terminal_event() -> None:
    runner = CliRunner()
    private_error = "private failure at /private/project/root"
    with (
        patch("src.cli.main.load_config", return_value={}),
        patch("src.cli.main.create_service", side_effect=ProjectCreationError(private_error)),
        patch("src.cli.main.capture_scaffold_create_terminal") as capture,
    ):
        result = runner.invoke(app, ["create", "service", "private-project-name", "--root", "/tmp"])

    assert result.exit_code == 1
    assert private_error in result.stdout
    capture.assert_called_once()
    context, outcome, error_category, _duration = capture.call_args.args
    assert isinstance(context, ScaffoldCreateContext)
    assert outcome is ScaffoldCreateOutcome.EXPECTED_ERROR
    assert error_category is ScaffoldCreateErrorCategory.PROJECT_CREATION_ERROR
    assert private_error not in repr(context)


def test_unexpected_creation_failure_attempts_one_terminal_event() -> None:
    runner = CliRunner()
    with (
        patch("src.cli.main.load_config", return_value={}),
        patch("src.cli.main.create_service", side_effect=RuntimeError("synthetic unexpected failure")),
        patch("src.cli.main.capture_scaffold_create_terminal") as capture,
    ):
        result = runner.invoke(app, ["create", "service", "private-project-name", "--root", "/tmp"])

    assert result.exit_code == 1
    capture.assert_called_once()
    assert capture.call_args.args[1:3] == (
        ScaffoldCreateOutcome.UNEXPECTED_ERROR,
        ScaffoldCreateErrorCategory.UNEXPECTED_ERROR,
    )


def test_keyboard_interrupt_preserves_exit_130_and_attempts_one_terminal_event() -> None:
    runner = CliRunner()
    with (
        patch("src.cli.main.load_config", side_effect=KeyboardInterrupt),
        patch("src.cli.main.capture_scaffold_create_terminal") as capture,
    ):
        result = runner.invoke(app, ["create", "service", "private-project-name"])

    assert result.exit_code == 130
    capture.assert_called_once()
    assert capture.call_args.args[1:3] == (
        ScaffoldCreateOutcome.CANCELLED,
        ScaffoldCreateErrorCategory.INTERRUPTED,
    )


def test_input_end_preserves_exit_2_and_attempts_one_terminal_event() -> None:
    runner = CliRunner()
    with (
        patch("src.cli.main.load_config", side_effect=EOFError),
        patch("src.cli.main.capture_scaffold_create_terminal") as capture,
    ):
        result = runner.invoke(app, ["create", "service", "private-project-name"])

    assert result.exit_code == 2
    capture.assert_called_once()
    assert capture.call_args.args[1:3] == (
        ScaffoldCreateOutcome.INPUT_ENDED,
        ScaffoldCreateErrorCategory.INPUT_ENDED,
    )


def test_missing_name_marks_partial_argument_prompt_flow_interactive() -> None:
    runner = CliRunner()
    with (
        patch("src.cli.main.load_config", return_value={}),
        patch("src.cli.main.Prompt.ask", side_effect=["none", "none", "none", "fastapi"]),
        patch("src.cli.main.capture_scaffold_create_terminal") as capture,
    ):
        result = runner.invoke(app, ["create", "service"])

    assert result.exit_code == 1
    capture.assert_called_once()
    context = capture.call_args.args[0]
    assert isinstance(context, ScaffoldCreateContext)
    assert context.interactive is True


def test_parser_failure_before_create_emits_no_event() -> None:
    runner = CliRunner()
    with patch("src.cli.main.capture_scaffold_create_terminal") as capture:
        result = runner.invoke(app, ["create", "service", "private-project-name", "--not-a-real-option"])

    assert result.exit_code == 2
    capture.assert_not_called()


def test_non_create_commands_emit_no_event() -> None:
    runner = CliRunner()
    with patch("src.cli.main.capture_scaffold_create_terminal") as capture:
        help_result = runner.invoke(app, ["--help"])
        version_result = runner.invoke(app, ["version"])

    assert help_result.exit_code == 0
    assert version_result.exit_code == 0
    capture.assert_not_called()
