"""Rich contact details card rendering for the Textual interface."""

from collections.abc import Iterable
from textwrap import wrap
from typing import Final

from assistant_t800.application.enums import SystemValue
from assistant_t800.domain.contacts import Contact

EMPTY_VALUE: Final[str] = "--"
LABEL_WIDTH: Final[int] = 18


def build_contact_panel(*, panel_cls, text_cls, contact: Contact, width: int):
    """Build a contact details panel sized to ``width``.

    ``panel_cls`` and ``text_cls`` are the Rich ``Panel`` and ``Text`` classes,
    injected so this module stays free of a hard Rich import at call sites.
    """
    content = text_cls()

    _append_title(content, contact)
    _append_separator(content, width)

    for label, value in _main_rows(contact):
        _append_field(content, label, value, width)

    if _has_note(contact):
        _append_separator(content, width)
        _append_section_title(content, "▣", "Нотатка")
        _append_wrapped_text(content, contact.note, width)

    if contact.tags:
        _append_separator(content, width)
        _append_section_title(content, "◇", "Теги")
        _append_wrapped_text(content, "; ".join(sorted(contact.tags)), width)

    panel = panel_cls(
        content,
        border_style="cyan",
        padding=(0, 2),
        width=width,
    )

    return panel


def _append_title(content, contact: Contact) -> None:
    """Append contact card title."""
    content.append("◎  ", style="cyan")
    content.append(contact.name.value, style="bold white")
    content.append("\n")


def _append_separator(content, width: int) -> None:
    """Append section separator."""
    line_width = max(24, width - 8)
    content.append("─" * line_width, style="cyan")
    content.append("\n")


def _main_rows(contact: Contact) -> tuple[tuple[str, str], ...]:
    """Return main contact rows."""
    rows = (
        (
            "Телефон",
            _join_values(str(item) for item in contact.phones),
        ),
        (
            "Email",
            _join_values(item.value for item in contact.emails),
        ),
        (
            "Адреса",
            contact.formatted_address if contact.address is not None else EMPTY_VALUE,
        ),
        (
            "День народження",
            str(contact.birthday) if contact.birthday is not None else EMPTY_VALUE,
        ),
    )

    return rows


def _append_field(content, label: str, value: str, width: int) -> None:
    """Append wrapped key-value row."""
    value_width = max(20, width - LABEL_WIDTH - 10)
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


def _append_wrapped_text(content, value: str, width: int) -> None:
    """Append multiline wrapped text."""
    text_width = max(20, width - 12)

    for paragraph in value.splitlines() or [EMPTY_VALUE]:
        lines = wrap(paragraph, width=text_width) or [""]
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
