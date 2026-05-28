"""Unit tests for application enums in ``assistant_t800.application.enums``."""

from enum import Enum

from assistant_t800.application.enums import InterfaceMode, SystemValue


# ---------- SystemValue ----------


def test_system_value_is_enum():
    assert issubclass(SystemValue, Enum)


def test_system_value_empty_text_is_zero_width_space():
    assert SystemValue.EMPTY_TEXT.value == "\u200b"


def test_system_value_multi_value_separators_contain_semicolon_and_comma():
    separators = SystemValue.MULTI_VALUE_SEPARATORS.value

    assert ";" in separators
    assert "," in separators


def test_system_value_date_separators_contain_dash_slash_and_dot():
    separators = SystemValue.DATE_VALUE_SEPARATORS.value

    assert "-" in separators
    assert "/" in separators
    assert "." in separators


def test_system_value_members_are_distinct():
    values = {member.value for member in SystemValue}

    assert len(values) == len(list(SystemValue))


# ---------- InterfaceMode ----------


def test_interface_mode_is_enum():
    assert issubclass(InterfaceMode, Enum)


def test_interface_mode_cli_value():
    assert InterfaceMode.CLI.value == "cli"


def test_interface_mode_tui_value():
    assert InterfaceMode.TUI.value == "tui"


def test_interface_mode_lookup_by_value():
    assert InterfaceMode("cli") is InterfaceMode.CLI
    assert InterfaceMode("tui") is InterfaceMode.TUI


def test_interface_mode_members_count():
    assert len(list(InterfaceMode)) == 2
