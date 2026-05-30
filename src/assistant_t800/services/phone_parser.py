"""Deterministic phone parsing."""

from assistant_t800.application.phone_markers import PhoneMarkers
from assistant_t800.domain.phones import ParsedPhone


def parse_phone(phone: str) -> ParsedPhone | None:
    """Parse phone by deterministic rules and known Ukrainian markers."""
    digits = PhoneMarkers.clean(phone)
    normalized = PhoneMarkers.normalize_ukrainian_shape(digits)
    parsed = PhoneMarkers.resolve_ukrainian(normalized)

    if parsed is not None:
        result = parsed
    elif _is_explicit_international(phone, normalized):
        result = ParsedPhone(
            normalized=normalized,
            is_valid=True,
        )
    else:
        result = None

    return result


def _is_explicit_international(raw_phone: str, digits: str) -> bool:
    """Return whether value is a plausible international phone."""
    result = (
        digits.isdigit()
        and PhoneMarkers.MIN_DIGITS < len(digits) <= PhoneMarkers.MAX_DIGITS
    )

    return result
