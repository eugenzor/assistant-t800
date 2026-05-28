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


def test_phone_accepts_ten_digit_value():
    phone = Phone("0501234567")

    assert phone.value == "0501234567"


def test_phone_strips_surrounding_whitespace():
    phone = Phone("  0501234567  ")

    assert phone.value == "0501234567"


@pytest.mark.parametrize(
    "raw",
    ["", "123", "12345678901", "050123456a", "+380501234567", "050 123 4567"],
)
def test_phone_rejects_invalid_value(raw):
    with pytest.raises(ValueError):
        Phone(raw)


def test_phone_is_valid_accepts_clean_value():
    assert Phone.is_valid("0501234567")


def test_phone_is_valid_accepts_padded_value():
    assert Phone.is_valid("  0501234567  ")


@pytest.mark.parametrize("raw", ["", "123", "12345678901", "abcdefghij"])
def test_phone_is_valid_rejects_invalid_value(raw):
    assert not Phone.is_valid(raw)


def test_phone_is_valid_rejects_non_string_value():
    assert not Phone.is_valid(1234567890)  # type: ignore[arg-type]


@pytest.mark.parametrize("raw", ["0501234567", "1", "12345678901234"])
def test_phone_looks_like_accepts_digits_only(raw):
    assert Phone.looks_like(raw)


@pytest.mark.parametrize("raw", ["", "abc", "050-123-4567", "+380501234567"])
def test_phone_looks_like_rejects_non_digit_value(raw):
    assert not Phone.looks_like(raw)


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


def test_address_strips_surrounding_whitespace():
    address = Address("  Київ, Хрещатик 1  ")

    assert address.value == "Київ, Хрещатик 1"


@pytest.mark.parametrize("raw", ["", "   ", "\t"])
def test_address_rejects_empty_or_whitespace_value(raw):
    with pytest.raises(ValueError):
        Address(raw)


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
