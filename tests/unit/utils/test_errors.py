import pytest

from src.utils.errors import (
    DirectoryCreationError,
    ExtensionError,
    FileOperationError,
    InvalidProjectNameError,
    KickstartError,
    LanguageNotSupportedError,
    MissingCreateArgumentsError,
    ProjectCreationError,
    TemplateError,
    UnsupportedOptionError,
    UnsupportedProjectTypeError,
)

SUBCLASSES = (
    ProjectCreationError,
    TemplateError,
    DirectoryCreationError,
    FileOperationError,
    LanguageNotSupportedError,
    InvalidProjectNameError,
    UnsupportedProjectTypeError,
    UnsupportedOptionError,
    MissingCreateArgumentsError,
    ExtensionError,
)


def test_kickstart_error_without_context_str_is_just_message():
    error = KickstartError("something failed")
    assert str(error) == "something failed"
    assert error.message == "something failed"
    assert error.context == {}


def test_kickstart_error_with_context_appends_it_to_str():
    error = KickstartError("something failed", {"path": "/tmp/x", "attempt": 2})
    assert str(error) == "something failed (context: path=/tmp/x, attempt=2)"


def test_kickstart_error_context_is_mutable_copy():
    context = {"key": "value"}
    error = KickstartError("failed", context)
    error.context["key"] = "changed"
    assert context["key"] == "value"


@pytest.mark.parametrize("error_cls", SUBCLASSES)
def test_subclasses_are_kickstart_errors(error_cls):
    error = error_cls("boom")
    assert isinstance(error, KickstartError)
    assert str(error) == "boom"
