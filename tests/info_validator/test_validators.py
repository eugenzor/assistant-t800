"""Unit tests for per-entity validators."""

import pytest

from assistant_t800.domain.phone_validation import (
    PhoneClassification,
    PhoneCountry,
    normalize,
)
from assistant_t800.info_validator.models import EntityKind, EntitySource
from assistant_t800.info_validator.validators import (
    BirthdayValidator,
    EmailValidator,
    PhoneValidator,
)


# ---------- PhoneValidator ----------


@pytest.mark.parametrize(
    "raw, value, operator",
    [
        ("0671234567", "+380671234567", "Kyivstar"),
        ("+380501234567", "+380501234567", "Vodafone"),
        ("+38 (050) 123-45-67", "+380501234567", "Vodafone"),
    ],
)
def test_phone_validator_recognizes_and_normalizes(raw, value, operator):
    entity = PhoneValidator().validate(raw)

    assert entity is not None
    assert entity.kind is EntityKind.PHONE
    assert entity.value == value
    assert entity.metadata["operator"] == operator
    assert entity.metadata["country"] == "UA"
    assert entity.source is EntitySource.REGEX


@pytest.mark.parametrize("raw", ["", "abc", "12345", "not-a-phone"])
def test_phone_validator_rejects_non_phone(raw):
    assert PhoneValidator().validate(raw) is None


def test_phone_validator_uses_phone_ai_only_when_unresolved():
    calls: list[str] = []

    def phone_ai(value: str):
        calls.append(value)
        national = normalize(value)
        return PhoneClassification(
            national=national,
            e164="+380001234567",
            country=PhoneCountry.UA,
            operator="MysteryNet",
            is_valid=True,
            looks_like_phone=True,
            source="ai",
        )

    validator = PhoneValidator(phone_ai_fallback=phone_ai)

    resolved = validator.validate("0671234567")
    assert resolved.metadata["operator"] == "Kyivstar"
    assert resolved.source is EntitySource.REGEX
    assert calls == []

    refined = validator.validate("0001234567")
    assert refined.metadata["operator"] == "MysteryNet"
    assert refined.source is EntitySource.AI
    assert calls == ["0001234567"]


# ---------- EmailValidator ----------


def test_email_validator_recognizes():
    entity = EmailValidator().validate("ivan@example.com")

    assert entity is not None
    assert entity.kind is EntityKind.EMAIL
    assert entity.value == "ivan@example.com"


@pytest.mark.parametrize("raw", ["", "not-an-email", "ivan@", "0501234567"])
def test_email_validator_rejects_non_email(raw):
    assert EmailValidator().validate(raw) is None


# ---------- BirthdayValidator ----------


@pytest.mark.parametrize(
    "raw, value",
    [("01.01.1990", "01.01.1990"), ("01/01/1990", "01.01.1990")],
)
def test_birthday_validator_recognizes_and_canonicalizes(raw, value):
    entity = BirthdayValidator().validate(raw)

    assert entity is not None
    assert entity.kind is EntityKind.BIRTHDAY
    assert entity.value == value


@pytest.mark.parametrize("raw", ["", "not-a-date", "0501234567"])
def test_birthday_validator_rejects_non_date(raw):
    assert BirthdayValidator().validate(raw) is None


# ---------- AddressValidator ----------


def test_address_validator_builds_structured_entity():
    from assistant_t800.info_validator.validators import AddressValidator

    entity = AddressValidator().validate(
        {
            "country": "Ukraine",
            "city": "Київ",
            "line": "вул. Хрещатик 1",
            "zip_code": "01001",
        }
    )

    assert entity is not None
    assert entity.kind.name == "ADDRESS"
    assert entity.value == "UA, 01001, Київ, вул. Хрещатик 1"
    assert entity.metadata["country"] == "UA"
    assert entity.metadata["zip_code"] == "01001"
    assert entity.metadata["region"] is None


def test_address_validator_returns_none_for_missing_required():
    from assistant_t800.info_validator.validators import AddressValidator

    assert AddressValidator().validate({"country": "UA", "city": "Київ"}) is None
    assert AddressValidator().validate({"country": "UA"}) is None
    assert AddressValidator().validate({}) is None


def test_address_validator_returns_none_for_unknown_country():
    from assistant_t800.info_validator.validators import AddressValidator

    assert (
        AddressValidator().validate({"country": "Narnia", "city": "X", "line": "Y"})
        is None
    )


def test_address_validator_uses_country_ai_fallback():
    from assistant_t800.info_validator.validators import AddressValidator

    entity = AddressValidator(country_ai_fallback=lambda v: "AT").validate(
        {"country": "Atlantis", "city": "X", "line": "Y"}
    )

    assert entity is not None
    assert entity.metadata["country"] == "AT"
