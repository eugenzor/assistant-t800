"""Tests for domain address structures."""

from assistant_t800.domain.addresses import ParsedAddress


def test_parsed_address_is_complete_when_required_parts_exist():
    parsed = ParsedAddress(
        country="Україна",
        city="м. Київ",
        address_line="вул. Хрещатик, 1",
    )

    assert parsed.is_complete is True
    assert parsed.has_data is True


def test_parsed_address_without_address_line_is_not_complete():
    parsed = ParsedAddress(country="Україна", city="м. Київ")

    assert parsed.is_complete is False
    assert parsed.has_data is True


def test_empty_parsed_address_has_no_data():
    parsed = ParsedAddress()

    assert parsed.has_data is False
