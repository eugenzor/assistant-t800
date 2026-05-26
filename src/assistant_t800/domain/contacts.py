"""Contact domain model.

The module defines the ``Contact`` entity and delegates field validation
to dedicated domain field types.
"""

from datetime import datetime, timedelta
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

    def upcoming_birthday(self, window: int = 7):
        """Return greeting date for the next birthday within window days."""
        birthday = self.birthday

        if birthday is None:
            return None

        birthday_date = birthday.date
        today = datetime.now().date()
        end_date = today + timedelta(days=window)

        birthday_this_year = birthday_date.replace(year=today.year)

        # today is 2026-12-28, contact birthday is 1995-01-02, previous op gave us 2026-01-02
        # and we would skip this when real upcoming birthday is 2027-01-02
        if birthday_this_year < today:
            birthday_this_year = birthday_date.replace(year=today.year + 1)

        if not today <= birthday_this_year <= end_date:
            return None

        greeting_date = birthday_this_year

        # if birthday is on Saturday or Sunday, move to the next Monday
        # even if Monday is outside window, since birthday is still within the window
        if greeting_date.weekday() == 5:  # Saturday
            greeting_date += timedelta(days=2)
        elif greeting_date.weekday() == 6:  # Sunday
            greeting_date += timedelta(days=1)

        return greeting_date

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
