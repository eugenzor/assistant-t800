"""Rich upcoming birthdays rendering for the Textual interface."""

from collections.abc import Sequence
from typing import Final

from rich import box

from assistant_t800.domain.birthdays import BirthdaysListContact

NARROW_LAYOUT_WIDTH: Final[int] = 100


def build_birthdays_table(
    *,
    table_cls,
    contacts: Sequence[BirthdaysListContact],
    width: int,
):
    """Build an upcoming birthdays table sized to ``width``.

    ``table_cls`` is the Rich ``Table`` class, injected by the caller. The age
    column is dropped on narrow layouts to keep rows readable.
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
    table.add_column("День народження", style="white")

    if not is_narrow:
        table.add_column("Вік", justify="right", style="white")

    table.add_column("Вітати", style="bold white")

    for contact in contacts:
        row = [
            contact.name,
            contact.birthday,
        ]

        if not is_narrow:
            row.append(contact.age)

        row.append(contact.congratulation_date)
        table.add_row(*row)

    return table


def _is_narrow(width: int) -> bool:
    """Return whether the layout should drop optional columns."""
    return width < NARROW_LAYOUT_WIDTH
