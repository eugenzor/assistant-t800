"""LLM tool helpers: field filtering and JSON formatting for tool results."""

import json
from enum import StrEnum
from typing import Any, Literal, TypeVar

from assistant_t800.application.enums import SystemValue
from assistant_t800.config import settings
from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact


class ContactField(StrEnum):
    """User-facing contact attribute names."""

    NAME = "name"
    PHONES = "phones"
    EMAILS = "emails"
    ADDRESS = "address"
    BIRTHDAY = "birthday"
    NOTE = "note"
    TAGS = "tags"


CONTACT_FIELD_NAMES: frozenset[str] = frozenset(field.value for field in ContactField)

ItemT = TypeVar("ItemT")

DEFAULT_READ_TOOL_FIELDS: tuple[ContactField, ...] = (ContactField.NAME,)


def coalesce_read_fields(fields: list[str] | None) -> list[str]:
    """Return effective read-tool fields, applying the default when omitted."""
    return list(DEFAULT_READ_TOOL_FIELDS if fields is None else fields)


def resolve_contact_fields(fields: list[ContactField]) -> frozenset[str]:
    """Normalize a field filter for LLM tool output.

    ``name`` is always included for identification.
    """
    normalized = {field.value for field in fields}
    normalized.add(ContactField.NAME.value)
    return frozenset(normalized)


def _cap_items(items: list[ItemT], max_items: int | None) -> tuple[list[ItemT], int]:
    """Return a capped prefix of items and how many were hidden."""
    limit = max_items if max_items is not None else settings.max_contacts_in_tool_return
    shown = items[:limit]
    return shown, len(items) - len(shown)


def _uk_count_phrase(count: int, *, one: str, few: str, many: str) -> str:
    """Build a Ukrainian count phrase with basic plural rules."""
    if count % 10 == 1 and count % 100 != 11:
        return one.format(count=count)
    if count % 10 in {2, 3, 4} and count % 100 not in {12, 13, 14}:
        return few.format(count=count)
    return many.format(count=count)


def _hidden_items_message(
    hidden: int, *, kind: Literal["contacts", "birthdays"]
) -> str:
    """Return a Ukrainian truncation hint for capped tool results."""
    if kind == "contacts":
        phrase = _uk_count_phrase(
            hidden,
            one="{count} контакт",
            few="{count} контакти",
            many="{count} контактів",
        )
    else:
        phrase = _uk_count_phrase(
            hidden,
            one="{count} день народження",
            few="{count} дні народження",
            many="{count} днів народження",
        )

    return f"Ще {phrase} не показано — уточни запит або звузь пошук."


def contact_to_dict(
    contact: Contact,
    *,
    fields: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Return a JSON-serializable contact dict for LLM tool results."""
    explicit_fields = fields is not None
    active_fields = fields if explicit_fields else CONTACT_FIELD_NAMES
    data: dict[str, Any] = {}

    if "name" in active_fields:
        data["name"] = contact.name.value

    if "phones" in active_fields:
        phones = [item.value for item in contact.phones]
        if explicit_fields or phones:
            data["phones"] = phones

    if "emails" in active_fields:
        emails = [item.value for item in contact.emails]
        if explicit_fields or emails:
            data["emails"] = emails

    if "address" in active_fields:
        address = contact.address.value if contact.address is not None else None
        if explicit_fields or address is not None:
            data["address"] = address

    if "birthday" in active_fields:
        birthday = str(contact.birthday) if contact.birthday is not None else None
        if explicit_fields or birthday is not None:
            data["birthday"] = birthday

    if "note" in active_fields:
        note = contact.note if contact.note != SystemValue.EMPTY_TEXT.value else None
        if explicit_fields or note is not None:
            data["note"] = note

    if "tags" in active_fields:
        tags = sorted(contact.tags)
        if explicit_fields or tags:
            data["tags"] = tags

    return data


def birthday_to_dict(item: BirthdaysListContact) -> dict[str, str]:
    """Return a JSON-serializable upcoming birthday dict for LLM tool results."""
    return {
        "name": item.name,
        "birthday": item.birthday,
        "age": item.age,
        "congratulation_date": item.congratulation_date,
    }


def format_contacts_for_llm(
    contacts: list[Contact],
    *,
    fields: frozenset[str] | None = None,
    max_items: int | None = None,
) -> str:
    """Return a JSON payload of contacts, capped to ``max_items``."""
    if not contacts:
        return ""

    shown, hidden = _cap_items(contacts, max_items)
    payload: dict[str, Any] = {
        "contacts": [contact_to_dict(contact, fields=fields) for contact in shown],
    }

    if hidden > 0:
        payload["hidden_count"] = hidden
        payload["message"] = _hidden_items_message(hidden, kind="contacts")

    return json.dumps(payload, ensure_ascii=False)


def format_birthdays_for_llm(
    birthdays: list[BirthdaysListContact],
    *,
    max_items: int | None = None,
) -> str:
    """Return a JSON payload of upcoming birthdays, capped to ``max_items``."""
    if not birthdays:
        return ""

    shown, hidden = _cap_items(birthdays, max_items)
    payload: dict[str, Any] = {
        "birthdays": [birthday_to_dict(item) for item in shown],
    }

    if hidden > 0:
        payload["hidden_count"] = hidden
        payload["message"] = _hidden_items_message(hidden, kind="birthdays")

    return json.dumps(payload, ensure_ascii=False)
