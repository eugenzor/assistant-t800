"""Application command execution context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from assistant_t800.services.contacts import ContactsService

if TYPE_CHECKING:
    from assistant_t800.application.commands import Command


@dataclass
class AppContext:
    """Runtime data required by application command handlers."""

    contacts: ContactsService
    args: dict[str, str] = field(default_factory=dict)
    raw_args: tuple[str, ...] = ()
    registry: dict[str, Command] = field(default_factory=dict)
    confirmed: bool = False
