"""Structured results returned by AI agent tools."""

from dataclasses import dataclass
from typing import Literal

from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact


@dataclass(frozen=True)
class DisplayPayload:
    """Payload for updating the UI display panel after a tool run."""

    kind: Literal["contacts", "birthdays", "text"]
    contacts: list[Contact] | None = None
    birthdays: list[BirthdaysListContact] | None = None
    text: str | None = None
