"""Unit tests for ``BirthdaysListContact`` in ``assistant_t800.domain.birthdays``."""

import dataclasses

import pytest

from assistant_t800.domain.birthdays import BirthdaysListContact


# ---------- construction ----------


def test_birthdays_list_contact_stores_all_fields():
    item = BirthdaysListContact(
        name="Іван",
        birthday="01.01.1990",
        age="35",
        congratulation_date="01.01.2025",
    )

    assert item.name == "Іван"
    assert item.birthday == "01.01.1990"
    assert item.age == "35"
    assert item.congratulation_date == "01.01.2025"


def test_birthdays_list_contact_supports_keyword_arguments():
    item = BirthdaysListContact(
        congratulation_date="02.02.2025",
        age="20",
        birthday="02.02.2005",
        name="Олена",
    )

    assert item.name == "Олена"
    assert item.birthday == "02.02.2005"
    assert item.age == "20"
    assert item.congratulation_date == "02.02.2025"


# ---------- immutability ----------


def test_birthdays_list_contact_is_frozen():
    item = BirthdaysListContact(
        name="Іван",
        birthday="01.01.1990",
        age="35",
        congratulation_date="01.01.2025",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        item.name = "Петро"  # type: ignore[misc]


def test_birthdays_list_contact_age_is_frozen():
    item = BirthdaysListContact(
        name="Іван",
        birthday="01.01.1990",
        age="35",
        congratulation_date="01.01.2025",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        item.age = "36"  # type: ignore[misc]


# ---------- equality ----------


def test_birthdays_list_contacts_with_same_fields_are_equal():
    first = BirthdaysListContact(
        name="Іван",
        birthday="01.01.1990",
        age="35",
        congratulation_date="01.01.2025",
    )
    second = BirthdaysListContact(
        name="Іван",
        birthday="01.01.1990",
        age="35",
        congratulation_date="01.01.2025",
    )

    assert first == second


def test_birthdays_list_contacts_with_different_fields_are_not_equal():
    first = BirthdaysListContact(
        name="Іван",
        birthday="01.01.1990",
        age="35",
        congratulation_date="01.01.2025",
    )
    second = BirthdaysListContact(
        name="Іван",
        birthday="01.01.1990",
        age="35",
        congratulation_date="02.01.2025",
    )

    assert first != second


# ---------- hashability ----------


def test_birthdays_list_contact_is_hashable():
    item = BirthdaysListContact(
        name="Іван",
        birthday="01.01.1990",
        age="35",
        congratulation_date="01.01.2025",
    )

    # Frozen dataclasses are hashable; usable as a set/dict key.
    assert {item} == {item}
