"""Unit tests for Rich inline edit renderers."""

from dataclasses import dataclass, field

from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.interfaces.rich.inline_edit import (
    request_note_edit,
    request_tag_edit,
)
from assistant_t800.interfaces.rich.inline_hint import display_inline_hint


@dataclass
class FakeConsole:
    """Capture printed Rich renderables."""

    items: list[object] = field(default_factory=list)

    def print(self, *objects: object) -> None:
        self.items.extend(objects)


class FakeText:
    """Small stand-in for Rich Text."""

    def __init__(self, text: str = "", **params: object) -> None:
        self.text = text
        self.params = params

    def append(self, text: str, **params: object) -> None:
        self.text += text

    def __str__(self) -> str:
        return self.text


class FakePanel:
    """Small stand-in for Rich Panel."""

    def __init__(self, renderable: object, **params: object) -> None:
        self.renderable = renderable
        self.params = params


class FakePresenter:
    """Presenter surface required by inline edit renderers."""

    def __init__(self) -> None:
        self.console = FakeConsole()
        self.panel_cls = FakePanel
        self.text_cls = FakeText
        self.header_calls = 0

    def display_results_header(self) -> None:
        self.header_calls += 1


def test_display_inline_hint_uses_square_light_bar():
    presenter = FakePresenter()

    display_inline_hint(presenter, "Enter → save")

    assert len(presenter.console.items) == 1
    panel = presenter.console.items[0]
    assert isinstance(panel, FakePanel)
    assert panel.params["border_style"] == "grey50"
    assert panel.params["style"] == "white"
    assert panel.params["padding"] == (0, 1)
    assert str(panel.renderable) == "Enter → save"


def test_request_tag_edit_displays_contact_then_hint_and_calls_editable_input():
    presenter = FakePresenter()
    contact = Contact(Name("John Smith"))
    captured: dict[str, str] = {}

    def editable_func(prompt: str, default: str) -> str:
        captured["prompt"] = prompt
        captured["default"] = default

        return "work; usa"

    result = request_tag_edit(
        presenter,
        contact=contact,
        current_tags="old",
        editable_func=editable_func,
    )

    assert result == "work; usa"
    assert presenter.header_calls == 1
    assert captured["prompt"].strip() == ">"
    assert captured["default"] == "old"
    assert len(presenter.console.items) >= 2


def test_request_note_edit_displays_contact_then_hint_and_calls_text_input():
    presenter = FakePresenter()
    contact = Contact(Name("Аліса"))
    captured: dict[str, str] = {}

    def text_input_func(prompt: str, default: str) -> str:
        captured["prompt"] = prompt
        captured["default"] = default

        return "оновлена нотатка"

    result = request_note_edit(
        presenter,
        contact=contact,
        current_note="стара нотатка",
        text_input_func=text_input_func,
    )

    assert result == "оновлена нотатка"
    assert presenter.header_calls == 1
    assert captured["prompt"].strip() == ">"
    assert captured["default"] == "стара нотатка"
    assert len(presenter.console.items) >= 2
