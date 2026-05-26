"""Unit tests for AI agent tools in ``assistant_t800.ai.tools``.

Tests verify observable state changes (service storage, presenter calls)
rather than asserting on the text of the tool's return message — the
wording is a template that the assistant uses for chat responses and
should be free to change without breaking tests.
"""

import pytest

from assistant_t800.ai import tools
from assistant_t800.domain.birthdays import BirthdaysListContact


# ---------- add_contact ----------


def test_add_contact_creates_contact_and_refreshes_panel(ctx, service, presenter):
    tools.add_contact(ctx, "Іван", phone="0501234567", email="ivan@example.com")

    contacts = service.list_contacts()
    assert len(contacts) == 1, "exactly one contact should be stored"
    contact = contacts[0]
    assert contact.name.value == "Іван"
    assert [p.value for p in contact.phones] == ["0501234567"]
    assert [e.value for e in contact.emails] == ["ivan@example.com"]
    assert len(presenter.refresh_calls) == 1, "panel must be refreshed exactly once"
    assert [c.name.value for c in presenter.refresh_calls[-1]] == ["Іван"], (
        "panel must receive the newly created contact"
    )


def test_add_contact_invalid_phone_leaves_state_untouched(ctx, service, presenter):
    tools.add_contact(ctx, "Іван", phone="123")

    assert service.list_contacts() == [], (
        "no contact must be stored when phone validation fails"
    )
    assert presenter.refresh_calls == [], "panel must not be refreshed on error"


def test_add_contact_duplicate_name_does_not_create_second_contact(
    ctx, service, presenter
):
    tools.add_contact(ctx, "Іван")
    presenter.refresh_calls.clear()

    tools.add_contact(ctx, "Іван")

    assert len(service.list_contacts()) == 1, (
        "duplicate name must not create a second contact"
    )
    assert presenter.refresh_calls == [], (
        "panel must not be refreshed when duplicate is rejected"
    )


# ---------- get_contact ----------


def test_get_contact_refreshes_panel_with_single_contact(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    presenter.refresh_calls.clear()

    tools.get_contact(ctx, "Іван")

    assert len(presenter.refresh_calls) == 1
    panel = presenter.refresh_calls[0]
    assert [c.name.value for c in panel] == ["Іван"]


def test_get_contact_missing_does_not_touch_presenter(ctx, presenter):
    tools.get_contact(ctx, "Невідомий")

    assert presenter.refresh_calls == [], (
        "panel must not be refreshed when the contact does not exist"
    )


# ---------- list_contacts ----------


def test_list_contacts_empty_refreshes_panel_with_empty_list(ctx, presenter):
    tools.list_contacts(ctx)

    assert presenter.refresh_calls == [[]], (
        "panel must be refreshed once with an empty list to clear stale entries"
    )


def test_list_contacts_with_data_refreshes_panel_with_all_contacts(
    ctx, service, presenter
):
    tools.add_contact(ctx, "Іван")
    tools.add_contact(ctx, "Марія")
    presenter.refresh_calls.clear()

    tools.list_contacts(ctx)

    assert len(presenter.refresh_calls) == 1
    names = [c.name.value for c in presenter.refresh_calls[-1]]
    assert names == ["Іван", "Марія"]


# ---------- search_contacts (general) ----------


def test_search_contacts_finds_by_any_field(ctx, presenter):
    tools.add_contact(ctx, "Іван", phone="0501234567")
    presenter.refresh_calls.clear()

    tools.search_contacts(ctx, "0501234567")

    matched = presenter.refresh_calls[-1]
    assert [c.name.value for c in matched] == ["Іван"]


def test_search_contacts_no_match_refreshes_panel_with_empty_list(ctx, presenter):
    tools.add_contact(ctx, "Іван")
    presenter.refresh_calls.clear()

    tools.search_contacts(ctx, "qzqzqz")

    assert presenter.refresh_calls[-1] == []


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
    presenter.refresh_calls.clear()

    tool_fn(ctx, query)

    matched = presenter.refresh_calls[-1]
    if expected_match:
        assert [c.name.value for c in matched] == ["Іван"]
    else:
        assert matched == []


def test_search_contacts_by_note(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    service.get_contact("Іван").set_note("важливий клієнт")
    presenter.refresh_calls.clear()

    tools.search_contacts_by_note(ctx, "клієнт")
    tools.search_contacts_by_note(ctx, "qqq")

    matched, missed = presenter.refresh_calls
    assert [c.name.value for c in matched] == ["Іван"]
    assert missed == []


def test_search_contacts_by_tag(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    service.get_contact("Іван").add_tag("робота")
    presenter.refresh_calls.clear()

    tools.search_contacts_by_tag(ctx, "робота")
    tools.search_contacts_by_tag(ctx, "хобі")

    matched, missed = presenter.refresh_calls
    assert [c.name.value for c in matched] == ["Іван"]
    assert missed == []


# ---------- search_upcoming_birthdays ----------


def test_search_upcoming_birthdays_empty_emits_a_single_notification(ctx, presenter):
    tools.search_upcoming_birthdays(ctx)

    assert len(presenter.print_calls) == 1, (
        "empty result must still notify the user via a single print call"
    )


def test_search_upcoming_birthdays_prints_input_fields(ctx, presenter, monkeypatch):
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

    tools.search_upcoming_birthdays(ctx, days=10)

    assert len(presenter.print_calls) == 1, (
        "all upcoming birthdays must be rendered in a single print call"
    )
    printed = presenter.print_calls[0]
    for field_value in ("Іван", "26.05.1990", "26.05.2026", "36"):
        assert field_value in printed, (
            f"rendered output must include input field value {field_value!r}"
        )


# ---------- set_address ----------


def test_set_address_updates_value(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    presenter.refresh_calls.clear()

    tools.set_address(ctx, "Іван", "Київ, Хрещатик 1")

    assert service.get_contact("Іван").address.value == "Київ, Хрещатик 1"
    assert len(presenter.refresh_calls) == 1


def test_set_address_missing_contact_leaves_state_untouched(ctx, service, presenter):
    tools.set_address(ctx, "Невідомий", "Київ")

    assert service.list_contacts() == [], (
        "missing-contact errors must not create a placeholder contact"
    )
    assert presenter.refresh_calls == [], "panel must not be refreshed on error"


def test_set_address_empty_value_does_not_set(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    presenter.refresh_calls.clear()

    tools.set_address(ctx, "Іван", "   ")

    assert service.get_contact("Іван").address is None, (
        "whitespace-only address must be rejected and leave the field unset"
    )
    assert presenter.refresh_calls == [], "panel must not be refreshed on error"


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


# ---------- add_phones ----------


def test_add_phones_appends_multiple(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    presenter.refresh_calls.clear()

    tools.add_phones(ctx, "Іван", ["0501112233", "0509998877"])

    phones = [item.value for item in service.get_contact("Іван").phones]
    assert phones == ["0501112233", "0509998877"]
    assert len(presenter.refresh_calls) == 1


def test_add_phones_invalid_value_leaves_state_untouched(ctx, service, presenter):
    tools.add_contact(ctx, "Іван")
    presenter.refresh_calls.clear()

    tools.add_phones(ctx, "Іван", ["123"])

    assert service.get_contact("Іван").phones == [], (
        "no phone must be appended when validation fails"
    )
    assert presenter.refresh_calls == [], "panel must not be refreshed on error"


def test_add_phones_missing_contact_leaves_state_untouched(ctx, service, presenter):
    tools.add_phones(ctx, "Невідомий", ["0501112233"])

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []


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
    presenter.refresh_calls.clear()

    tools.remove_contact(ctx, "Іван")

    assert service.list_contacts() == [], "removed contact must be gone from storage"
    assert presenter.refresh_calls == [[]], (
        "panel must be refreshed with an empty list to drop the removed contact"
    )


def test_remove_contact_missing_leaves_state_untouched(ctx, service, presenter):
    tools.remove_contact(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []


# ---------- remove_address ----------


def test_remove_address_clears_value(ctx, service):
    tools.add_contact(ctx, "Іван", address="Київ")

    tools.remove_address(ctx, "Іван")

    assert service.get_contact("Іван").address is None


def test_remove_address_missing_contact_leaves_state_untouched(ctx, service, presenter):
    tools.remove_address(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []


# ---------- remove_birthday ----------


def test_remove_birthday_clears_value(ctx, service):
    tools.add_contact(ctx, "Іван", birthday="01.01.1990")

    tools.remove_birthday(ctx, "Іван")

    assert service.get_contact("Іван").birthday is None


def test_remove_birthday_missing_contact_leaves_state_untouched(
    ctx, service, presenter
):
    tools.remove_birthday(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []


# ---------- remove_phones ----------


def test_remove_phones_removes_listed_values(ctx, service, presenter):
    tools.add_contact(ctx, "Іван", phone="0501112233")
    service.add_phones("Іван", ["0509998877"])
    presenter.refresh_calls.clear()

    tools.remove_phones(ctx, "Іван", ["0501112233"])

    remaining = [item.value for item in service.get_contact("Іван").phones]
    assert remaining == ["0509998877"]
    assert len(presenter.refresh_calls) == 1


def test_remove_phones_unknown_phone_leaves_state_untouched(ctx, service, presenter):
    tools.add_contact(ctx, "Іван", phone="0501112233")
    presenter.refresh_calls.clear()

    tools.remove_phones(ctx, "Іван", ["0509998877"])

    phones = [item.value for item in service.get_contact("Іван").phones]
    assert phones == ["0501112233"], (
        "removing a non-existent phone must not affect existing phones"
    )
    assert presenter.refresh_calls == [], "panel must not be refreshed on error"


def test_remove_phones_missing_contact_leaves_state_untouched(ctx, service, presenter):
    tools.remove_phones(ctx, "Невідомий", ["0501112233"])

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []


# ---------- remove_all_phones ----------


def test_remove_all_phones_clears_collection(ctx, service):
    tools.add_contact(ctx, "Іван", phone="0501112233")
    service.add_phones("Іван", ["0509998877"])

    tools.remove_all_phones(ctx, "Іван")

    assert service.get_contact("Іван").phones == []


def test_remove_all_phones_missing_contact_leaves_state_untouched(
    ctx, service, presenter
):
    tools.remove_all_phones(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []


# ---------- remove_emails ----------


def test_remove_emails_removes_listed_values(ctx, service):
    tools.add_contact(ctx, "Іван", email="a@example.com")
    service.add_emails("Іван", ["b@example.com"])

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
    service.add_emails("Іван", ["b@example.com"])

    tools.remove_all_emails(ctx, "Іван")

    assert service.get_contact("Іван").emails == []


def test_remove_all_emails_missing_contact_leaves_state_untouched(
    ctx, service, presenter
):
    tools.remove_all_emails(ctx, "Невідомий")

    assert service.list_contacts() == []
    assert presenter.refresh_calls == []
