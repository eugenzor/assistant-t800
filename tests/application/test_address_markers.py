"""Tests for address marker datasets."""

from assistant_t800.application.address_markers import (
    AddressMarkers,
    CountryAddressFormat,
)


def test_resolve_country_uses_grouped_aliases():
    assert AddressMarkers.resolve_country("ukraine") is CountryAddressFormat.UA
    assert AddressMarkers.resolve_country("Polska") is CountryAddressFormat.PL
    assert AddressMarkers.resolve_country("Deutschland") is CountryAddressFormat.DE


def test_country_format_formats_ukrainian_region_and_city():
    country = CountryAddressFormat.UA

    assert country.country == "Україна"
    assert country.region("Київська") == "Київська обл."
    assert country.city("Київ") == "м. Київ"
