"""Unit tests for ``ContactsService`` in ``assistant_t800.services.contacts``."""

import pytest

from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import AddressInput
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService


@pytest.fixture
def service() -> ContactsService:
    return ContactsService(ContactsRepository())


# ---------- add_contact ----------


def test_add_contact_creates_contact_with_only_name(service):
    contact = service.add_contact("Іван")

    assert isinstance(contact, Contact)
    assert contact.name.value == "Іван"
    assert contact.phones == []
    assert contact.emails == []
    assert contact.address is None
    assert contact.birthday is None


def test_add_contact_stores_contact_in_repository(service):
    service.add_contact("Іван")

    assert service.get_contact("Іван").name.value == "Іван"


def test_add_contact_with_single_phone(service):
    contact = service.add_contact("Іван", phone="0501234567")

    assert [item.value for item in contact.phones] == ["+380501234567"]


def test_add_contact_with_phones_sequence(service):
    contact = service.add_contact("Іван", phones=("0501234567", "0509998877"))

    assert [item.value for item in contact.phones] == ["+380501234567", "+380509998877"]


def test_add_contact_combines_phone_and_phones_with_single_first(service):
    contact = service.add_contact(
        "Іван",
        phone="0501234567",
        phones=("0509998877",),
    )

    assert [item.value for item in contact.phones] == ["+380501234567", "+380509998877"]


def test_add_contact_with_single_email(service):
    contact = service.add_contact("Іван", email="ivan@example.com")

    assert [item.value for item in contact.emails] == ["ivan@example.com"]


def test_add_contact_combines_email_and_emails(service):
    contact = service.add_contact(
        "Іван",
        email="primary@example.com",
        emails=("work@example.com",),
    )

    assert [item.value for item in contact.emails] == [
        "primary@example.com",
        "work@example.com",
    ]


def test_add_contact_with_address(service):
    contact = service.add_contact(
        "Іван",
        address=AddressInput(country="UA", city="Kyiv", line="вул. Хрещатик 1"),
    )

    assert contact.address is not None
    assert contact.address.value == "UA, Kyiv, вул. Хрещатик 1"


def test_add_contact_with_birthday(service):
    contact = service.add_contact("Іван", birthday="01.01.1990")

    assert contact.birthday is not None
    assert str(contact.birthday) == "01.01.1990"


def test_add_contact_with_empty_address_does_not_set_address(service):
    contact = service.add_contact("Іван", address=None)

    assert contact.address is None


def test_add_contact_with_empty_birthday_does_not_set_birthday(service):
    contact = service.add_contact("Іван", birthday="")

    assert contact.birthday is None


def test_add_contact_raises_on_duplicate(service):
    service.add_contact("Іван")

    with pytest.raises(ValueError):
        service.add_contact("Іван")


def test_add_contact_propagates_validation_error_for_phone(service):
    with pytest.raises(ValueError):
        service.add_contact("Іван", phone="not-a-phone")


def test_add_contact_propagates_validation_error_for_email(service):
    with pytest.raises(ValueError):
        service.add_contact("Іван", email="not-an-email")


# ---------- get_contact ----------


def test_get_contact_returns_existing_contact(service):
    service.add_contact("Іван")

    contact = service.get_contact("Іван")

    assert contact.name.value == "Іван"


def test_get_contact_raises_key_error_for_unknown(service):
    with pytest.raises(KeyError):
        service.get_contact("Невідомий")


def test_get_contact_is_case_insensitive(service):
    service.add_contact("Іван")

    contact = service.get_contact("ІВАН")

    assert contact.name.value == "Іван"


# ---------- list_contacts ----------


def test_list_contacts_empty(service):
    assert service.list_contacts() == []


def test_list_contacts_returns_added_contacts(service):
    service.add_contact("Іван")
    service.add_contact("Олена")

    result = service.list_contacts()

    assert {item.name.value for item in result} == {"Іван", "Олена"}


# ---------- search_contacts ----------


def test_search_contacts_returns_empty_for_no_match(service):
    service.add_contact("Іван")

    assert service.search_contacts("xyz") == []


def test_search_contacts_matches_by_name(service):
    service.add_contact("Іванко")
    service.add_contact("Олена")

    result = service.search_contacts("іва")

    assert [item.name.value for item in result] == ["Іванко"]


def test_search_contacts_by_name_only_matches_name(service):
    service.add_contact("Олена", phone="0501234567")

    assert service.search_contacts_by_name("12345") == []


def test_search_contacts_by_phone(service):
    service.add_contact("Іван", phone="0501234567")
    service.add_contact("Олена", phone="0509998877")

    result = service.search_contacts_by_phone("9998")

    assert [item.name.value for item in result] == ["Олена"]


def test_search_contacts_by_email(service):
    service.add_contact("Іван", email="ivan@example.com")

    result = service.search_contacts_by_email("EXAMPLE")

    assert [item.name.value for item in result] == ["Іван"]


def test_search_contacts_by_note(service):
    service.add_contact("Іван")
    service.set_note("Іван", "Loves coffee")

    result = service.search_contacts_by_note("coffee")

    assert [item.name.value for item in result] == ["Іван"]


def test_search_contacts_by_tag(service):
    contact = service.add_contact("Іван")
    contact.add_tag("Family")

    result = service.search_contacts_by_tag("famil")

    assert [item.name.value for item in result] == ["Іван"]


def test_search_upcoming_birthdays_delegates_to_repository(service):
    # Empty contacts: should return empty list regardless of window.
    assert service.search_upcoming_birthdays(7) == []
    assert service.search_upcoming_birthdays(365) == []


# ---------- set_address ----------


def test_set_address_assigns_address(service):
    service.add_contact("Іван")

    contact = service.set_address(
        "Іван", AddressInput(country="UA", city="Kyiv", line="вул. X")
    )

    assert contact.address is not None
    assert contact.address.value == "UA, Kyiv, вул. X"


def test_set_address_overrides_existing_address(service):
    service.add_contact(
        "Іван",
        address=AddressInput(country="UA", city="Kyiv", line="вул. X"),
    )

    contact = service.set_address(
        "Іван", AddressInput(country="UA", city="Lviv", line="пл. Y")
    )

    assert contact.address.value == "UA, Lviv, пл. Y"


def test_set_address_raises_when_contact_missing(service):
    with pytest.raises(KeyError):
        service.set_address(
            "Невідомий",
            AddressInput(country="UA", city="Kyiv", line="вул. X"),
        )


# ---------- set_birthday ----------


def test_set_birthday_assigns_birthday(service):
    service.add_contact("Іван")

    contact = service.set_birthday("Іван", "01.01.1990")

    assert str(contact.birthday) == "01.01.1990"


def test_set_birthday_raises_on_invalid_format(service):
    service.add_contact("Іван")

    with pytest.raises(ValueError):
        service.set_birthday("Іван", "not-a-date")


# ---------- add_phones / add_emails ----------


def test_add_phones_appends_to_existing(service):
    service.add_contact("Іван", phone="0501234567")

    contact = service.add_phones("Іван", ("0509998877",))

    assert [item.value for item in contact.phones] == [
        "+380501234567",
        "+380509998877",
    ]


def test_add_phones_with_empty_sequence_keeps_existing_phones(service):
    service.add_contact("Іван", phone="0501234567")

    contact = service.add_phones("Іван", ())

    assert [item.value for item in contact.phones] == ["+380501234567"]


def test_add_phones_raises_on_duplicate(service):
    service.add_contact("Іван", phone="0501234567")

    with pytest.raises(ValueError):
        service.add_phones("Іван", ("0501234567",))


def test_add_emails_appends_to_existing(service):
    service.add_contact("Іван", email="a@example.com")

    contact = service.add_emails("Іван", ("b@example.com",))

    assert [item.value for item in contact.emails] == [
        "a@example.com",
        "b@example.com",
    ]


# ---------- set_note / remove_note ----------


def test_set_note_assigns_note(service):
    service.add_contact("Іван")

    contact = service.set_note("Іван", "Best friend")

    assert contact.note == "Best friend"


def test_remove_note_clears_note(service):
    service.add_contact("Іван")
    service.set_note("Іван", "Best friend")

    contact = service.remove_note("Іван")

    # Note is reset to the EMPTY_TEXT sentinel, not the original string.
    assert contact.note != "Best friend"


# ---------- remove_contact ----------


def test_remove_contact_removes_from_repository(service):
    service.add_contact("Іван")

    service.remove_contact("Іван")

    with pytest.raises(KeyError):
        service.get_contact("Іван")


def test_remove_contact_returns_removed_contact(service):
    contact = service.add_contact("Іван")

    removed = service.remove_contact("Іван")

    assert removed is contact


def test_remove_contact_raises_for_missing(service):
    with pytest.raises(KeyError):
        service.remove_contact("Невідомий")


# ---------- remove_address / remove_birthday ----------


def test_remove_address_clears_address(service):
    service.add_contact(
        "Іван",
        address=AddressInput(country="UA", city="Kyiv", line="вул. X"),
    )

    contact = service.remove_address("Іван")

    assert contact.address is None


def test_remove_birthday_clears_birthday(service):
    service.add_contact("Іван", birthday="01.01.1990")

    contact = service.remove_birthday("Іван")

    assert contact.birthday is None


# ---------- remove_phones / remove_all_phones ----------


def test_remove_phones_removes_specified_phones(service):
    service.add_contact("Іван", phones=("0501234567", "0509998877"))

    contact = service.remove_phones("Іван", ("0501234567",))

    assert [item.value for item in contact.phones] == ["+380509998877"]


def test_remove_phones_raises_for_unknown_phone(service):
    service.add_contact("Іван", phone="0501234567")

    with pytest.raises(ValueError):
        service.remove_phones("Іван", ("0000000000",))


def test_remove_all_phones_clears_phones(service):
    service.add_contact("Іван", phones=("0501234567", "0509998877"))

    contact = service.remove_all_phones("Іван")

    assert contact.phones == []


def test_remove_all_phones_on_contact_without_phones(service):
    service.add_contact("Іван")

    contact = service.remove_all_phones("Іван")

    assert contact.phones == []


# ---------- remove_emails / remove_all_emails ----------


def test_remove_emails_removes_specified_emails(service):
    service.add_contact(
        "Іван",
        emails=("a@example.com", "b@example.com"),
    )

    contact = service.remove_emails("Іван", ("a@example.com",))

    assert [item.value for item in contact.emails] == ["b@example.com"]


def test_remove_all_emails_clears_emails(service):
    service.add_contact(
        "Іван",
        emails=("a@example.com", "b@example.com"),
    )

    contact = service.remove_all_emails("Іван")

    assert contact.emails == []


# ---------- _merge_values (internal) ----------


def test_merge_values_drops_none_and_keeps_sequence():
    result = ContactsService._merge_values(None, ("a", "b"))

    assert result == ("a", "b")


def test_merge_values_drops_empty_string():
    """Falsy single value is filtered out by truthiness check in implementation."""
    result = ContactsService._merge_values("", ("a",))

    assert result == ("a",)


def test_merge_values_combines_single_and_sequence():
    result = ContactsService._merge_values("a", ("b", "c"))

    assert result == ("a", "b", "c")


def test_merge_values_returns_empty_tuple_for_no_inputs():
    result = ContactsService._merge_values(None, ())

    assert result == ()


# ---------- set_tags_from_text / clear_tags ----------


def test_set_tags_from_text_replaces_existing_tags(service):
    service.add_contact("John Smith")
    service.set_tags_from_text("John Smith", "old, work")

    contact = service.set_tags_from_text("John Smith", "Family, USA")

    assert contact.tags == {"family", "usa"}


def test_set_tags_from_text_splits_by_all_multi_value_separators(service):
    service.add_contact("Іван")

    contact = service.set_tags_from_text("Іван", "робота;Important, США")

    assert contact.tags == {"робота", "important", "сша"}


def test_set_tags_from_text_ignores_empty_tags(service):
    service.add_contact("Іван")

    contact = service.set_tags_from_text("Іван", ", робота,   ,")

    assert contact.tags == {"робота"}


def test_parse_tags_uses_system_value_separators():
    result = ContactsService.parse_tags(" work; USA, friends ")

    assert result == ("work", "USA", "friends")


def test_format_tags_uses_first_system_separator(service):
    service.add_contact("John Smith")
    contact = service.set_tags_from_text("John Smith", "work, usa")

    assert service.format_tags(contact.tags) == "usa; work"


def test_clear_tags_removes_all_tags(service):
    service.add_contact("John Smith")
    service.set_tags_from_text("John Smith", "work, important")

    contact = service.clear_tags("John Smith")

    assert contact.tags == set()


def test_set_tags_from_text_raises_for_missing_contact(service):
    with pytest.raises(KeyError):
        service.set_tags_from_text("Unknown", "work")


def test_clear_tags_raises_for_missing_contact(service):
    with pytest.raises(KeyError):
        service.clear_tags("Unknown")
