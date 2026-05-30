"""Unit tests for ``ContactsRepository`` in ``assistant_t800.repositories.contacts``."""

from datetime import date, datetime

import pytest

from assistant_t800.application.enums import SystemValue
from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.repositories import contacts as contacts_module
from assistant_t800.repositories.contacts import ContactsRepository


# ---------- helpers ----------


def _make_contact(name: str) -> Contact:
    """Build a bare contact with just a name."""
    return Contact(Name(name))


class _FrozenDatetime(datetime):
    """``datetime`` subclass with a frozen ``now`` for deterministic birthday tests."""

    _frozen: date

    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return datetime.combine(cls._frozen, datetime.min.time())


@pytest.fixture
def freeze_today(monkeypatch):
    """Return a callable that freezes ``datetime.now`` to the supplied date."""

    def _freeze(value: date) -> None:
        _FrozenDatetime._frozen = value
        monkeypatch.setattr(contacts_module, "datetime", _FrozenDatetime)

    return _freeze


# ---------- add / remove / get ----------


def test_add_stores_contact_and_makes_it_retrievable():
    repo = ContactsRepository()
    contact = _make_contact("Іван")

    repo.add(contact)

    assert repo.get("Іван") is contact


def test_add_raises_on_duplicate_name():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    with pytest.raises(ValueError, match="вже існує"):
        repo.add(_make_contact("Іван"))


def test_add_treats_names_case_insensitively_as_duplicates():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    with pytest.raises(ValueError):
        repo.add(_make_contact("іван"))


def test_add_trims_name_for_duplicate_detection():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    with pytest.raises(ValueError):
        repo.add(_make_contact("  Іван  "))


def test_remove_returns_removed_contact():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    repo.add(contact)

    removed = repo.remove("Іван")

    assert removed is contact
    assert repo.get("Іван") is None


def test_remove_is_case_insensitive():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    repo.remove("ІВАН")

    assert repo.get("Іван") is None


def test_remove_raises_key_error_for_missing_contact():
    repo = ContactsRepository()

    with pytest.raises(KeyError):
        repo.remove("Невідомий")


def test_get_returns_none_for_missing_contact():
    repo = ContactsRepository()

    assert repo.get("Невідомий") is None


def test_get_is_case_insensitive():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    repo.add(contact)

    assert repo.get("ІВАН") is contact
    assert repo.get("іван") is contact


# ---------- exists ----------


def test_exists_returns_true_when_contact_present():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    assert repo.exists("Іван") is True


def test_exists_returns_false_when_contact_missing():
    repo = ContactsRepository()

    assert repo.exists("Іван") is False


def test_exists_is_case_insensitive():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    assert repo.exists("іВаН") is True


# ---------- all ----------


def test_all_returns_empty_list_for_empty_repository():
    assert ContactsRepository().all() == []


def test_all_returns_every_stored_contact():
    repo = ContactsRepository()
    first = _make_contact("Іван")
    second = _make_contact("Олена")
    repo.add(first)
    repo.add(second)

    assert set(repo.all()) == {first, second}


def test_all_returns_independent_list():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    snapshot = repo.all()
    snapshot.clear()

    assert len(repo.all()) == 1, "all() must return a copy"


# ---------- search (any field) ----------


def test_search_returns_empty_list_for_empty_query():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    assert repo.search("") == []


def test_search_returns_empty_list_for_whitespace_query():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    assert repo.search("   ") == []


def test_search_matches_by_name():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))
    repo.add(_make_contact("Олена"))

    result = repo.search("іва")

    assert [item.name.value for item in result] == ["Іван"]


def test_search_matches_by_phone():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.add_phone("1234567890")
    repo.add(contact)

    result = repo.search("12345")

    assert result == [contact]


def test_search_matches_by_email():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.add_email("ivan@example.com")
    repo.add(contact)

    result = repo.search("EXAMPLE")

    assert result == [contact]


def test_search_matches_by_address():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_address("Kyiv, Ukraine")
    repo.add(contact)

    result = repo.search("kyiv")

    assert result == [contact]


def test_search_matches_by_birthday():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_birthday("01.01.1990")
    repo.add(contact)

    result = repo.search("01.01.1990")

    assert result == [contact]


def test_search_matches_by_note():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_note("Best friend")
    repo.add(contact)

    result = repo.search("friend")

    assert result == [contact]


def test_search_matches_by_tag():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.add_tag("Family")
    repo.add(contact)

    result = repo.search("famil")

    assert result == [contact]


def test_search_ignores_empty_note_marker():
    """Empty notes use a zero-width sentinel; searching for it must not match."""
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    result = repo.search(SystemValue.EMPTY_TEXT.value)

    assert result == []


# ---------- search_name ----------


def test_search_name_returns_empty_for_empty_query():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    assert repo.search_name("") == []


def test_search_name_partial_match():
    repo = ContactsRepository()
    repo.add(_make_contact("Іванко"))
    repo.add(_make_contact("Олена"))

    result = repo.search_name("іва")

    assert [item.name.value for item in result] == ["Іванко"]


def test_search_name_ignores_phone_and_email_fields():
    repo = ContactsRepository()
    contact = _make_contact("Олена")
    contact.add_phone("1234567890")
    contact.add_email("ivan@example.com")
    repo.add(contact)

    assert repo.search_name("1234567890") == []
    assert repo.search_name("ivan") == []


# ---------- search_phone ----------


def test_search_phone_matches_any_phone():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.add_phone("1234567890")
    contact.add_phone("9876543210")
    repo.add(contact)

    result = repo.search_phone("9876")

    assert result == [contact]


def test_search_phone_ignores_non_phone_fields():
    repo = ContactsRepository()
    contact = _make_contact("12345")  # name that looks like digits
    repo.add(contact)

    # Name shouldn't be matched by search_phone — the contact has no phones.
    assert repo.search_phone("12345") == []


# ---------- search_email ----------


def test_search_email_matches_any_email():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.add_email("ivan@example.com")
    contact.add_email("ivan.work@example.org")
    repo.add(contact)

    result = repo.search_email("work")

    assert result == [contact]


def test_search_email_returns_no_results_when_no_emails():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    assert repo.search_email("example") == []


# ---------- search_note ----------


def test_search_note_ignores_empty_note_marker_in_data():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))  # default note is the EMPTY_TEXT sentinel

    assert repo.search_note(SystemValue.EMPTY_TEXT.value) == []


def test_search_note_matches_note_substring():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_note("Loves coffee")
    repo.add(contact)

    result = repo.search_note("coffee")

    assert result == [contact]


def test_search_note_is_case_insensitive():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_note("Loves Coffee")
    repo.add(contact)

    result = repo.search_note("COFFEE")

    assert result == [contact]


# ---------- search_tag ----------


def test_search_tag_returns_empty_for_empty_query():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.add_tag("friend")
    repo.add(contact)

    assert repo.search_tag("") == []


def test_search_tag_matches_partial_tag():
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.add_tag("Family")
    repo.add(contact)

    result = repo.search_tag("fam")

    assert result == [contact]


def test_search_tag_returns_no_results_when_no_tags():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    assert repo.search_tag("anything") == []


# ---------- search_upcoming_birthdays ----------


def test_search_upcoming_birthdays_returns_empty_for_no_contacts():
    repo = ContactsRepository()

    assert repo.search_upcoming_birthdays(7) == []


def test_search_upcoming_birthdays_skips_contacts_without_birthday():
    repo = ContactsRepository()
    repo.add(_make_contact("Іван"))

    assert repo.search_upcoming_birthdays(7) == []


def test_search_upcoming_birthdays_returns_contact_within_window(freeze_today):
    # Wednesday 01.01.2025 — birthday on 03.01 is two days ahead.
    freeze_today(date(2025, 1, 1))
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_birthday("03.01.1990")
    repo.add(contact)

    result = repo.search_upcoming_birthdays(7)

    assert len(result) == 1
    item = result[0]
    assert isinstance(item, BirthdaysListContact)
    assert item.name == "Іван"
    assert item.birthday == "03.01.1990"
    assert item.congratulation_date == "03.01.2025"
    assert item.age == "35"


def test_search_upcoming_birthdays_excludes_contacts_beyond_window(freeze_today):
    freeze_today(date(2025, 1, 1))
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_birthday("15.01.1990")
    repo.add(contact)

    assert repo.search_upcoming_birthdays(7) == []


def test_search_upcoming_birthdays_today_is_included(freeze_today):
    # 06.01.2025 is a Monday, so no weekend shift; congrats date equals today.
    freeze_today(date(2025, 1, 6))
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_birthday("06.01.1990")
    repo.add(contact)

    result = repo.search_upcoming_birthdays(7)

    assert len(result) == 1
    assert result[0].congratulation_date == "06.01.2025"


def test_search_upcoming_birthdays_shifts_saturday_to_monday(freeze_today):
    # 04.01.2025 is a Saturday. Frozen "today" is 31.12.2024 (Tuesday).
    freeze_today(date(2024, 12, 31))
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_birthday("04.01.1990")
    repo.add(contact)

    result = repo.search_upcoming_birthdays(7)

    assert len(result) == 1
    assert result[0].birthday == "04.01.1990"
    assert result[0].congratulation_date == "06.01.2025"


def test_search_upcoming_birthdays_shifts_sunday_to_monday(freeze_today):
    # 05.01.2025 is a Sunday. Frozen "today" is 31.12.2024.
    freeze_today(date(2024, 12, 31))
    repo = ContactsRepository()
    contact = _make_contact("Олена")
    contact.set_birthday("05.01.1990")
    repo.add(contact)

    result = repo.search_upcoming_birthdays(7)

    assert len(result) == 1
    assert result[0].congratulation_date == "06.01.2025"


def test_search_upcoming_birthdays_wraps_to_next_year_when_past(freeze_today):
    # 15.06.2025: birthday on 10.06.1990 already passed, so it should roll over to 2026.
    freeze_today(date(2025, 6, 15))
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_birthday("10.06.1990")
    repo.add(contact)

    # 365 days window so the rolled-over 2026 birthday is captured.
    result = repo.search_upcoming_birthdays(365)

    assert len(result) == 1
    assert result[0].congratulation_date == "10.06.2026"
    assert result[0].age == "36"


def test_search_upcoming_birthdays_results_are_sorted_by_congratulation_date(
    freeze_today,
):
    freeze_today(date(2025, 1, 1))
    repo = ContactsRepository()

    second = _make_contact("Олена")
    second.set_birthday("05.01.1995")  # Sunday -> Monday 06.01
    repo.add(second)

    first = _make_contact("Іван")
    first.set_birthday("02.01.1990")  # Thursday 02.01
    repo.add(first)

    result = repo.search_upcoming_birthdays(7)

    assert [item.name for item in result] == ["Іван", "Олена"]


def test_search_upcoming_birthdays_default_window_is_seven_days(freeze_today):
    freeze_today(date(2025, 1, 1))
    repo = ContactsRepository()

    inside = _make_contact("Іван")
    inside.set_birthday("07.01.1990")  # Tuesday — within 7 days
    repo.add(inside)

    outside = _make_contact("Олена")
    outside.set_birthday("15.01.1990")  # well beyond 7 days
    repo.add(outside)

    result = repo.search_upcoming_birthdays()

    assert [item.name for item in result] == ["Іван"]


def test_search_upcoming_birthdays_age_reflects_year_of_congratulation(freeze_today):
    # In Jan 2026 the person born in 1990 turns 36.
    freeze_today(date(2025, 12, 31))  # Wednesday
    repo = ContactsRepository()
    contact = _make_contact("Іван")
    contact.set_birthday("05.01.1990")  # Monday in 2026 — no weekend shift
    repo.add(contact)

    result = repo.search_upcoming_birthdays(10)

    assert len(result) == 1
    assert result[0].age == "36"
    assert result[0].congratulation_date == "05.01.2026"
