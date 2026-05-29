"""Textual presenter implementation for the AI agent."""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widgets import RichLog

from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact
from assistant_t800.interfaces.cli.metrics import get_actual_width
from assistant_t800.interfaces.rich.contact_card import build_contact_panel
from assistant_t800.interfaces.rich.contacts import build_contacts_table
from assistant_t800.localization import Message


class TextualPresenter:
    """Presenter that renders agent output into a Textual ``RichLog`` widget."""

    def __init__(self, log: RichLog, app) -> None:
        """Store Textual UI dependencies."""
        self._log = log
        self._app = app

    def refresh_contacts(self, contacts: list[Contact]) -> None:
        """Render contacts in the display panel."""
        # Tool calls may run from a worker thread, so UI updates must be proxied.
        self._app.call_from_thread(self._render_contacts, contacts)

    def refresh_contact(self, contact: Contact) -> None:
        """Render one contact as a card in the display panel."""
        self._app.call_from_thread(self._render_contact, contact)

    def refresh_birthdays(self, birthdays: list[BirthdaysListContact]) -> None:
        """Render upcoming birthdays in the display panel."""
        self._app.call_from_thread(self._render_birthdays, birthdays)

    def print(self, text: str) -> None:
        """Render arbitrary text in the display panel."""
        self._app.call_from_thread(self._render_text, text)

    def _render_contacts(self, contacts: list[Contact]) -> None:
        """Render the contact list into the display log."""
        self._log.clear()
        self._log.write(
            Message.CONTACTS_LISTED.render(count=len(contacts)),
            expand=False,
        )
        self._log.write(
            build_contacts_table(
                table_cls=Table,
                contacts=contacts,
                width=self._display_table_width(),
            ),
            expand=False,
        )

    def _render_contact(self, contact: Contact) -> None:
        """Render one contact card into the display log."""
        self._log.clear()
        self._log.write(
            build_contact_panel(
                panel_cls=Panel,
                text_cls=Text,
                contact=contact,
                width=self._display_table_width(),
            ),
            expand=False,
        )

    def _display_table_width(self) -> int:
        """Return width for Rich tables in the display pane."""
        pane_width = self._log.size.width
        if pane_width > 0:
            return max(pane_width - 2, 1)

        return get_actual_width()

    def _render_birthdays(self, birthdays: list[BirthdaysListContact]) -> None:
        """Render upcoming birthdays into the display log."""
        self._log.clear()

        if not birthdays:
            self._log.write("[dim]Найближчих днів народження немає.[/dim]")
            return

        for item in birthdays:
            self._log.write(
                Message.BIRTHDAY_LIST_ITEM.render(
                    name=item.name,
                    birthday=item.birthday,
                    age=item.age,
                    congratulation_date=item.congratulation_date,
                )
            )

    def _render_text(self, text: str) -> None:
        """Replace display panel content with arbitrary text."""
        self._log.clear()
        self._log.write(text)
