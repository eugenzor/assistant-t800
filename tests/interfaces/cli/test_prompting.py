"""Unit tests for CLI prompting factories."""

from assistant_t800.interfaces.cli.prompting import InputFactory


def test_create_base_falls_back_to_plain_input_without_prompt_toolkit(monkeypatch):
    factory = InputFactory()
    factory._prompt_toolkit_available = False
    factory._prompt_toolkit_error = RuntimeError("disabled")

    result = factory.create_base(["help", "birthdays"])

    assert result is input


def test_create_editable_fallback_returns_empty_text_for_empty_input(monkeypatch):
    factory = InputFactory()
    factory._prompt_toolkit_available = False
    monkeypatch.setattr("builtins.input", lambda prompt: "")

    edit = factory.create_editable()

    assert edit("Tags:", "work, usa") == ""


def test_create_text_fallback_keeps_default_on_empty_input(monkeypatch):
    factory = InputFactory()
    factory._prompt_toolkit_available = False
    monkeypatch.setattr("builtins.input", lambda prompt: "")

    text_input = factory.create_text()

    assert text_input("Note:", "Existing note") == "Existing note"


def test_create_text_fallback_returns_entered_value(monkeypatch):
    factory = InputFactory()
    factory._prompt_toolkit_available = False
    monkeypatch.setattr("builtins.input", lambda prompt: "New note")

    text_input = factory.create_text()

    assert text_input("Note:", "Existing note") == "New note"


def test_create_editable_fallback_returns_entered_value(monkeypatch):
    factory = InputFactory()
    factory._prompt_toolkit_available = False
    monkeypatch.setattr("builtins.input", lambda prompt: "work, usa")

    edit = factory.create_editable()

    assert edit("Tags:", "old") == "work, usa"
