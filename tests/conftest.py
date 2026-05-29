"""Shared fixtures for the assistant_t800 test suite."""

from dataclasses import dataclass, field
from typing import Any

import pytest

from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService


@dataclass
class FakePresenter:
    """Capture presenter calls for inspection in tests."""

    refresh_calls: list[list[Contact]] = field(default_factory=list)
    refresh_contact_calls: list[Contact] = field(default_factory=list)
    refresh_birthdays_calls: list[list[BirthdaysListContact]] = field(
        default_factory=list
    )
    print_calls: list[str] = field(default_factory=list)

    def refresh_contacts(self, contacts: list[Contact]) -> None:
        self.refresh_calls.append(list(contacts))

    def refresh_contact(self, contact: Contact) -> None:
        self.refresh_contact_calls.append(contact)

    def refresh_birthdays(self, birthdays: list[BirthdaysListContact]) -> None:
        self.refresh_birthdays_calls.append(list(birthdays))

    def print(self, text: str) -> None:
        self.print_calls.append(text)


@dataclass
class FakeRunContext:
    """Minimal stand-in for ``pydantic_ai.RunContext`` — tools only use ``.deps``."""

    deps: Any


@pytest.fixture
def service() -> ContactsService:
    return ContactsService(ContactsRepository())


@pytest.fixture
def presenter() -> FakePresenter:
    return FakePresenter()


@pytest.fixture
def deps(service: ContactsService, presenter: FakePresenter):
    """Return AI dependencies, skipping AI tests when pydantic_ai is unavailable."""
    pytest.importorskip("pydantic_ai")
    from assistant_t800.ai.deps import AgentDeps

    return AgentDeps(contacts_service=service, presenter=presenter)


@pytest.fixture
def ctx(deps) -> FakeRunContext:
    return FakeRunContext(deps=deps)
