"""Validated contact field types."""

import re
from datetime import date, datetime

from assistant_t800.application.phone_markers import PhoneMarkers
from assistant_t800.localization import ErrorCode


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
            raise ValueError(str(ErrorCode.EMPTY_NAME))

        super().__init__(normalized)


class Phone(Field):
    """Validated phone number digits."""

    _PATTERN = re.compile(r"^\d{10,15}$")

    def __init__(self, value: str) -> None:
        normalized = (value or "").strip()

        if not self._PATTERN.fullmatch(normalized):
            raise ValueError(str(ErrorCode.INVALID_PHONE_DIGITS_RANGE))

        super().__init__(normalized)

    @property
    def display_value(self) -> str:
        """Return user-facing phone with an international plus prefix."""
        result = f"+{self.value}"

        return result

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Return ``True`` when the value is a valid phone number."""
        result = isinstance(value, str) and bool(cls._PATTERN.fullmatch(value.strip()))

        return result

    @classmethod
    def looks_like(cls, value: str) -> bool:
        """Return ``True`` when the value looks like a phone number."""
        result = PhoneMarkers.looks_like(value)

        return result

    def __str__(self) -> str:
        return self.display_value


class Email(Field):
    """Validated email address.

    Uses a pragmatic regex suitable for user input validation in this project.
    """

    _PATTERN = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

    def __init__(self, value: str) -> None:
        normalized = (value or "").strip()

        if not self._PATTERN.fullmatch(normalized):
            raise ValueError(str(ErrorCode.INVALID_EMAIL))

        super().__init__(normalized)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Return ``True`` when the value is a valid email address."""
        return isinstance(value, str) and bool(cls._PATTERN.fullmatch(value.strip()))

    @staticmethod
    def looks_like(value: str) -> bool:
        """Return ``True`` when the value looks like an email address."""
        normalized = value.strip() if isinstance(value, str) else ""
        return "@" in normalized and " " not in normalized


class Address(Field):
    """Validated non-empty physical address."""

    def __init__(self, value: str) -> None:
        normalized = (value or "").strip()

        if not normalized:
            raise ValueError(str(ErrorCode.EMPTY_ADDRESS))

        super().__init__(normalized)


class Birthday(Field):
    """Validated birthday in ``DD.MM.YYYY`` format."""

    DATE_FORMAT = "%d.%m.%Y"
    INPUT_FORMATS = ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y")
    _LOOKS_LIKE_PATTERN = re.compile(r"^\d{1,2}[./-]\d{1,2}[./-]\d{4}$")

    def __init__(self, value: str) -> None:
        parsed = self._parse(value)

        if parsed is None:
            raise ValueError(str(ErrorCode.INVALID_BIRTHDAY_FORMAT))

        if parsed > date.today():
            raise ValueError(str(ErrorCode.FUTURE_BIRTHDAY))

        super().__init__(parsed.strftime(self.DATE_FORMAT))
        self.date: date = parsed

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Return ``True`` when the value is a valid birthday."""
        parsed = cls._parse(value)
        result = parsed is not None and parsed <= date.today()

        return result

    @classmethod
    def looks_like(cls, value: str) -> bool:
        """Return ``True`` when the value looks like a birthday date."""
        return isinstance(value, str) and bool(
            cls._LOOKS_LIKE_PATTERN.fullmatch(value.strip())
        )

    @classmethod
    def _parse(cls, value: str) -> date | None:
        """Parse a birthday from supported input formats."""
        parsed: date | None = None
        normalized = (value or "").strip()

        for date_format in cls.INPUT_FORMATS:
            try:
                parsed = datetime.strptime(normalized, date_format).date()
                break
            except (TypeError, ValueError):
                continue

        return parsed

    def __str__(self) -> str:
        return self.date.strftime(self.DATE_FORMAT)
