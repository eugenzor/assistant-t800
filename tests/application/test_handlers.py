"""Unit tests for application command handlers."""

import pytest

from assistant_t800.application import handlers
from assistant_t800.application.context import AppContext
from assistant_t800.application.enums import SystemValue
from assistant_t800.application.results import ResultStatus
from assistant_t800.localization import ErrorCode, Message
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService


def _context(
    *,
    args: dict[str, str] | None = None,
    raw_args: tuple[str, ...] = (),
    confirmed: bool = False,
) -> AppContext:
    """Build an application context backed by an empty in-memory service."""
    return AppContext(
        contacts=ContactsService(ContactsRepository()),
        args=args or {},
        raw_args=raw_args,
        confirmed=confirmed,
    )


# ---------- show_help / close_app ----------


def test_show_help_returns_registry_as_data():
    registry = {"help": object()}
    context = _context()
    context.registry = registry

    result = handlers.show_help(context)

    assert result.success is True
    assert result.status is ResultStatus.SUCCESS
    assert result.message is not None
    assert result.message.code is Message.HELP
    assert result.data is registry


def test_close_app_signals_exit():
    result = handlers.close_app(_context())

    assert result.success is True
    assert result.status is ResultStatus.SUCCESS
    assert result.should_exit is True
    assert result.message is not None
    assert result.message.code is Message.GOOD_BYE


# ---------- list_contacts ----------


def test_list_contacts_empty_reports_info_not_found():
    context = _context()

    result = handlers.list_contacts(context)

    assert result.success is False
    assert result.status is ResultStatus.INFO
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACTS_NOT_FOUND


def test_list_contacts_with_data_reports_contacts_listed():
    context = _context()
    context.contacts.add_contact("Іван")
    context.contacts.add_contact("John Smith", phone="0991112233")

    result = handlers.list_contacts(context)

    assert result.success is True
    assert result.status is ResultStatus.SUCCESS
    assert result.message is not None
    assert result.message.code is Message.CONTACTS_LISTED
    assert result.message.params["count"] == 2
    assert len(result.data) == 2


# ---------- get_contact ----------


def test_get_contact_returns_found_when_present():
    context = _context(args={"name": "John Smith"})
    context.contacts.add_contact("John Smith", email="john@example.com")

    result = handlers.get_contact(context)

    assert result.success is True
    assert result.status is ResultStatus.SUCCESS
    assert result.message is not None
    assert result.message.code is Message.CONTACT_FOUND
    assert result.data.name.value == "John Smith"


def test_get_contact_missing_returns_name_not_found_warning():
    context = _context(args={"name": "Невідомий"})

    result = handlers.get_contact(context)

    assert result.success is False
    assert result.status is ResultStatus.WARNING
    assert result.message is not None
    assert result.message.code is ErrorCode.NAME_NOT_FOUND
    assert result.message.params["query"] == "Невідомий"


# ---------- search handlers ----------


@pytest.mark.parametrize(
    ("handler", "error_code"),
    [
        (handlers.search_contacts, ErrorCode.QUERY_NOT_FOUND),
        (handlers.search_contacts_by_name, ErrorCode.NAME_NOT_FOUND),
        (handlers.search_contacts_by_phone, ErrorCode.PHONE_NOT_FOUND),
        (handlers.search_contacts_by_email, ErrorCode.EMAIL_NOT_FOUND),
        (handlers.search_contacts_by_note, ErrorCode.NOTE_NOT_FOUND),
        (handlers.search_contacts_by_tag, ErrorCode.TAG_NOT_FOUND),
    ],
)
def test_search_handlers_return_warning_for_no_matches(handler, error_code):
    context = _context(args={"query": "qzqzqz"})

    result = handler(context)

    assert result.success is False
    assert result.status is ResultStatus.WARNING
    assert result.message is not None
    assert result.message.code is error_code
    assert result.message.params["query"] == "qzqzqz"


def test_search_contacts_includes_matching_contacts_in_data():
    context = _context(args={"query": "New York"})
    context.contacts.add_contact(
        "John Smith",
        phone="0991112233",
        email="john@example.com",
        address="New York",
    )
    context.contacts.add_contact("Марія", phone="0506666666", address="Київ")

    result = handlers.search_contacts(context)

    assert result.success is True
    assert result.message is not None
    assert result.message.code is Message.CONTACTS_FOUND
    assert result.message.params["count"] == 1
    assert [item.name.value for item in result.data] == ["John Smith"]


# ---------- list_upcoming_birthdays ----------


def test_list_upcoming_birthdays_default_days_returns_info_no_birthdays():
    context = _context()

    result = handlers.list_upcoming_birthdays(context)

    assert result.success is False
    assert result.status is ResultStatus.INFO
    assert result.message is not None
    assert result.message.code is Message.NO_BIRTHDAYS
    assert result.message.params["days"] == 7


def test_list_upcoming_birthdays_parses_int_days():
    context = _context(args={"days": "10"})

    result = handlers.list_upcoming_birthdays(context)

    assert result.success is False
    assert result.status is ResultStatus.INFO
    assert result.message is not None
    assert result.message.params["days"] == 10


@pytest.mark.parametrize("value", ("abc", "0", "-1"))
def test_list_upcoming_birthdays_invalid_days_fails(value):
    context = _context(args={"days": value})

    result = handlers.list_upcoming_birthdays(context)

    assert result.success is False
    assert result.status is ResultStatus.ERROR
    assert result.message is not None
    assert result.message.code is ErrorCode.INVALID_DAYS


# ---------- edit_note ----------


def test_edit_note_sets_ukrainian_value():
    context = _context(raw_args=("Іван", "важливий клієнт"))
    context.contacts.add_contact("Іван")

    result = handlers.edit_note(context)

    assert result.success is True
    assert result.status is ResultStatus.SUCCESS
    assert context.contacts.get_contact("Іван").note == "важливий клієнт"
    assert result.data is context.contacts.get_contact("Іван")


def test_edit_note_sets_multiline_english_value():
    context = _context(raw_args=("John Smith", "Prepare docs\nCall next week"))
    context.contacts.add_contact("John Smith")

    result = handlers.edit_note(context)

    assert result.success is True
    assert context.contacts.get_contact("John Smith").note == (
        "Prepare docs\nCall next week"
    )


def test_edit_note_missing_value_fails_with_missing_arguments():
    context = _context(raw_args=("Іван",))

    result = handlers.edit_note(context)

    assert result.success is False
    assert result.status is ResultStatus.ERROR
    assert result.message is not None
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS


def test_edit_note_whitespace_only_value_clears_note_sentinel():
    context = _context(raw_args=("Іван", "   "))
    context.contacts.add_contact("Іван")

    result = handlers.edit_note(context)

    assert result.success is True
    assert result.status is ResultStatus.SUCCESS
    assert context.contacts.get_contact("Іван").note == SystemValue.EMPTY_TEXT.value


def test_edit_note_missing_contact_returns_name_not_found_warning():
    context = _context(raw_args=("Unknown", "note"))

    result = handlers.edit_note(context)

    assert result.success is False
    assert result.status is ResultStatus.WARNING
    assert result.message is not None
    assert result.message.code is ErrorCode.NAME_NOT_FOUND


# ---------- edit_tags ----------


def test_edit_tags_replaces_ukrainian_and_english_tags():
    context = _context(raw_args=("Іван", "робота, Important; США"))
    context.contacts.add_contact("Іван")

    result = handlers.edit_tags(context)

    assert result.success is True
    assert result.status is ResultStatus.SUCCESS
    assert result.message is not None
    assert result.message.code is Message.CONTACT_TAGS_UPDATED
    assert context.contacts.get_contact("Іван").tags == {"робота", "important", "сша"}


def test_edit_tags_replaces_existing_tags_instead_of_appending():
    context = _context(raw_args=("John Smith", "family, usa"))
    context.contacts.add_contact("John Smith")
    context.contacts.set_tags_from_text("John Smith", "old, work")

    result = handlers.edit_tags(context)

    assert result.success is True
    assert context.contacts.get_contact("John Smith").tags == {"family", "usa"}


def test_edit_tags_ignores_empty_chunks_and_duplicates():
    context = _context(raw_args=("John Smith", "work, , Work; important,,"))
    context.contacts.add_contact("John Smith")

    result = handlers.edit_tags(context)

    assert result.success is True
    assert context.contacts.get_contact("John Smith").tags == {"work", "important"}


def test_edit_tags_empty_value_requires_confirmation_before_clearing():
    context = _context(raw_args=("Іван", ""), confirmed=False)
    context.contacts.add_contact("Іван")
    context.contacts.set_tags_from_text("Іван", "work, urgent")

    result = handlers.edit_tags(context)

    assert result.requires_confirmation is True
    assert result.status is ResultStatus.WARNING
    assert result.confirmation is not None
    assert result.confirmation.message.code is Message.CONFIRM_REMOVE_TAGS
    assert context.contacts.get_contact("Іван").tags == {"work", "urgent"}


def test_edit_tags_empty_value_clears_tags_when_confirmed():
    context = _context(raw_args=("Іван", ""), confirmed=True)
    context.contacts.add_contact("Іван")
    context.contacts.set_tags_from_text("Іван", "work, urgent")

    result = handlers.edit_tags(context)

    assert result.success is True
    assert result.message is not None
    assert result.message.code is Message.REMOVED_TAGS
    assert context.contacts.get_contact("Іван").tags == set()


def test_edit_tags_missing_value_fails_with_missing_arguments():
    context = _context(raw_args=("Іван",))

    result = handlers.edit_tags(context)

    assert result.success is False
    assert result.status is ResultStatus.ERROR
    assert result.message is not None
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS


def test_edit_tags_missing_contact_returns_contact_not_found_error():
    context = _context(raw_args=("Unknown", "work, usa"))

    result = handlers.edit_tags(context)

    assert result.success is False
    assert result.status is ResultStatus.ERROR
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND


# ---------- add_contact ----------


def test_add_contact_creates_full_ukrainian_contact_from_raw_args():
    context = _context(
        raw_args=("Іван", "0501234567", "ivan@example.com", "01.01.1990", "Київ"),
    )

    result = handlers.add_contact(context)

    assert result.success is True
    contact = context.contacts.get_contact("Іван")
    assert [p.value for p in contact.phones] == ["0501234567"]
    assert [e.value for e in contact.emails] == ["ivan@example.com"]
    assert contact.birthday is not None
    assert contact.birthday.value == "01.01.1990"
    assert contact.address is not None
    assert contact.address.value == "Київ"


def test_add_contact_creates_full_english_contact_from_raw_args():
    context = _context(
        raw_args=(
            "John Smith",
            "0991112233",
            "john@example.com",
            "30.05.1990",
            "New York",
        ),
    )

    result = handlers.add_contact(context)

    assert result.success is True
    contact = context.contacts.get_contact("john smith")
    assert contact.name.value == "John Smith"
    assert contact.address.value == "New York"


def test_add_contact_no_args_fails_with_missing_arguments():
    context = _context(raw_args=())

    result = handlers.add_contact(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS


def test_add_contact_duplicate_name_fails_with_validation_error():
    context = _context(raw_args=("Іван",))
    context.contacts.add_contact("Іван")

    result = handlers.add_contact(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.VALIDATION_ERROR


# ---------- set_address / set_birthday ----------


def test_set_address_updates_english_value():
    context = _context(args={"name": "John Smith", "address": "New York"})
    context.contacts.add_contact("John Smith")

    result = handlers.set_address(context)

    assert result.success is True
    contact = context.contacts.get_contact("John Smith")
    assert contact.address is not None
    assert contact.address.value == "New York"


def test_set_address_missing_contact_returns_contact_not_found():
    context = _context(args={"name": "Невідомий", "address": "Київ"})

    result = handlers.set_address(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND


def test_set_birthday_normalizes_separators():
    context = _context(args={"name": "Іван", "birthday": "01/01/1990"})
    context.contacts.add_contact("Іван")

    result = handlers.set_birthday(context)

    assert result.success is True
    contact = context.contacts.get_contact("Іван")
    assert contact.birthday is not None
    assert contact.birthday.value == "01.01.1990"


def test_set_birthday_invalid_value_returns_validation_error():
    context = _context(args={"name": "Іван", "birthday": "not-a-date"})
    context.contacts.add_contact("Іван")

    result = handlers.set_birthday(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.VALIDATION_ERROR


# ---------- add_phone / add_email ----------


def test_add_phone_appends_multiple_values():
    context = _context(raw_args=("Іван", "0501112233;0509998877"))
    context.contacts.add_contact("Іван")

    result = handlers.add_phone(context)

    assert result.success is True
    phones = [p.value for p in context.contacts.get_contact("Іван").phones]
    assert phones == ["0501112233", "0509998877"]


def test_add_phone_missing_value_fails_with_missing_arguments():
    context = _context(raw_args=("Іван",))

    result = handlers.add_phone(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS


def test_add_phone_invalid_value_fails_with_validation_error():
    context = _context(raw_args=("Іван", "123"))
    context.contacts.add_contact("Іван")

    result = handlers.add_phone(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.VALIDATION_ERROR


def test_add_phone_missing_contact_returns_contact_not_found():
    context = _context(raw_args=("Unknown", "0991112233"))

    result = handlers.add_phone(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND


def test_add_email_appends_multiple_values():
    context = _context(raw_args=("John Smith", "john@example.com;work@example.org"))
    context.contacts.add_contact("John Smith")

    result = handlers.add_email(context)

    assert result.success is True
    emails = [e.value for e in context.contacts.get_contact("John Smith").emails]
    assert emails == ["john@example.com", "work@example.org"]


def test_add_email_invalid_value_fails_with_validation_error():
    context = _context(raw_args=("Іван", "not-an-email"))
    context.contacts.add_contact("Іван")

    result = handlers.add_email(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.VALIDATION_ERROR


# ---------- remove_contact (confirmation flow) ----------


def test_remove_contact_unconfirmed_returns_confirmation():
    context = _context(args={"name": "Іван"}, confirmed=False)
    context.contacts.add_contact("Іван")

    result = handlers.remove_contact(context)

    assert result.requires_confirmation is True
    assert result.status is ResultStatus.WARNING
    assert result.confirmation is not None
    assert result.confirmation.message.code is Message.CONFIRM_REMOVE_CONTACT


def test_remove_contact_confirmed_deletes_from_storage():
    context = _context(args={"name": "Іван"}, confirmed=True)
    context.contacts.add_contact("Іван")

    result = handlers.remove_contact(context)

    assert result.success is True
    assert result.message is not None
    assert result.message.code is Message.REMOVED_CONTACT
    assert context.contacts.list_contacts() == []


def test_remove_contact_confirmed_missing_returns_contact_not_found():
    context = _context(args={"name": "Невідомий"}, confirmed=True)

    result = handlers.remove_contact(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND


# ---------- remove_address / remove_birthday / remove_note ----------


@pytest.mark.parametrize(
    ("handler", "confirm_code"),
    [
        (handlers.remove_address, Message.CONFIRM_REMOVE_ADDRESS),
        (handlers.remove_birthday, Message.CONFIRM_REMOVE_BIRTHDAY),
        (handlers.remove_note, Message.CONFIRM_REMOVE_NOTE),
    ],
)
def test_scalar_remove_unconfirmed_returns_confirmation(handler, confirm_code):
    context = _context(args={"name": "Іван"}, confirmed=False)
    context.contacts.add_contact("Іван", address="Київ", birthday="01.01.1990")
    context.contacts.set_note("Іван", "важливий клієнт")

    result = handler(context)

    assert result.requires_confirmation is True
    assert result.confirmation is not None
    assert result.confirmation.message.code is confirm_code


def test_remove_address_confirmed_clears_value():
    context = _context(args={"name": "Іван"}, confirmed=True)
    context.contacts.add_contact("Іван", address="Київ")

    result = handlers.remove_address(context)

    assert result.success is True
    assert context.contacts.get_contact("Іван").address is None


def test_remove_birthday_confirmed_clears_value():
    context = _context(args={"name": "Іван"}, confirmed=True)
    context.contacts.add_contact("Іван", birthday="01.01.1990")

    result = handlers.remove_birthday(context)

    assert result.success is True
    assert context.contacts.get_contact("Іван").birthday is None


def test_remove_note_confirmed_clears_value():
    context = _context(args={"name": "John Smith"}, confirmed=True)
    context.contacts.add_contact("John Smith")
    context.contacts.set_note("John Smith", "important")

    result = handlers.remove_note(context)

    assert result.success is True
    assert result.message is not None
    assert result.message.code is Message.REMOVED_NOTE


# ---------- remove_phone ----------


def test_remove_phone_with_explicit_value_unconfirmed_returns_confirmation():
    context = _context(raw_args=("Іван", "0501112233"), confirmed=False)
    context.contacts.add_contact("Іван", phone="0501112233")

    result = handlers.remove_phone(context)

    assert result.requires_confirmation is True
    assert result.confirmation is not None
    assert result.confirmation.message.code is Message.CONFIRM_REMOVE_PHONE


def test_remove_phone_with_explicit_value_confirmed_removes_value():
    context = _context(raw_args=("Іван", "0501112233"), confirmed=True)
    context.contacts.add_contact("Іван", phone="0501112233")
    context.contacts.add_phones("Іван", ["0509998877"])

    result = handlers.remove_phone(context)

    assert result.success is True
    phones = [p.value for p in context.contacts.get_contact("Іван").phones]
    assert phones == ["0509998877"]


def test_remove_phone_without_value_when_field_empty_fails():
    context = _context(raw_args=("Іван",), confirmed=False)
    context.contacts.add_contact("Іван")

    result = handlers.remove_phone(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_FIELD_EMPTY


def test_remove_phone_without_value_with_one_value_asks_confirmation():
    context = _context(raw_args=("Іван",), confirmed=False)
    context.contacts.add_contact("Іван", phone="0501112233")

    result = handlers.remove_phone(context)

    assert result.requires_confirmation is True
    assert result.confirmation is not None
    assert result.confirmation.message.code is Message.CONFIRM_REMOVE_PHONE


def test_remove_phone_without_value_with_many_values_asks_remove_all_confirmation():
    context = _context(raw_args=("Іван",), confirmed=False)
    context.contacts.add_contact("Іван", phone="0501112233")
    context.contacts.add_phones("Іван", ["0509998877"])

    result = handlers.remove_phone(context)

    assert result.requires_confirmation is True
    assert result.confirmation is not None
    assert result.confirmation.message.code is Message.CONFIRM_REMOVE_ALL_PHONES


def test_remove_phone_without_value_with_many_values_confirmed_clears_all():
    context = _context(raw_args=("Іван",), confirmed=True)
    context.contacts.add_contact("Іван", phone="0501112233")
    context.contacts.add_phones("Іван", ["0509998877"])

    result = handlers.remove_phone(context)

    assert result.success is True
    assert context.contacts.get_contact("Іван").phones == []


def test_remove_phone_missing_contact_returns_contact_not_found():
    context = _context(raw_args=("Невідомий",), confirmed=False)

    result = handlers.remove_phone(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND


# ---------- remove_email ----------


def test_remove_email_with_explicit_value_unconfirmed_returns_confirmation():
    context = _context(raw_args=("John Smith", "john@example.com"), confirmed=False)
    context.contacts.add_contact("John Smith", email="john@example.com")

    result = handlers.remove_email(context)

    assert result.requires_confirmation is True
    assert result.confirmation is not None
    assert result.confirmation.message.code is Message.CONFIRM_REMOVE_EMAIL


def test_remove_email_without_value_when_field_empty_fails():
    context = _context(raw_args=("Іван",), confirmed=False)
    context.contacts.add_contact("Іван")

    result = handlers.remove_email(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_FIELD_EMPTY


def test_remove_email_without_value_with_many_values_confirmed_clears_all():
    context = _context(raw_args=("John Smith",), confirmed=True)
    context.contacts.add_contact("John Smith", email="john@example.com")
    context.contacts.add_emails("John Smith", ["work@example.org"])

    result = handlers.remove_email(context)

    assert result.success is True
    assert context.contacts.get_contact("John Smith").emails == []
