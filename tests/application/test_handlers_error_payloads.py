"""Tests for mutation error payloads that should keep contact context."""

from assistant_t800.application.context import AppContext
from assistant_t800.application.handlers import add_email, add_phone
from assistant_t800.domain.contacts import Contact
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService


def _context(*raw_args: str) -> AppContext:
    contacts = ContactsService(ContactsRepository())
    result = AppContext(contacts=contacts)
    result.raw_args = raw_args

    return result


def test_add_phone_validation_error_returns_existing_contact_as_payload():
    context = _context("John", "123")
    context.contacts.add_contact("John")

    result = add_phone(context)

    assert not result.success
    assert isinstance(result.data, Contact)
    assert result.data.name.value == "John"


def test_add_email_validation_error_returns_existing_contact_as_payload():
    context = _context("John", "invalid-email")
    context.contacts.add_contact("John")

    result = add_email(context)

    assert not result.success
    assert isinstance(result.data, Contact)
    assert result.data.name.value == "John"


def test_add_phone_missing_contact_error_does_not_attach_payload():
    context = _context("Missing", "123")

    result = add_phone(context)

    assert not result.success
    assert result.data is None
