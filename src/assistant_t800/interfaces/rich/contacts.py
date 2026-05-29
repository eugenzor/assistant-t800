"""Rich contact list rendering."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Final

from rich import box
from rich.table import Table

from assistant_t800.domain.contacts import Contact
from assistant_t800.interfaces.cli.metrics import NARROW_LAYOUT_WIDTH, get_actual_width
from assistant_t800.localization import Message

if TYPE_CHECKING:
    from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter

EMPTY_VALUE: Final[str] = "--"
MULTI_VALUE_SUFFIX: Final[str] = "…"


def display_contacts_table(
    presenter: "RichCliPresenter",
    contacts: Sequence[Contact],
    *,
    title: str,
) -> None:
    """Display contacts as a Rich table."""
    table = build_contacts_table(table_cls=presenter.table_cls, contacts=contacts)

    presenter.display_results_title(title)
    presenter.console.print(table)
    presenter.display_prompt_spacing()


def is_contact_list(data: object) -> bool:
    """Return whether payload is a contact list."""
    result = isinstance(data, list) and all(isinstance(item, Contact) for item in data)

    return result


def build_contacts_table(
    *,
    table_cls: type,
    contacts: Sequence[Contact],
    width: int | None = None,
) -> Table:
    """Build contacts table."""
    resolved_width = width if width is not None else get_actual_width()
    is_narrow = NARROW_LAYOUT_WIDTH > resolved_width

    table = table_cls(
        box=box.SIMPLE,
        border_style="grey35",
        header_style="white",
        row_styles=("", "dim"),
        expand=False,
        width=resolved_width,
    )

    # table.add_column("№", justify="right", no_wrap=True, width=2)
    table.add_column(str(Message.CONTACT_NAME), style="bold green")
    table.add_column(str(Message.CONTACT_PHONE))
    table.add_column(str(Message.CONTACT_EMAIL))

    if not is_narrow:
        table.add_column(str(Message.CONTACT_BIRTHDAY))

    for index, contact in enumerate(contacts, start=1):
        row = [
            # str(index),
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


def _render_first_value(values: Sequence[object]) -> str:
    """Return first value with ellipsis marker when multiple values exist."""
    if not values:
        result = EMPTY_VALUE
    else:
        result = str(values[0])

        if len(values) > 1:
            result = f"{result}{MULTI_VALUE_SUFFIX}"

    return result
