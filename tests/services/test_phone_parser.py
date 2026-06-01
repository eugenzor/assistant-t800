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


def test_parse_phone_normalizes_80_prefixed_ukrainian_number():
    # 11-digit "80XXXXXXXXX" shape -> prepend 3 to reach 380XXXXXXXXX.
    parsed = parse_phone("80501234567")

    assert parsed is not None
    assert parsed.normalized == "380501234567"
    assert parsed.country == "Україна"
    assert parsed.owner == "Vodafone"
    assert parsed.is_valid is True


def test_parse_phone_accepts_unknown_ukrainian_code_without_owner():
    # 012 is not a known operator/city code: number is still accepted by
    # length, but no owner/city is attached (recognition != rejection).
    parsed = parse_phone("0121234567")

    assert parsed is not None
    assert parsed.normalized == "380121234567"
    assert parsed.owner is None
    assert parsed.is_mobile is None
    assert parsed.is_valid is True


def test_parse_phone_rejects_too_long_value():
    # 16 digits exceed the E.164 max of 15.
    assert parse_phone("1234567890123456") is None
