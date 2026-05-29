"""Unit tests for validated contact field types in ``assistant_t800.domain.fields``."""

from datetime import date, timedelta

import pytest

from assistant_t800.domain.fields import (
    Address,
    Birthday,
    Email,
    Field,
    Name,
    Phone,
)


# ---------- Field base ----------


def test_field_str_returns_value():
    field = Field("hello")

    assert str(field) == "hello"


def test_field_str_coerces_non_string_value():
    field = Field.__new__(Field)
    field.value = 42  # type: ignore[assignment]

    assert str(field) == "42"


# ---------- Name ----------


def test_name_strips_surrounding_whitespace():
    name = Name("  Іван  ")

    assert name.value == "Іван"


def test_name_str_returns_normalized_value():
    name = Name("Іван")

    assert str(name) == "Іван"


@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_name_rejects_empty_or_whitespace_value(raw):
    with pytest.raises(ValueError):
        Name(raw)


def test_name_rejects_none_like_empty_value():
    with pytest.raises(ValueError):
        Name(None)  # type: ignore[arg-type]


# ---------- Phone ----------


def test_phone_stores_e164_canonical_value():
    phone = Phone("0501234567")

    assert phone.value == "+380501234567"
    assert phone.national == "0501234567"


def test_phone_strips_surrounding_whitespace():
    phone = Phone("  0501234567  ")

    assert phone.value == "+380501234567"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0501234567", "+380501234567"),
        ("+380501234567", "+380501234567"),
        ("380501234567", "+380501234567"),
        ("050 123 45 67", "+380501234567"),
        ("+38 (050) 123-45-67", "+380501234567"),
        ("501234567", "+380501234567"),
    ],
)
def test_phone_normalizes_to_e164(raw, expected):
    assert Phone(raw).value == expected


@pytest.mark.parametrize(
    "raw, operator",
    [
        ("0501234567", "Vodafone"),
        ("0671234567", "Kyivstar"),
        ("0631234567", "lifecell"),
        ("0911234567", "3Mob"),
        ("0941234567", "Intertelecom"),
    ],
)
def test_phone_resolves_known_operator(raw, operator):
    phone = Phone(raw)

    assert phone.operator == operator
    assert phone.country.value == "UA"


def test_phone_accepts_valid_shape_with_unknown_operator():
    phone = Phone("0001234567")

    assert phone.value == "+380001234567"
    assert phone.operator is None
    assert phone.country.value == "UA"


@pytest.mark.parametrize(
    "raw",
    ["", "123", "12345678901", "050123456a", "+380 50 123 45 6", "abc"],
)
def test_phone_rejects_invalid_value(raw):
    with pytest.raises(ValueError):
        Phone(raw)


def test_phone_uses_ai_fallback_only_when_unresolved():
    from assistant_t800.domain.phone_validation import (
        PhoneClassification,
        PhoneCountry,
    )

    calls: list[str] = []

    def ai(value: str):
        calls.append(value)
        return PhoneClassification(
            national="0001234567",
            e164="+380001234567",
            country=PhoneCountry.UA,
            operator="MysteryNet",
            is_valid=True,
            looks_like_phone=True,
            source="ai",
        )

    resolved = Phone("0501234567", ai_fallback=ai)
    assert resolved.operator == "Vodafone"
    assert calls == []  # regex resolved it; AI never consulted

    unresolved = Phone("0001234567", ai_fallback=ai)
    assert unresolved.operator == "MysteryNet"
    assert calls == ["0001234567"]


def test_phone_migrates_legacy_national_value_on_unpickle():
    import pickle

    legacy = Phone.__new__(Phone)
    legacy.__dict__["value"] = "0501234567"

    restored = pickle.loads(pickle.dumps(legacy))

    assert restored.value == "+380501234567"
    assert restored.national == "0501234567"
    assert restored.operator == "Vodafone"


def test_phone_pickle_round_trip_is_stable():
    import pickle

    phone = Phone("0671234567")
    restored = pickle.loads(pickle.dumps(phone))

    assert restored.value == "+380671234567"


def test_phone_is_valid_accepts_clean_value():
    assert Phone.is_valid("0501234567")


def test_phone_is_valid_accepts_padded_value():
    assert Phone.is_valid("  0501234567  ")


def test_phone_is_valid_accepts_international_format():
    assert Phone.is_valid("+380501234567")


@pytest.mark.parametrize("raw", ["", "123", "12345678901", "abcdefghij"])
def test_phone_is_valid_rejects_invalid_value(raw):
    assert not Phone.is_valid(raw)


def test_phone_is_valid_rejects_non_string_value():
    assert not Phone.is_valid(1234567890)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw",
    ["0501234567", "+380501234567", "050-123-45-67", "(050) 123 45 67"],
)
def test_phone_looks_like_accepts_phone_shapes(raw):
    assert Phone.looks_like(raw)


@pytest.mark.parametrize("raw", ["", "abc", "1", "12345"])
def test_phone_looks_like_rejects_non_phone_value(raw):
    assert not Phone.looks_like(raw)


def test_phone_looks_like_rejects_non_string_value():
    assert not Phone.looks_like(1234567890)  # type: ignore[arg-type]


# ---------- Email ----------


def test_email_accepts_typical_address():
    email = Email("ivan@example.com")

    assert email.value == "ivan@example.com"


def test_email_strips_surrounding_whitespace():
    email = Email("  ivan@example.com  ")

    assert email.value == "ivan@example.com"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "not-an-email",
        "ivan@",
        "@example.com",
        "ivan@example",
        "ivan @example.com",
        "ivan@example.c",
    ],
)
def test_email_rejects_invalid_value(raw):
    with pytest.raises(ValueError):
        Email(raw)


def test_email_is_valid_accepts_clean_value():
    assert Email.is_valid("ivan@example.com")


def test_email_is_valid_rejects_invalid_value():
    assert not Email.is_valid("not-an-email")


def test_email_is_valid_rejects_non_string_value():
    assert not Email.is_valid(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw",
    ["ivan@example.com", "ivan@x", "@x", "a@b"],
)
def test_email_looks_like_accepts_at_symbol_value(raw):
    assert Email.looks_like(raw)


@pytest.mark.parametrize("raw", ["", "no-at-sign", "ivan @example.com"])
def test_email_looks_like_rejects_value_without_at_or_with_space(raw):
    assert not Email.looks_like(raw)


def test_email_looks_like_rejects_non_string_value():
    assert not Email.looks_like(123)  # type: ignore[arg-type]


# ---------- Address ----------


def test_address_builds_canonical_value_with_all_fields():
    address = Address(
        country="Ukraine",
        city="Київ",
        line="вул. Хрещатик 1",
        zip_code="01001",
        region="Київська обл.",
    )

    assert address.country == "UA"
    assert address.value == "UA, 01001, Київ, Київська обл., вул. Хрещатик 1"


def test_address_omits_absent_optional_fields():
    address = Address(country="UA", city="Львів", line="пл. Ринок 1")

    assert address.value == "UA, Львів, пл. Ринок 1"
    assert address.zip_code is None
    assert address.region is None


def test_address_resolves_country_aliases():
    assert Address(country="україна", city="Київ", line="X").country == "UA"
    assert Address(country="usa", city="NYC", line="5th Ave").country == "US"


def test_address_as_dict_returns_components():
    address = Address(country="UA", city="Київ", line="вул. X", zip_code="01001")

    assert address.as_dict() == {
        "country": "UA",
        "zip_code": "01001",
        "city": "Київ",
        "region": None,
        "line": "вул. X",
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"country": "Narnia", "city": "X", "line": "Y"},
        {"country": "UA", "city": "", "line": "Y"},
        {"country": "UA", "city": "X", "line": ""},
        {"country": "", "city": "X", "line": "Y"},
        {"country": "UA", "city": "X", "line": "Y", "zip_code": "abc"},
    ],
)
def test_address_rejects_invalid_input(kwargs):
    with pytest.raises(ValueError):
        Address(**kwargs)


def test_address_accepts_flexible_zip():
    address = Address(country="UA", city="X", line="Y", zip_code="01-001")

    assert address.zip_code == "01-001"


def test_address_uses_country_ai_fallback_when_table_misses():
    address = Address(
        country="Atlantis",
        city="X",
        line="Y",
        country_ai_fallback=lambda value: "AT",
    )

    assert address.country == "AT"


def test_address_migrates_legacy_string_on_unpickle():
    import pickle

    legacy = Address.__new__(Address)
    legacy.__dict__["value"] = "Київ, вул. Хрещатик 1"

    restored = pickle.loads(pickle.dumps(legacy))

    assert restored.country == "UA"
    assert restored.city == "Київ"
    assert restored.line == "вул. Хрещатик 1"
    assert restored.as_dict()["country"] == "UA"


# ---------- Birthday ----------


@pytest.mark.parametrize(
    "raw",
    ["01.01.1990", "01-01-1990", "01/01/1990"],
)
def test_birthday_accepts_supported_input_formats(raw):
    birthday = Birthday(raw)

    assert birthday.value == "01.01.1990"
    assert birthday.date == date(1990, 1, 1)


def test_birthday_str_returns_canonical_format():
    birthday = Birthday("01/01/1990")

    assert str(birthday) == "01.01.1990"


@pytest.mark.parametrize(
    "raw",
    ["", "not-a-date", "1990-01-01", "32.01.1990", "01.13.1990"],
)
def test_birthday_rejects_invalid_format(raw):
    with pytest.raises(ValueError):
        Birthday(raw)


def test_birthday_rejects_future_date():
    future = date.today() + timedelta(days=1)
    raw = future.strftime("%d.%m.%Y")

    with pytest.raises(ValueError):
        Birthday(raw)


def test_birthday_is_valid_accepts_past_value():
    assert Birthday.is_valid("01.01.1990")


def test_birthday_is_valid_rejects_future_value():
    future = date.today() + timedelta(days=1)

    assert not Birthday.is_valid(future.strftime("%d.%m.%Y"))


def test_birthday_is_valid_rejects_garbage_value():
    assert not Birthday.is_valid("not-a-date")


@pytest.mark.parametrize(
    "raw",
    ["01.01.1990", "1-1-1990", "1/01/1990", "31.12.2024"],
)
def test_birthday_looks_like_accepts_date_pattern(raw):
    assert Birthday.looks_like(raw)


@pytest.mark.parametrize("raw", ["", "01.01.90", "01-01", "0501234567"])
def test_birthday_looks_like_rejects_non_date_value(raw):
    assert not Birthday.looks_like(raw)


def test_birthday_looks_like_rejects_non_string_value():
    assert not Birthday.looks_like(19900101)  # type: ignore[arg-type]
