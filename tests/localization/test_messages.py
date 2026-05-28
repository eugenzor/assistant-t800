"""Unit tests for ``MultiLangEnum``-based enums in ``assistant_t800.localization.messages``."""

from enum import Enum, auto

import pytest

from assistant_t800.localization.messages import (
    APP_VERSION,
    ErrorCode,
    Message,
    MultiLangEnum,
)


# ---------- APP_VERSION ----------


def test_app_version_is_non_empty_string():
    assert isinstance(APP_VERSION, str)
    assert APP_VERSION != ""


# ---------- MultiLangEnum: structural sanity ----------


def test_message_is_subclass_of_multilang_enum():
    assert issubclass(Message, MultiLangEnum)


def test_error_code_is_subclass_of_multilang_enum():
    assert issubclass(ErrorCode, MultiLangEnum)


def test_message_members_are_distinct():
    values = {member.value for member in Message}

    assert len(values) == len(list(Message))


def test_error_code_members_are_distinct():
    values = {member.value for member in ErrorCode}

    assert len(values) == len(list(ErrorCode))


# ---------- .text property ----------


def test_message_text_is_string():
    assert isinstance(Message.GOOD_BYE.text, str)


def test_error_code_text_is_string():
    assert isinstance(ErrorCode.UNKNOWN_COMMAND.text, str)


def test_message_str_matches_text():
    assert str(Message.GOOD_BYE) == Message.GOOD_BYE.text


def test_error_code_str_matches_text():
    assert str(ErrorCode.UNKNOWN_COMMAND) == ErrorCode.UNKNOWN_COMMAND.text


# ---------- .render ----------


def test_render_returns_text_when_no_placeholders():
    assert Message.GOOD_BYE.render() == Message.GOOD_BYE.text


def test_render_substitutes_named_parameters():
    rendered = Message.CONTACT_ADDED.render(name="Іван")

    assert "Іван" in rendered


def test_render_substitutes_error_code_parameters():
    rendered = ErrorCode.CONTACT_NOT_FOUND.render(name="Невідомий")

    assert "Невідомий" in rendered


# ---------- .confirm_render ----------


def test_confirm_render_appends_yes_no_suffix():
    rendered = Message.CONFIRM_REMOVE_CONTACT.confirm_render(name="Іван")

    assert "Іван" in rendered
    assert str(Message.YES) in rendered
    assert str(Message.NO) in rendered
    assert rendered.endswith(": ")


def test_confirm_render_includes_parentheses():
    rendered = Message.CONFIRM_REMOVE_CONTACT.confirm_render(name="Іван")

    assert "(" in rendered
    assert ")" in rendered


# ---------- .confirm_check ----------


def test_confirm_check_accepts_full_yes_word():
    assert Message.CONFIRM_REMOVE_CONTACT.confirm_check(str(Message.YES)) is True


def test_confirm_check_accepts_yes_first_letter():
    assert Message.CONFIRM_REMOVE_CONTACT.confirm_check(str(Message.YES)[0]) is True


def test_confirm_check_accepts_english_yes():
    assert Message.CONFIRM_REMOVE_CONTACT.confirm_check("yes") is True


def test_confirm_check_accepts_english_y():
    assert Message.CONFIRM_REMOVE_CONTACT.confirm_check("y") is True


def test_confirm_check_accepts_uppercase():
    assert Message.CONFIRM_REMOVE_CONTACT.confirm_check("YES") is True


def test_confirm_check_strips_whitespace():
    assert Message.CONFIRM_REMOVE_CONTACT.confirm_check("  y  ") is True


def test_confirm_check_rejects_empty_string():
    assert Message.CONFIRM_REMOVE_CONTACT.confirm_check("") is False


def test_confirm_check_rejects_no():
    assert Message.CONFIRM_REMOVE_CONTACT.confirm_check("no") is False


def test_confirm_check_rejects_unrelated_text():
    assert Message.CONFIRM_REMOVE_CONTACT.confirm_check("maybe") is False


# ---------- custom MultiLangEnum subclass behavior ----------


class _CustomEnum(MultiLangEnum):
    KEY_A = auto()


def test_custom_subclass_text_falls_back_to_section_dot_key():
    """An unknown subclass with no INI section falls back to section.key text."""
    text = _CustomEnum.KEY_A.text

    assert text == "_CustomEnum.KEY_A"


def test_custom_subclass_render_without_params_returns_fallback():
    assert _CustomEnum.KEY_A.render() == "_CustomEnum.KEY_A"
