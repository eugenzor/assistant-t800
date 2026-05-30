"""AI agent tool functions for contact management.

Each tool receives ``RunContext[AgentDeps]`` and returns a
``ToolReturn`` with a short chat message and optional display metadata.
Tools map 1:1 to methods on :class:`assistant_t800.services.contacts.ContactsService`.
"""

from typing import Optional

from pydantic_ai import RunContext
from pydantic_ai.messages import ToolReturn

from assistant_t800.ai.deps import AgentDeps
from assistant_t800.ai.utils import (
    ContactField,
    coalesce_read_fields,
    format_birthdays_for_llm,
    format_contacts_for_llm,
    resolve_contact_fields,
)
from assistant_t800.ai.results import DisplayPayload
from assistant_t800.application.normalizers import normalize_address, normalize_phone
from assistant_t800.domain.contacts import Contact
from assistant_t800.services.contacts import ContactsService


def _ok(message: str, display: DisplayPayload | None = None) -> ToolReturn[str]:
    """Build a successful tool return with optional display metadata."""
    return ToolReturn(return_value=message, metadata=display)


def _fail(message: str) -> ToolReturn[str]:
    """Build a failed tool return without display metadata."""
    return ToolReturn(return_value=message)


def _contacts_display(contacts: list) -> DisplayPayload:
    """Build a contacts display payload."""
    return DisplayPayload(kind="contacts", contacts=contacts)


def _contact_display(contact: Contact) -> DisplayPayload:
    """Build a single-contact card display payload."""
    return DisplayPayload(kind="contact", contact=contact)


def _mutated_contact_display(service: ContactsService, name: str) -> DisplayPayload:
    """Build card payload for the contact affected by a mutation."""
    contact = service.get_contact(name)
    return _contact_display(contact)


def print_text(ctx: RunContext[AgentDeps], text: str) -> ToolReturn[str]:
    """Render free-form ``text`` in the UI panel for a custom layout.

    Use this ONLY when the user explicitly asks for a layout the structured
    tools cannot express (e.g. "as a phonebook", "group by tag", "as CSV").
    Prefer the structured read tools (``list_contacts``, ``get_contact``,
    ``search_*``) for ordinary views — they render the data directly and
    cannot misreport it.

    Format ``text`` as Markdown: use ``**bold**``, bullet lists, and Markdown
    tables (``| a | b |``) for structure. Avoid ``#`` headings — they render
    heavily in the narrow panel. Only render data fetched via a tool in this
    same turn — never values recalled from memory — and copy every value
    (phones, emails) verbatim.
    """
    return _ok(
        "Користувацький вигляд виведено на панель.",
        DisplayPayload(kind="text", text=text),
    )


def _contacts_llm_message(
    header: str,
    contacts: list[Contact],
    *,
    fields: frozenset[str] | None = None,
) -> str:
    """Build a tool return message with contact summaries for the LLM."""
    body = format_contacts_for_llm(contacts, fields=fields)
    if not body:
        return header

    return f"{header}\n{body}"


def _contacts_read_result(
    matches: list[Contact],
    *,
    header: str,
    empty_message: str,
    fields: list[str] | None = None,
) -> ToolReturn[str]:
    """Build a read-tool return with LLM JSON and UI display metadata."""
    if not matches:
        return _ok(empty_message, _contacts_display([]))

    resolved = resolve_contact_fields(coalesce_read_fields(fields))
    return _ok(
        _contacts_llm_message(header, matches, fields=resolved),
        _contacts_display(matches),
    )


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
        parsed_address = normalize_address(address) if address else None
        normalized_phone = normalize_phone(phone) if phone else None
        contact = ctx.deps.contacts_service.add_contact(
            name,
            phone=normalized_phone,
            email=email,
            address=address,
            parsed_address=parsed_address,
            birthday=birthday,
        )
    except ValueError as exc:
        return _fail(f"Не вдалося додати контакт: {exc}")

    return _ok(
        f"Контакт «{contact.name.value}» додано.",
        _contact_display(contact),
    )


def get_contact(
    ctx: RunContext[AgentDeps],
    name: str,
    fields: list[ContactField] | None = None,
) -> ToolReturn[str]:
    """Look up a single contact by name and show it in the UI panel.

    ``fields`` limits contact data returned to the LLM as JSON (not the UI panel).
    Defaults to ``[ContactField.NAME]``; pass additional ``ContactField`` values when
    more attributes are needed.
    """
    try:
        contact = ctx.deps.contacts_service.get_contact(name)
    except KeyError as exc:
        return _fail(f"Контакт не знайдено: {exc}")

    resolved = resolve_contact_fields(coalesce_read_fields(fields))
    return _ok(
        _contacts_llm_message(
            f"Контакт «{contact.name.value}»:",
            [contact],
            fields=resolved,
        ),
        _contact_display(contact),
    )


def list_contacts(
    ctx: RunContext[AgentDeps],
    fields: list[ContactField] | None = None,
) -> ToolReturn[str]:
    """Display all stored contacts in the UI panel.

    ``fields`` limits contact data returned to the LLM as JSON (not the UI panel).
    Defaults to ``[ContactField.NAME]``; pass additional ``ContactField`` values when
    more attributes are needed.
    """
    contacts = ctx.deps.contacts_service.list_contacts()
    return _contacts_read_result(
        contacts,
        header=f"Контактів: {len(contacts)}.",
        empty_message="Контактів поки немає. Панель відображення порожня.",
        fields=fields,
    )


def search_contacts(
    ctx: RunContext[AgentDeps],
    query: str,
    fields: list[ContactField] | None = None,
) -> ToolReturn[str]:
    """Search contacts across all searchable fields.

    ``fields`` limits contact data returned to the LLM as JSON (not the UI panel).
    Defaults to ``[ContactField.NAME]``; pass additional ``ContactField`` values when
    more attributes are needed.
    """
    matches = ctx.deps.contacts_service.search_contacts(query)
    return _contacts_read_result(
        matches,
        header=f"Знайдено контактів за запитом «{query}»: {len(matches)}.",
        empty_message=f"Жоден контакт не відповідає запиту «{query}».",
        fields=fields,
    )


def search_contacts_by_name(
    ctx: RunContext[AgentDeps],
    query: str,
    fields: list[ContactField] | None = None,
) -> ToolReturn[str]:
    """Search contacts by name only.

    ``fields`` limits contact data returned to the LLM as JSON (not the UI panel).
    Defaults to ``[ContactField.NAME]``; pass additional ``ContactField`` values when
    more attributes are needed.
    """
    matches = ctx.deps.contacts_service.search_contacts_by_name(query)
    return _contacts_read_result(
        matches,
        header=f"Знайдено контактів за іменем «{query}»: {len(matches)}.",
        empty_message=f"Жоден контакт не відповідає імені «{query}».",
        fields=fields,
    )


def search_contacts_by_phone(
    ctx: RunContext[AgentDeps],
    query: str,
    fields: list[ContactField] | None = None,
) -> ToolReturn[str]:
    """Search contacts by phone number only.

    ``fields`` limits contact data returned to the LLM as JSON (not the UI panel).
    Defaults to ``[ContactField.NAME]``; pass additional ``ContactField`` values when
    more attributes are needed.
    """
    matches = ctx.deps.contacts_service.search_contacts_by_phone(query)
    return _contacts_read_result(
        matches,
        header=f"Знайдено контактів за телефоном «{query}»: {len(matches)}.",
        empty_message=f"Жоден контакт не відповідає телефону «{query}».",
        fields=fields,
    )


def search_contacts_by_email(
    ctx: RunContext[AgentDeps],
    query: str,
    fields: list[ContactField] | None = None,
) -> ToolReturn[str]:
    """Search contacts by email only.

    ``fields`` limits contact data returned to the LLM as JSON (not the UI panel).
    Defaults to ``[ContactField.NAME]``; pass additional ``ContactField`` values when
    more attributes are needed.
    """
    matches = ctx.deps.contacts_service.search_contacts_by_email(query)
    return _contacts_read_result(
        matches,
        header=f"Знайдено контактів за e-mail «{query}»: {len(matches)}.",
        empty_message=f"Жоден контакт не відповідає e-mail «{query}».",
        fields=fields,
    )


def search_contacts_by_note(
    ctx: RunContext[AgentDeps],
    query: str,
    fields: list[ContactField] | None = None,
) -> ToolReturn[str]:
    """Search contacts by note content only.

    ``fields`` limits contact data returned to the LLM as JSON (not the UI panel).
    Defaults to ``[ContactField.NAME]``; pass additional ``ContactField`` values when
    more attributes are needed.
    """
    matches = ctx.deps.contacts_service.search_contacts_by_note(query)
    return _contacts_read_result(
        matches,
        header=f"Знайдено контактів за нотаткою «{query}»: {len(matches)}.",
        empty_message=f"Жоден контакт не відповідає нотатці «{query}».",
        fields=fields,
    )


def search_contacts_by_tag(
    ctx: RunContext[AgentDeps],
    query: str,
    fields: list[ContactField] | None = None,
) -> ToolReturn[str]:
    """Search contacts by tag only.

    ``fields`` limits contact data returned to the LLM as JSON (not the UI panel).
    Defaults to ``[ContactField.NAME]``; pass additional ``ContactField`` values when
    more attributes are needed.
    """
    matches = ctx.deps.contacts_service.search_contacts_by_tag(query)
    return _contacts_read_result(
        matches,
        header=f"Знайдено контактів за тегом «{query}»: {len(matches)}.",
        empty_message=f"Жоден контакт не відповідає тегу «{query}».",
        fields=fields,
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

    header = f"Найближчих днів народження: {len(upcoming)}."
    body = format_birthdays_for_llm(upcoming)
    message = header if not body else f"{header}\n{body}"
    return _ok(message, DisplayPayload(kind="birthdays", birthdays=upcoming))


def set_address(ctx: RunContext[AgentDeps], name: str, address: str) -> ToolReturn[str]:
    """Set or update an existing contact address.

    Address is a structured record. Required fields: ``country``, ``city`` and
    ``line`` (street address). ``zip_code`` and ``region`` are optional.
    """
    try:
        parsed_address = normalize_address(address)
        ctx.deps.contacts_service.set_address(name, address, parsed_address)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося встановити адресу: {exc}")

    return _ok(
        f"Адресу контакту «{name}» оновлено.",
        _mutated_contact_display(ctx.deps.contacts_service, name),
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
        _mutated_contact_display(ctx.deps.contacts_service, name),
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
        _mutated_contact_display(ctx.deps.contacts_service, name),
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
        _mutated_contact_display(ctx.deps.contacts_service, name),
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
        _mutated_contact_display(ctx.deps.contacts_service, name),
    )


def remove_note(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove the note from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_note(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити нотатку: {exc}")

    return _ok(
        f"Нотатку контакту «{name}» видалено.",
        _mutated_contact_display(ctx.deps.contacts_service, name),
    )


def set_tags_from_text(
    ctx: RunContext[AgentDeps], name: str, tags: str
) -> ToolReturn[str]:
    """Replace all tags on an existing contact from comma/semicolon-separated text.

    Tags are separated by ``;`` or ``,``. Empty or whitespace-only text clears
    all tags. To add or remove individual tags, read current tags first, then
    pass the full desired tag list.
    """
    try:
        ctx.deps.contacts_service.set_tags_from_text(name, tags)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося встановити теги: {exc}")

    return _ok(
        f"Теги контакту «{name}» оновлено.",
        _mutated_contact_display(ctx.deps.contacts_service, name),
    )


def clear_tags(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove all tags from an existing contact."""
    try:
        ctx.deps.contacts_service.clear_tags(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося очистити теги: {exc}")

    return _ok(
        f"Усі теги контакту «{name}» видалено.",
        _mutated_contact_display(ctx.deps.contacts_service, name),
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
        _mutated_contact_display(ctx.deps.contacts_service, name),
    )


def remove_birthday(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove the birthday from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_birthday(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити день народження: {exc}")

    return _ok(
        f"День народження контакту «{name}» видалено.",
        _mutated_contact_display(ctx.deps.contacts_service, name),
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
        _mutated_contact_display(ctx.deps.contacts_service, name),
    )


def remove_all_phones(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove every phone number from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_all_phones(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити телефони: {exc}")

    return _ok(
        f"Усі телефони контакту «{name}» видалено.",
        _mutated_contact_display(ctx.deps.contacts_service, name),
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
        _mutated_contact_display(ctx.deps.contacts_service, name),
    )


def remove_all_emails(ctx: RunContext[AgentDeps], name: str) -> ToolReturn[str]:
    """Remove every email address from an existing contact."""
    try:
        ctx.deps.contacts_service.remove_all_emails(name)
    except (KeyError, ValueError) as exc:
        return _fail(f"Не вдалося видалити e-mail: {exc}")

    return _ok(
        f"Усі e-mail контакту «{name}» видалено.",
        _mutated_contact_display(ctx.deps.contacts_service, name),
    )
