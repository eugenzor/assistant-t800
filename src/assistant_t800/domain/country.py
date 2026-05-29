"""Country resolution for addresses."""

from __future__ import annotations

import re
from typing import Callable, Optional

# Aliases (lowercased) -> ISO 3166-1 alpha-2 canonical code.
_COUNTRY_ALIASES: dict[str, str] = {
    "ua": "UA",
    "ukr": "UA",
    "ukraine": "UA",
    "україна": "UA",
    "украина": "UA",
    "pl": "PL",
    "pol": "PL",
    "poland": "PL",
    "польща": "PL",
    "польша": "PL",
    "de": "DE",
    "ger": "DE",
    "germany": "DE",
    "deutschland": "DE",
    "німеччина": "DE",
    "sk": "SK",
    "slovakia": "SK",
    "словаччина": "SK",
    "hu": "HU",
    "hungary": "HU",
    "угорщина": "HU",
    "ro": "RO",
    "romania": "RO",
    "румунія": "RO",
    "md": "MD",
    "moldova": "MD",
    "молдова": "MD",
    "us": "US",
    "usa": "US",
    "united states": "US",
    "сша": "US",
    "uk": "GB",
    "gb": "GB",
    "united kingdom": "GB",
    "британія": "GB",
}

_ALPHA2_PATTERN = re.compile(r"^[A-Za-z]{2}$")

CountryAIResolver = Callable[[str], Optional[str]]


def resolve_country(
    value: str,
    ai_fallback: Optional[CountryAIResolver] = None,
) -> Optional[str]:
    """Resolve a free-form country string to an ISO alpha-2 code."""
    if not isinstance(value, str):
        return None

    candidate = value.strip()

    if not candidate:
        return None

    table_hit = _COUNTRY_ALIASES.get(candidate.casefold())

    if table_hit is not None:
        return table_hit

    if _ALPHA2_PATTERN.fullmatch(candidate):
        return candidate.upper()

    if ai_fallback is not None:
        resolved = ai_fallback(candidate)

        if isinstance(resolved, str) and _ALPHA2_PATTERN.fullmatch(resolved.strip()):
            return resolved.strip().upper()

    return None


def is_known_country(value: str) -> bool:
    """Return whether ``value`` resolves via the hardcoded table alone."""
    return isinstance(value, str) and value.strip().casefold() in _COUNTRY_ALIASES
