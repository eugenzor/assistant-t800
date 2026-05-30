"""Tests for application normalizers."""

from assistant_t800.application import normalizers
from assistant_t800.domain.addresses import ParsedAddress


def test_normalize_address_does_not_call_ai_when_rules_are_complete(monkeypatch):
    calls = []

    def fake_ai(raw_address, parsed):
        calls.append((raw_address, parsed))
        return None

    monkeypatch.setattr(normalizers, "parse_address_with_ai", fake_ai)

    parsed = normalizers.normalize_address("Україна м. Kyiv Khreshchatyk 1 01001")

    assert parsed is not None
    assert parsed.is_complete is True
    assert calls == []


def test_normalize_address_uses_ai_fallback_when_rules_are_incomplete(monkeypatch):
    def fake_ai(raw_address, parsed):
        return ParsedAddress(
            country="Україна",
            city="м. Київ",
            postal_code="01001",
            address_line="вул. Хрещатик, 1",
        )

    monkeypatch.setattr(normalizers, "parse_address_with_ai", fake_ai)

    parsed = normalizers.normalize_address("Хрещатик 1")

    assert parsed is not None
    assert parsed.country == "Україна"
    assert parsed.city == "м. Київ"
    assert parsed.postal_code == "01001"
    assert parsed.address_line == "вул. Хрещатик, 1"
    assert parsed.is_complete is True


# ---------- phone normalization ----------


def test_normalize_phone_converts_ukrainian_local_mobile_to_international():
    result = normalizers.normalize_phone("050 123-45-67")

    assert result == "380501234567"


def test_normalize_phone_converts_ukrainian_eleven_digit_trunk_prefix():
    result = normalizers.normalize_phone("80501234567")

    assert result == "380501234567"


def test_normalize_phone_keeps_explicit_non_ukrainian_international_digits_without_ai(
    monkeypatch,
):
    calls = []

    def fake_ai(phone):
        calls.append(phone)
        return None

    monkeypatch.setattr(normalizers, "parse_phone_with_ai", fake_ai)

    result = normalizers.normalize_phone("+48 123 456 789")

    assert result == "48123456789"
    assert calls == []


def test_normalize_phone_uses_ai_fallback_for_unknown_ten_digit_number(monkeypatch):
    from assistant_t800.domain.phones import ParsedPhone

    calls = []

    def fake_ai(phone):
        calls.append(phone)

        return ParsedPhone(
            normalized="4915112345678",
            country="Deutschland",
            owner="Telekom",
            is_mobile=True,
            is_valid=True,
        )

    monkeypatch.setattr(normalizers, "parse_phone_with_ai", fake_ai)

    result = normalizers.normalize_phone("1773909269")

    assert result == "4915112345678"
    assert calls == ["1773909269"]


def test_normalize_phone_rejects_unknown_ten_digit_number_when_ai_cannot_validate(
    monkeypatch,
):
    monkeypatch.setattr(normalizers, "parse_phone_with_ai", lambda phone: None)

    try:
        normalizers.normalize_phone("1773909269")
        raised = False
    except ValueError:
        raised = True

    assert raised is True


def test_normalize_phone_rejects_short_number_without_ai_call(monkeypatch):
    calls = []

    def fake_ai(phone):
        calls.append(phone)
        return None

    monkeypatch.setattr(normalizers, "parse_phone_with_ai", fake_ai)

    try:
        normalizers.normalize_phone("123456789")
        raised = False
    except ValueError:
        raised = True

    assert raised is True
    assert calls == []
