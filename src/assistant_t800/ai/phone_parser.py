"""Narrow AI phone parser."""

import json
import os
import re
from functools import lru_cache
from typing import Any

from assistant_t800.application.phone_markers import PhoneMarkers
from assistant_t800.config import settings
from assistant_t800.domain.phones import ParsedPhone

DEFAULT_MODEL = "google:gemini-3.1-flash-lite"

SYSTEM_PROMPT = """\
You are a strict phone number parser.

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations.
Do not invent data.

Task:
- Validate a single phone number.
- Return normalized digits only, without plus sign or spaces.
- Identify country if reasonably confident.
- Identify mobile operator or city/area name if reasonably confident.
- Identify whether the number belongs to a mobile operator or a city/landline code.
- If the phone cannot be recognized, return is_valid=false.

Rules:
1. Do not invent operator or city names.
2. Do not invent country.
3. Do not change the subscriber number unless it is required for international normalization.
4. Ukrainian numbers may be normalized to 380XXXXXXXXX.
5. If a local Ukrainian number starts with 0 and has 10 digits, normalize it by adding 38.
6. If a Ukrainian number starts with 80 and has 11 digits, normalize it by adding 3.
7. If unsure, set is_valid=false.

JSON schema:
{
  "normalized": string | null,
  "country": string | null,
  "owner": string | null,
  "is_mobile": boolean | null,
  "is_valid": boolean
}
"""


@lru_cache(maxsize=1)
def _get_agent():
    """Create a narrow AI agent for phone parsing only."""
    from pydantic_ai import Agent

    model = os.environ.get("ASSISTANT_T800_MODEL", settings.assistant_t800_model)
    agent = Agent(
        model or DEFAULT_MODEL,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent


def parse_phone_with_ai(phone: str) -> ParsedPhone | None:
    """Parse phone with AI fallback."""
    result = None

    try:
        digits = PhoneMarkers.clean(phone)
        response = _get_agent().run_sync(
            f"Raw phone:\n{phone}\n\nDigits only:\n{digits}\n\nReturn JSON only."
        )
        payload = _parse_json(response.output)
        result = _parsed_from_payload(payload) if payload else None
    except Exception:
        result = None

    return result


def _parse_json(value: str) -> dict[str, Any] | None:
    """Parse JSON object from AI text."""
    result = None
    text = value.strip()

    try:
        parsed = json.loads(text)
        result = parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)

        if match:
            try:
                parsed = json.loads(match.group(0))
                result = parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                result = None

    return result


def _parsed_from_payload(payload: dict[str, Any]) -> ParsedPhone | None:
    """Create ParsedPhone from AI JSON payload."""
    normalized = _optional_str(payload.get("normalized"))
    is_valid = payload.get("is_valid") is True

    if normalized is None or not is_valid:
        result = None
    else:
        normalized = PhoneMarkers.clean(normalized)
        result = ParsedPhone(
            normalized=normalized,
            country=_optional_str(payload.get("country")),
            owner=_optional_str(payload.get("owner")),
            is_mobile=_optional_bool(payload.get("is_mobile")),
            is_valid=PhoneMarkers.is_valid_digits(normalized),
        )

    return result


def _optional_str(value: Any) -> str | None:
    """Return clean string or None."""
    result = None

    if isinstance(value, str) and value.strip():
        result = value.strip()

    return result


def _optional_bool(value: Any) -> bool | None:
    """Return bool or None."""
    result = value if isinstance(value, bool) else None

    return result
