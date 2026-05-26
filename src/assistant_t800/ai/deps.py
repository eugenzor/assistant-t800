"""AI agent dependencies and presenter protocol definitions."""

from dataclasses import dataclass, field
from typing import Protocol

from pydantic_ai.messages import ModelMessage

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
        message_history: Session-scoped chat history replayed on each agent
            call so the model has context from previous turns.
    """

    contacts_service: ContactsService
    presenter: Presenter
    message_history: list[ModelMessage] = field(default_factory=list)
