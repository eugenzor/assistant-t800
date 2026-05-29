"""Unit tests for the layered phone validation pipeline."""

import pytest

from assistant_t800.domain.phone_validation import (
    PhoneClassification,
    PhoneCountry,
    classify_phone,
    looks_like_phone,
    normalize,
)


# ---------- normalize ----------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0501234567", "0501234567"),
        ("  0501234567  ", "0501234567"),
        ("+380501234567", "0501234567"),
        ("380501234567", "0501234567"),
        ("501234567", "0501234567"),
        ("050 123 45 67", "0501234567"),
        ("050-123-45-67", "0501234567"),
        ("(050) 123.45.67", "0501234567"),
        ("+38 (050) 123-45-67", "0501234567"),
    ],
)
def test_normalize_accepts_ukrainian_shapes(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "abc",
        "123",
        "12345678901",
        "+380 50 123 45 6",
        "050123456a",
        "1234567890",  # 10 digits but no trunk leading zero -> not UA national
        "9876543210",
    ],
)
def test_normalize_rejects_invalid(raw):
    assert normalize(raw) is None


def test_normalize_rejects_non_string():
    assert normalize(1234567890) is None  # type: ignore[arg-type]


# ---------- e164 ----------


@pytest.mark.parametrize(
    "raw, e164",
    [
        ("0501234567", "+380501234567"),
        ("+380671234567", "+380671234567"),
        ("050 123 45 67", "+380501234567"),
        ("501234567", "+380501234567"),
    ],
)
def test_classify_produces_e164(raw, e164):
    assert classify_phone(raw).e164 == e164


# ---------- looks_like_phone ----------


@pytest.mark.parametrize(
    "raw",
    ["0501234567", "+380501234567", "050-123-45-67", "(050) 123 45 67", "1234567"],
)
def test_looks_like_phone_accepts_plausible(raw):
    assert looks_like_phone(raw)


@pytest.mark.parametrize("raw", ["", "abc", "1", "12345", "12 34", "01.01.1990"])
def test_looks_like_phone_rejects_implausible(raw):
    assert not looks_like_phone(raw)


def test_looks_like_phone_rejects_non_string():
    assert not looks_like_phone(123)  # type: ignore[arg-type]


# ---------- classify_phone: regex layer ----------


@pytest.mark.parametrize(
    "raw, operator",
    [
        ("0671234567", "Kyivstar"),
        ("0501234567", "Vodafone"),
        ("0631234567", "lifecell"),
        ("0911234567", "3Mob"),
        ("0941234567", "Intertelecom"),
    ],
)
def test_classify_resolves_known_operators_via_regex(raw, operator):
    result = classify_phone(raw)

    assert result.is_valid
    assert result.source == "regex"
    assert result.country is PhoneCountry.UA
    assert result.operator == operator
    assert result.e164 is not None and result.e164.startswith("+380")
    assert result.resolved


def test_classify_valid_shape_unknown_operator_keeps_country_but_unresolved():
    result = classify_phone("0001234567")

    assert result.is_valid
    assert result.source == "regex"
    # Passed UA normalization, so country is known even if operator is not.
    assert result.country is PhoneCountry.UA
    assert result.e164 == "+380001234567"
    assert result.operator is None
    assert not result.resolved


def test_classify_invalid_input():
    result = classify_phone("nonsense")

    assert not result.is_valid
    assert result.national is None
    assert result.e164 is None
    assert result.source == "none"


# ---------- classify_phone: AI fallback layer ----------


def _ai(operator="MysteryNet", country=PhoneCountry.UA):
    calls: list[str] = []

    def fallback(value: str):
        calls.append(value)
        return PhoneClassification(
            national=normalize(value),
            e164=None,
            country=country,
            operator=operator,
            is_valid=True,
            looks_like_phone=True,
            source="ai",
        )

    return fallback, calls


def test_ai_fallback_not_called_when_regex_resolves():
    fallback, calls = _ai()

    result = classify_phone("0501234567", ai_fallback=fallback)

    assert result.source == "regex"
    assert result.operator == "Vodafone"
    assert calls == []


def test_ai_fallback_called_when_unresolved_but_plausible():
    fallback, calls = _ai()

    result = classify_phone("0001234567", ai_fallback=fallback)

    assert result.source == "ai"
    assert result.operator == "MysteryNet"
    assert calls == ["0001234567"]


def test_ai_fallback_not_called_for_non_phone_input():
    fallback, calls = _ai()

    result = classify_phone("nonsense", ai_fallback=fallback)

    assert result.source == "none"
    assert calls == []


def test_ai_fallback_returning_none_keeps_regex_result():
    def fallback(value: str):
        return None

    result = classify_phone("0001234567", ai_fallback=fallback)

    assert result.source == "regex"
    assert result.operator is None
