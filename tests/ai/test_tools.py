"""Unit tests for AI agent tools in ``assistant_t800.ai.tools``.

Tests verify service state changes and structured display metadata returned
by tools. Tools must not call the presenter directly — display updates are
applied by ``run_chat`` after the agent run.
"""

import pytest

from assistant_t800.ai import tools
from assistant_t800.ai.results import DisplayPayload
from assistant_t800.config import settings
from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import ContactField


def _contacts(result) -> list:
    """Return contact names from a tool result display payload."""
    assert isinstance(result.metadata, DisplayPayload)
    assert result.metadata.kind == "contacts"
    assert result.metadata.contacts is not None
    return result.metadata.contacts


def _contact(result):
    """Return a single contact from a card display payload."""
    assert isinstance(result.metadata, DisplayPayload)
    assert result.metadata.kind == "contact"
    assert result.metadata.contact is not None
    return result.metadata.contact


def _birthdays(result) -> list:
    """Return birthday records from a tool result display payload."""
    assert isinstance(result.metadata, DisplayPayload)
    assert result.metadata.kind == "birthdays"
    assert result.metadata.birthdays is not None
    return result.metadata.birthdays


# ---------- add_contact ----------


def test_add_contact_creates_contact_and_returns_display(ctx, service, presenter):
    result = tools.add_contact(
        ctx, "Іван", phone="0501234567", email="ivan@example.com"
    )

    contacts = service.list_contacts()
    assert len(contacts) == 1, "exactly one contact should be stored"
    contact = contacts[0]
    assert contact.name.value == "Іван"
    assert [p.value for p in contact.phones] == ["+380501234567"]
    assert [e.value for e in contact.emails] == ["ivan@example.com"]
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_add_contact_invalid_phone_leaves_state_untouched(ctx, service, presenter):
    result = tools.add_contact(ctx, "Іван", phone="123")

    assert service.list_contacts() == [], (
        "no contact must be stored when phone validation fails"
    )
    assert presenter.refresh_calls == []
    assert result.metadata is None


def test_add_contact_duplicate_name_does_not_create_second_contact(
    ctx, service, presenter
):
    tools.add_contact(ctx, "Іван")

    result = tools.add_contact(ctx, "Іван")

    assert len(service.list_contacts()) == 1, (
        "duplicate name must not create a second contact"
    )
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- get_contact ----------


def test_get_contact_returns_single_contact_display(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")

    result = tools.get_contact(ctx, "Іван")

    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_get_contact_missing_has_no_display(ctx, presenter):
    result = tools.get_contact(ctx, "Невідомий")

    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- list_contacts ----------


def test_list_contacts_empty_returns_empty_display(ctx, presenter):
    result = tools.list_contacts(ctx)

    assert presenter.refresh_calls == []
    assert _contacts(result) == []


def test_list_contacts_with_data_returns_all_contacts(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    tools.add_contact(ctx, "Марія")

    result = tools.list_contacts(ctx)

    assert presenter.refresh_calls == []
    names = [c.name.value for c in _contacts(result)]
    assert names == ["Іван", "Марія"]


# ---------- search_contacts (general) ----------


def test_search_contacts_finds_by_any_field(ctx, presenter):
    tools.add_contact(ctx, "Іван", phone="0501234567")

    result = tools.search_contacts(ctx, "0501234567")

    matched = _contacts(result)
    assert [c.name.value for c in matched] == ["Іван"]
    assert presenter.refresh_calls == []


def test_search_contacts_no_match_returns_empty_display(ctx, presenter):
    tools.add_contact(ctx, "Іван")

    result = tools.search_contacts(ctx, "qzqzqz")

    assert _contacts(result) == []
    assert presenter.refresh_calls == []


# ---------- fielded searches ----------


@pytest.mark.parametrize(
    ("tool_fn", "query", "expected_match"),
    [
        (tools.search_contacts_by_name, "Іван", True),
        (tools.search_contacts_by_name, "Петро", False),
        (tools.search_contacts_by_phone, "0501234567", True),
        (tools.search_contacts_by_phone, "0999999999", False),
        (tools.search_contacts_by_email, "ivan@example.com", True),
        (tools.search_contacts_by_email, "other@example.com", False),
    ],
)
def test_fielded_searches(ctx, presenter, tool_fn, query, expected_match):
    tools.add_contact(ctx, "Іван", phone="0501234567", email="ivan@example.com")

    result = tool_fn(ctx, query)

    matched = _contacts(result)
    if expected_match:
        assert [c.name.value for c in matched] == ["Іван"]
    else:
        assert matched == []
    assert presenter.refresh_calls == []


def test_search_contacts_by_note(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    service.get_contact("Іван").set_note("важливий клієнт")

    matched_result = tools.search_contacts_by_note(ctx, "клієнт")
    missed_result = tools.search_contacts_by_note(ctx, "qqq")

    assert [c.name.value for c in _contacts(matched_result)] == ["Іван"]
    assert _contacts(missed_result) == []
    assert presenter.refresh_calls == []


def test_search_contacts_by_tag(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    service.get_contact("Іван").add_tag("робота")

    matched_result = tools.search_contacts_by_tag(ctx, "робота")
    missed_result = tools.search_contacts_by_tag(ctx, "хобі")

    assert [c.name.value for c in _contacts(matched_result)] == ["Іван"]
    assert _contacts(missed_result) == []
    assert presenter.refresh_calls == []


# ---------- search_upcoming_birthdays ----------


def test_search_upcoming_birthdays_empty_returns_birthdays_display(ctx, presenter):
    result = tools.search_upcoming_birthdays(ctx)

    assert presenter.refresh_calls == []
    assert presenter.print_calls == []
    assert _birthdays(result) == []


def test_search_upcoming_birthdays_returns_birthday_records(
    ctx, presenter, monkeypatch
):
    fake = [
        BirthdaysListContact(
            name="Іван",
            birthday="26.05.1990",
            age="36",
            congratulation_date="26.05.2026",
        )
    ]
    monkeypatch.setattr(
        ctx.deps.contacts_service,
        "search_upcoming_birthdays",
        lambda days=7: fake,
    )

    result = tools.search_upcoming_birthdays(ctx, days=10)

    assert presenter.refresh_calls == []
    assert presenter.print_calls == []
    records = _birthdays(result)
    assert len(records) == 1
    assert records[0].name == "Іван"
    assert records[0].birthday == "26.05.1990"
    assert records[0].congratulation_date == "26.05.2026"
    assert records[0].age == "36"


# ---------- set_address ----------


def test_set_address_updates_value(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")

    result = tools.set_address(
        ctx, "Іван", country="UA", city="Київ", line="Хрещатик 1"
    )

    assert service.get_contact("Іван").address.value == "UA, Київ, Хрещатик 1"
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_set_address_missing_contact_leaves_state_untouched(ctx, service, presenter):
    result = tools.set_address(
        ctx, "Невідомий", country="UA", city="Київ", line="вул. X"
    )

    assert service.list_contacts() == [], (
        "missing-contact errors must not create a placeholder contact"
    )
    assert presenter.refresh_calls == []
    assert result.metadata is None


def test_set_address_invalid_country_does_not_set(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")

    result = tools.set_address(ctx, "Іван", country="Narnia", city="X", line="Y")

    assert service.get_contact("Іван").address is None, (
        "invalid country must be rejected and leave the field unset"
    )
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- set_birthday ----------


def test_set_birthday_updates_value(ctx, service):
    tools.add_contact(ctx, "Іван")

    tools.set_birthday(ctx, "Іван", "01.01.1990")

    assert service.get_contact("Іван").birthday.value == "01.01.1990"


def test_set_birthday_invalid_format_does_not_set(ctx, service):
    tools.add_contact(ctx, "Іван")

    tools.set_birthday(ctx, "Іван", "1990/01/40")

    assert service.get_contact("Іван").birthday is None, (
        "invalid date must be rejected and leave the birthday unset"
    )


def test_set_birthday_missing_contact_leaves_state_untouched(ctx, service):
    tools.set_birthday(ctx, "Невідомий", "01.01.1990")

    assert service.list_contacts() == []


# ---------- set_note ----------


def test_set_note_updates_value(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")

    result = tools.set_note(ctx, "Іван", "важливий клієнт")

    assert service.get_contact("Іван").note == "важливий клієнт"
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_set_note_replaces_existing_note(ctx, service):
    tools.add_contact(ctx, "Іван")
    tools.set_note(ctx, "Іван", "first")

    tools.set_note(ctx, "Іван", "second")

    assert service.get_contact("Іван").note == "second"


def test_set_note_missing_contact_leaves_state_untouched(ctx, service, presenter):
    result = tools.set_note(ctx, "Невідомий", "нотатка")

    assert service.list_contacts() == [], (
        "missing-contact errors must not create a placeholder contact"
    )
    assert presenter.refresh_calls == []
    assert result.metadata is None


def test_set_note_empty_value_is_rejected(ctx, service, presenter):
    from assistant_t800.application.enums import SystemValue

    tools.add_contact(ctx, "Іван")

    result = tools.set_note(ctx, "Іван", "   ")

    assert service.get_contact("Іван").note == SystemValue.EMPTY_TEXT.value, (
        "whitespace-only note must be rejected and leave the field unset"
    )
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- remove_note ----------


def test_remove_note_clears_value(ctx, service, presenter):
    from assistant_t800.application.enums import SystemValue

    tools.add_contact(ctx, "Іван")
    tools.set_note(ctx, "Іван", "важливий клієнт")

    result = tools.remove_note(ctx, "Іван")

    assert service.get_contact("Іван").note == SystemValue.EMPTY_TEXT.value
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_remove_note_missing_contact_leaves_state_untouched(ctx, service, presenter):
    result = tools.remove_note(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- add_phones ----------


def test_add_phones_appends_multiple(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")

    result = tools.add_phones(ctx, "Іван", ["0501112233", "0509998877"])

    phones = [item.value for item in service.get_contact("Іван").phones]
    assert phones == ["+380501112233", "+380509998877"]
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_add_phones_invalid_value_leaves_state_untouched(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")

    result = tools.add_phones(ctx, "Іван", ["123"])

    assert service.get_contact("Іван").phones == [], (
        "no phone must be appended when validation fails"
    )
    assert presenter.refresh_calls == []
    assert result.metadata is None


def test_add_phones_missing_contact_leaves_state_untouched(ctx, service, presenter):
    result = tools.add_phones(ctx, "Невідомий", ["0501112233"])

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- add_emails ----------


def test_add_emails_appends_multiple(ctx, service):
    tools.add_contact(ctx, "Іван")

    tools.add_emails(ctx, "Іван", ["a@example.com", "b@example.com"])

    emails = [item.value for item in service.get_contact("Іван").emails]
    assert emails == ["a@example.com", "b@example.com"]


def test_add_emails_invalid_value_leaves_state_untouched(ctx, service):
    tools.add_contact(ctx, "Іван")

    tools.add_emails(ctx, "Іван", ["not-an-email"])

    assert service.get_contact("Іван").emails == [], (
        "no e-mail must be appended when validation fails"
    )


# ---------- remove_contact ----------


def test_remove_contact_removes_from_storage(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")

    result = tools.remove_contact(ctx, "Іван")

    assert service.list_contacts() == [], "removed contact must be gone from storage"
    assert presenter.refresh_calls == []
    assert _contacts(result) == []


def test_remove_contact_missing_leaves_state_untouched(ctx, service, presenter):
    result = tools.remove_contact(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- remove_address ----------


def test_remove_address_clears_value(ctx, service):
    tools.add_contact(
        ctx,
        "Іван",
        address_country="UA",
        address_city="Київ",
        address_line="вул. X",
    )

    tools.remove_address(ctx, "Іван")

    assert service.get_contact("Іван").address is None


def test_remove_address_missing_contact_leaves_state_untouched(ctx, service, presenter):
    result = tools.remove_address(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- remove_birthday ----------


def test_remove_birthday_clears_value(ctx, service):
    tools.add_contact(ctx, "Іван", birthday="01.01.1990")

    tools.remove_birthday(ctx, "Іван")

    assert service.get_contact("Іван").birthday is None


def test_remove_birthday_missing_contact_leaves_state_untouched(
    ctx, service, presenter
):
    result = tools.remove_birthday(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- remove_phones ----------


def test_remove_phones_removes_listed_values(ctx, service, presenter):
    tools.add_contact(ctx, "Іван", phone="0501112233")
    ctx.deps.contacts_service.add_phones("Іван", ["0509998877"])

    result = tools.remove_phones(ctx, "Іван", ["0501112233"])

    remaining = [item.value for item in service.get_contact("Іван").phones]
    assert remaining == ["+380509998877"]
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_remove_phones_unknown_phone_leaves_state_untouched(ctx, service, presenter):
    tools.add_contact(ctx, "Іван", phone="0501112233")

    result = tools.remove_phones(ctx, "Іван", ["0509998877"])

    phones = [item.value for item in service.get_contact("Іван").phones]
    assert phones == ["+380501112233"], (
        "removing a non-existent phone must not affect existing phones"
    )
    assert presenter.refresh_calls == []
    assert result.metadata is None


def test_remove_phones_missing_contact_leaves_state_untouched(ctx, service, presenter):
    result = tools.remove_phones(ctx, "Невідомий", ["0501112233"])

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- remove_all_phones ----------


def test_remove_all_phones_clears_collection(ctx, service):
    tools.add_contact(ctx, "Іван", phone="0501112233")
    ctx.deps.contacts_service.add_phones("Іван", ["0509998877"])

    tools.remove_all_phones(ctx, "Іван")

    assert service.get_contact("Іван").phones == []


def test_remove_all_phones_missing_contact_leaves_state_untouched(
    ctx, service, presenter
):
    result = tools.remove_all_phones(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- remove_emails ----------


def test_remove_emails_removes_listed_values(ctx, service):
    tools.add_contact(ctx, "Іван", email="a@example.com")
    ctx.deps.contacts_service.add_emails("Іван", ["b@example.com"])

    tools.remove_emails(ctx, "Іван", ["a@example.com"])

    remaining = [item.value for item in service.get_contact("Іван").emails]
    assert remaining == ["b@example.com"]


def test_remove_emails_unknown_leaves_state_untouched(ctx, service):
    tools.add_contact(ctx, "Іван", email="a@example.com")

    tools.remove_emails(ctx, "Іван", ["unknown@example.com"])

    emails = [item.value for item in service.get_contact("Іван").emails]
    assert emails == ["a@example.com"], (
        "removing a non-existent e-mail must not affect existing e-mails"
    )


# ---------- remove_all_emails ----------


def test_remove_all_emails_clears_collection(ctx, service):
    tools.add_contact(ctx, "Іван", email="a@example.com")
    ctx.deps.contacts_service.add_emails("Іван", ["b@example.com"])

    tools.remove_all_emails(ctx, "Іван")

    assert service.get_contact("Іван").emails == []


def test_remove_all_emails_missing_contact_leaves_state_untouched(
    ctx, service, presenter
):
    result = tools.remove_all_emails(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- set_tags_from_text ----------


def test_set_tags_from_text_replaces_tags(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")

    result = tools.set_tags_from_text(ctx, "Іван", "робота, vip")

    tags = service.get_contact("Іван").tags
    assert tags == {"робота", "vip"}
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_set_tags_from_text_replaces_existing(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    service.set_tags_from_text("Іван", "old, work")

    result = tools.set_tags_from_text(ctx, "Іван", "new")

    assert service.get_contact("Іван").tags == {"new"}
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_set_tags_from_text_parses_separators(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")

    result = tools.set_tags_from_text(ctx, "Іван", "робота; vip")

    assert service.get_contact("Іван").tags == {"робота", "vip"}
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_set_tags_from_text_empty_clears_tags(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    service.set_tags_from_text("Іван", "робота, vip")

    result = tools.set_tags_from_text(ctx, "Іван", "   ")

    assert service.get_contact("Іван").tags == set()
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_set_tags_from_text_missing_contact_leaves_state_untouched(
    ctx, service, presenter
):
    result = tools.set_tags_from_text(ctx, "Невідомий", "робота")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- clear_tags ----------


def test_clear_tags_removes_all(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    service.set_tags_from_text("Іван", "робота, vip")

    result = tools.clear_tags(ctx, "Іван")

    assert service.get_contact("Іван").tags == set()
    assert presenter.refresh_calls == []
    assert _contact(result).name.value == "Іван"


def test_clear_tags_missing_contact_leaves_state_untouched(ctx, service, presenter):
    result = tools.clear_tags(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
    assert result.metadata is None


# ---------- LLM return_value summaries ----------


def test_get_contact_return_value_includes_contact_details(ctx, service):
    tools.add_contact(ctx, "Іван", phone="0501234567", birthday="15.12.1990")

    result = tools.get_contact(ctx, "Іван", fields=list(ContactField))

    assert "Іван" in result.return_value
    assert "0501234567" in result.return_value
    assert "15.12.1990" in result.return_value


def test_get_contact_default_fields_returns_name_only(ctx, service):
    tools.add_contact(ctx, "Іван", phone="0501234567", birthday="15.12.1990")

    result = tools.get_contact(ctx, "Іван")

    assert '"name": "Іван"' in result.return_value
    assert "0501234567" not in result.return_value
    assert "15.12.1990" not in result.return_value


def test_list_contacts_return_value_includes_all_contacts(ctx, service):
    tools.add_contact(ctx, "Іван")
    tools.add_contact(ctx, "Олена", birthday="03.01.1988")

    result = tools.list_contacts(ctx, fields=list(ContactField))

    assert '"name": "Іван"' in result.return_value
    assert '"name": "Олена"' in result.return_value
    assert "03.01.1988" in result.return_value


def test_list_contacts_return_value_truncates_when_over_cap(ctx, monkeypatch):
    monkeypatch.setattr(settings, "max_contacts_in_tool_return", 2)
    for index in range(3):
        tools.add_contact(ctx, f"Contact{index}")

    result = tools.list_contacts(ctx)

    assert "Contact0" in result.return_value
    assert "Contact1" in result.return_value
    assert "Contact2" not in result.return_value
    assert "Ще 1 контакт не показано" in result.return_value


def test_search_contacts_return_value_includes_match_details(ctx):
    tools.add_contact(ctx, "Іван", phone="0501234567")

    result = tools.search_contacts(
        ctx,
        "0501234567",
        fields=[ContactField.NAME, ContactField.PHONES],
    )

    assert "Іван" in result.return_value
    assert '"phones": ["+380501234567"]' in result.return_value


def test_search_upcoming_birthdays_return_value_includes_records(ctx, monkeypatch):
    fake = [
        BirthdaysListContact(
            name="Іван",
            birthday="26.05.1990",
            age="36",
            congratulation_date="26.05.2026",
        )
    ]
    monkeypatch.setattr(
        ctx.deps.contacts_service,
        "search_upcoming_birthdays",
        lambda days=7: fake,
    )

    result = tools.search_upcoming_birthdays(ctx, days=10)

    assert "Іван" in result.return_value
    assert "26.05.1990" in result.return_value
    assert "26.05.2026" in result.return_value


# ---------- fields parameter ----------


def test_list_contacts_fields_limits_return_value(ctx):
    tools.add_contact(ctx, "Іван", phone="0501234567", birthday="15.12.1990")

    result = tools.list_contacts(ctx, fields=[ContactField.BIRTHDAY])

    assert "15.12.1990" in result.return_value
    assert "0501234567" not in result.return_value


def test_get_contact_fields_limits_return_value(ctx):
    tools.add_contact(ctx, "Іван", phone="0501234567", birthday="15.12.1990")

    result = tools.get_contact(ctx, "Іван", fields=[ContactField.BIRTHDAY])

    assert "15.12.1990" in result.return_value
    assert "0501234567" not in result.return_value


def test_search_contacts_fields_limits_return_value(ctx):
    tools.add_contact(ctx, "Іван", phone="0501234567", email="ivan@example.com")

    result = tools.search_contacts(ctx, "ivan", fields=[ContactField.EMAILS])

    assert "ivan@example.com" in result.return_value
    assert "0501234567" not in result.return_value
