"""Unit tests for ``AgentDeps`` in ``assistant_t800.ai.deps``."""

from assistant_t800.ai.deps import AgentDeps, Presenter
from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService


# ---------- helpers ----------


class _PresenterStub:
    """Minimal Presenter implementation for type-shape verification."""

    def refresh_contacts(self, contacts):
        pass

    def refresh_birthdays(self, birthdays):
        pass

    def print(self, text):
        pass


def _service() -> ContactsService:
    return ContactsService(ContactsRepository())


# ---------- AgentDeps defaults ----------


def test_agent_deps_default_message_history_is_empty_list():
    deps = AgentDeps(
        contacts_service=_service(),
        presenter=_PresenterStub(),
    )

    assert deps.message_history == []


def test_agent_deps_default_message_history_is_mutable_list():
    deps = AgentDeps(
        contacts_service=_service(),
        presenter=_PresenterStub(),
    )

    deps.message_history.append("entry")  # type: ignore[arg-type]

    assert len(deps.message_history) == 1


def test_agent_deps_default_message_history_is_isolated_between_instances():
    first = AgentDeps(
        contacts_service=_service(),
        presenter=_PresenterStub(),
    )
    second = AgentDeps(
        contacts_service=_service(),
        presenter=_PresenterStub(),
    )

    first.message_history.append("entry")  # type: ignore[arg-type]

    assert second.message_history == []


# ---------- AgentDeps stores supplied values ----------


def test_agent_deps_stores_contacts_service():
    service = _service()
    deps = AgentDeps(
        contacts_service=service,
        presenter=_PresenterStub(),
    )

    assert deps.contacts_service is service


def test_agent_deps_stores_presenter():
    presenter = _PresenterStub()
    deps = AgentDeps(
        contacts_service=_service(),
        presenter=presenter,
    )

    assert deps.presenter is presenter


def test_agent_deps_accepts_existing_message_history():
    history: list = ["a", "b"]
    deps = AgentDeps(
        contacts_service=_service(),
        presenter=_PresenterStub(),
        message_history=history,
    )

    assert deps.message_history is history


# ---------- Presenter protocol structural compatibility ----------


def test_presenter_stub_is_protocol_compatible():
    """A class implementing the three required methods satisfies the Presenter protocol."""
    stub = _PresenterStub()

    # Protocol membership is structural — runtime checks just look at attributes.
    assert hasattr(stub, "refresh_contacts")
    assert hasattr(stub, "refresh_birthdays")
    assert hasattr(stub, "print")


def test_agent_deps_presenter_supports_refresh_contacts():
    """Sanity check: a stored presenter actually answers the protocol methods."""
    deps = AgentDeps(
        contacts_service=_service(),
        presenter=_PresenterStub(),
    )

    # Should not raise.
    deps.presenter.refresh_contacts([Contact(Name("Іван"))])


def test_agent_deps_presenter_supports_refresh_birthdays():
    deps = AgentDeps(
        contacts_service=_service(),
        presenter=_PresenterStub(),
    )

    deps.presenter.refresh_birthdays(
        [
            BirthdaysListContact(
                name="Іван",
                birthday="01.01.1990",
                age="35",
                congratulation_date="01.01.2025",
            )
        ]
    )


def test_agent_deps_presenter_supports_print():
    deps = AgentDeps(
        contacts_service=_service(),
        presenter=_PresenterStub(),
    )

    deps.presenter.print("hello")
