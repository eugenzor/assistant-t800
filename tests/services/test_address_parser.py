"""Tests for deterministic address parser."""

from assistant_t800.services.address_parser import parse_address


def test_parse_ukrainian_address_with_spaces_extracts_and_removes_parts():
    parsed = parse_address("Україна м. Kyiv Khreshchatyk 1 01001")

    assert parsed is not None
    assert parsed.country == "Україна"
    assert parsed.city == "м. Kyiv"
    assert parsed.postal_code == "01001"
    assert parsed.address_line == "Khreshchatyk 1"


def test_parse_polish_address_with_postal_code_and_street_marker():
    parsed = parse_address("Polska Warszawa ul. Marszałkowska 10 00-001")

    assert parsed is not None
    assert parsed.country == "Polska"
    assert parsed.city == "Warszawa"
    assert parsed.postal_code == "00-001"
    assert parsed.address_line == "ul. Marszałkowska 10"


def test_parse_cyrillic_address_sets_likely_ukraine_without_city():
    parsed = parse_address("Хрещатик 1")

    assert parsed is not None
    assert parsed.country == "Україна"
    assert parsed.address_line == "Хрещатик 1"
    assert parsed.is_complete is False
