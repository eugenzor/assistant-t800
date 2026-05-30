"""Tests for Rich contact table phone display formatting."""


from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.interfaces.cli.rich.contacts import _render_first_value


def test_rich_first_value_displays_phone_with_plus_prefix():
    contact = Contact(Name("John"))
    contact.add_phone("380501234567")

    assert _render_first_value(contact.phones) == "+380501234567"
