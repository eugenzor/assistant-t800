"""Contact management service layer."""

from collections.abc import Sequence
from typing import Optional

from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.repositories.contacts import ContactsRepository


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

    def add_tags(self, name: str, tags: Sequence[str]) -> Contact:
        """Add tags to an existing contact."""
        contact = self.get_contact(name)

        for tag in tags:
            contact.add_tag(tag)

        return contact

    def remove_tags(self, name: str, tags: Sequence[str]) -> Contact:
        """Remove tags from an existing contact."""
        contact = self.get_contact(name)

        for tag in tags:
            contact.remove_tag(tag)

        return contact

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
