"""Structured models for the info validator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional


class EntityKind(Enum):
    """The kind of contact data a token was recognized as."""

    PHONE = auto()
    EMAIL = auto()
    BIRTHDAY = auto()
    ADDRESS = auto()
    UNKNOWN = auto()


class EntitySource(Enum):
    """How an entity classification was produced."""

    REGEX = auto()
    AI = auto()
    NONE = auto()


@dataclass(frozen=True)
class ValidatedEntity:
    """A single recognized (or unrecognized) piece of contact data."""

    kind: EntityKind
    raw: str
    value: Optional[str] = None
    source: EntitySource = EntitySource.REGEX
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def resolved(self) -> bool:
        return self.kind is not EntityKind.UNKNOWN and self.value is not None


@dataclass(frozen=True)
class InfoResult:
    """Structured result of validating a batch of contact data."""

    entities: tuple[ValidatedEntity, ...] = ()

    @property
    def phones(self) -> tuple[ValidatedEntity, ...]:
        return self._by_kind(EntityKind.PHONE)

    @property
    def emails(self) -> tuple[ValidatedEntity, ...]:
        return self._by_kind(EntityKind.EMAIL)

    @property
    def birthdays(self) -> tuple[ValidatedEntity, ...]:
        return self._by_kind(EntityKind.BIRTHDAY)

    @property
    def addresses(self) -> tuple[ValidatedEntity, ...]:
        return self._by_kind(EntityKind.ADDRESS)

    @property
    def unknown(self) -> tuple[ValidatedEntity, ...]:
        return self._by_kind(EntityKind.UNKNOWN)

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict bucketed by entity kind."""
        return {
            "phones": [entity.value for entity in self.phones],
            "emails": [entity.value for entity in self.emails],
            "birthdays": [entity.value for entity in self.birthdays],
            "address": self.addresses[0].value if self.addresses else None,
            "unknown": [entity.raw for entity in self.unknown],
        }

    def _by_kind(self, kind: EntityKind) -> tuple[ValidatedEntity, ...]:
        return tuple(entity for entity in self.entities if entity.kind is kind)
