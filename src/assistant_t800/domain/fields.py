"""Validated contact field types."""

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Optional

from assistant_t800.domain.country import resolve_country
from assistant_t800.domain.phone_validation import (
    PhoneClassification,
    classify_phone,
    looks_like_phone,
    normalize,
)


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
    """Validated phone number, stored in canonical E.164 form."""

    def __init__(
        self,
        value: str,
        ai_fallback: Optional[Callable[[str], Optional[PhoneClassification]]] = None,
    ) -> None:
        classification = classify_phone(value, ai_fallback=ai_fallback)

        if not classification.is_valid or classification.national is None:
            raise ValueError(
                "Некоректний номер телефону. Очікується номер у форматі "
                "+380XXXXXXXXX (або 10 цифр національного формату)"
            )

        canonical = classification.e164 or classification.national

        super().__init__(canonical)
        self.national = classification.national
        self.country = classification.country
        self.operator = classification.operator
        self.classification = classification

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return isinstance(value, str) and normalize(value) is not None

    @classmethod
    def looks_like(cls, value: str) -> bool:
        return looks_like_phone(value)

    def __setstate__(self, state: dict) -> None:
        """Restore from pickle, migrating legacy national-format values."""
        self.__dict__.update(state)

        raw = state.get("value")

        if isinstance(raw, str) and not raw.startswith("+"):
            classification = classify_phone(raw)

            if classification.is_valid and classification.national is not None:
                self.value = classification.e164 or classification.national
                self.national = classification.national
                self.country = classification.country
                self.operator = classification.operator
                self.classification = classification


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

    @staticmethod
    def looks_like(value: str) -> bool:
        """Return ``True`` when the value looks like an email address."""
        normalized = value.strip() if isinstance(value, str) else ""
        return "@" in normalized and " " not in normalized


@dataclass(frozen=True)
class AddressInput:
    """Structured input for building an :class:`Address`."""

    country: str
    city: str
    line: str
    zip_code: Optional[str] = None
    region: Optional[str] = None

    @classmethod
    def from_legacy_string(cls, value: str) -> "AddressInput":
        """Build from a free-form string; fabricates required fields."""
        text = (value or "").strip()
        chunks = [chunk.strip() for chunk in text.split(",") if chunk.strip()]

        if len(chunks) >= 2:
            city, line = chunks[0], ", ".join(chunks[1:])
        else:
            city = line = text

        return cls(country="UA", city=city, line=line)


class Address(Field):
    """Validated structured postal address (Country, Zip, City, Region, Line)."""

    def __init__(
        self,
        country: str,
        city: str,
        line: str,
        zip_code: Optional[str] = None,
        region: Optional[str] = None,
        country_ai_fallback: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        resolved_country = resolve_country(
            country or "", ai_fallback=country_ai_fallback
        )

        if resolved_country is None:
            raise ValueError(
                "Не вдалося розпізнати країну. Вкажіть назву або код (напр. UA)"
            )

        city_value = (city or "").strip()
        line_value = (line or "").strip()

        if not city_value:
            raise ValueError("Місто (City) є обов'язковим")

        if not line_value:
            raise ValueError("Адресний рядок (Address Line) є обов'язковим")

        zip_value = self._normalize_zip(zip_code)
        region_value = (region or "").strip() or None

        self.country = resolved_country
        self.city = city_value
        self.line = line_value
        self.zip_code = zip_value
        self.region = region_value

        super().__init__(self._format())

    @classmethod
    def _normalize_zip(cls, zip_code: Optional[str]) -> Optional[str]:
        if zip_code is None:
            return None

        candidate = zip_code.strip()

        if not candidate:
            return None

        digits = re.sub(r"[\s\-]", "", candidate)

        if not digits.isdigit():
            raise ValueError("Поштовий індекс (Zip) має складатися з цифр")

        return candidate

    def _format(self) -> str:
        parts = [
            self.country,
            self.zip_code,
            self.city,
            self.region,
            self.line,
        ]

        return ", ".join(part for part in parts if part)

    def as_dict(self) -> dict:
        return {
            "country": self.country,
            "zip_code": self.zip_code,
            "city": self.city,
            "region": self.region,
            "line": self.line,
        }

    def __setstate__(self, state: dict) -> None:
        """Restore from pickle, migrating legacy plain-string addresses."""
        self.__dict__.update(state)

        if "country" not in state or "city" not in state or "line" not in state:
            legacy = AddressInput.from_legacy_string(state.get("value", ""))
            self.country = resolve_country(legacy.country) or legacy.country
            self.city = legacy.city
            self.line = legacy.line
            self.zip_code = None
            self.region = None


class Birthday(Field):
    """Validated birthday in ``DD.MM.YYYY`` format."""

    DATE_FORMAT = "%d.%m.%Y"
    INPUT_FORMATS = ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y")
    _LOOKS_LIKE_PATTERN = re.compile(r"^\d{1,2}[./-]\d{1,2}[./-]\d{4}$")

    def __init__(self, value: str) -> None:
        parsed = self._parse(value)

        if parsed is None:
            raise ValueError("Некоректний формат дати. Використовуйте DD.MM.YYYY")

        if parsed > date.today():
            raise ValueError("День народження не може бути в майбутньому")

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
