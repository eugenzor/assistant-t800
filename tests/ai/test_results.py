"""Unit tests for the ``DisplayPayload`` dataclass in ``assistant_t800.ai.results``."""

from assistant_t800.ai.results import DisplayPayload
from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name


# ---------- construction ----------


def test_display_payload_contacts_kind_holds_contact_list():
    contact = Contact(Name("Іван"))

    payload = DisplayPayload(kind="contacts", contacts=[contact])

    assert payload.kind == "contacts"
    assert payload.contacts == [contact]
    assert payload.birthdays is None
    assert payload.text is None


def test_display_payload_birthdays_kind_holds_birthday_records():
    record = BirthdaysListContact(
        name="Іван",
        birthday="01.01.1990",
        age="36",
        congratulation_date="01.01.2026",
    )

    payload = DisplayPayload(kind="birthdays", birthdays=[record])

    assert payload.kind == "birthdays"
    assert payload.birthdays == [record]
    assert payload.contacts is None
    assert payload.text is None


def test_display_payload_text_kind_holds_text_value():
    payload = DisplayPayload(kind="text", text="hello")

    assert payload.kind == "text"
    assert payload.text == "hello"
    assert payload.contacts is None
    assert payload.birthdays is None


def test_display_payload_is_frozen():
    """The dataclass must be immutable so tool returns are safe to share."""
    payload = DisplayPayload(kind="text", text="hello")

    import dataclasses

    try:
        payload.text = "changed"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return

    raise AssertionError("DisplayPayload must be frozen")