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


def test_kickstart_error_context_defaults_to_empty_dict_when_none():
    error = KickstartError("failed", None)
    assert error.context == {}


def test_kickstart_error_context_is_mutable_copy():
    context = {"key": "value"}
    error = KickstartError("failed", context)
    error.context["key"] = "changed"
    assert context["key"] == "value"


def test_kickstart_error_is_an_exception():
    with pytest.raises(KickstartError):
        raise KickstartError("boom")


@pytest.mark.parametrize("error_cls", SUBCLASSES)
def test_subclasses_are_kickstart_errors(error_cls):
    error = error_cls("boom")
    assert isinstance(error, KickstartError)
    assert str(error) == "boom"


@pytest.mark.parametrize("error_cls", SUBCLASSES)
def test_subclasses_carry_context_in_str(error_cls):
    error = error_cls("boom", {"k": "v"})
    assert str(error) == "boom (context: k=v)"


def test_subclasses_are_distinguishable_from_each_other():
    assert not isinstance(ProjectCreationError("x"), TemplateError)
    assert not isinstance(TemplateError("x"), ProjectCreationError)


def test_kickstart_error_chains_cause():
    original = ValueError("root cause")
    try:
        try:
            raise original
        except ValueError as exc:
            raise KickstartError("wrapped") from exc
    except KickstartError as error:
        assert error.__cause__ is original
