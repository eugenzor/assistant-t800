"""AI agent tool functions for contact management.

Each tool receives ``RunContext[AgentDeps]`` and returns a short text
message that the agent can use in the chat response.
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
    """Create a new contact and refresh the UI contact list.

    Args:
        ctx: Agent runtime context with services and presenter.
        name: Contact name.
        phone: Optional phone number.
        email: Optional email address.
        address: Optional contact address.
        birthday: Optional birthday in DD.MM.YYYY format.

    Returns:
        Short status message for the AI chat response.
    """
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


def add_phone(ctx: RunContext[AgentDeps], name: str, phone: str) -> str:
    """Add a phone number to an existing contact.

    Args:
        ctx: Agent runtime context with services and presenter.
        name: Existing contact name.
        phone: Phone number to add.

    Returns:
        Short status message for the AI chat response.
    """
    try:
        ctx.deps.contacts_service.add_phone(name, phone)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося додати телефон: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Телефон {phone} додано до контакту «{name}»."


def edit_phone(
    ctx: RunContext[AgentDeps],
    name: str,
    old_phone: str,
    new_phone: str,
) -> str:
    """Replace an existing phone number in a contact.

    Args:
        ctx: Agent runtime context with services and presenter.
        name: Existing contact name.
        old_phone: Phone number that should be replaced.
        new_phone: Replacement phone number.

    Returns:
        Short status message for the AI chat response.
    """
    try:
        ctx.deps.contacts_service.edit_phone(name, old_phone, new_phone)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося змінити телефон: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Телефон контакту «{name}» оновлено."


def add_email(ctx: RunContext[AgentDeps], name: str, email: str) -> str:
    """Add an email address to an existing contact.

    Args:
        ctx: Agent runtime context with services and presenter.
        name: Existing contact name.
        email: Email address to add.

    Returns:
        Short status message for the AI chat response.
    """
    try:
        ctx.deps.contacts_service.add_email(name, email)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося додати e-mail: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"E-mail {email} додано до контакту «{name}»."


def set_address(ctx: RunContext[AgentDeps], name: str, address: str) -> str:
    """Set or update an existing contact address.

    Args:
        ctx: Agent runtime context with services and presenter.
        name: Existing contact name.
        address: Contact address value.

    Returns:
        Short status message for the AI chat response.
    """
    try:
        ctx.deps.contacts_service.set_address(name, address)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося встановити адресу: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"Адресу контакту «{name}» оновлено."


def set_birthday(ctx: RunContext[AgentDeps], name: str, birthday: str) -> str:
    """Set or update an existing contact birthday.

    Args:
        ctx: Agent runtime context with services and presenter.
        name: Existing contact name.
        birthday: Birthday in DD.MM.YYYY format.

    Returns:
        Short status message for the AI chat response.
    """
    try:
        ctx.deps.contacts_service.set_birthday(name, birthday)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося встановити день народження: {exc}"

    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())

    return f"День народження контакту «{name}» оновлено."


def search_contacts(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search contacts and display matching results in the UI panel.

    The search is performed across contact names, phone numbers,
    email addresses, and addresses.

    Args:
        ctx: Agent runtime context with services and presenter.
        query: Search substring.

    Returns:
        Short search result summary for the AI chat response.
    """
    matches = ctx.deps.contacts_service.search_contacts(query)

    ctx.deps.presenter.refresh_contacts(matches)

    if not matches:
        return f"Жоден контакт не відповідає запиту «{query}»."

    return f"Знайдено контактів за запитом «{query}»: {len(matches)}."


def list_contacts(ctx: RunContext[AgentDeps]) -> str:
    """Display all stored contacts in the UI panel.

    Args:
        ctx: Agent runtime context with services and presenter.

    Returns:
        Short status message with the number of displayed contacts.
    """
    contacts = ctx.deps.contacts_service.list_contacts()

    ctx.deps.presenter.refresh_contacts(contacts)

    if not contacts:
        return "Контактів поки немає. Панель відображення порожня."

    return f"У панелі відображення показано контактів: {len(contacts)}."


def print_to_display(ctx: RunContext[AgentDeps], text: str) -> str:
    """Display arbitrary text in the UI output panel.

    Args:
        ctx: Agent runtime context with presenter.
        text: Text to display.

    Returns:
        Short status message for the AI chat response.
    """
    ctx.deps.presenter.print(text)

    return "Текст виведено у панель відображення."
