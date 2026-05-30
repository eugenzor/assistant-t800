"""Deterministic best-effort address parser."""

import re
from typing import Final

from assistant_t800.application.address_markers import (
    AddressMarkers,
    CountryAddressFormat,
)
from assistant_t800.domain.addresses import ParsedAddress

CYRILLIC_PATTERN: Final[re.Pattern[str]] = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")


def parse_address(address: str) -> ParsedAddress | None:
    """Parse raw address text into structured parts using deterministic rules."""
    raw = address.strip()
    result = None

    if raw:
        parser = _AddressParser(raw)
        parsed = parser.parse()
        result = parsed if parsed.has_data else None

    return result


class _AddressParser:
    """Internal extract-and-remove parser implementation."""

    def __init__(self, raw: str) -> None:
        self._raw = raw
        self._remaining = raw
        self._country_format: CountryAddressFormat | None = None
        self._country: str | None = None
        self._region: str | None = None
        self._city: str | None = None
        self._postal_code: str | None = None
        self._address_line: str | None = None

    def parse(self) -> ParsedAddress:
        """Run deterministic parsing."""
        self._extract_country()
        self._extract_postal_code()
        self._extract_marked_part(AddressMarkers.REGION, "_region")
        self._extract_marked_city()
        self._extract_city_hint()
        self._extract_street_line()
        self._fill_address_line_from_remaining()
        self._apply_cyrillic_country_fallback()
        self._format_region_city()

        result = ParsedAddress(
            country=self._country,
            region=self._region,
            city=self._city,
            postal_code=self._postal_code,
            address_line=self._address_line,
        )
        return result

    def _extract_country(self) -> None:
        """Extract explicit country alias from chunks or free text."""
        for country, aliases in AddressMarkers.COUNTRY_ALIASES.items():
            for alias in sorted(aliases, key=len, reverse=True):
                if self._remove_token(alias):
                    self._country_format = country
                    self._country = country.country
                    return

    def _extract_postal_code(self) -> None:
        """Extract the first postal code candidate."""
        for pattern in AddressMarkers.POSTAL_CODE_PATTERNS:
            match = pattern.search(self._remaining)

            if match:
                self._postal_code = match.group(0).strip()
                self._remaining = self._remove_span(
                    self._remaining,
                    match.start(),
                    match.end(),
                )
                break

    def _extract_marked_part(self, markers: frozenset[str], attribute: str) -> None:
        """Extract a short value that follows a known marker."""
        if getattr(self, attribute) is not None:
            return

        match = self._marker_pattern(markers).search(self._remaining)

        if match:
            value = self._first_value_token(match.group("tail"))
            if value:
                setattr(self, attribute, value)
                self._remaining = self._remove_span(
                    self._remaining,
                    match.start(),
                    match.start("tail") + len(value),
                )

    def _extract_marked_city(self) -> None:
        """Extract city value after a city marker."""
        if self._city is not None:
            return

        match = self._marker_pattern(AddressMarkers.CITY).search(self._remaining)

        if match:
            tail = match.group("tail")
            value = self._known_city_prefix(tail) or self._first_value_token(tail)

            if value:
                self._city = value
                self._remaining = self._remove_span(
                    self._remaining,
                    match.start(),
                    match.start("tail") + len(value),
                )

    def _extract_city_hint(self) -> None:
        """Extract city/country from known city hints."""
        if self._city is not None:
            return

        normalized_remaining = self._normalize_search(self._remaining)

        for city, country in AddressMarkers.CITY_COUNTRY_HINTS.items():
            if self._contains_token(normalized_remaining, city):
                self._city = city.title()
                self._remove_token(city)

                if self._country is None:
                    self._country_format = country
                    self._country = country.country

                break

    def _extract_street_line(self) -> None:
        """Extract street-like address line."""
        if self._address_line is not None:
            return

        match = self._marker_pattern(AddressMarkers.STREET).search(self._remaining)

        if match:
            value = match.group(0).strip(" ,;")
            self._address_line = value
            self._remaining = self._remove_span(
                self._remaining,
                match.start(),
                match.end(),
            )

    def _fill_address_line_from_remaining(self) -> None:
        """Use the leftover text as address line when possible."""
        remaining = self._compact(self._remaining)

        if self._address_line is None and remaining:
            self._address_line = remaining
            self._remaining = ""

    def _apply_cyrillic_country_fallback(self) -> None:
        """Use Ukraine as likely country for Cyrillic addresses."""
        if self._country is None and CYRILLIC_PATTERN.search(self._raw):
            self._country_format = CountryAddressFormat.UA
            self._country = CountryAddressFormat.UA.country

    def _format_region_city(self) -> None:
        """Apply country-specific region and city display format."""
        if self._country_format is not None:
            if self._region:
                self._region = self._country_format.region(self._region)
            if self._city:
                self._city = self._country_format.city(self._city)

    @staticmethod
    def _marker_pattern(markers: frozenset[str]) -> re.Pattern[str]:
        """Build a marker followed by tail regex."""
        marker_pattern = "|".join(
            re.escape(marker) for marker in sorted(markers, key=len, reverse=True)
        )
        result = re.compile(
            rf"(?<!\w)(?P<marker>{marker_pattern})\.?"
            rf"\s+(?P<tail>[^,;]+)",
            re.IGNORECASE,
        )

        return result

    @staticmethod
    def _first_value_token(value: str) -> str | None:
        """Return the first meaningful token after a marker."""
        match = re.search(r"[\wА-Яа-яІіЇїЄєҐґ'’\-]+", value)
        result = match.group(0) if match else None

        return result

    @staticmethod
    def _known_city_prefix(value: str) -> str | None:
        """Return known city hint that starts the given value."""
        normalized = _AddressParser._normalize_search(value)
        result = None

        for city in sorted(AddressMarkers.CITY_COUNTRY_HINTS, key=len, reverse=True):
            if normalized.startswith(city.casefold()):
                result = value[: len(city)].strip()
                break

        return result

    def _remove_token(self, value: str) -> bool:
        """Remove one token-like value from remaining text."""
        pattern = re.compile(
            rf"(?<!\w){re.escape(value)}(?!\w)",
            re.IGNORECASE,
        )
        match = pattern.search(self._remaining)
        result = match is not None

        if match:
            self._remaining = self._remove_span(
                self._remaining,
                match.start(),
                match.end(),
            )

        return result

    @staticmethod
    def _remove_span(value: str, start: int, end: int) -> str:
        """Remove a substring by span and compact separators."""
        result = _AddressParser._compact(f"{value[:start]} {value[end:]}")

        return result

    @staticmethod
    def _compact(value: str) -> str:
        """Compact spaces and separators."""
        result = re.sub(r"\s+", " ", value)
        result = re.sub(r"\s*[,;]\s*", ", ", result)
        result = result.strip(" ,;")

        return result

    @staticmethod
    def _normalize_search(value: str) -> str:
        """Normalize text for contains checks."""
        result = value.casefold().replace(".", " ")
        result = re.sub(r"\s+", " ", result).strip()

        return result

    @staticmethod
    def _contains_token(value: str, token: str) -> bool:
        """Return whether normalized text contains token as words."""
        pattern = re.compile(rf"(?<!\w){re.escape(token.casefold())}(?!\w)")
        result = bool(pattern.search(value))

        return result
