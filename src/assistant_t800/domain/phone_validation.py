"""Phone number normalization and validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

_NATIONAL_LENGTH = 10
_UA_COUNTRY_CODE = "380"

# National operator codes (``0XY``) matched against ``national[:3]``.
_UA_MOBILE_OPERATORS: dict[str, str] = {
    "067": "Kyivstar",
    "068": "Kyivstar",
    "096": "Kyivstar",
    "097": "Kyivstar",
    "098": "Kyivstar",
    "050": "Vodafone",
    "066": "Vodafone",
    "095": "Vodafone",
    "099": "Vodafone",
    "063": "lifecell",
    "073": "lifecell",
    "093": "lifecell",
    "091": "3Mob",
    "094": "Intertelecom",
}

_LOOKS_LIKE_PATTERN = re.compile(r"^\+?[\d\s\-().]*\d[\d\s\-().]*$")
_SEPARATORS_PATTERN = re.compile(r"[\s\-().]")
# Dates like ``01.01.1990`` pass the permissive phone shape, so exclude them.
_DATE_SHAPE_PATTERN = re.compile(r"^\d{1,2}[./-]\d{1,2}[./-]\d{4}$")


class PhoneCountry(str, Enum):
    """Resolved country for a phone number."""

    UA = "UA"
    UNKNOWN = "UNKNOWN"


_COUNTRY_DIAL_CODES: dict[PhoneCountry, str] = {
    PhoneCountry.UA: _UA_COUNTRY_CODE,
}


def _to_e164(national: Optional[str], country: PhoneCountry) -> Optional[str]:
    """Build ``+<dial><significant>`` from a national number with trunk ``0``."""
    if national is None:
        return None

    dial = _COUNTRY_DIAL_CODES.get(country)

    if dial is None:
        return None

    significant = national[1:] if national.startswith("0") else national

    return f"+{dial}{significant}"


@dataclass(frozen=True)
class PhoneClassification:
    """Result of classifying a phone number."""

    national: Optional[str]
    e164: Optional[str]
    country: PhoneCountry
    operator: Optional[str]
    is_valid: bool
    looks_like_phone: bool
    source: str

    @property
    def resolved(self) -> bool:
        return self.country is not PhoneCountry.UNKNOWN and self.operator is not None


def looks_like_phone(value: str) -> bool:
    """Return whether ``value`` plausibly resembles a phone number."""
    if not isinstance(value, str):
        return False

    candidate = value.strip()

    if not candidate or not _LOOKS_LIKE_PATTERN.fullmatch(candidate):
        return False

    if _DATE_SHAPE_PATTERN.fullmatch(candidate):
        return False

    digits = _strip_separators(candidate)

    return digits.isdigit() and len(digits) >= 7


def normalize(value: str) -> Optional[str]:
    """Normalize ``value`` to a canonical 10-digit Ukrainian national number."""
    if not isinstance(value, str):
        return None

    candidate = value.strip()

    if not candidate:
        return None

    has_plus = candidate.startswith("+")
    digits = _strip_separators(candidate)

    if not digits.isdigit():
        return None

    if digits.startswith(_UA_COUNTRY_CODE) and (
        has_plus or len(digits) == len(_UA_COUNTRY_CODE) + (_NATIONAL_LENGTH - 1)
    ):
        digits = "0" + digits[len(_UA_COUNTRY_CODE) :]
    elif len(digits) == _NATIONAL_LENGTH - 1 and not digits.startswith("0"):
        digits = "0" + digits

    if len(digits) != _NATIONAL_LENGTH or not digits.startswith("0"):
        return None

    return digits


def classify_phone(
    value: str,
    ai_fallback: Optional[Callable[[str], Optional[PhoneClassification]]] = None,
) -> PhoneClassification:
    """Classify a phone number: normalize, match operator, optionally AI."""
    resembles = looks_like_phone(value)
    national = normalize(value)

    if national is not None:
        operator = _UA_MOBILE_OPERATORS.get(national[:3])
        regex_result = PhoneClassification(
            national=national,
            e164=_to_e164(national, PhoneCountry.UA),
            country=PhoneCountry.UA,
            operator=operator,
            is_valid=True,
            looks_like_phone=True,
            source="regex",
        )
    else:
        regex_result = PhoneClassification(
            national=None,
            e164=None,
            country=PhoneCountry.UNKNOWN,
            operator=None,
            is_valid=False,
            looks_like_phone=resembles,
            source="none",
        )

    if (
        ai_fallback is not None
        and regex_result.looks_like_phone
        and (not regex_result.resolved)
    ):
        ai_result = ai_fallback(value)

        if ai_result is not None:
            return ai_result

    return regex_result


def _strip_separators(value: str) -> str:
    without_plus = value[1:] if value.startswith("+") else value

    return _SEPARATORS_PATTERN.sub("", without_plus)
