"""Unit tests for application command handlers in ``assistant_t800.application.handlers``."""

import pytest

from assistant_t800.application import handlers
from assistant_t800.application.context import AppContext
from assistant_t800.application.results import AppResult
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
    assert result.message is not None
    assert result.message.code is Message.HELP
    assert result.data is registry


def test_close_app_signals_exit():
    result = handlers.close_app(_context())

    assert result.success is True
    assert result.should_exit is True
    assert result.message is not None
    assert result.message.code is Message.GOOD_BYE


# ---------- list_contacts ----------


def test_list_contacts_empty_reports_no_contacts():
    context = _context()

    result = handlers.list_contacts(context)

    assert result.success is True
    assert result.message is not None
    assert result.message.code is Message.NO_CONTACTS
    assert result.message.params["count"] == 0


def test_list_contacts_with_data_reports_contacts_listed():
    context = _context()
    context.contacts.add_contact("Іван")

    result = handlers.list_contacts(context)

    assert result.message is not None
    assert result.message.code is Message.CONTACTS_LISTED
    assert result.message.params["count"] == 1


# ---------- get_contact ----------


def test_get_contact_returns_found_when_present():
    context = _context(args={"name": "Іван"})
    context.contacts.add_contact("Іван")

    result = handlers.get_contact(context)

    assert result.success is True
    assert result.message is not None
    assert result.message.code is Message.CONTACT_FOUND


def test_get_contact_missing_returns_contact_not_found():
    context = _context(args={"name": "Невідомий"})

    result = handlers.get_contact(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND


# ---------- search handlers ----------


@pytest.mark.parametrize(
    "handler",
    [
        handlers.search_contacts,
        handlers.search_contacts_by_name,
        handlers.search_contacts_by_phone,
        handlers.search_contacts_by_email,
        handlers.search_contacts_by_note,
        handlers.search_contacts_by_tag,
    ],
)
def test_search_handlers_return_contacts_found_message(handler):
    context = _context(args={"query": "qzqzqz"})

    result = handler(context)

    assert result.success is True
    assert result.message is not None
    assert result.message.code is Message.CONTACTS_FOUND
    assert result.message.params["count"] == 0


def test_search_contacts_includes_matching_contacts_in_data():
    context = _context(args={"query": "Іван"})
    context.contacts.add_contact("Іван", phone="0501234567")

    result = handlers.search_contacts(context)

    assert isinstance(result.data, list)
    assert len(result.data) == 1


# ---------- list_upcoming_birthdays ----------


def test_list_upcoming_birthdays_default_days_returns_no_birthdays():
    context = _context()

    result = handlers.list_upcoming_birthdays(context)

    assert result.success is True
    assert result.message is not None
    assert result.message.code is Message.NO_BIRTHDAYS
    assert result.message.params["days"] == 7


def test_list_upcoming_birthdays_parses_int_days():
    context = _context(args={"days": "10"})

    result = handlers.list_upcoming_birthdays(context)

    assert result.success is True
    assert result.message is not None
    assert result.message.params["days"] == 10


def test_list_upcoming_birthdays_non_integer_days_fails():
    context = _context(args={"days": "abc"})

    result = handlers.list_upcoming_birthdays(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.INVALID_DAYS


def test_list_upcoming_birthdays_zero_days_fails():
    context = _context(args={"days": "0"})

    result = handlers.list_upcoming_birthdays(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.INVALID_DAYS


def test_list_upcoming_birthdays_negative_days_fails():
    context = _context(args={"days": "-1"})

    result = handlers.list_upcoming_birthdays(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.INVALID_DAYS


# ---------- edit_note ----------


def test_edit_note_sets_value():
    context = _context(raw_args=("Іван", "важливий клієнт"))
    context.contacts.add_contact("Іван")

    result = handlers.edit_note(context)

    assert result.success is True
    assert context.contacts.get_contact("Іван").note == "важливий клієнт"


def test_edit_note_missing_value_fails_with_missing_arguments():
    context = _context(raw_args=("Іван",))

    result = handlers.edit_note(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS


def test_edit_note_whitespace_only_value_fails_with_validation_error():
    context = _context(raw_args=("Іван", "   "))
    context.contacts.add_contact("Іван")

    result = handlers.edit_note(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.VALIDATION_ERROR


def test_edit_note_missing_contact_returns_contact_not_found():
    context = _context(raw_args=("Невідомий", "примітка"))

    result = handlers.edit_note(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND


# ---------- add_tag / remove_tag ----------


def test_add_tag_is_not_implemented():
    result = handlers.add_tag(_context())

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.NOT_IMPLEMENTED


def test_remove_tag_is_not_implemented():
    result = handlers.remove_tag(_context())

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.NOT_IMPLEMENTED


# ---------- add_contact ----------


def test_add_contact_creates_full_contact_from_raw_args():
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


def test_set_address_updates_value():
    context = _context(args={"name": "Іван", "address": "Київ"})
    context.contacts.add_contact("Іван")

    result = handlers.set_address(context)

    assert result.success is True
    contact = context.contacts.get_contact("Іван")
    assert contact.address is not None
    assert contact.address.value == "Київ"


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
    context = _context(raw_args=("Невідомий", "0501234567"))

    result = handlers.add_phone(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND


def test_add_email_appends_multiple_values():
    context = _context(raw_args=("Іван", "a@example.com;b@example.com"))
    context.contacts.add_contact("Іван")

    result = handlers.add_email(context)

    assert result.success is True
    emails = [e.value for e in context.contacts.get_contact("Іван").emails]
    assert emails == ["a@example.com", "b@example.com"]


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


# ---------- remove_address / remove_birthday ----------


def test_remove_address_unconfirmed_returns_confirmation():
    context = _context(args={"name": "Іван"}, confirmed=False)
    context.contacts.add_contact("Іван", address="Київ")

    result = handlers.remove_address(context)

    assert result.requires_confirmation is True
    assert result.confirmation is not None
    assert result.confirmation.message.code is Message.CONFIRM_REMOVE_ADDRESS


def test_remove_address_confirmed_clears_value():
    context = _context(args={"name": "Іван"}, confirmed=True)
    context.contacts.add_contact("Іван", address="Київ")

    result = handlers.remove_address(context)

    assert result.success is True
    assert context.contacts.get_contact("Іван").address is None


def test_remove_address_confirmed_missing_contact_returns_contact_not_found():
    context = _context(args={"name": "Невідомий"}, confirmed=True)

    result = handlers.remove_address(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND


def test_remove_birthday_unconfirmed_returns_confirmation():
    context = _context(args={"name": "Іван"}, confirmed=False)
    context.contacts.add_contact("Іван", birthday="01.01.1990")

    result = handlers.remove_birthday(context)

    assert result.requires_confirmation is True
    assert result.confirmation is not None
    assert result.confirmation.message.code is Message.CONFIRM_REMOVE_BIRTHDAY


def test_remove_birthday_confirmed_clears_value():
    context = _context(args={"name": "Іван"}, confirmed=True)
    context.contacts.add_contact("Іван", birthday="01.01.1990")

    result = handlers.remove_birthday(context)

    assert result.success is True
    assert context.contacts.get_contact("Іван").birthday is None


# ---------- remove_note ----------


def test_remove_note_unconfirmed_returns_confirmation():
    context = _context(args={"name": "Іван"}, confirmed=False)
    context.contacts.add_contact("Іван")
    context.contacts.set_note("Іван", "важливий клієнт")

    result = handlers.remove_note(context)

    assert result.requires_confirmation is True
    assert result.confirmation is not None
    assert result.confirmation.message.code is Message.CONFIRM_REMOVE_NOTE


def test_remove_note_confirmed_clears_value():
    context = _context(args={"name": "Іван"}, confirmed=True)
    context.contacts.add_contact("Іван")
    context.contacts.set_note("Іван", "важливий клієнт")

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


def test_remove_phone_without_value_with_one_value_confirmed_removes_it():
    context = _context(raw_args=("Іван",), confirmed=True)
    context.contacts.add_contact("Іван", phone="0501112233")

    result = handlers.remove_phone(context)

    assert result.success is True
    assert context.contacts.get_contact("Іван").phones == []


def test_remove_phone_missing_contact_returns_contact_not_found():
    context = _context(raw_args=("Невідомий",), confirmed=False)

    result = handlers.remove_phone(context)

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND


# ---------- remove_email (mirrors remove_phone) ----------


def test_remove_email_with_explicit_value_unconfirmed_returns_confirmation():
    context = _context(raw_args=("Іван", "a@example.com"), confirmed=False)
    context.contacts.add_contact("Іван", email="a@example.com")

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
    context = _context(raw_args=("Іван",), confirmed=True)
    context.contacts.add_contact("Іван", email="a@example.com")
    context.contacts.add_emails("Іван", ["b@example.com"])

    result = handlers.remove_email(context)

    assert result.success is True
    assert context.contacts.get_contact("Іван").emails == []