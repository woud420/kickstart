import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.errors import (
    DirectoryCreationError,
    FileOperationError,
    KickstartError,
    LanguageNotSupportedError,
)
from src.utils.error_handling import (
    ErrorCollector,
    batch_operation_wrapper,
    ensure_directory_exists,
    error_context,
    format_error_message,
    handle_directory_operations,
    handle_file_operations,
    handle_http_operations,
    handle_template_operations,
    log_operation_result,
    safe_binary_write,
    safe_file_copy,
    safe_file_write,
    safe_operation,
    safe_operation_context,
    validate_language_support,
)


# --- error_context ---------------------------------------------------------

def test_error_context_yields_on_success():
    with error_context("do the thing"):
        result = 1 + 1
    assert result == 2


def test_error_context_reraises_kickstart_error_unchanged():
    original = KickstartError("already typed")
    with pytest.raises(KickstartError) as exc_info:
        with error_context("do the thing"):
            raise original
    assert exc_info.value is original


def test_error_context_wraps_other_exceptions_with_context():
    with pytest.raises(KickstartError) as exc_info:
        with error_context("do the thing", target="/tmp/x"):
            raise ValueError("bad value")
    error = exc_info.value
    assert "Operation 'do the thing' failed: bad value" in str(error)
    assert error.context == {"target": "/tmp/x"}
    assert isinstance(error.__cause__, ValueError)


# --- handle_file_operations -------------------------------------------------

def test_handle_file_operations_returns_value_on_success():
    @handle_file_operations(default_return="default")
    def op():
        return "ok"

    assert op() == "ok"


def test_handle_file_operations_returns_default_on_error():
    @handle_file_operations(default_return="default", log_errors=False)
    def op():
        raise FileNotFoundError("missing")

    assert op() == "default"


def test_handle_file_operations_reraises_as_file_operation_error():
    @handle_file_operations(default_return=None, reraise=True)
    def op():
        raise PermissionError("denied")

    with pytest.raises(FileOperationError):
        op()


def test_handle_file_operations_ignores_other_exceptions():
    @handle_file_operations(default_return=None)
    def op():
        raise ValueError("not a file error")

    with pytest.raises(ValueError):
        op()


# --- handle_template_operations ----------------------------------------------

def test_handle_template_operations_returns_value_on_success():
    @handle_template_operations(default_return="default")
    def op():
        return "ok"

    assert op() == "ok"


def test_handle_template_operations_returns_default_and_warns_on_error():
    @handle_template_operations(default_return="default")
    def op():
        raise RuntimeError("template broke")

    with patch("src.utils.error_handling.warn") as mock_warn:
        assert op() == "default"
        mock_warn.assert_called_once()


# --- handle_directory_operations ---------------------------------------------

def test_handle_directory_operations_returns_value_on_success():
    @handle_directory_operations(default_return=False)
    def op():
        return True

    assert op() is True


def test_handle_directory_operations_returns_default_and_warns_on_oserror():
    @handle_directory_operations(default_return=False)
    def op():
        raise OSError("disk full")

    with patch("src.utils.error_handling.warn") as mock_warn:
        assert op() is False
        mock_warn.assert_called_once()


def test_handle_directory_operations_ignores_non_os_errors():
    @handle_directory_operations(default_return=False)
    def op():
        raise ValueError("nope")

    with pytest.raises(ValueError):
        op()


# --- handle_http_operations ---------------------------------------------------

def test_handle_http_operations_returns_value_on_success():
    @handle_http_operations("fetch", default_return=None)
    def op():
        return {"ok": True}

    assert op() == {"ok": True}


def test_handle_http_operations_returns_default_on_generic_exception():
    @handle_http_operations("fetch", default_return="default")
    def op():
        raise RuntimeError("network is down")

    assert op() == "default"


def test_handle_http_operations_reraises_as_kickstart_error():
    @handle_http_operations("fetch", default_return=None, reraise=True)
    def op():
        raise RuntimeError("network is down")

    with pytest.raises(KickstartError):
        op()


def test_handle_http_operations_reports_http_status_from_response():
    import requests

    response = requests.Response()
    response.status_code = 503

    @handle_http_operations("fetch", default_return=None, reraise=True)
    def op():
        raise requests.RequestException("service unavailable", response=response)

    with pytest.raises(KickstartError) as exc_info:
        op()
    assert "HTTP 503" in str(exc_info.value)


def test_handle_http_operations_reports_network_error_without_response():
    import requests

    @handle_http_operations("fetch", default_return=None, reraise=True)
    def op():
        raise requests.ConnectionError("connection refused")

    with pytest.raises(KickstartError) as exc_info:
        op()
    assert "network error" in str(exc_info.value)


# --- safe_operation -------------------------------------------------------------

def test_safe_operation_returns_value_on_success():
    @safe_operation("do thing", default_return="default")
    def op():
        return "ok"

    assert op() == "ok"


def test_safe_operation_returns_default_on_error_without_reraise():
    @safe_operation("do thing", default_return="default")
    def op():
        raise RuntimeError("boom")

    assert op() == "default"


def test_safe_operation_reraises_as_requested_type():
    @safe_operation("do thing", reraise_as=KickstartError)
    def op():
        raise RuntimeError("boom")

    with pytest.raises(KickstartError):
        op()


# --- safe_operation_context -------------------------------------------------------

def test_safe_operation_context_yields_on_success():
    with safe_operation_context("do thing"):
        result = 1 + 1
    assert result == 2


def test_safe_operation_context_suppresses_exceptions_by_default():
    with safe_operation_context("do thing"):
        raise RuntimeError("boom")


def test_safe_operation_context_reraises_when_not_suppressing():
    with pytest.raises(RuntimeError):
        with safe_operation_context("do thing", suppress_exceptions=False):
            raise RuntimeError("boom")


# --- ErrorCollector -------------------------------------------------------------

def test_error_collector_tracks_success_and_totals():
    collector = ErrorCollector("batch")
    collector.increment_total()
    collector.increment_success()
    assert collector.success_count == 1
    assert collector.total_count == 1
    assert not collector.has_errors()
    assert not collector.has_warnings()


def test_error_collector_add_error_and_warning():
    collector = ErrorCollector("batch")
    collector.add_error("bad thing")
    collector.add_warning("meh thing")
    assert collector.has_errors()
    assert collector.has_warnings()
    assert collector.errors == ["bad thing"]
    assert collector.warnings == ["meh thing"]


def test_error_collector_get_summary_reports_counts():
    collector = ErrorCollector("batch")
    collector.increment_total()
    collector.increment_total()
    collector.increment_success()
    collector.add_error("bad")
    collector.add_warning("meh")
    summary = collector.get_summary()
    assert "1/2 operations successful" in summary
    assert "1 errors" in summary
    assert "1 warnings" in summary


def test_error_collector_log_summary_warns_user_when_errors_present():
    collector = ErrorCollector("batch")
    collector.add_error("bad")
    with patch("src.utils.error_handling.warn") as mock_warn:
        collector.log_summary()
        mock_warn.assert_called_once()


def test_error_collector_log_summary_clean_when_only_warnings(caplog):
    collector = ErrorCollector("batch")
    collector.add_warning("meh")
    with caplog.at_level(logging.WARNING, logger="src.utils.error_handling"):
        collector.log_summary()
    assert any("meh" in message for message in caplog.messages)


def test_error_collector_log_summary_clean_when_no_issues(caplog):
    collector = ErrorCollector("batch")
    collector.increment_total()
    collector.increment_success()
    with caplog.at_level(logging.INFO, logger="src.utils.error_handling"):
        collector.log_summary()
    assert any("1/1 operations successful" in message for message in caplog.messages)


def test_error_collector_report_failures_reports_errors_and_warnings():
    collector = ErrorCollector("batch")
    collector.add_error("bad")
    collector.add_warning("meh")
    with patch("src.utils.error_handling.warn") as mock_warn:
        collector.report_failures()
        mock_warn.assert_called_once()
        assert "bad" in mock_warn.call_args[0][0]


def test_error_collector_report_failures_noop_when_clean():
    collector = ErrorCollector("batch")
    with patch("src.utils.error_handling.warn") as mock_warn:
        collector.report_failures()
        mock_warn.assert_not_called()


# --- format_error_message / log_operation_result --------------------------------

def test_format_error_message_without_context():
    message = format_error_message("write", "/tmp/x", ValueError("bad"))
    assert message == "write failed for '/tmp/x': bad"


def test_format_error_message_with_context():
    message = format_error_message("write", "/tmp/x", ValueError("bad"), {"attempt": 2})
    assert message == "write failed for '/tmp/x': bad (context: attempt=2)"


def test_log_operation_result_success(caplog):
    with caplog.at_level(logging.DEBUG, logger="src.utils.error_handling"):
        log_operation_result("write", success=True, target="/tmp/x")
    assert any("write succeeded for '/tmp/x'" in message for message in caplog.messages)


def test_log_operation_result_failure_with_error(caplog):
    with caplog.at_level(logging.ERROR, logger="src.utils.error_handling"):
        log_operation_result("write", success=False, target="/tmp/x", error=ValueError("bad"))
    assert any("write failed for '/tmp/x': bad" in message for message in caplog.messages)


def test_log_operation_result_failure_without_error_uses_default(caplog):
    with caplog.at_level(logging.ERROR, logger="src.utils.error_handling"):
        log_operation_result("write", success=False)
    assert any("Unknown error" in message for message in caplog.messages)


# --- batch_operation_wrapper -----------------------------------------------------

def test_batch_operation_wrapper_all_succeed():
    collector = batch_operation_wrapper([1, 2, 3], lambda item: True, "batch")
    assert collector.success_count == 3
    assert collector.total_count == 3
    assert not collector.has_errors()


def test_batch_operation_wrapper_records_failures():
    collector = batch_operation_wrapper(
        [1, 2], lambda item: item != 2, "batch", item_name_func=lambda item: f"item-{item}"
    )
    assert collector.success_count == 1
    assert collector.errors == ["Operation failed for item-2"]


def test_batch_operation_wrapper_records_exceptions():
    def blow_up(item):
        raise RuntimeError("kaboom")

    collector = batch_operation_wrapper([1], blow_up, "batch")
    assert collector.total_count == 1
    assert collector.success_count == 0
    assert "Exception processing 1: kaboom" in collector.errors[0]


# --- validate_language_support ---------------------------------------------------

def test_validate_language_support_accepts_supported_language():
    validate_language_support("python", ["python", "rust"])


def test_validate_language_support_rejects_unsupported_language():
    with pytest.raises(LanguageNotSupportedError):
        validate_language_support("cobol", ["python", "rust"])


# --- ensure_directory_exists -------------------------------------------------------

def test_ensure_directory_exists_true_when_already_present(tmp_path: Path):
    assert ensure_directory_exists(tmp_path) is True


def test_ensure_directory_exists_false_when_missing_and_create_disabled(tmp_path: Path):
    missing = tmp_path / "missing"
    assert ensure_directory_exists(missing, create=False) is False


def test_ensure_directory_exists_creates_directory(tmp_path: Path):
    target = tmp_path / "nested" / "dir"
    assert ensure_directory_exists(target) is True
    assert target.is_dir()


def test_ensure_directory_exists_raises_on_oserror(tmp_path: Path):
    target = tmp_path / "dir"
    with patch("pathlib.Path.mkdir", side_effect=OSError("no space")):
        with pytest.raises(DirectoryCreationError):
            ensure_directory_exists(target)


# --- safe_binary_write / safe_file_write / safe_file_copy ---------------------------

def test_safe_binary_write_writes_bytes_and_sets_permissions(tmp_path: Path):
    target = tmp_path / "nested" / "file.bin"
    assert safe_binary_write(target, b"data", permissions=0o644) is True
    assert target.read_bytes() == b"data"


def test_safe_binary_write_raises_file_operation_error(tmp_path: Path):
    target = tmp_path / "file.bin"
    with patch("pathlib.Path.write_bytes", side_effect=OSError("disk full")):
        with pytest.raises(FileOperationError):
            safe_binary_write(target, b"data")


def test_safe_file_write_writes_text(tmp_path: Path):
    target = tmp_path / "nested" / "file.txt"
    assert safe_file_write(target, "hello") is True
    assert target.read_text() == "hello"


def test_safe_file_write_raises_file_operation_error(tmp_path: Path):
    target = tmp_path / "file.txt"
    with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
        with pytest.raises(FileOperationError):
            safe_file_write(target, "hello")


def test_safe_file_copy_preserves_metadata_by_default(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("hello")
    target = tmp_path / "nested" / "target.txt"
    assert safe_file_copy(source, target) is True
    assert target.read_text() == "hello"


def test_safe_file_copy_without_preserving_metadata(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("hello")
    target = tmp_path / "target.txt"
    assert safe_file_copy(source, target, preserve_metadata=False) is True
    assert target.read_text() == "hello"


def test_safe_file_copy_raises_file_operation_error(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("hello")
    target = tmp_path / "target.txt"
    with patch("shutil.copy2", side_effect=OSError("disk full")):
        with pytest.raises(FileOperationError):
            safe_file_copy(source, target)
