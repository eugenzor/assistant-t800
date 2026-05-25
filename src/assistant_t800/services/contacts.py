"""Contact management service layer."""

from typing import Optional

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
        address: Optional[str] = None,
        birthday: Optional[str] = None,
    ) -> Contact:
        """Create and store a new contact.

        Args:
            name: Contact name.
            phone: Optional phone number.
            email: Optional email address.
            address: Optional physical address.
            birthday: Optional birthday in DD.MM.YYYY format.

        Returns:
            Created contact instance.
        """
        contact = Contact(Name(name))

        if phone:
            contact.add_phone(phone)

        if email:
            contact.add_email(email)

        if address:
            contact.set_address(address)

        if birthday:
            contact.set_birthday(birthday)

        self._repo.add(contact)

        return contact

    def get_contact(self, name: str) -> Contact:
        """Return a contact by name.

        Raises:
            KeyError: If the contact does not exist.
        """
        contact = self._repo.get(name)

        if contact is None:
            raise KeyError(f"Контакт «{name}» не знайдено")

        return contact

    def list_contacts(self) -> list[Contact]:
        """Return all stored contacts."""
        return self._repo.all()
