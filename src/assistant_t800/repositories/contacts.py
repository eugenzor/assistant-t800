"""In-memory contact repository implementation."""

from typing import Optional

from assistant_t800.domain.contacts import Contact


class ContactsRepository:
    """Case-insensitive in-memory contact storage."""

    def __init__(self) -> None:
        self._data: dict[str, Contact] = {}

    @staticmethod
    def _key(name: str) -> str:
        """Normalize a contact name for internal dictionary usage."""
        return name.strip().lower()

    def add(self, contact: Contact) -> None:
        """Store a new contact.

        Raises:
            ValueError: If a contact with the same name already exists.
        """
        key = self._key(contact.name.value)

        if key in self._data:
            raise ValueError(f"Контакт «{contact.name.value}» вже існує")

        self._data[key] = contact

    def get(self, name: str) -> Optional[Contact]:
        """Return a contact by name, or ``None`` if it does not exist."""
        return self._data.get(self._key(name))

    def exists(self, name: str) -> bool:
        """Return ``True`` if the contact exists in the repository."""
        return self._key(name) in self._data

    def set(self, contact: Contact) -> None:
        """Replace an existing contact or add a new one."""
        self._data[self._key(contact.name.value)] = contact

    def remove(self, name: str) -> None:
        """Remove a contact by name. Raises: KeyError if the contact does not exist. Service upstream should handle error."""
        del self._data[self._key(name)]

    @staticmethod
    def _contains(value: str, query: str) -> bool:
        """Return whether value contains query, case-insensitively."""
        return query.strip().lower() in value.lower()

    def find(self, query: str) -> list[Contact]:
        """Return contacts that contain the query in searchable fields."""
        normalized_query = query.strip().lower()

        if not normalized_query:
            return self.all()

        matches: list[Contact] = []

        for contact in self._data.values():
            # name, phones, emails always exist as attributes; rest are optional, so we check if they exist
            searchable_values = [
                contact.name.value,
                *(phone.value for phone in contact.phones),
                *(email.value for email in contact.emails),
                *(field.value for field in (contact.address,) if field is not None),
                *(str(field) for field in (contact.birthday,) if field is not None),
            ]

            if any(self._contains(value, normalized_query) for value in searchable_values):
                matches.append(contact)

        return matches

    def find_by_name(self, query: str) -> list[Contact]:
        """Return contacts whose names contain the query."""
        return [
            contact
            for contact in self._data.values()
            if self._contains(contact.name.value, query)
        ]

    def find_by_phone(self, query: str) -> list[Contact]:
        """Return contacts whose phone numbers contain the query."""
        return [
            contact
            for contact in self._data.values()
            if any(self._contains(phone.value, query) for phone in contact.phones)
        ]

    def find_by_email(self, query: str) -> list[Contact]:
        """Return contacts whose email addresses contain the query."""
        return [
            contact
            for contact in self._data.values()
            if any(self._contains(email.value, query) for email in contact.emails)
        ]

    def find_by_address(self, query: str) -> list[Contact]:
        """Return contacts whose addresses contain the query."""
        return [
            contact
            for contact in self._data.values()
            if contact.address is not None and self._contains(contact.address.value, query)
        ]

    def upcoming_birthdays(self, window: int) -> list[Contact]:
        """Return contacts with upcoming birthdays within specified window. If a window is not specified, defaults to 7 days."""
        return [
            contact
            for contact in self._data.values()
            if contact.upcoming_birthday(window) is not None
        ]

    def ordered(self) -> list[Contact]:
        """Return contacts sorted by name."""
        return sorted(self._data.values(), key=lambda c: c.name.value.lower())

    def all(self) -> list[Contact]:
        """Return all stored contacts."""
        return list(self._data.values())
