"""Rich contact list rendering for the Textual interface."""

from collections.abc import Sequence
from typing import Final

from rich import box

from assistant_t800.domain.contacts import Contact

EMPTY_VALUE: Final[str] = "--"
MULTI_VALUE_SUFFIX: Final[str] = "…"
NARROW_LAYOUT_WIDTH: Final[int] = 100


def build_contacts_table(*, table_cls, contacts: Sequence[Contact], width: int):
    """Build a contacts table sized to ``width``.

    ``table_cls`` is the Rich ``Table`` class, injected by the caller. The
    birthday column is dropped on narrow layouts to keep rows readable.
    """
    is_narrow = _is_narrow(width)

    table = table_cls(
        box=box.SIMPLE,
        border_style="grey35",
        header_style="white",
        row_styles=("", "dim"),
        expand=False,
        width=width,
    )

    table.add_column("Ім'я", style="bold green")
    table.add_column("Телефон")
    table.add_column("Email")

    if not is_narrow:
        table.add_column("День народження")

    for contact in contacts:
        row = [
            contact.name.value,
            _render_first_value(contact.phones),
            _render_first_value(contact.emails),
        ]

        if not is_narrow:
            row.append(
                str(contact.birthday) if contact.birthday is not None else EMPTY_VALUE
            )

        table.add_row(*row)

    return table


def _is_narrow(width: int) -> bool:
    """Return whether the layout should drop optional columns."""
    return width < NARROW_LAYOUT_WIDTH


def _render_first_value(values: Sequence[object]) -> str:
    """Return first value with ellipsis marker when multiple values exist."""
    if not values:
        result = EMPTY_VALUE
    else:
        result = str(values[0])

        if len(values) > 1:
            result = f"{result}{MULTI_VALUE_SUFFIX}"

    return result
