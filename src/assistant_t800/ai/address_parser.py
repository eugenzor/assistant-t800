"""AI-assisted address parser fallback."""

import json
import os
import re
from functools import lru_cache
from typing import Any, Final

from assistant_t800.config import settings
from assistant_t800.domain.addresses import ParsedAddress

DEFAULT_MODEL: Final[str] = "google:gemini-3.1-flash-lite"

SYSTEM_PROMPT: Final[str] = """\
You are a strict address parser.

Your task is to parse one raw address into structured fields.
Return ONLY valid JSON. Do not include markdown. Do not explain anything.

Rules:
1. You may safely normalize address notation for a course project.
2. You may add obvious street markers, for example:
    "Хрещатик 1" -> "вул. Хрещатик, 1",
    "Warszawska 15" -> "ul. Warszawska 15".
3. Do not invent apartment, floor, entrance, building, district, region, city,
   country, or postal code when confidence is low.
4. If country is missing, you may infer it from a well-known city + street
   combination when confidence is high.
5. If postal code is missing, you may infer it from a full precise address when
   confidence is high.
6. If postal code and country exist and city is missing, you may infer missing
   city when confidence is high.
7. If postal code and city exist and country is missing, you may infer missing
   country when confidence is high.
8. If a field is unknown, return null.
9. Use normalized human-readable country names and address text in address country language.
10. Return fields only from this schema:
   country, region, city, postal_code, address_line.

JSON schema:
{
  "country": string | null,
  "region": string | null,
  "city": string | null,
  "postal_code": string | null,
  "address_line": string | null
}
"""


@lru_cache(maxsize=1)
def _get_agent():
    """Create a narrow AI agent for address parsing only."""
    from pydantic_ai import Agent

    model = os.environ.get("ASSISTANT_T800_MODEL", settings.assistant_t800_model)
    agent = Agent(
        model or DEFAULT_MODEL,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent


def parse_address_with_ai(
    raw_address: str,
    parsed: ParsedAddress | None = None,
) -> ParsedAddress | None:
    """Complete address parts with a narrow AI prompt."""
    result = None

    try:
        response = _get_agent().run_sync(_build_prompt(raw_address, parsed))
        payload = _parse_json(response.output)
        result = _parsed_from_payload(payload) if payload else None
    except Exception:
        result = None

    return result


def _build_prompt(raw_address: str, parsed: ParsedAddress | None) -> str:
    """Build strict user prompt for address parsing."""
    detected = {
        "country": parsed.country if parsed else None,
        "region": parsed.region if parsed else None,
        "city": parsed.city if parsed else None,
        "postal_code": parsed.postal_code if parsed else None,
        "address_line": parsed.address_line if parsed else None,
    }
    result = (
        "Raw address:\n"
        f"{raw_address}\n\n"
        "Already detected by deterministic parser:\n"
        f"{json.dumps(detected, ensure_ascii=False)}\n\n"
        "Complete or correct only fields that can be determined with high "
        "confidence. Return JSON only."
    )
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


def _parsed_from_payload(payload: dict[str, Any]) -> ParsedAddress:
    """Create ParsedAddress from AI JSON payload."""
    result = ParsedAddress(
        country=_optional_str(payload.get("country")),
        region=_optional_str(payload.get("region")),
        city=_optional_str(payload.get("city")),
        postal_code=_optional_str(payload.get("postal_code")),
        address_line=_optional_str(payload.get("address_line")),
    )

    return result


def _optional_str(value: Any) -> str | None:
    """Return clean string or None."""
    result = None

    if isinstance(value, str) and value.strip():
        result = value.strip()

    return result
