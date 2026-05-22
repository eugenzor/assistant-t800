"""Textual presenter implementation for the AI agent."""

from textual.widgets import RichLog

from assistant_t800.domain.contacts import Contact


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

    def print(self, text: str) -> None:
        """Render arbitrary text in the display panel."""
        self._app.call_from_thread(self._render_text, text)

    def _render_contacts(self, contacts: list[Contact]) -> None:
        """Render the contact list into the display log."""
        self._log.clear()

        if not contacts:
            self._log.write("[dim]Контактів немає.[/dim]")
            return

        for idx, contact in enumerate(contacts, start=1):
            self._log.write(f"[bold]{idx}. {contact.name.value}[/bold]")

            if contact.phones:
                self._log.write(
                    "   телефони: " + ", ".join(item.value for item in contact.phones)
                )

            if contact.emails:
                self._log.write(
                    "   e-mail: " + ", ".join(item.value for item in contact.emails)
                )

            if contact.address is not None:
                self._log.write(f"   адреса: {contact.address.value}")

            if contact.birthday is not None:
                self._log.write(f"   день народження: {contact.birthday}")

    def _render_text(self, text: str) -> None:
        """Replace display panel content with arbitrary text."""
        self._log.clear()
        self._log.write(text)
