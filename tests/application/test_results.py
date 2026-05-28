"""Unit tests for application result builders in ``assistant_t800.application.results``."""

from assistant_t800.application.results import (
    AppConfirmation,
    AppMessage,
    AppResult,
)
from assistant_t800.localization import ErrorCode, Message


# ---------- AppMessage ----------


def test_app_message_defaults_to_empty_params():
    message = AppMessage(code=Message.HELP)

    assert message.params == {}


def test_app_message_preserves_supplied_params():
    message = AppMessage(code=Message.HELP, params={"name": "Іван"})

    assert message.params == {"name": "Іван"}


# ---------- AppResult.ok ----------


def test_ok_without_message_yields_success_without_payload():
    result = AppResult.ok()

    assert result.success is True
    assert result.message is None
    assert result.data is None
    assert result.should_exit is False
    assert result.confirmation is None


def test_ok_with_message_wraps_params():
    result = AppResult.ok(Message.CONTACT_ADDED, name="Іван")

    assert result.success is True
    assert result.message is not None
    assert result.message.code is Message.CONTACT_ADDED
    assert result.message.params == {"name": "Іван"}


def test_ok_preserves_data_and_exit_flag():
    result = AppResult.ok(Message.GOOD_BYE, data=42, should_exit=True)

    assert result.data == 42
    assert result.should_exit is True


# ---------- AppResult.fail ----------


def test_fail_builds_failed_result_with_error_code():
    result = AppResult.fail(ErrorCode.CONTACT_NOT_FOUND, name="Невідомий")

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND
    assert result.message.params == {"name": "Невідомий"}


def test_fail_has_no_confirmation():
    result = AppResult.fail(ErrorCode.UNKNOWN_COMMAND, command="foo")

    assert result.confirmation is None
    assert result.requires_confirmation is False


# ---------- AppResult.confirm ----------


def test_confirm_sets_confirmation_payload():
    result = AppResult.confirm(Message.CONFIRM_REMOVE_CONTACT, name="Іван")

    assert isinstance(result.confirmation, AppConfirmation)
    assert result.confirmation.message.code is Message.CONFIRM_REMOVE_CONTACT
    assert result.confirmation.message.params == {"name": "Іван"}


def test_confirm_is_not_successful():
    result = AppResult.confirm(Message.CONFIRM_REMOVE_CONTACT, name="Іван")

    assert result.success is False


def test_confirm_marks_requires_confirmation():
    result = AppResult.confirm(Message.CONFIRM_REMOVE_CONTACT, name="Іван")

    assert result.requires_confirmation is True


def test_ok_does_not_require_confirmation():
    result = AppResult.ok(Message.CONTACT_ADDED, name="Іван")

    assert result.requires_confirmation is False
