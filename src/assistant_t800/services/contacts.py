"""Contact management service layer."""

import re

from collections.abc import Iterable, Sequence
from typing import Optional

from assistant_t800.application.enums import SystemValue
from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name, Phone, Address, Birthday
from assistant_t800.repositories.contacts import ContactsRepository

# Maximum number of AI-suggested tags returned per request.
MAX_SUGGESTED_TAGS = 5


def mask_phones(phones: Sequence[Phone]) -> list[str]:
    """Mask phone numbers; keep only ones with a country-code prefix."""
    masked = [
        phone.value[:4] + "*" * (len(phone.value) - 4)
        for phone in phones
        if phone.value.startswith("+")
    ]
    return masked


def address_geo_fields(address: Address) -> dict[str, str] | None:
    """Return geo fields from a structured address. Today: always None.

    TODO: replace with structured access after Address refactor — extract
    country, city, region from the structured record. Address Line is
    never returned (street/building PII).
    """
    return None


def birthday_month(birthday: Birthday) -> str | None:
    """Return a month of the birthday."""
    if not birthday:
        return None
    return birthday.date.strftime("%B").lower()


def build_tag_suggestion_snapshot(contact: Contact) -> dict:
    """Build a snapshot of a contact for tag suggestion."""
    snapshot = {"name": contact.name.value}

    if len(contact.tags) > 0:
        snapshot["tags"] = sorted(contact.tags)

    if contact.note and contact.note != SystemValue.EMPTY_TEXT.value:
        snapshot["note"] = contact.note

    if contact.phones:
        masked = mask_phones(contact.phones)
        if masked:
            snapshot["phones"] = masked

    if contact.address:
        geo = address_geo_fields(contact.address)
        if geo:
            snapshot["geo_location"] = geo

    if contact.birthday:
        snapshot["birthday_month"] = birthday_month(contact.birthday)

    return snapshot


def clean_suggested_tags(raw_tags: Iterable[str], existing: set[str]) -> list[str]:
    """Normalize raw LLM tag output, drop duplicates and empties, cap the result.

    Args:
        raw_tags: Raw tag list from the LLM.
        existing: The contact's existing tags (already normalized).

    Returns:
        Cleaned tag list, in the order proposed, with no duplicates against
        ``existing`` or within the result, truncated to ``MAX_SUGGESTED_TAGS``.
    """
    cleaned: list[str] = []
    seen: set[str] = set()

    for tag in raw_tags:
        normalized = tag.strip().casefold()
        if not normalized:
            continue
        if normalized in existing or normalized in seen:
            continue
        cleaned.append(normalized)
        seen.add(normalized)
        if len(cleaned) >= MAX_SUGGESTED_TAGS:
            break

    return cleaned


class ContactsService:
    """High-level contact management service."""

    def __init__(self, repo: ContactsRepository) -> None:
        """Initialize the service with a contact repository."""
        self._repo = repo

    def add_contact(
        self,
        name: str,
        *,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        phones: Sequence[str] = (),
        emails: Sequence[str] = (),
        address: Optional[str] = None,
        birthday: Optional[str] = None,
    ) -> Contact:
        """Create and store a new contact."""
        contact = Contact(Name(name))

        for value in self._merge_values(phone, phones):
            contact.add_phone(value)

        for value in self._merge_values(email, emails):
            contact.add_email(value)

        if address:
            contact.set_address(address)

        if birthday:
            contact.set_birthday(birthday)

        self._repo.add(contact)

        return contact

    def get_contact(self, name: str) -> Contact:
        """Return a contact by name."""
        contact = self._repo.get(name)

        if contact is None:
            raise KeyError(name)

        return contact

    def list_contacts(self) -> list[Contact]:
        """Return all stored contacts."""
        return self._repo.all()

    def search_contacts(self, query: str) -> list[Contact]:
        """Search contacts by all searchable fields."""
        return self._repo.search(query)

    def search_contacts_by_name(self, query: str) -> list[Contact]:
        """Search contacts by name."""
        return self._repo.search_name(query)

    def search_contacts_by_phone(self, query: str) -> list[Contact]:
        """Search contacts by phone."""
        return self._repo.search_phone(query)

    def search_contacts_by_email(self, query: str) -> list[Contact]:
        """Search contacts by email."""
        return self._repo.search_email(query)

    def search_contacts_by_note(self, query: str) -> list[Contact]:
        """Search contacts by note."""
        return self._repo.search_note(query)

    def search_contacts_by_tag(self, query: str) -> list[Contact]:
        """Search contacts by tag."""
        return self._repo.search_tag(query)

    def search_upcoming_birthdays(self, days: int = 7) -> list[BirthdaysListContact]:
        """Search contacts with upcoming congratulation dates."""
        return self._repo.search_upcoming_birthdays(days)

    def set_address(self, name: str, address: str) -> Contact:
        """Set or replace a contact address."""
        contact = self.get_contact(name)
        contact.set_address(address)

        return contact

    def set_birthday(self, name: str, birthday: str) -> Contact:
        """Set or replace a contact birthday."""
        contact = self.get_contact(name)
        contact.set_birthday(birthday)

        return contact

    def add_phones(self, name: str, phones: Sequence[str]) -> Contact:
        """Add phone numbers to an existing contact."""
        contact = self.get_contact(name)

        for phone in phones:
            contact.add_phone(phone)

        return contact

    def add_emails(self, name: str, emails: Sequence[str]) -> Contact:
        """Add email addresses to an existing contact."""
        contact = self.get_contact(name)

        for email in emails:
            contact.add_email(email)

        return contact

    def set_note(self, name: str, note: str) -> Contact:
        """Set or replace a contact note."""
        contact = self.get_contact(name)
        contact.set_note(note)

        return contact

    def remove_note(self, name: str) -> Contact:
        """Remove a contact note."""
        contact = self.get_contact(name)
        contact.clear_note()

        return contact

    def set_tags_from_text(self, name: str, raw_tags: str) -> Contact:
        """Replace contact tags parsed from user text."""
        contact = self.get_contact(name)
        contact.set_tags(self.parse_tags(raw_tags))

        return contact

    def clear_tags(self, name: str) -> Contact:
        """Remove all contact tags."""
        contact = self.get_contact(name)
        contact.clear_tags()

        return contact

    def tag_suggestion_snapshot(self, name: str) -> dict:
        """Return an LLM-ready snapshot of a contact for tag suggestion."""
        contact = self.get_contact(name)
        return build_tag_suggestion_snapshot(contact)

    def suggest_tags(self, name: str) -> list[str]:
        """Return AI-suggested tags for a contact, cleaned and capped.

        Loads the contact, builds an LLM snapshot, calls the tag-suggestion
        model, then normalizes the response, drops duplicates against the
        contact's existing tags, and caps the result at
        :data:`MAX_SUGGESTED_TAGS`.

        Raises:
            KeyError: If the contact does not exist.
        """
        # Lazy import to break the cycle:
        # ai.agent -> ai.deps -> services.contacts.
        from assistant_t800.ai.agent import suggest_tags as _llm_suggest_tags

        contact = self.get_contact(name)
        snapshot = build_tag_suggestion_snapshot(contact)
        raw_tags = _llm_suggest_tags(snapshot)
        return clean_suggested_tags(raw_tags, contact.tags)

    @classmethod
    def parse_tags(cls, raw_tags: str) -> tuple[str, ...]:
        """Parse user tag text by configured multi-value separators."""
        pattern = f"[{re.escape(SystemValue.MULTI_VALUE_SEPARATORS.value)}]"
        result = tuple(
            tag.strip() for tag in re.split(pattern, raw_tags) if tag.strip()
        )

        return result

    @staticmethod
    def format_tags(tags: set[str]) -> str:
        """Format tags for inline editing using the canonical separator."""
        separator = f"{SystemValue.MULTI_VALUE_SEPARATORS.value[0]} "
        result = separator.join(sorted(tags))

        return result

    def remove_contact(self, name: str) -> Contact:
        """Remove a contact from storage."""
        return self._repo.remove(name)

    def remove_address(self, name: str) -> Contact:
        """Remove a contact address."""
        contact = self.get_contact(name)
        contact.remove_address()

        return contact

    def remove_birthday(self, name: str) -> Contact:
        """Remove a contact birthday."""
        contact = self.get_contact(name)
        contact.remove_birthday()

        return contact

    def remove_phones(self, name: str, phones: Sequence[str]) -> Contact:
        """Remove phone numbers from an existing contact."""
        contact = self.get_contact(name)

        for phone in phones:
            contact.remove_phone(phone)

        return contact

    def remove_all_phones(self, name: str) -> Contact:
        """Remove all phone numbers from an existing contact."""
        contact = self.get_contact(name)
        contact.phones.clear()

        return contact

    def remove_emails(self, name: str, emails: Sequence[str]) -> Contact:
        """Remove email addresses from an existing contact."""
        contact = self.get_contact(name)

        for email in emails:
            contact.remove_email(email)

        return contact

    def remove_all_emails(self, name: str) -> Contact:
        """Remove all email addresses from an existing contact."""
        contact = self.get_contact(name)
        contact.emails.clear()

        return contact

    @staticmethod
    def _merge_values(value: str | None, values: Sequence[str]) -> tuple[str, ...]:
        """Merge one optional value with a sequence of values."""
        result = (*(item for item in (value,) if item), *values)

        return result
