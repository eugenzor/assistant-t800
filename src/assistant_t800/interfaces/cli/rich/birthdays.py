"""Rich upcoming birthdays rendering."""

from collections.abc import Sequence
from typing import TYPE_CHECKING

from rich import box

from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.interfaces.cli.metrics import get_actual_width, is_narrow_layout
from assistant_t800.localization import Message

if TYPE_CHECKING:
    from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter


def display_birthdays_table(
    presenter: "RichCliPresenter",
    contacts: Sequence[BirthdaysListContact],
    *,
    title: str,
) -> None:
    """Display upcoming birthdays as a Rich table."""
    presenter.display_results_title(title)
    presenter.console.print(_build_birthdays_table(presenter, contacts))
    presenter.display_prompt_spacing()


def is_birthdays_list(data: object) -> bool:
    """Return whether payload is an upcoming birthdays list."""
    result = isinstance(data, list) and all(
        isinstance(item, BirthdaysListContact) for item in data
    )

    return result


def _build_birthdays_table(
    presenter: "RichCliPresenter",
    contacts: Sequence[BirthdaysListContact],
):
    """Build upcoming birthdays table."""
    table = presenter.table_cls(
        box=box.SIMPLE,
        border_style="grey35",
        header_style="white",
        row_styles=("", "dim"),
        expand=False,
        width=get_actual_width(),
    )

    table.add_column(str(Message.CONTACT_NAME), style="bold green")
    table.add_column(str(Message.CONTACT_BIRTHDAY), style="white")

    if not is_narrow_layout():
        table.add_column("Вік", justify="right", style="white")

    table.add_column("Вітати", style="bold white")

    for contact in contacts:
        row = [
            contact.name,
            contact.birthday,
        ]

        if not is_narrow_layout():
            row.append(contact.age)

        row.append(contact.congratulation_date)
        table.add_row(*row)

    return table
