"""Contact domain model.

The module defines the ``Contact`` entity and delegates field validation
to dedicated domain field types.
"""

from typing import Optional

from assistant_t800.application.enums import SystemValue
from assistant_t800.domain.fields import Address, Birthday, Email, Name, Phone


class Contact:
    """Contact aggregate with validated personal data fields."""

    def __init__(self, name: Name) -> None:
        """Initialize a contact with required name and empty optional fields."""
        self.name: Name = name
        self.phones: list[Phone] = []
        self.emails: list[Email] = []
        self.address: Optional[Address] = None
        self.birthday: Optional[Birthday] = None
        self.note: str = SystemValue.EMPTY_TEXT.value
        self.tags: set[str] = set()

    def add_phone(self, phone: str) -> None:
        """Add a validated unique phone number to the contact."""
        new_phone = Phone(phone)

        if self.find_phone(new_phone.value) is not None:
            raise ValueError(f"Телефон {new_phone.value} вже існує")

        self.phones.append(new_phone)

    def remove_phone(self, phone: str) -> None:
        """Remove an existing phone number from the contact."""
        current = self.find_phone(Phone(phone).value)

        if current is None:
            raise ValueError(f"Телефон {phone} не знайдено")

        self.phones.remove(current)

    def find_phone(self, phone: str) -> Optional[Phone]:
        """Return a phone by exact value, or ``None`` if it is not present."""
        result = next((item for item in self.phones if item.value == phone), None)

        return result

    def add_email(self, email: str) -> None:
        """Add a validated unique email address to the contact."""
        new_email = Email(email)

        if self.find_email(new_email.value) is not None:
            raise ValueError(f"E-mail {new_email.value} вже існує")

        self.emails.append(new_email)

    def remove_email(self, email: str) -> None:
        """Remove an existing email address from the contact."""
        current = self.find_email(Email(email).value)

        if current is None:
            raise ValueError(f"E-mail {email} не знайдено")

        self.emails.remove(current)

    def find_email(self, email: str) -> Optional[Email]:
        """Return an email by exact value, or ``None`` if it is not present."""
        result = next((item for item in self.emails if item.value == email), None)

        return result

    def set_address(self, address: str) -> None:
        """Set or replace the contact address."""
        self.address = Address(address)

    def remove_address(self) -> None:
        """Remove the contact address."""
        self.address = None

    def set_birthday(self, birthday: str) -> None:
        """Set or replace the contact birthday."""
        self.birthday = Birthday(birthday)

    def remove_birthday(self) -> None:
        """Remove the contact birthday."""
        self.birthday = None

    def set_note(self, note: str) -> None:
        """Set or replace the contact note."""
        self.note = note.strip() or SystemValue.EMPTY_TEXT.value

    def clear_note(self) -> None:
        """Reset the contact note to the internal empty value."""
        self.note = SystemValue.EMPTY_TEXT.value

    def add_tag(self, tag: str) -> None:
        """Add a normalized tag to the contact."""
        normalized = tag.strip().casefold()

        if normalized:
            self.tags.add(normalized)

    def remove_tag(self, tag: str) -> None:
        """Remove a normalized tag from the contact."""
        normalized = tag.strip().casefold()

        if normalized not in self.tags:
            raise ValueError(f"Тег {tag} не знайдено")

        self.tags.remove(normalized)

    def __str__(self) -> str:
        """Return a compact user-facing contact representation."""
        parts = [f"Ім'я контакту: {self.name.value}"]

        if self.phones:
            parts.append("телефони: " + "; ".join(item.value for item in self.phones))

        if self.emails:
            parts.append("e-mail: " + "; ".join(item.value for item in self.emails))

        if self.address is not None:
            parts.append(f"адреса: {self.address.value}")

        if self.birthday is not None:
            parts.append(f"день народження: {self.birthday}")

        return ", ".join(parts)
