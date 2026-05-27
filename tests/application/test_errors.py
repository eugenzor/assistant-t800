"""Unit tests for application exceptions in ``assistant_t800.application.errors``."""

import pytest

from assistant_t800.application.errors import AppError, CommandError
from assistant_t800.localization import ErrorCode


# ---------- AppError ----------


def test_app_error_stores_code_and_params():
    error = AppError(ErrorCode.CONTACT_NOT_FOUND, name="Іван")

    assert error.code is ErrorCode.CONTACT_NOT_FOUND
    assert error.params == {"name": "Іван"}


def test_app_error_string_representation_is_code_name():
    error = AppError(ErrorCode.UNKNOWN_COMMAND, command="foo")

    assert str(error) == ErrorCode.UNKNOWN_COMMAND.name


def test_app_error_without_params_has_empty_params():
    error = AppError(ErrorCode.EMPTY_COMMAND)

    assert error.params == {}


def test_app_error_is_an_exception():
    with pytest.raises(AppError):
        raise AppError(ErrorCode.UNKNOWN_COMMAND, command="foo")


# ---------- CommandError ----------


def test_command_error_is_an_app_error():
    error = CommandError(ErrorCode.INVALID_COMMAND_SYNTAX, reason="oops")

    assert isinstance(error, AppError)


def test_command_error_preserves_code_and_params():
    error = CommandError(ErrorCode.INVALID_COMMAND_SYNTAX, reason="oops")

    assert error.code is ErrorCode.INVALID_COMMAND_SYNTAX
    assert error.params == {"reason": "oops"}