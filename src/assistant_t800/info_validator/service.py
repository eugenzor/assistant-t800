"""Facade that orchestrates entity validation."""

from __future__ import annotations

from typing import Callable, Iterable, Optional, Sequence

from assistant_t800.info_validator.models import (
    EntityKind,
    EntitySource,
    InfoResult,
    ValidatedEntity,
)
from assistant_t800.info_validator.validators import (
    DEFAULT_VALIDATORS,
    AddressValidator,
    EntityValidator,
)

# Returns mapping ``raw_token -> ValidatedEntity`` for tokens it could classify.
AIFallback = Callable[[Sequence[str]], dict[str, ValidatedEntity]]


class InfoValidator:
    """Validate and classify raw contact data into structured entities."""

    def __init__(
        self,
        validators: Sequence[EntityValidator] = DEFAULT_VALIDATORS,
        ai_fallback: Optional[AIFallback] = None,
        address_validator: Optional[AddressValidator] = None,
        *,
        promote_unknown_to_address: bool = True,
    ) -> None:
        self._validators = tuple(validators)
        self._ai_fallback = ai_fallback
        self._address_validator = address_validator or AddressValidator()
        self._promote_unknown_to_address = promote_unknown_to_address

    def validate(self, tokens: str | Iterable[str]) -> InfoResult:
        """Validate one token or a batch and return a structured result."""
        raw_tokens = [tokens] if isinstance(tokens, str) else list(tokens)
        entities = [self._classify_deterministic(token) for token in raw_tokens]

        unresolved = [entity.raw for entity in entities if not entity.resolved]

        if self._ai_fallback is not None and unresolved:
            entities = self._apply_ai_fallback(entities, unresolved)

        if self._promote_unknown_to_address:
            entities = self._promote_first_address(entities)

        return InfoResult(entities=tuple(entities))

    def validate_address(self, fields: dict) -> Optional[ValidatedEntity]:
        """Validate a structured address from named fields."""
        return self._address_validator.validate(fields)

    def _classify_deterministic(self, raw: str) -> ValidatedEntity:
        candidate = raw.strip() if isinstance(raw, str) else ""

        for validator in self._validators:
            entity = validator.validate(candidate)

            if entity is not None:
                return entity

        return ValidatedEntity(
            kind=EntityKind.UNKNOWN,
            raw=candidate,
            value=None,
            source=EntitySource.NONE,
        )

    def _apply_ai_fallback(
        self,
        entities: list[ValidatedEntity],
        unresolved: list[str],
    ) -> list[ValidatedEntity]:
        try:
            resolved = self._ai_fallback(unresolved)  # type: ignore[misc]
        except Exception:  # noqa: BLE001 - AI must never break validation
            return entities

        if not resolved:
            return entities

        return [
            resolved.get(entity.raw, entity) if not entity.resolved else entity
            for entity in entities
        ]

    @staticmethod
    def _promote_first_address(
        entities: list[ValidatedEntity],
    ) -> list[ValidatedEntity]:
        promoted = False
        result: list[ValidatedEntity] = []

        for entity in entities:
            if not promoted and entity.kind is EntityKind.UNKNOWN and entity.raw:
                result.append(
                    ValidatedEntity(
                        kind=EntityKind.ADDRESS,
                        raw=entity.raw,
                        value=entity.raw,
                        source=EntitySource.REGEX,
                    )
                )
                promoted = True
            else:
                result.append(entity)

        return result
