"""Unit tests for the ``ContactsService`` in ``assistant_t800.services.contacts``."""

import pytest

from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService


# ---------- add_contact ----------


def test_add_contact_creates_with_name_only(service):
    contact = service.add_contact("Іван")

    assert contact.name.value == "Іван"
    assert contact.phones == []
    assert contact.emails == []
    assert contact.address is None
    assert contact.birthday is None


def test_add_contact_creates_with_single_phone_and_email(service):
    contact = service.add_contact(
        "Іван", phone="0501234567", email="ivan@example.com"
    )

    assert [p.value for p in contact.phones] == ["0501234567"]
    assert [e.value for e in contact.emails] == ["ivan@example.com"]


def test_add_contact_merges_single_value_and_sequence(service):
    contact = service.add_contact(
        "Іван",
        phone="0501234567",
        phones=("0509998877",),
        email="ivan@example.com",
        emails=("other@example.com",),
    )

    phones = [item.value for item in contact.phones]
    emails = [item.value for item in contact.emails]
    assert phones == ["0501234567", "0509998877"]
    assert emails == ["ivan@example.com", "other@example.com"]


def test_add_contact_sets_address_and_birthday(service):
    contact = service.add_contact(
        "Іван",
        address="Київ",
        birthday="01.01.1990",
    )

    assert contact.address is not None
    assert contact.address.value == "Київ"
    assert contact.birthday is not None
    assert contact.birthday.value == "01.01.1990"


def test_add_contact_persists_to_repository(service):
    service.add_contact("Іван")

    assert [c.name.value for c in service.list_contacts()] == ["Іван"]


def test_add_contact_duplicate_name_raises(service):
    service.add_contact("Іван")

    with pytest.raises(ValueError):
        service.add_contact("Іван")


def test_add_contact_invalid_phone_propagates_error(service):
    with pytest.raises(ValueError):
        service.add_contact("Іван", phone="123")


# ---------- get_contact ----------


def test_get_contact_returns_existing_contact(service):
    service.add_contact("Іван")

    contact = service.get_contact("Іван")

    assert contact.name.value == "Іван"


def test_get_contact_is_case_insensitive(service):
    service.add_contact("Іван")

    contact = service.get_contact("іван")

    assert contact.name.value == "Іван"


def test_get_contact_missing_raises_key_error(service):
    with pytest.raises(KeyError):
        service.get_contact("Невідомий")


# ---------- list_contacts ----------


def test_list_contacts_empty_returns_empty_list(service):
    assert service.list_contacts() == []


def test_list_contacts_returns_all_added(service):
    service.add_contact("Іван")
    service.add_contact("Марія")

    names = [c.name.value for c in service.list_contacts()]

    assert names == ["Іван", "Марія"]


# ---------- search_* delegation ----------


def test_search_contacts_delegates_to_repository(service):
    service.add_contact("Іван", phone="0501234567")

    matched = service.search_contacts("0501234567")

    assert [c.name.value for c in matched] == ["Іван"]


def test_search_contacts_by_name_finds_match(service):
    service.add_contact("Іван")

    matched = service.search_contacts_by_name("Іван")

    assert [c.name.value for c in matched] == ["Іван"]


def test_search_contacts_by_phone_finds_match(service):
    service.add_contact("Іван", phone="0501234567")

    matched = service.search_contacts_by_phone("0501234567")

    assert [c.name.value for c in matched] == ["Іван"]


def test_search_contacts_by_email_finds_match(service):
    service.add_contact("Іван", email="ivan@example.com")

    matched = service.search_contacts_by_email("ivan@example.com")

    assert [c.name.value for c in matched] == ["Іван"]


def test_search_contacts_by_note_finds_match(service):
    service.add_contact("Іван")
    service.set_note("Іван", "важливий клієнт")

    matched = service.search_contacts_by_note("клієнт")

    assert [c.name.value for c in matched] == ["Іван"]


def test_search_contacts_by_tag_finds_match(service):
    service.add_contact("Іван")
    service.get_contact("Іван").add_tag("робота")

    matched = service.search_contacts_by_tag("робота")

    assert [c.name.value for c in matched] == ["Іван"]


def test_search_upcoming_birthdays_delegates_with_default_window(service):
    """Default ``days=7`` must be passed to the repository."""
    assert service.search_upcoming_birthdays() == []


# ---------- set_address / set_birthday ----------


def test_set_address_updates_existing_contact(service):
    service.add_contact("Іван")

    contact = service.set_address("Іван", "Київ")

    assert contact.address is not None
    assert contact.address.value == "Київ"


def test_set_address_missing_contact_raises(service):
    with pytest.raises(KeyError):
        service.set_address("Невідомий", "Київ")


def test_set_birthday_updates_existing_contact(service):
    service.add_contact("Іван")

    contact = service.set_birthday("Іван", "01.01.1990")

    assert contact.birthday is not None
    assert contact.birthday.value == "01.01.1990"


def test_set_birthday_missing_contact_raises(service):
    with pytest.raises(KeyError):
        service.set_birthday("Невідомий", "01.01.1990")


# ---------- add_phones / add_emails ----------


def test_add_phones_appends_multiple(service):
    service.add_contact("Іван")

    service.add_phones("Іван", ["0501112233", "0509998877"])

    phones = [item.value for item in service.get_contact("Іван").phones]
    assert phones == ["0501112233", "0509998877"]


def test_add_phones_missing_contact_raises(service):
    with pytest.raises(KeyError):
        service.add_phones("Невідомий", ["0501112233"])


def test_add_emails_appends_multiple(service):
    service.add_contact("Іван")

    service.add_emails("Іван", ["a@example.com", "b@example.com"])

    emails = [item.value for item in service.get_contact("Іван").emails]
    assert emails == ["a@example.com", "b@example.com"]


def test_add_emails_missing_contact_raises(service):
    with pytest.raises(KeyError):
        service.add_emails("Невідомий", ["a@example.com"])


# ---------- note operations ----------


def test_set_note_updates_value(service):
    service.add_contact("Іван")

    contact = service.set_note("Іван", "важливий клієнт")

    assert contact.note == "важливий клієнт"


def test_set_note_missing_contact_raises(service):
    with pytest.raises(KeyError):
        service.set_note("Невідомий", "примітка")


def test_remove_note_clears_value(service):
    service.add_contact("Іван")
    service.set_note("Іван", "важливий клієнт")

    contact = service.remove_note("Іван")

    assert contact.note != "важливий клієнт"


def test_remove_note_missing_contact_raises(service):
    with pytest.raises(KeyError):
        service.remove_note("Невідомий")


# ---------- removal operations ----------


def test_remove_contact_removes_from_repository(service):
    service.add_contact("Іван")

    service.remove_contact("Іван")

    assert service.list_contacts() == []


def test_remove_contact_missing_raises(service):
    with pytest.raises(KeyError):
        service.remove_contact("Невідомий")


def test_remove_address_clears_value(service):
    service.add_contact("Іван", address="Київ")

    contact = service.remove_address("Іван")

    assert contact.address is None


def test_remove_address_missing_contact_raises(service):
    with pytest.raises(KeyError):
        service.remove_address("Невідомий")


def test_remove_birthday_clears_value(service):
    service.add_contact("Іван", birthday="01.01.1990")

    contact = service.remove_birthday("Іван")

    assert contact.birthday is None


def test_remove_birthday_missing_contact_raises(service):
    with pytest.raises(KeyError):
        service.remove_birthday("Невідомий")


def test_remove_phones_drops_listed_values(service):
    service.add_contact("Іван", phone="0501112233")
    service.add_phones("Іван", ["0509998877"])

    service.remove_phones("Іван", ["0501112233"])

    phones = [item.value for item in service.get_contact("Іван").phones]
    assert phones == ["0509998877"]


def test_remove_phones_unknown_value_raises(service):
    service.add_contact("Іван", phone="0501112233")

    with pytest.raises(ValueError):
        service.remove_phones("Іван", ["0509998877"])


def test_remove_all_phones_clears_collection(service):
    service.add_contact("Іван", phone="0501112233")
    service.add_phones("Іван", ["0509998877"])

    service.remove_all_phones("Іван")

    assert service.get_contact("Іван").phones == []


def test_remove_all_phones_missing_contact_raises(service):
    with pytest.raises(KeyError):
        service.remove_all_phones("Невідомий")


def test_remove_emails_drops_listed_values(service):
    service.add_contact("Іван", email="a@example.com")
    service.add_emails("Іван", ["b@example.com"])

    service.remove_emails("Іван", ["a@example.com"])

    emails = [item.value for item in service.get_contact("Іван").emails]
    assert emails == ["b@example.com"]


def test_remove_all_emails_clears_collection(service):
    service.add_contact("Іван", email="a@example.com")
    service.add_emails("Іван", ["b@example.com"])

    service.remove_all_emails("Іван")

    assert service.get_contact("Іван").emails == []


def test_remove_all_emails_missing_contact_raises(service):
    with pytest.raises(KeyError):
        service.remove_all_emails("Невідомий")


# ---------- _merge_values ----------


@pytest.mark.parametrize(
    ("value", "values", "expected"),
    [
        (None, (), ()),
        ("a", (), ("a",)),
        (None, ("a", "b"), ("a", "b")),
        ("a", ("b", "c"), ("a", "b", "c")),
        ("", ("a",), ("a",)),
    ],
)
def test_merge_values_handles_single_and_sequence(value, values, expected):
    assert ContactsService._merge_values(value, values) == expected


# ---------- shared repository fixture sanity ----------


def test_service_uses_provided_repository_instance():
    repo = ContactsRepository()
    service = ContactsService(repo)
    service.add_contact("Іван")

    assert repo.exists("Іван"), "service must persist to the supplied repository"