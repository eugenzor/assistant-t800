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

    def all(self) -> list[Contact]:
        """Return all stored contacts."""
        return list(self._data.values())