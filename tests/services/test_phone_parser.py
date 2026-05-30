"""Tests for deterministic phone parser."""

from assistant_t800.services.phone_parser import parse_phone


def test_parse_phone_resolves_ukrainian_mobile_operator():
    parsed = parse_phone("0501234567")

    assert parsed is not None
    assert parsed.normalized == "380501234567"
    assert parsed.country == "Україна"
    assert parsed.owner == "Vodafone"
    assert parsed.is_mobile is True
    assert parsed.is_valid is True


def test_parse_phone_resolves_ukrainian_city_code():
    parsed = parse_phone("0441234567")

    assert parsed is not None
    assert parsed.normalized == "380441234567"
    assert parsed.country == "Україна"
    assert parsed.owner == "Kyiv"
    assert parsed.is_mobile is False
    assert parsed.is_valid is True


def test_parse_phone_keeps_plausible_international_number():
    parsed = parse_phone("48123456789")

    assert parsed is not None
    assert parsed.normalized == "48123456789"
    assert parsed.country is None
    assert parsed.owner is None
    assert parsed.is_mobile is None
    assert parsed.is_valid is True


def test_parse_phone_rejects_too_short_value():
    assert parse_phone("123") is None
