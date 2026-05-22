"""AI agent dependencies and presenter protocol definitions."""

from dataclasses import dataclass
from typing import Protocol

from assistant_t800.domain.contacts import Contact
from assistant_t800.services.contacts import ContactsService


class Presenter(Protocol):
    """UI presenter protocol for displaying data to the user."""

    def refresh_contacts(self, contacts: list[Contact]) -> None:
        """Refresh the contact list display."""
        ...

    def print(self, text: str) -> None:
        """Display arbitrary text in the output panel."""
        ...


@dataclass
class AgentDeps:
    """Runtime dependencies passed to the AI agent.

    Attributes:
        contacts_service: Service for contact management operations.
        presenter: UI presenter implementation.
    """

    contacts_service: ContactsService
    presenter: Presenter
