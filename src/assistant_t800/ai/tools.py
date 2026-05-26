"""AI agent tool functions for contact management.

Each tool receives ``RunContext[AgentDeps]`` and returns a short text
message that the agent can use in the chat response. Tools map 1:1
to methods on :class:`assistant_t800.services.contacts.ContactsService`.
"""

from typing import Optional

from pydantic_ai import RunContext

from assistant_t800.ai.deps import AgentDeps


def add_contact(
    ctx: RunContext[AgentDeps],
    name: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
    birthday: Optional[str] = None,
) -> str:
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
        return f"Не вдалося додати контакт: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Контакт «{contact.name.value}» додано."


def get_contact(ctx: RunContext[AgentDeps], name: str) -> str:
    """Look up a single contact by name and show it in the UI panel."""
    try:
        contact = ctx.deps.contacts_service.get_contact(name)
    except KeyError as exc:
        return f"Контакт не знайдено: {exc}"

    ctx.deps.presenter.refresh_contacts([contact])

    return f"Контакт «{contact.name.value}» відображено."


def list_contacts(ctx: RunContext[AgentDeps]) -> str:
    """Display all stored contacts in the UI panel."""
    contacts = ctx.deps.contacts_service.list_contacts()

    ctx.deps.presenter.refresh_contacts(contacts)

    if not contacts:
        return "Контактів поки немає. Панель відображення порожня."

    return f"У панелі відображення показано контактів: {len(contacts)}."


def search_contacts(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search contacts across all searchable fields."""
    matches = ctx.deps.contacts_service.search_contacts(query)

    ctx.deps.presenter.refresh_contacts(matches)

    if not matches:
        return f"Жоден контакт не відповідає запиту «{query}»."

    return f"Знайдено контактів за запитом «{query}»: {len(matches)}."


def search_contacts_by_name(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search contacts by name only."""
    matches = ctx.deps.contacts_service.search_contacts_by_name(query)

    ctx.deps.presenter.refresh_contacts(matches)

    if not matches:
        return f"Жоден контакт не відповідає імені «{query}»."

    return f"Знайдено контактів за іменем «{query}»: {len(matches)}."


def search_contacts_by_phone(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search contacts by phone number only."""
    matches = ctx.deps.contacts_service.search_contacts_by_phone(query)

    ctx.deps.presenter.refresh_contacts(matches)

    if not matches:
        return f"Жоден контакт не відповідає телефону «{query}»."

    return f"Знайдено контактів за телефоном «{query}»: {len(matches)}."


def search_contacts_by_email(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search contacts by email only."""
    matches = ctx.deps.contacts_service.search_contacts_by_email(query)

    ctx.deps.presenter.refresh_contacts(matches)

    if not matches:
        return f"Жоден контакт не відповідає e-mail «{query}»."

    return f"Знайдено контактів за e-mail «{query}»: {len(matches)}."


def search_contacts_by_note(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search contacts by note content only."""
    matches = ctx.deps.contacts_service.search_contacts_by_note(query)

    ctx.deps.presenter.refresh_contacts(matches)

    if not matches:
        return f"Жоден контакт не відповідає нотатці «{query}»."

    return f"Знайдено контактів за нотаткою «{query}»: {len(matches)}."


def search_contacts_by_tag(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search contacts by tag only."""
    matches = ctx.deps.contacts_service.search_contacts_by_tag(query)

    ctx.deps.presenter.refresh_contacts(matches)

    if not matches:
        return f"Жоден контакт не відповідає тегу «{query}»."

    return f"Знайдено контактів за тегом «{query}»: {len(matches)}."


def search_upcoming_birthdays(ctx: RunContext[AgentDeps], days: int = 7) -> str:
    """List upcoming birthdays within the given number of days."""
    upcoming = ctx.deps.contacts_service.search_upcoming_birthdays(days)

    if not upcoming:
        ctx.deps.presenter.print("Найближчих днів народження немає.")
        return "Найближчих днів народження немає."

    lines = [
        f"{item.name} — {item.birthday} (вітати: {item.congratulation_date}, вік: {item.age})"
        for item in upcoming
    ]
    ctx.deps.presenter.print("\n".join(lines))

    return f"Найближчих днів народження: {len(upcoming)}."


def set_address(ctx: RunContext[AgentDeps], name: str, address: str) -> str:
    """Set or update an existing contact address."""
    try:
        ctx.deps.contacts_service.set_address(name, address)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося встановити адресу: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Адресу контакту «{name}» оновлено."


def set_birthday(ctx: RunContext[AgentDeps], name: str, birthday: str) -> str:
    """Set or update an existing contact birthday (DD.MM.YYYY)."""
    try:
        ctx.deps.contacts_service.set_birthday(name, birthday)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося встановити день народження: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"День народження контакту «{name}» оновлено."


def add_phones(ctx: RunContext[AgentDeps], name: str, phones: list[str]) -> str:
    """Add one or more phone numbers to an existing contact."""
    try:
        ctx.deps.contacts_service.add_phones(name, phones)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося додати телефони: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Телефони додано до контакту «{name}»: {len(phones)}."


def add_emails(ctx: RunContext[AgentDeps], name: str, emails: list[str]) -> str:
    """Add one or more email addresses to an existing contact."""
    try:
        ctx.deps.contacts_service.add_emails(name, emails)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося додати e-mail: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"E-mail додано до контакту «{name}»: {len(emails)}."


def remove_contact(ctx: RunContext[AgentDeps], name: str) -> str:
    """Remove a contact from storage."""
    try:
        ctx.deps.contacts_service.remove_contact(name)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося видалити контакт: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Контакт «{name}» видалено."


def remove_address(ctx: RunContext[AgentDeps], name: str) -> str:
    """Remove the address from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_address(name)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося видалити адресу: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Адресу контакту «{name}» видалено."


def remove_birthday(ctx: RunContext[AgentDeps], name: str) -> str:
    """Remove the birthday from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_birthday(name)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося видалити день народження: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"День народження контакту «{name}» видалено."


def remove_phones(ctx: RunContext[AgentDeps], name: str, phones: list[str]) -> str:
    """Remove one or more phone numbers from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_phones(name, phones)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося видалити телефони: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Телефони видалено у контакту «{name}»: {len(phones)}."


def remove_all_phones(ctx: RunContext[AgentDeps], name: str) -> str:
    """Remove every phone number from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_all_phones(name)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося видалити телефони: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Усі телефони контакту «{name}» видалено."


def remove_emails(ctx: RunContext[AgentDeps], name: str, emails: list[str]) -> str:
    """Remove one or more email addresses from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_emails(name, emails)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося видалити e-mail: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"E-mail видалено у контакту «{name}»: {len(emails)}."


def remove_all_emails(ctx: RunContext[AgentDeps], name: str) -> str:
    """Remove every email address from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_all_emails(name)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося видалити e-mail: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Усі e-mail контакту «{name}» видалено."


def print_to_display(ctx: RunContext[AgentDeps], text: str) -> str:
    """Display arbitrary text in the UI output panel."""
    ctx.deps.presenter.print(text)

    return "Текст виведено у панель відображення."
