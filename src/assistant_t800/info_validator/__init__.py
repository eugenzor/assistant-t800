"""Structured validation and classification of raw contact data."""

from assistant_t800.info_validator.models import (
    EntityKind,
    EntitySource,
    InfoResult,
    ValidatedEntity,
)
from assistant_t800.info_validator.service import AIFallback, InfoValidator
from assistant_t800.info_validator.validators import (
    DEFAULT_VALIDATORS,
    AddressValidator,
    BirthdayValidator,
    EmailValidator,
    EntityValidator,
    PhoneValidator,
)

__all__ = [
    "AIFallback",
    "AddressValidator",
    "BirthdayValidator",
    "DEFAULT_VALIDATORS",
    "EmailValidator",
    "EntityKind",
    "EntitySource",
    "EntityValidator",
    "InfoResult",
    "InfoValidator",
    "PhoneValidator",
    "ValidatedEntity",
]
