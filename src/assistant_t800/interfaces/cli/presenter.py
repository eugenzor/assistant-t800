"""CLI result presenter."""

from assistant_t800.application.commands import Command
from assistant_t800.application.enums import SystemValue
from assistant_t800.application.results import AppResult
from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact
from assistant_t800.localization import Message, render_message


class CliPresenter:
    """Render application results for terminal output."""

    def render(self, result: AppResult) -> str:
        """Render one application result."""
        rows = []
        message = render_message(result.message)

        if message:
            rows.append(message)

        if rendered_data := self._render_data(result.data):
            rows.append(rendered_data)

        output = "\n".join(rows)

        return output

    def _render_data(self, data: object | None) -> str:
        """Render supported data payloads."""
        if data is None:
            result = ""
        elif isinstance(data, Contact):
            result = self._render_contact(data)
        elif isinstance(data, list):
            result = "\n\n".join(self._render_item(item) for item in data)
        elif isinstance(data, dict) and all(
            isinstance(item, Command) for item in data.values()
        ):
            result = self._render_help(data)
        else:
            result = str(data)

        return result

    def _render_item(self, item: object) -> str:
        """Render one supported list item."""
        if isinstance(item, Contact):
            result = self._render_contact(item)
        elif isinstance(item, BirthdaysListContact):
            result = self._render_birthday_contact(item)
        else:
            result = str(item)

        return result

    @staticmethod
    def _render_contact(contact: Contact) -> str:
        """Render one contact."""
        rows = [f"{Message.CONTACT_NAME}: {contact.name.value}"]

        if contact.phones:
            label = (
                str(Message.CONTACT_PHONES)
                if len(contact.phones) > 1
                else str(Message.CONTACT_PHONES)[:-1]
            )
            rows.append(f"{label}: " + "; ".join(item.value for item in contact.phones))

        if contact.emails:
            label = (
                str(Message.CONTACT_EMAILS)
                if len(contact.emails) > 1
                else str(Message.CONTACT_EMAILS)[:-1]
            )
            rows.append(f"{label}: " + "; ".join(item.value for item in contact.emails))

        if contact.address is not None:
            rows.append(f"{Message.CONTACT_ADDRESS}: {contact.address.value}")

        if contact.birthday is not None:
            rows.append(f"{Message.CONTACT_BIRTHDAY}: {contact.birthday}")

        if contact.note != SystemValue.EMPTY_TEXT.value:
            rows.append(f"{Message.CONTACT_NOTE}: {contact.note}")

        if contact.tags:
            rows.append(f"{Message.CONTACT_TAGS}: " + "; ".join(sorted(contact.tags)))

        result = "\n".join(rows)

        return result

    @staticmethod
    def _render_birthday_contact(contact: BirthdaysListContact) -> str:
        """Render one upcoming birthday record."""
        result = Message.BIRTHDAY_LIST_ITEM.render(
            name=contact.name,
            birthday=contact.birthday,
            age=contact.age,
            congratulation_date=contact.congratulation_date,
        )

        return result

    @staticmethod
    def _render_help(registry: dict[str, Command]) -> str:
        """Render unique command definitions."""
        seen: set[str] = set()
        commands = tuple(
            command
            for command in registry.values()
            if command.name not in seen and not seen.add(command.name)
        )
        command_rows = tuple(
            (command.syntax, command.description) for command in commands
        )
        command_width = max((len(name) for name, _ in command_rows), default=0)
        result = "\n".join(
            f"  {name:<{command_width}}  {description.text}"
            for name, description in command_rows
        )

        return result
