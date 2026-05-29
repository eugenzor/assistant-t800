"""Unit tests for ``MultiLang`` in ``assistant_t800.localization.multilang``."""

from configparser import ConfigParser
from enum import Enum, auto
from pathlib import Path


from assistant_t800.application.results import AppMessage
from assistant_t800.localization.messages import ErrorCode, Message
from assistant_t800.localization.multilang import MultiLang, render_message


# ---------- MultiLang.get: returns strings for known keys ----------


def test_multilang_get_returns_non_empty_string_for_message_member():
    text = MultiLang.get(Message.GOOD_BYE)

    assert isinstance(text, str)
    assert text != ""


def test_multilang_get_returns_non_empty_string_for_error_code_member():
    text = MultiLang.get(ErrorCode.UNKNOWN_COMMAND)

    assert isinstance(text, str)
    assert text != ""


# ---------- MultiLang.get: fallback for unknown keys ----------


class _UnknownEnum(Enum):
    NOT_A_REAL_KEY = auto()


def test_multilang_get_uses_section_dot_key_fallback_for_unknown_member():
    text = MultiLang.get(_UnknownEnum.NOT_A_REAL_KEY)

    assert text == "_UnknownEnum.NOT_A_REAL_KEY"


# ---------- MultiLang.get: escape sequence expansion ----------


def test_multilang_get_expands_literal_backslash_n(monkeypatch, tmp_path):
    """Values with a literal ``\\n`` must expand to a real newline."""
    fake_locale_dir = tmp_path
    (fake_locale_dir / "en.ini").write_text(
        "[_FakeMessage]\nGREET = first\\nsecond\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(MultiLang, "LOCALE_DIR", fake_locale_dir)
    monkeypatch.setattr(MultiLang, "_storage", {})

    class _FakeMessage(Enum):
        GREET = auto()

    text = MultiLang.get(_FakeMessage.GREET)

    assert text == "first\nsecond"


def test_multilang_get_expands_literal_backslash_t_to_spaces(monkeypatch, tmp_path):
    """Values with literal ``\\t`` expand to four spaces, not a tab character."""
    fake_locale_dir = tmp_path
    (fake_locale_dir / "en.ini").write_text(
        "[_TabbedMessage]\nINDENT = before\\tafter\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(MultiLang, "LOCALE_DIR", fake_locale_dir)
    monkeypatch.setattr(MultiLang, "_storage", {})

    class _TabbedMessage(Enum):
        INDENT = auto()

    text = MultiLang.get(_TabbedMessage.INDENT)

    assert text == "before    after"


# ---------- MultiLang._load: storage is cached per language ----------


def test_multilang_load_caches_config_per_language(monkeypatch, tmp_path):
    fake_locale_dir = tmp_path
    (fake_locale_dir / "en.ini").write_text(
        "[X]\nA = 1\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(MultiLang, "LOCALE_DIR", fake_locale_dir)
    monkeypatch.setattr(MultiLang, "_storage", {})

    first = MultiLang._load("en")
    second = MultiLang._load("en")

    assert first is second


def test_multilang_load_falls_back_to_default_when_language_missing(
    monkeypatch, tmp_path
):
    """When a non-default language file is absent, defaults must still load."""
    fake_locale_dir = tmp_path
    (fake_locale_dir / "en.ini").write_text(
        "[Section]\nKEY = english\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(MultiLang, "LOCALE_DIR", fake_locale_dir)
    monkeypatch.setattr(MultiLang, "_storage", {})

    # "xx" has no INI file — defaults must still be available.
    config = MultiLang._load("xx")

    assert config.get("Section", "KEY") == "english"


def test_multilang_load_overrides_default_when_language_file_present(
    monkeypatch, tmp_path
):
    fake_locale_dir = tmp_path
    (fake_locale_dir / "en.ini").write_text(
        "[Section]\nKEY = english\nOTHER = shared\n",
        encoding="utf-8",
    )
    (fake_locale_dir / "uk.ini").write_text(
        "[Section]\nKEY = українська\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(MultiLang, "LOCALE_DIR", fake_locale_dir)
    monkeypatch.setattr(MultiLang, "_storage", {})

    config = MultiLang._load("uk")

    assert config.get("Section", "KEY") == "українська"
    # Keys not overridden remain from the default language.
    assert config.get("Section", "OTHER") == "shared"


# ---------- MultiLang._get_value: fallback formatting ----------


def test_multilang_get_value_returns_section_dot_key_when_missing():
    config = ConfigParser()
    config.add_section("Section")

    result = MultiLang._get_value(config, "Section", "MISSING")

    assert result == "Section.MISSING"


def test_multilang_get_value_returns_stored_value_when_present():
    config = ConfigParser()
    config.add_section("Section")
    config.set("Section", "KEY", "value")

    result = MultiLang._get_value(config, "Section", "KEY")

    assert result == "value"


# ---------- MultiLang._detect_posix_language ----------


def test_detect_posix_language_returns_two_letter_code_for_locale(monkeypatch):
    monkeypatch.setattr(
        "assistant_t800.localization.multilang.getlocale",
        lambda: ("uk_UA", "UTF-8"),
    )

    assert MultiLang._detect_posix_language() == "uk"


def test_detect_posix_language_returns_en_when_locale_is_empty(monkeypatch):
    monkeypatch.setattr(
        "assistant_t800.localization.multilang.getlocale",
        lambda: (None, None),
    )

    assert MultiLang._detect_posix_language() == "en"


def test_detect_posix_language_returns_full_string_when_no_underscore(monkeypatch):
    monkeypatch.setattr(
        "assistant_t800.localization.multilang.getlocale",
        lambda: ("en", None),
    )

    assert MultiLang._detect_posix_language() == "en"


# ---------- MultiLang.LOCALE_DIR ----------


def test_multilang_locale_dir_exists():
    assert isinstance(MultiLang.LOCALE_DIR, Path)
    assert MultiLang.LOCALE_DIR.is_dir()


def test_multilang_default_language_file_exists():
    default_file = MultiLang.LOCALE_DIR / f"{MultiLang.DEFAULT_LANGUAGE}.ini"

    assert default_file.is_file()


# ---------- render_message ----------


def test_render_message_returns_empty_string_for_none():
    assert render_message(None) == ""


def test_render_message_renders_without_params():
    message = AppMessage(code=Message.HELP)

    result = render_message(message)

    assert isinstance(result, str)
    assert result != ""


def test_render_message_formats_params_into_template():
    message = AppMessage(
        code=Message.CONTACT_ADDED,
        params={"name": "Іван"},
    )

    result = render_message(message)

    assert "Іван" in result


def test_render_message_handles_error_code_messages():
    message = AppMessage(
        code=ErrorCode.CONTACT_NOT_FOUND,
        params={"name": "Невідомий"},
    )

    result = render_message(message)

    assert isinstance(result, str)
    assert result != ""
