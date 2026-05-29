"""Optional Rich-based CLI presenter."""

import os

from assistant_t800.application.commands import Command
from assistant_t800.application.results import AppResult, ResultStatus
from assistant_t800.domain.contacts import Contact
from assistant_t800.interfaces.cli.prompting import EditableInputFunc, TextInputFunc
from assistant_t800.interfaces.cli.presenter import CliPresenter
from assistant_t800.interfaces.rich.birthdays import (
    display_birthdays_table,
    is_birthdays_list,
)
from assistant_t800.interfaces.rich.contact_card import (
    display_contact_card,
    is_contact,
)
from assistant_t800.interfaces.rich.contacts import (
    display_contacts_table,
    is_contact_list,
)
from assistant_t800.interfaces.rich.header import (
    display_results_header,
    display_results_title,
    display_welcome_header,
)
from assistant_t800.interfaces.rich.help import display_help
from assistant_t800.interfaces.rich.inline_edit import (
    request_note_edit,
    request_tag_edit,
)
from assistant_t800.interfaces.rich.status import display_status
from assistant_t800.interfaces.rich.welcome import display_welcome
from assistant_t800.localization import Message, render_message


class RichCliPresenter:
    """Rich presenter facade with plain presenter fallback."""

    def __init__(self, fallback: CliPresenter) -> None:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        self._console = Console()
        self._panel_cls = Panel
        self._table_cls = Table
        self._text_cls = Text
        self._fallback = fallback

    @property
    def console(self):
        return self._console

    @property
    def panel_cls(self):
        return self._panel_cls

    @property
    def table_cls(self):
        return self._table_cls

    @property
    def text_cls(self):
        return self._text_cls

    def request_note_edit(
        self,
        *,
        contact: Contact,
        current_note: str,
        text_input_func: TextInputFunc,
    ) -> str | None:
        """Request note text for contact editing."""
        result = request_note_edit(
            self,
            contact=contact,
            current_note=current_note,
            text_input_func=text_input_func,
        )

        return result

    def request_tag_edit(
        self,
        *,
        contact: Contact,
        current_tags: str,
        editable_func: EditableInputFunc,
    ) -> str | None:
        """Request tag text for contact editing."""
        result = request_tag_edit(
            self,
            contact=contact,
            current_tags=current_tags,
            editable_func=editable_func,
        )

        return result

    def display_welcome_header(self) -> None:
        """Display Rich welcome header."""
        display_welcome_header(self)

    def display_welcome(self) -> None:
        """Display Rich welcome screen."""
        display_welcome(self)
        self.display_prompt_spacing()

    def display_results_header(self) -> None:
        """Display compact Rich results header."""
        display_results_header(self)

    def display_results_title(self, text: str | Message) -> None:
        """Display command execution results title."""
        display_results_title(self, text)

    def display_help(self, registry: dict[str, Command]) -> None:
        """Display Rich command help."""
        display_help(self, registry)

    def display_contacts(self, contacts: list[Contact]) -> None:
        """Display Rich contact list."""
        display_contacts_table(
            self,
            contacts,
            title=Message.CONTACTS_LISTED.render(count=len(contacts)),
        )

    def display_goodbye(self) -> None:
        """Display goodbye message."""
        self._fallback.display_goodbye()

    def display(self, result: AppResult) -> None:
        """Display one application result."""
        is_list = is_contact_list(result.data)
        is_birthdays = is_birthdays_list(result.data)

        if self._should_display_status(result, is_list, is_birthdays):
            display_status(self, result)

        if self._is_command_registry(result.data):
            self.display_help(result.data)
        elif is_contact(result.data):
            display_contact_card(self, result.data)
        elif is_list:
            self.display_contacts(result.data)
        elif is_birthdays:
            display_birthdays_table(
                self,
                result.data,
                title=render_message(result.message),
            )
        elif result.data is not None:
            self._fallback.display(result)

        self.display_prompt_spacing()

    @staticmethod
    def _should_display_status(
        result: AppResult,
        is_list: bool,
        is_birthdays: bool,
    ) -> bool:
        """Return whether a separate status panel should be displayed."""
        message_code = result.message.code if result.message is not None else None
        is_success_payload = (
            result.status == ResultStatus.SUCCESS and result.data is not None
        )
        is_found_contact = (
            is_contact(result.data) and message_code is Message.CONTACT_FOUND
        )
        should_display = not (
            (is_list and result.status == ResultStatus.SUCCESS)
            or (is_birthdays and result.status == ResultStatus.SUCCESS)
            or (is_success_payload and is_found_contact)
        )

        return should_display

    def display_prompt_spacing(self) -> None:
        """Display spacing before the next prompt."""
        self._console.print()

    def clear(self) -> None:
        """Clear terminal screen."""
        os.system("cls||clear")

    @staticmethod
    def _is_command_registry(data: object) -> bool:
        """Return whether payload is a command registry."""
        result = isinstance(data, dict) and all(
            isinstance(item, Command) for item in data.values()
        )

        return result
