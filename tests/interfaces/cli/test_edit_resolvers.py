"""Unit tests for interactive edit resolvers."""

from dataclasses import dataclass

from assistant_t800.application.context import AppContext
from assistant_t800.interfaces.cli.commands import build_registry
from assistant_t800.interfaces.cli.edit_resolvers import NoteEditResolver
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService


@dataclass
class FakePresenter:
    """Capture note edit requests."""

    contact_name: str | None = None
    current_note: str | None = None

    def request_note_edit(self, *, contact, current_note, text_input_func):
        self.contact_name = contact.name.value
        self.current_note = current_note

        return text_input_func(">", current_note)


def test_note_edit_resolver_requests_inline_edit_for_contact_card():
    service = ContactsService(ContactsRepository())
    service.add_contact("Аліса")
    service.set_note("Аліса", "поточна нотатка")
    context = AppContext(contacts=service)
    context.registry = build_registry()
    presenter = FakePresenter()

    resolver = NoteEditResolver(
        context=context,
        presenter=presenter,
        text_input_func=lambda prompt, default: "нова нотатка",
    )

    result = resolver.resolve("edit-note Аліса")

    assert result == 'edit-note "Аліса" "нова нотатка"'
    assert presenter.contact_name == "Аліса"
    assert presenter.current_note == "поточна нотатка"
