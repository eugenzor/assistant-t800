"""Презентер для Textual TUI: виводить дані у віджет ``RichLog``.

Реалізує контракт ``Presenter``, очікуваний AI-агентом, і безпечно
викликає UI-методи з потоку воркера через ``call_from_thread``.
"""

from textual.widgets import RichLog

from assistant_t800.domain.contacts import Contact


class TextualPresenter:
    """Презентер, що використовує віджет ``RichLog`` у Textual-застосунку.

    Усі оновлення UI відбуваються через ``call_from_thread``, щоб
    безпечно працювати з UI-потоком із фонових воркерів.
    """

    def __init__(self, log: RichLog, app) -> None:
        """Зберігає посилання на лог-віджет і сам застосунок Textual."""
        self._log = log
        self._app = app

    def refresh_contacts(self, contacts: list[Contact]) -> None:
        """Перерисовує панель списком контактів."""
        # Виконуємо рендер у UI-потоці
        self._app.call_from_thread(self._render_contacts, contacts)

    def print(self, text: str) -> None:
        """Виводить довільний текст у панель відображення."""
        self._app.call_from_thread(self._render_text, text)

    def _render_contacts(self, contacts: list[Contact]) -> None:
        """Внутрішній рендер списку контактів у віджет ``RichLog``."""
        self._log.clear()
        if not contacts:
            # Спеціальне повідомлення, коли список порожній
            self._log.write("[dim]Контактів немає.[/dim]")
            return
        for idx, contact in enumerate(contacts, start=1):
            self._log.write(f"[bold]{idx}. {contact.name.value}[/bold]")
            if contact.phones:
                self._log.write(
                    "   телефони: " + ", ".join(p.value for p in contact.phones)
                )
            if contact.emails:
                self._log.write(
                    "   e-mail: " + ", ".join(e.value for e in contact.emails)
                )
            if contact.address is not None:
                self._log.write(f"   адреса: {contact.address.value}")
            if contact.birthday is not None:
                self._log.write(f"   день народження: {contact.birthday}")

    def _render_text(self, text: str) -> None:
        """Внутрішній рендер довільного тексту: очищує панель і пише новий."""
        self._log.clear()
        self._log.write(text)
