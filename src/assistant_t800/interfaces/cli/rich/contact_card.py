"""Rich contact details card rendering."""

from collections.abc import Iterable
from textwrap import wrap
from typing import TYPE_CHECKING, Final

from assistant_t800.application.enums import SystemValue
from assistant_t800.domain.contacts import Contact
from assistant_t800.interfaces.cli.metrics import get_actual_width
from assistant_t800.localization import Message

if TYPE_CHECKING:
    from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter

EMPTY_VALUE: Final[str] = "--"
LABEL_WIDTH: Final[int] = 18


def display_contact_card(presenter: "RichCliPresenter", contact: Contact) -> None:
    """Display one contact as a Rich details card."""
    presenter.console.print(_build_contact_panel(presenter, contact))


def is_contact(data: object) -> bool:
    """Return whether payload is a contact."""
    result = isinstance(data, Contact)

    return result


def _build_contact_panel(presenter: "RichCliPresenter", contact: Contact):
    """Build contact details panel."""
    content = presenter.text_cls()

    _append_title(content, presenter, contact)
    _append_separator(content, presenter)

    for row in _main_rows(contact):
        _append_field(content, *row)

    if _has_note(contact):
        _append_separator(content, presenter)
        _append_section_title(content, "▣", str(Message.CONTACT_NOTE))
        _append_wrapped_text(content, contact.note)

    if contact.tags:
        _append_separator(content, presenter)
        _append_section_title(content, "◇", str(Message.CONTACT_TAGS))
        _append_wrapped_text(content, "; ".join(sorted(contact.tags)))

    panel = presenter.panel_cls(
        content,
        border_style="cyan",
        padding=(0, 2),
        width=get_actual_width(),
    )

    return panel


def _append_title(content, presenter: "RichCliPresenter", contact: Contact) -> None:
    """Append contact card title."""
    content.append("◎  ", style="cyan")
    content.append(contact.name.value, style="bold white")
    content.append("\n")


def _append_separator(content, presenter: "RichCliPresenter") -> None:
    """Append section separator."""
    width = max(24, get_actual_width() - 8)
    content.append("─" * width, style="cyan")
    content.append("\n")


def _main_rows(contact: Contact) -> tuple[tuple[str, str], ...]:
    """Return main contact rows."""
    rows = (
        (
            str(Message.CONTACT_PHONE),
            _join_values(str(item) for item in contact.phones),
        ),
        (
            str(Message.CONTACT_EMAIL),
            _join_values(item.value for item in contact.emails),
        ),
        (
            str(Message.CONTACT_ADDRESS),
            contact.formatted_address if contact.address is not None else EMPTY_VALUE,
        ),
        (
            str(Message.CONTACT_BIRTHDAY),
            str(contact.birthday) if contact.birthday is not None else EMPTY_VALUE,
        ),
    )

    return rows


def _append_field(content, label: str, value: str) -> None:
    """Append wrapped key-value row."""
    value_width = max(20, get_actual_width() - LABEL_WIDTH - 10)
    lines = wrap(value, width=value_width) or [EMPTY_VALUE]

    content.append(f"{label:<{LABEL_WIDTH}}", style="bold white")
    content.append(" : ", style="cyan")
    content.append(lines[0], style="white")
    content.append("\n")

    for line in lines[1:]:
        content.append(f"{'':<{LABEL_WIDTH}}", style="bold white")
        content.append("   ", style="cyan")
        content.append(line, style="white")
        content.append("\n")


def _append_section_title(content, icon: str, title: str) -> None:
    """Append section title."""
    content.append(f"{icon}  ", style="cyan")
    content.append(title, style="bold cyan")
    content.append("\n")


def _append_wrapped_text(content, value: str) -> None:
    """Append multiline wrapped text."""
    width = max(20, get_actual_width() - 12)

    for paragraph in value.splitlines() or [EMPTY_VALUE]:
        lines = wrap(paragraph, width=width) or [""]
        for line in lines:
            content.append("   ")
            content.append(line, style="white")
            content.append("\n")


def _join_values(values: Iterable[str]) -> str:
    """Join values or return an empty marker."""
    result = "; ".join(values) or EMPTY_VALUE

    return result


def _has_note(contact: Contact) -> bool:
    """Return whether contact has a user-facing note."""
    result = bool(contact.note and contact.note != SystemValue.EMPTY_TEXT.value)

    return result
