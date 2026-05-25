"""Contact domain model.

The module defines the ``Contact`` entity and delegates field validation
to dedicated domain field types.
"""

from typing import Optional

from assistant_t800.domain.fields import Address, Birthday, Email, Name, Phone


class Contact:
    """Contact aggregate with validated personal data fields.

    Attributes:
        name: Required contact name.
        phones: Contact phone numbers.
        emails: Contact email addresses.
        address: Optional physical address.
        birthday: Optional birthday date.
    """

    def __init__(self, name: Name) -> None:
        """Initialize a contact with required name and empty optional fields."""
        self.name: Name = name
        self.phones: list[Phone] = []
        self.emails: list[Email] = []
        self.address: Optional[Address] = None
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone: str) -> None:
        """Add a validated unique phone number to the contact.

        Raises:
            ValueError: If the phone number is invalid or already exists.
        """
        new_phone = Phone(phone)

        if self.find_phone(new_phone.value) is not None:
            raise ValueError(f"Телефон {new_phone.value} вже існує")

        self.phones.append(new_phone)

    def find_phone(self, phone: str) -> Optional[Phone]:
        """Return a phone by exact value, or ``None`` if it is not present."""
        for item in self.phones:
            if item.value == phone:
                return item

        return None

    def add_email(self, email: str) -> None:
        """Add a validated unique email address to the contact.

        Raises:
            ValueError: If the email address is invalid or already exists.
        """
        new_email = Email(email)

        if self.find_email(new_email.value) is not None:
            raise ValueError(f"E-mail {new_email.value} вже існує")

        self.emails.append(new_email)

    def find_email(self, email: str) -> Optional[Email]:
        """Return an email by exact value, or ``None`` if it is not present."""
        for item in self.emails:
            if item.value == email:
                return item

        return None

    def set_address(self, address: str) -> None:
        """Set or replace the contact address."""
        self.address = Address(address)

    def set_birthday(self, birthday: str) -> None:
        """Set or replace the contact birthday."""
        self.birthday = Birthday(birthday)

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
