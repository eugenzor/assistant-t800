"""Unit tests for note-related methods on ``ContactsService``."""

import pytest

from assistant_t800.application.enums import SystemValue


def test_set_note_assigns_text_to_contact(service):
    service.add_contact("Іван")

    contact = service.set_note("Іван", "важливий клієнт")

    assert contact.note == "важливий клієнт"
    assert service.get_contact("Іван").note == "важливий клієнт"


def test_set_note_replaces_existing_note(service):
    service.add_contact("Іван")
    service.set_note("Іван", "first")

    service.set_note("Іван", "second")

    assert service.get_contact("Іван").note == "second"


def test_set_note_strips_surrounding_whitespace(service):
    service.add_contact("Іван")

    service.set_note("Іван", "  важливий клієнт  ")

    assert service.get_contact("Іван").note == "важливий клієнт"


def test_set_note_whitespace_only_resets_to_internal_empty(service):
    service.add_contact("Іван")

    service.set_note("Іван", "   ")

    assert service.get_contact("Іван").note == SystemValue.EMPTY_TEXT.value


def test_set_note_unknown_contact_raises_key_error(service):
    with pytest.raises(KeyError):
        service.set_note("Невідомий", "note")


def test_remove_note_resets_to_internal_empty_value(service):
    service.add_contact("Іван")
    service.set_note("Іван", "важливий клієнт")

    contact = service.remove_note("Іван")

    assert contact.note == SystemValue.EMPTY_TEXT.value
    assert service.get_contact("Іван").note == SystemValue.EMPTY_TEXT.value


def test_remove_note_is_idempotent_when_note_not_set(service):
    service.add_contact("Іван")

    service.remove_note("Іван")

    assert service.get_contact("Іван").note == SystemValue.EMPTY_TEXT.value


def test_remove_note_unknown_contact_raises_key_error(service):
    with pytest.raises(KeyError):
        service.remove_note("Невідомий")


def test_search_contacts_by_note_finds_set_note(service):
    service.add_contact("Іван")
    service.set_note("Іван", "важливий клієнт")

    matches = service.search_contacts_by_note("клієнт")

    assert [c.name.value for c in matches] == ["Іван"]


def test_search_contacts_by_note_ignores_removed_note(service):
    service.add_contact("Іван")
    service.set_note("Іван", "важливий клієнт")
    service.remove_note("Іван")

    assert service.search_contacts_by_note("клієнт") == []
