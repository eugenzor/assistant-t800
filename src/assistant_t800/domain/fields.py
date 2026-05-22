"""Validated contact field types."""

import re
from datetime import date, datetime


class Field:
    """Base field wrapper for string-based contact values."""

    def __init__(self, value: str) -> None:
        self.value: str = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    """Validated contact name."""

    def __init__(self, value: str) -> None:
        normalized = (value or "").strip()

        if not normalized:
            raise ValueError("Ім'я не може бути порожнім")

        super().__init__(normalized)


class Phone(Field):
    """Validated phone number with exactly 10 digits."""

    _PATTERN = re.compile(r"^\d{10}$")

    def __init__(self, value: str) -> None:
        normalized = (value or "").strip()

        if not self._PATTERN.fullmatch(normalized):
            raise ValueError("Номер телефону має містити рівно 10 цифр")

        super().__init__(normalized)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Return ``True`` when the value is a valid phone number."""
        return isinstance(value, str) and bool(cls._PATTERN.fullmatch(value.strip()))


class Email(Field):
    """Validated email address.

    Uses a pragmatic regex suitable for user input validation in this project.
    """

    _PATTERN = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

    def __init__(self, value: str) -> None:
        normalized = (value or "").strip()

        if not self._PATTERN.fullmatch(normalized):
            raise ValueError("Некоректна електронна адреса")

        super().__init__(normalized)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Return ``True`` when the value is a valid email address."""
        return isinstance(value, str) and bool(cls._PATTERN.fullmatch(value.strip()))


class Address(Field):
    """Validated non-empty physical address."""

    def __init__(self, value: str) -> None:
        normalized = (value or "").strip()

        if not normalized:
            raise ValueError("Адреса не може бути порожньою")

        super().__init__(normalized)


class Birthday(Field):
    """Validated birthday in ``DD.MM.YYYY`` format."""

    DATE_FORMAT = "%d.%m.%Y"

    def __init__(self, value: str) -> None:
        try:
            parsed = datetime.strptime((value or "").strip(), self.DATE_FORMAT).date()
        except (TypeError, ValueError):
            raise ValueError("Некоректний формат дати. Використовуйте DD.MM.YYYY")

        if parsed > date.today():
            raise ValueError("День народження не може бути в майбутньому")

        super().__init__(parsed.strftime(self.DATE_FORMAT))
        self.date: date = parsed

    def __str__(self) -> str:
        return self.date.strftime(self.DATE_FORMAT)
