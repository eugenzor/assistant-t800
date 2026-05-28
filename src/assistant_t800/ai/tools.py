"""AI agent tool functions for contact management.

Each tool receives ``RunContext[AgentDeps]`` and returns a
``ToolReturn`` with a short chat message and optional display metadata.
Tools map 1:1 to methods on :class:`assistant_t800.services.contacts.ContactsService`.
"""

from typing import Optional

from pydantic_ai import RunContext
from pydantic_ai.messages import ToolReturn

from assistant_t800.ai.deps import AgentDeps
from assistant_t800.ai.results import DisplayPayload


def _ok(message: str, display: DisplayPayload | None = None) -> ToolReturn[str]:
    """Build a successful tool return with optional display metadata."""
    return ToolReturn(return_value=message, metadata=display)


def _fail(message: str) -> ToolReturn[str]:
    """Build a failed tool return without display metadata."""
    return ToolReturn(return_value=message)


def _contacts_display(contacts: list) -> DisplayPayload:
    """Build a contacts display payload."""
    return DisplayPayload(kind="contacts", contacts=contacts)


def add_contact(
    ctx: RunContext[AgentDeps],
    name: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
    birthday: Optional[str] = None,
) -> ToolReturn[str]:
    """Create a new contact and refresh the UI contact list."""
    try:
        contact = ctx.deps.contacts_service.add_contact(
            name,
            phone=phone,
            email=email,
            address=address,
            birthday=birthday,
        )
    except ValueError as exc:
        return _fail(f"Не вдалося додати контакт: {exc}")

    return _ok(
        f"Контакт «{contact.name.value}» додано.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def get_contact(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Look up a single contact by name and show it in the UI panel."""
    try:
        contact = ctx.deps.contacts_service.get_contact(name)
    except KeyError as exc:
        return _fail(f"Контакт не знайдено: {exc}")

    return _ok(
        f"Контакт «{contact.name.value}» відображено.",
        _contacts_display([contact]),
    )


def list_contacts(ctx: RunContext[AgentDeps]) -> ToolReturn[str]:
    """Display all stored contacts in the UI panel."""
    contacts = ctx.deps.contacts_service.list_contacts()

    if not contacts:
        return _ok(
            "Контактів поки немає. Панель відображення порожня.",
            _contacts_display([]),
        )

    return _ok(
        f"У панелі відображення показано контактів: {len(contacts)}.",
        _contacts_display(contacts),
    )


def search_contacts(ctx: RunContext[AgentDeps], query: str) -> ToolReturn[str]:
    """Search contacts across all searchable fields."""
    matches = ctx.deps.contacts_service.search_contacts(query)

    if not matches:
        return _ok(
            f"Жоден контакт не відповідає запиту «{query}».",
            _contacts_display([]),
        )

    return _ok(
        f"Знайдено контактів за запитом «{query}»: {len(matches)}.",
        _contacts_display(matches),
    )


def search_contacts_by_name(ctx: RunContext[AgentDeps], query: str) -> ToolReturn[str]:
    """Search contacts by name only."""
    matches = ctx.deps.contacts_service.search_contacts_by_name(query)

    if not matches:
        return _ok(
            f"Жоден контакт не відповідає імені «{query}».",
            _contacts_display([]),
        )

    return _ok(
        f"Знайдено контактів за іменем «{query}»: {len(matches)}.",
        _contacts_display(matches),
    )


def search_contacts_by_phone(ctx: RunContext[AgentDeps], query: str) -> ToolReturn[str]:
    """Search contacts by phone number only."""
    matches = ctx.deps.contacts_service.search_contacts_by_phone(query)

    if not matches:
        return _ok(
            f"Жоден контакт не відповідає телефону «{query}».",
            _contacts_display([]),
        )

    return _ok(
        f"Знайдено контактів за телефоном «{query}»: {len(matches)}.",
        _contacts_display(matches),
    )


def search_contacts_by_email(ctx: RunContext[AgentDeps], query: str) -> ToolReturn[str]:
    """Search contacts by email only."""
    matches = ctx.deps.contacts_service.search_contacts_by_email(query)

    if not matches:
        return _ok(
            f"Жоден контакт не відповідає e-mail «{query}».",
            _contacts_display([]),
        )

    return _ok(
        f"Знайдено контактів за e-mail «{query}»: {len(matches)}.",
        _contacts_display(matches),
    )


def search_contacts_by_note(ctx: RunContext[AgentDeps], query: str) -> ToolReturn[str]:
    """Search contacts by note content only."""
    matches = ctx.deps.contacts_service.search_contacts_by_note(query)

    if not matches:
        return _ok(
            f"Жоден контакт не відповідає нотатці «{query}».",
            _contacts_display([]),
        )

    return _ok(
        f"Знайдено контактів за нотаткою «{query}»: {len(matches)}.",
        _contacts_display(matches),
    )


def search_contacts_by_tag(ctx: RunContext[AgentDeps], query: str) -> ToolReturn[str]:
    """Search contacts by tag only."""
    matches = ctx.deps.contacts_service.search_contacts_by_tag(query)

    if not matches:
        return _ok(
            f"Жоден контакт не відповідає тегу «{query}».",
            _contacts_display([]),
        )

    return _ok(
        f"Знайдено контактів за тегом «{query}»: {len(matches)}.",
        _contacts_display(matches),
    )


def search_upcoming_birthdays(
    ctx: RunContext[AgentDeps], days: int = 7
) -> ToolReturn[str]:
    """List upcoming birthdays within the given number of days."""
    upcoming = ctx.deps.contacts_service.search_upcoming_birthdays(days)

    if not upcoming:
        return _ok(
            "Найближчих днів народження немає.",
            DisplayPayload(kind="birthdays", birthdays=[]),
        )

    return _ok(
        f"Найближчих днів народження: {len(upcoming)}.",
        DisplayPayload(kind="birthdays", birthdays=upcoming),
    )


def set_address(ctx: RunContext[AgentDeps], name: str, address: str) -> ToolReturn[str]:
    """Set or update an existing contact address."""
    try:
        ctx.deps.contacts_service.set_address(name, address)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося встановити адресу: {exc}")

    return _ok(
        f"Адресу контакту «{name}» оновлено.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def set_birthday(
    ctx: RunContext[AgentDeps], name: str, birthday: str
) -> ToolReturn[str]:
    """Set or update an existing contact birthday (DD.MM.YYYY)."""
    try:
        ctx.deps.contacts_service.set_birthday(name, birthday)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося встановити день народження: {exc}")

    return _ok(
        f"День народження контакту «{name}» оновлено.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def add_phones(
    ctx: RunContext[AgentDeps], name: str, phones: list[str]
) -> ToolReturn[str]:
    """Add one or more phone numbers to an existing contact."""
    try:
        ctx.deps.contacts_service.add_phones(name, phones)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося додати телефони: {exc}")

    return _ok(
        f"Телефони додано до контакту «{name}»: {len(phones)}.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def add_emails(
    ctx: RunContext[AgentDeps], name: str, emails: list[str]
) -> ToolReturn[str]:
    """Add one or more email addresses to an existing contact."""
    try:
        ctx.deps.contacts_service.add_emails(name, emails)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося додати e-mail: {exc}")

    return _ok(
        f"E-mail додано до контакту «{name}»: {len(emails)}.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def set_note(ctx: RunContext[AgentDeps], name: str, note: str) -> ToolReturn[str]:
    """Set or update an existing contact note."""
    if not note.strip():
        return _fail("Не вдалося встановити нотатку: нотатка не може бути порожньою.")

    try:
        ctx.deps.contacts_service.set_note(name, note)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося встановити нотатку: {exc}")

    return _ok(
        f"Нотатку контакту «{name}» оновлено.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def remove_note(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove the note from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_note(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити нотатку: {exc}")

    return _ok(
        f"Нотатку контакту «{name}» видалено.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def add_tags(ctx: RunContext[AgentDeps], name: str, tags: list[str]) -> ToolReturn[str]:
    """Add one or more tags to an existing contact."""
    if not tags or not any(tag.strip() for tag in tags):
        return _fail("Не вдалося додати теги: тег не може бути порожнім.")

    try:
        ctx.deps.contacts_service.add_tags(name, tags)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося додати теги: {exc}")

    return _ok(
        f"Теги додано до контакту «{name}»: {len(tags)}.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def remove_tags(
    ctx: RunContext[AgentDeps], name: str, tags: list[str]
) -> ToolReturn[str]:
    """Remove one or more tags from an existing contact."""
    if not tags or not any(tag.strip() for tag in tags):
        return _fail("Не вдалося видалити теги: тег не може бути порожнім.")

    try:
        ctx.deps.contacts_service.remove_tags(name, tags)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити теги: {exc}")

    return _ok(
        f"Теги видалено у контакту «{name}»: {len(tags)}.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def remove_contact(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove a contact from storage."""
    try:
        ctx.deps.contacts_service.remove_contact(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити контакт: {exc}")

    return _ok(
        f"Контакт «{name}» видалено.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def remove_address(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove the address from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_address(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити адресу: {exc}")

    return _ok(
        f"Адресу контакту «{name}» видалено.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def remove_birthday(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove the birthday from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_birthday(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити день народження: {exc}")

    return _ok(
        f"День народження контакту «{name}» видалено.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def remove_phones(
    ctx: RunContext[AgentDeps], name: str, phones: list[str]
) -> ToolReturn[str]:
    """Remove one or more phone numbers from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_phones(name, phones)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити телефони: {exc}")

    return _ok(
        f"Телефони видалено у контакту «{name}»: {len(phones)}.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def remove_all_phones(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove every phone number from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_all_phones(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити телефони: {exc}")

    return _ok(
        f"Усі телефони контакту «{name}» видалено.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def remove_emails(
    ctx: RunContext[AgentDeps], name: str, emails: list[str]
) -> ToolReturn[str]:
    """Remove one or more email addresses from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_emails(name, emails)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити e-mail: {exc}")

    return _ok(
        f"E-mail видалено у контакту «{name}»: {len(emails)}.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )


def remove_all_emails(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove every email address from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_all_emails(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити e-mail: {exc}")

    return _ok(
        f"Усі e-mail контакту «{name}» видалено.",
        _contacts_display(ctx.deps.contacts_service.list_contacts()),
    )
