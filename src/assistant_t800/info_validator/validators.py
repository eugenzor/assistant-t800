"""Per-entity validators used by the info validator facade."""

from __future__ import annotations

from typing import Callable, Optional, Protocol

from assistant_t800.domain.fields import Address, Birthday, Email, Phone
from assistant_t800.domain.phone_validation import PhoneClassification, classify_phone
from assistant_t800.info_validator.models import (
    EntityKind,
    EntitySource,
    ValidatedEntity,
)


class EntityValidator(Protocol):
    """Recognize a single token as a specific entity kind."""

    def validate(self, raw: str) -> Optional[ValidatedEntity]: ...


class PhoneValidator:
    """Recognize phone numbers via the layered phone pipeline."""

    def __init__(
        self,
        phone_ai_fallback: Optional[
            Callable[[str], "PhoneClassification | None"]
        ] = None,
    ) -> None:
        self._phone_ai_fallback = phone_ai_fallback

    def validate(self, raw: str) -> Optional[ValidatedEntity]:
        if not Phone.looks_like(raw):
            return None

        classification = classify_phone(raw, ai_fallback=self._phone_ai_fallback)

        if not classification.is_valid or classification.national is None:
            return None

        return ValidatedEntity(
            kind=EntityKind.PHONE,
            raw=raw,
            value=classification.e164 or classification.national,
            source=(
                EntitySource.AI if classification.source == "ai" else EntitySource.REGEX
            ),
            metadata={
                "country": classification.country.value,
                "operator": classification.operator,
                "national": classification.national,
            },
        )


class EmailValidator:
    """Recognize email addresses via the ``Email`` field."""

    def validate(self, raw: str) -> Optional[ValidatedEntity]:
        if not Email.is_valid(raw):
            return None

        return ValidatedEntity(
            kind=EntityKind.EMAIL,
            raw=raw,
            value=Email(raw).value,
            source=EntitySource.REGEX,
        )


class BirthdayValidator:
    """Recognize birthdays via the ``Birthday`` field."""

    def validate(self, raw: str) -> Optional[ValidatedEntity]:
        if not Birthday.is_valid(raw):
            return None

        return ValidatedEntity(
            kind=EntityKind.BIRTHDAY,
            raw=raw,
            value=Birthday(raw).value,
            source=EntitySource.REGEX,
        )


class AddressValidator:
    """Build a structured address entity from named fields."""

    def __init__(
        self,
        country_ai_fallback: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        self._country_ai_fallback = country_ai_fallback

    def validate(self, fields: dict) -> Optional[ValidatedEntity]:
        try:
            address = Address(
                country=fields.get("country", ""),
                city=fields.get("city", ""),
                line=fields.get("line", ""),
                zip_code=fields.get("zip_code"),
                region=fields.get("region"),
                country_ai_fallback=self._country_ai_fallback,
            )
        except ValueError:
            return None

        return ValidatedEntity(
            kind=EntityKind.ADDRESS,
            raw=address.value,
            value=address.value,
            source=EntitySource.REGEX,
            metadata=address.as_dict(),
        )


# Token validators tried in order; AddressValidator is driven separately.
DEFAULT_VALIDATORS: tuple[EntityValidator, ...] = (
    PhoneValidator(),
    EmailValidator(),
    BirthdayValidator(),
)
