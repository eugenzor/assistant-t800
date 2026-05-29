"""Tests for the ``set-address`` key=value parser and address-aware ``add``."""

import pytest

from assistant_t800.application.contacts_args import (
    ContactArgumentsParser,
    ContactDraft,
)
from assistant_t800.application.results import AppResult
from assistant_t800.domain.fields import AddressInput


# ---------- parse_set_address ----------


def test_parse_set_address_required_fields():
    result = ContactArgumentsParser.parse_set_address(
        ("Іван", "country=UA", "city=Київ", "line=вул. Хрещатик 1")
    )

    assert isinstance(result, tuple)
    name, address = result
    assert name == "Іван"
    assert isinstance(address, AddressInput)
    assert address.country == "UA"
    assert address.city == "Київ"
    assert address.line == "вул. Хрещатик 1"
    assert address.zip_code is None
    assert address.region is None


def test_parse_set_address_with_all_fields():
    result = ContactArgumentsParser.parse_set_address(
        (
            "Іван",
            "country=ua",
            "city=Київ",
            "line=вул. X",
            "zip=01001",
            "region=Київська обл.",
        )
    )

    assert isinstance(result, tuple)
    _, address = result
    assert address.zip_code == "01001"
    assert address.region == "Київська обл."


def test_parse_set_address_supports_uk_aliases():
    result = ContactArgumentsParser.parse_set_address(
        ("Іван", "країна=Україна", "місто=Львів", "вулиця=пл. Ринок 1")
    )

    assert isinstance(result, tuple)
    _, address = result
    assert address.country == "Україна"
    assert address.city == "Львів"
    assert address.line == "пл. Ринок 1"


def test_parse_set_address_missing_required_returns_error():
    result = ContactArgumentsParser.parse_set_address(
        ("Іван", "country=UA", "city=Київ")
    )

    assert isinstance(result, AppResult)
    assert result.success is False


def test_parse_set_address_unknown_key_returns_error():
    result = ContactArgumentsParser.parse_set_address(
        ("Іван", "country=UA", "city=Київ", "line=X", "junk=Y")
    )

    assert isinstance(result, AppResult)
    assert result.success is False


def test_parse_set_address_malformed_token_returns_error():
    result = ContactArgumentsParser.parse_set_address(
        ("Іван", "country=UA", "city=Київ", "no_equals_sign")
    )

    assert isinstance(result, AppResult)
    assert result.success is False


def test_parse_set_address_no_args_returns_error():
    result = ContactArgumentsParser.parse_set_address(())

    assert isinstance(result, AppResult)
    assert result.success is False


# ---------- parse_add with key=value address ----------


def test_parse_add_collects_key_value_address():
    result = ContactArgumentsParser.parse_add(
        ("Іван", "country=UA", "city=Київ", "line=вул. X")
    )

    assert isinstance(result, ContactDraft)
    assert result.address is not None
    assert result.address.country == "UA"
    assert result.address.city == "Київ"
    assert result.address.line == "вул. X"


def test_parse_add_kv_address_mixed_with_other_tokens():
    result = ContactArgumentsParser.parse_add(
        (
            "Іван",
            "0671234567",
            "country=UA",
            "ivan@example.com",
            "city=Львів",
            "line=пл. Ринок 1",
            "01.01.1990",
        )
    )

    assert isinstance(result, ContactDraft)
    assert result.phones == ("0671234567",)
    assert result.emails == ("ivan@example.com",)
    assert result.birthday == "01.01.1990"
    assert result.address is not None
    assert result.address.city == "Львів"


def test_parse_add_kv_address_missing_required_returns_error():
    result = ContactArgumentsParser.parse_add(("Іван", "country=UA", "city=Київ"))

    assert isinstance(result, AppResult)
    assert result.success is False


def test_parse_add_legacy_bare_token_still_bridges_to_address():
    result = ContactArgumentsParser.parse_add(("Іван", "0671234567", "Київ Хрещатик 1"))

    assert isinstance(result, ContactDraft)
    assert result.address is not None
    assert result.address.country == "UA"
    assert result.address.city == "Київ Хрещатик 1"


# ---------- looks_like_address gating ----------


@pytest.mark.parametrize(
    "token",
    [
        "Київ Хрещатик 1",  # has whitespace
        "Київ, вул. X",  # comma separator
        "вул.Лесі",  # known marker
        "м.Київ",  # known marker
        "Lviv center",  # whitespace
        "St. Petersburg",  # dot + whitespace
    ],
)
def test_looks_like_address_accepts_plausible(token):
    assert ContactArgumentsParser.looks_like_address(token)


@pytest.mark.parametrize("token", ["", "   ", "abc", "050123456a", "x", "123junk"])
def test_looks_like_address_rejects_junk(token):
    assert not ContactArgumentsParser.looks_like_address(token)


def test_looks_like_address_rejects_non_string():
    assert not ContactArgumentsParser.looks_like_address(None)  # type: ignore[arg-type]


@pytest.mark.parametrize("token", ["abc", "050123456a", "junk"])
def test_parse_add_rejects_non_address_bare_token(token):
    """Bare leftover tokens that do not resemble an address must error out."""
    result = ContactArgumentsParser.parse_add(("Іван", token))

    assert isinstance(result, AppResult)
    assert result.success is False
