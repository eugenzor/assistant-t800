"""Optional AI fallback for phone classification."""

from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field

from assistant_t800.domain.phone_validation import (
    PhoneClassification,
    PhoneCountry,
    _to_e164,
    looks_like_phone,
    normalize,
)

try:
    from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
except ImportError:  # pragma: no cover
    ModelHTTPError = RuntimeError
    UnexpectedModelBehavior = RuntimeError


_SYSTEM_PROMPT = (
    "You classify phone numbers. Given a single phone number, determine its "
    "country (ISO 3166-1 alpha-2 code, uppercase) and, if it is a mobile "
    "number, the carrier/operator name. If you cannot determine a field with "
    "reasonable confidence, leave it empty. Never invent operators."
)


class AIPhoneClassification(BaseModel):
    """Structured AI phone classification result."""

    country: str = Field(default="")
    operator: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)


class AIPhoneClassifier:
    """Classify phone numbers via optional Pydantic AI integration."""

    def __init__(
        self, model: Optional[str] = None, min_confidence: float = 70.0
    ) -> None:
        self._model = model if model is not None else self._default_model()
        self._min_confidence = min_confidence

    @property
    def available(self) -> bool:
        return bool(self._model) and self._has_pydantic_ai()

    def classify(self, value: str) -> Optional[PhoneClassification]:
        """Return an AI-derived classification, or ``None`` on any failure."""
        if not self.available or not looks_like_phone(value):
            return None

        try:
            return self._classify(value)
        except (
            ModelHTTPError,
            UnexpectedModelBehavior,
            RuntimeError,
            ValueError,
            TimeoutError,
        ):
            return None

    def _classify(self, value: str) -> Optional[PhoneClassification]:
        from pydantic_ai import Agent

        agent = Agent(
            self._model,
            output_type=AIPhoneClassification,
            system_prompt=_SYSTEM_PROMPT,
        )

        response = agent.run_sync(f"Phone number: {value}")
        ai_result = response.output

        if ai_result.confidence < self._min_confidence:
            return None

        country_code = ai_result.country.strip().upper()
        operator = ai_result.operator.strip() or None

        try:
            country = PhoneCountry(country_code)
        except ValueError:
            country = PhoneCountry.UNKNOWN

        if country is PhoneCountry.UNKNOWN and operator is None:
            return None

        national = normalize(value)

        return PhoneClassification(
            national=national,
            e164=_to_e164(national, country),
            country=country,
            operator=operator,
            is_valid=True,
            looks_like_phone=True,
            source="ai",
        )

    @staticmethod
    def _default_model() -> str:
        if os.getenv("GOOGLE_API_KEY"):
            return os.getenv("GOOGLE_API_MODEL", "google:gemini-3.1-flash-lite")

        if os.getenv("OPENAI_API_KEY"):
            return os.getenv("OPENAI_API_MODEL", "openai-chat:gpt-4o-mini")

        return ""

    @staticmethod
    def _has_pydantic_ai() -> bool:
        try:
            import pydantic_ai  # noqa: F401

            return True
        except ImportError:
            return False
