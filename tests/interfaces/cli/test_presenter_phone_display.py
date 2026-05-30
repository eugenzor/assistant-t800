"""Tests for user-facing phone formatting in presenters."""

from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.interfaces.cli.presenter import CliPresenter


def test_classic_contact_renderer_displays_phone_with_plus_prefix():
    contact = Contact(Name("John"))
    contact.add_phone("380501234567")

    output = CliPresenter()._render_contact(contact)

    assert "+380501234567" in output
    assert " 380501234567" not in output


def test_contact_string_displays_phone_with_plus_prefix():
    contact = Contact(Name("John"))
    contact.add_phone("380501234567")

    output = str(contact)

    assert "+380501234567" in output
    assert "телефони: 380501234567" not in output
