"""Application-level value normalizers."""

from assistant_t800.ai.address_parser import parse_address_with_ai
from assistant_t800.ai.phone_parser import parse_phone_with_ai
from assistant_t800.domain.addresses import ParsedAddress
from assistant_t800.services.phone_parser import parse_phone
from assistant_t800.services.address_parser import parse_address
from assistant_t800.localization import ErrorCode


def normalize_address(address: str) -> ParsedAddress | None:
    """Normalize address with deterministic parser and optional AI fallback."""
    parsed = parse_address(address)

    if parsed is None or not parsed.is_complete:
        ai_parsed = parse_address_with_ai(address, parsed)
        parsed = _merge_addresses(parsed, ai_parsed)

    result = parsed if parsed is not None and parsed.has_data else None

    return result


def _merge_addresses(
    base: ParsedAddress | None,
    override: ParsedAddress | None,
) -> ParsedAddress | None:
    """Merge parsed addresses, preferring AI-provided values when present."""
    if base is None:
        result = override
    elif override is None:
        result = base
    else:
        result = ParsedAddress(
            country=override.country or base.country,
            region=override.region or base.region,
            city=override.city or base.city,
            postal_code=override.postal_code or base.postal_code,
            address_line=override.address_line or base.address_line,
        )

    return result


def normalize_phone(phone: str) -> str:
    """Normalize phone with deterministic rules and optional AI fallback."""
    from assistant_t800.application.phone_markers import PhoneMarkers

    digits = PhoneMarkers.clean(phone)

    if len(digits) < PhoneMarkers.MIN_DIGITS or len(digits) > PhoneMarkers.MAX_DIGITS:
        raise ValueError(str(ErrorCode.INVALID_PHONE_DIGITS_RANGE))

    parsed = parse_phone(phone)

    if parsed is None:
        parsed = parse_phone_with_ai(phone)

    if parsed is None or not parsed.is_valid:
        raise ValueError(str(ErrorCode.PHONE_NOT_RECOGNIZED))

    result = parsed.normalized

    return result
