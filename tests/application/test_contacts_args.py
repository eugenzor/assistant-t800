"""Unit tests for ``ContactArgumentsParser`` in ``assistant_t800.application.contacts_args``."""

from assistant_t800.application.contacts_args import (
    ContactArgumentsParser,
    ContactDraft,
)
from assistant_t800.application.results import AppResult
from assistant_t800.localization import ErrorCode


# ---------- ContactDraft dataclass ----------


def test_contact_draft_defaults_to_empty_collections():
    draft = ContactDraft(name="Іван")

    assert draft.name == "Іван"
    assert draft.phones == ()
    assert draft.emails == ()
    assert draft.address is None
    assert draft.birthday is None


def test_contact_draft_stores_supplied_values():
    draft = ContactDraft(
        name="Іван",
        phones=("1234567890",),
        emails=("a@example.com",),
        address="Kyiv",
        birthday="01.01.1990",
    )

    assert draft.phones == ("1234567890",)
    assert draft.emails == ("a@example.com",)
    assert draft.address == "Kyiv"
    assert draft.birthday == "01.01.1990"


# ---------- split_multi_values ----------


def test_split_multi_values_splits_by_semicolon():
    result = ContactArgumentsParser.split_multi_values("a;b;c")

    assert result == ("a", "b", "c")


def test_split_multi_values_splits_by_comma():
    result = ContactArgumentsParser.split_multi_values("a,b,c")

    assert result == ("a", "b", "c")


def test_split_multi_values_handles_mixed_separators():
    result = ContactArgumentsParser.split_multi_values("a;b,c")

    assert result == ("a", "b", "c")


def test_split_multi_values_trims_whitespace_around_items():
    result = ContactArgumentsParser.split_multi_values(" a ;  b  ,c ")

    assert result == ("a", "b", "c")


def test_split_multi_values_drops_empty_segments():
    result = ContactArgumentsParser.split_multi_values("a;;b;,;c")

    assert result == ("a", "b", "c")


def test_split_multi_values_returns_single_item_when_no_separator():
    result = ContactArgumentsParser.split_multi_values("a")

    assert result == ("a",)


def test_split_multi_values_for_empty_string_returns_empty_tuple():
    result = ContactArgumentsParser.split_multi_values("")

    assert result == ()


# ---------- normalize_birthday ----------


def test_normalize_birthday_keeps_dot_separator():
    result = ContactArgumentsParser.normalize_birthday("01.01.1990")

    assert result == "01.01.1990"


def test_normalize_birthday_converts_dashes_to_dots():
    result = ContactArgumentsParser.normalize_birthday("01-01-1990")

    assert result == "01.01.1990"


def test_normalize_birthday_converts_slashes_to_dots():
    result = ContactArgumentsParser.normalize_birthday("01/01/1990")

    assert result == "01.01.1990"


def test_normalize_birthday_strips_whitespace():
    result = ContactArgumentsParser.normalize_birthday("  01-01-1990  ")

    assert result == "01.01.1990"


def test_normalize_birthday_handles_mixed_separators():
    result = ContactArgumentsParser.normalize_birthday("01/01-1990")

    assert result == "01.01.1990"


# ---------- parse_add: validation errors ----------


def test_parse_add_with_empty_args_returns_missing_arguments():
    result = ContactArgumentsParser.parse_add(())

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS
    assert result.message.params["command"] == "add"
    assert "syntax" in result.message.params


# ---------- parse_add: name only ----------


def test_parse_add_with_only_name_returns_draft():
    result = ContactArgumentsParser.parse_add(("Іван",))

    assert isinstance(result, ContactDraft)
    assert result.name == "Іван"
    assert result.phones == ()
    assert result.emails == ()
    assert result.address is None
    assert result.birthday is None


# ---------- parse_add: phone detection ----------


def test_parse_add_detects_phone_token():
    result = ContactArgumentsParser.parse_add(("Іван", "1234567890"))

    assert isinstance(result, ContactDraft)
    assert result.phones == ("1234567890",)


def test_parse_add_detects_multiple_phones_in_single_token():
    result = ContactArgumentsParser.parse_add(
        ("Іван", "1234567890;9876543210"),
    )

    assert isinstance(result, ContactDraft)
    assert result.phones == ("1234567890", "9876543210")


def test_parse_add_detects_phone_collection_with_comma_separator():
    result = ContactArgumentsParser.parse_add(
        ("Іван", "1234567890,9876543210"),
    )

    assert isinstance(result, ContactDraft)
    assert result.phones == ("1234567890", "9876543210")


# ---------- parse_add: email detection ----------


def test_parse_add_detects_email_token():
    result = ContactArgumentsParser.parse_add(("Іван", "ivan@example.com"))

    assert isinstance(result, ContactDraft)
    assert result.emails == ("ivan@example.com",)


def test_parse_add_detects_multiple_emails_in_single_token():
    result = ContactArgumentsParser.parse_add(
        ("Іван", "a@example.com;b@example.com"),
    )

    assert isinstance(result, ContactDraft)
    assert result.emails == ("a@example.com", "b@example.com")


# ---------- parse_add: birthday detection ----------


def test_parse_add_detects_birthday_token_with_dots():
    result = ContactArgumentsParser.parse_add(("Іван", "01.01.1990"))

    assert isinstance(result, ContactDraft)
    assert result.birthday == "01.01.1990"


def test_parse_add_detects_birthday_token_with_dashes_and_normalizes():
    result = ContactArgumentsParser.parse_add(("Іван", "01-01-1990"))

    assert isinstance(result, ContactDraft)
    assert result.birthday == "01.01.1990"


def test_parse_add_detects_birthday_token_with_slashes_and_normalizes():
    result = ContactArgumentsParser.parse_add(("Іван", "01/01/1990"))

    assert isinstance(result, ContactDraft)
    assert result.birthday == "01.01.1990"


def test_parse_add_rejects_second_birthday_token():
    result = ContactArgumentsParser.parse_add(
        ("Іван", "01.01.1990", "02.02.1995"),
    )

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.EXTRA_ARGUMENTS
    assert result.message.params["command"] == "add"


# ---------- parse_add: address detection ----------


def test_parse_add_uses_non_typed_token_as_address():
    result = ContactArgumentsParser.parse_add(("Іван", "Kyiv"))

    assert isinstance(result, ContactDraft)
    assert result.address == "Kyiv"
    assert result.phones == ()
    assert result.emails == ()
    assert result.birthday is None


def test_parse_add_uses_second_unknown_token_as_extra_arguments():
    result = ContactArgumentsParser.parse_add(
        ("Іван", "Kyiv", "Lviv"),
    )

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.EXTRA_ARGUMENTS


# ---------- parse_add: combined fields ----------


def test_parse_add_combines_phone_email_address_and_birthday():
    result = ContactArgumentsParser.parse_add(
        (
            "Іван",
            "1234567890",
            "ivan@example.com",
            "Kyiv",
            "01.01.1990",
        ),
    )

    assert isinstance(result, ContactDraft)
    assert result.name == "Іван"
    assert result.phones == ("1234567890",)
    assert result.emails == ("ivan@example.com",)
    assert result.address == "Kyiv"
    assert result.birthday == "01.01.1990"


def test_parse_add_supports_arbitrary_token_order():
    result = ContactArgumentsParser.parse_add(
        (
            "Іван",
            "01.01.1990",
            "Kyiv",
            "ivan@example.com",
            "1234567890",
        ),
    )

    assert isinstance(result, ContactDraft)
    assert result.phones == ("1234567890",)
    assert result.emails == ("ivan@example.com",)
    assert result.address == "Kyiv"
    assert result.birthday == "01.01.1990"


# ---------- parse_values ----------


def test_parse_values_returns_name_and_split_values():
    result = ContactArgumentsParser.parse_values(
        ("Іван", "1234567890;9876543210"),
        command="add-phone",
        value_name="phones",
    )

    assert result == ("Іван", ("1234567890", "9876543210"))


def test_parse_values_with_single_value():
    result = ContactArgumentsParser.parse_values(
        ("Іван", "1234567890"),
        command="add-phone",
        value_name="phones",
    )

    assert result == ("Іван", ("1234567890",))


def test_parse_values_missing_value_returns_missing_arguments():
    result = ContactArgumentsParser.parse_values(
        ("Іван",),
        command="add-phone",
        value_name="phones",
    )

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS
    assert result.message.params["command"] == "add-phone"


def test_parse_values_no_arguments_returns_missing_arguments():
    result = ContactArgumentsParser.parse_values(
        (),
        command="add-phone",
        value_name="phones",
    )

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS


def test_parse_values_too_many_arguments_returns_extra_arguments():
    result = ContactArgumentsParser.parse_values(
        ("Іван", "1234567890", "extra"),
        command="add-phone",
        value_name="phones",
    )

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message.code is ErrorCode.EXTRA_ARGUMENTS


# ---------- parse_optional_values ----------


def test_parse_optional_values_with_only_name_returns_empty_tuple():
    result = ContactArgumentsParser.parse_optional_values(
        ("Іван",),
        command="remove-phone",
        value_name="phone",
    )

    assert result == ("Іван", ())


def test_parse_optional_values_with_value_returns_split_values():
    result = ContactArgumentsParser.parse_optional_values(
        ("Іван", "1234567890;9876543210"),
        command="remove-phone",
        value_name="phone",
    )

    assert result == ("Іван", ("1234567890", "9876543210"))


def test_parse_optional_values_no_arguments_returns_missing_arguments():
    result = ContactArgumentsParser.parse_optional_values(
        (),
        command="remove-phone",
        value_name="phone",
    )

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS


def test_parse_optional_values_too_many_arguments_returns_extra_arguments():
    result = ContactArgumentsParser.parse_optional_values(
        ("Іван", "1234567890", "extra"),
        command="remove-phone",
        value_name="phone",
    )

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message.code is ErrorCode.EXTRA_ARGUMENTS


# ---------- parse_named_value ----------


def test_parse_named_value_returns_name_and_value():
    result = ContactArgumentsParser.parse_named_value(
        ("Іван", "Kyiv"),
        command="set-address",
        value_name="address",
    )

    assert result == ("Іван", "Kyiv")


def test_parse_named_value_missing_value_returns_missing_arguments():
    result = ContactArgumentsParser.parse_named_value(
        ("Іван",),
        command="set-address",
        value_name="address",
    )

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS


def test_parse_named_value_too_many_arguments_returns_extra_arguments():
    result = ContactArgumentsParser.parse_named_value(
        ("Іван", "Kyiv", "Lviv"),
        command="set-address",
        value_name="address",
    )

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message.code is ErrorCode.EXTRA_ARGUMENTS


def test_parse_named_value_no_arguments_returns_missing_arguments():
    result = ContactArgumentsParser.parse_named_value(
        (),
        command="set-address",
        value_name="address",
    )

    assert isinstance(result, AppResult)
    assert result.success is False
    assert result.message.code is ErrorCode.MISSING_ARGUMENTS
