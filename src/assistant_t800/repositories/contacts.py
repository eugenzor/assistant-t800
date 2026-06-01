"""In-memory contact repository implementation."""

import calendar
from datetime import date, datetime, timedelta
from typing import Optional

from assistant_t800.application.enums import SystemValue
from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact


class ContactsRepository:
    """Case-insensitive in-memory contact storage."""

    def __init__(self) -> None:
        self._data: dict[str, Contact] = {}

    @staticmethod
    def _key(name: str) -> str:
        """Normalize a contact name for internal dictionary usage."""
        return name.strip().casefold()

    @staticmethod
    def _search_key(value: str) -> str:
        """Normalize a value for partial search."""
        return value.strip().casefold()

    def add(self, contact: Contact) -> None:
        """Store a new contact."""
        key = self._key(contact.name.value)

        if key in self._data:
            raise ValueError(f"Контакт «{contact.name.value}» вже існує")

        self._data[key] = contact

    def remove(self, name: str) -> Contact:
        """Remove and return a contact by name."""
        key = self._key(name)
        contact = self._data.pop(key, None)

        if contact is None:
            raise KeyError(name)

        return contact

    def get(self, name: str) -> Optional[Contact]:
        """Return a contact by name, or ``None`` if it does not exist."""
        return self._data.get(self._key(name))

    def exists(self, name: str) -> bool:
        """Return ``True`` if the contact exists in the repository."""
        return self._key(name) in self._data

    def all(self) -> list[Contact]:
        """Return all stored contacts."""
        return list(self._data.values())

    def search(self, query: str) -> list[Contact]:
        """Search contacts by all indexed fields."""
        return self._filter(
            lambda contact, value: self._matches_any(contact, value), query
        )

    def search_name(self, query: str) -> list[Contact]:
        """Search contacts by name."""
        return self._filter(
            lambda contact, value: value in self._search_key(contact.name.value), query
        )

    def search_phone(self, query: str) -> list[Contact]:
        """Search contacts by phone."""
        return self._filter(
            lambda contact, value: any(
                (
                    value in self._search_key(item.value)
                    or value in self._search_key(str(item))
                )
                for item in contact.phones
            ),
            query,
        )

    def search_email(self, query: str) -> list[Contact]:
        """Search contacts by email."""
        return self._filter(
            lambda contact, value: any(
                value in self._search_key(item.value) for item in contact.emails
            ),
            query,
        )

    def search_note(self, query: str) -> list[Contact]:
        """Search contacts by note text."""
        return self._filter(
            lambda contact, value: (
                contact.note != SystemValue.EMPTY_TEXT.value
                and value in self._search_key(contact.note)
            ),
            query,
        )

    def search_tag(self, query: str) -> list[Contact]:
        """Search contacts by tag."""
        return self._filter(
            lambda contact, value: any(
                value in self._search_key(tag) for tag in contact.tags
            ),
            query,
        )

    def search_upcoming_birthdays(self, days: int = 7) -> list[BirthdaysListContact]:
        """
        Return contacts who should be congratulated within the next days.

        If a birthday falls on Saturday or Sunday, the congratulation date is moved
        to the following Monday.
        """

        def get_congratulation_date(birthday_date: date) -> date:
            """Move birthday date to the following Monday if it falls on weekend."""
            shift_days = {
                5: 2,  # Saturday -> Monday
                6: 1,  # Sunday -> Monday
            }.get(birthday_date.weekday(), 0)

            return birthday_date + timedelta(days=shift_days)

        def birthday_in_year(birthday_date: date, year: int) -> date:
            """Project a birthday onto a target year.

            Only a 29 February birthday can become invalid when the year
            changes; in a non-leap target year it is celebrated on 28 February.
            """
            is_feb29 = birthday_date.month == 2 and birthday_date.day == 29

            if is_feb29 and not calendar.isleap(year):
                return birthday_date.replace(year=year, day=28)

            return birthday_date.replace(year=year)

        today = datetime.now().date()
        period_end = today + timedelta(days=days)
        result: list[BirthdaysListContact] = []

        for contact in self.all():
            if contact.birthday is None:
                continue

            birthday = contact.birthday.date
            birthday_date = birthday_in_year(birthday, today.year)
            congratulation_date = get_congratulation_date(birthday_date)

            if congratulation_date < today:
                birthday_date = birthday_in_year(birthday, today.year + 1)
                congratulation_date = get_congratulation_date(birthday_date)

            if today <= congratulation_date <= period_end:
                result.append(
                    BirthdaysListContact(
                        name=str(contact.name),
                        birthday=birthday.strftime("%d.%m.%Y"),
                        age=str(congratulation_date.year - birthday.year),
                        congratulation_date=congratulation_date.strftime("%d.%m.%Y"),
                    )
                )

        return sorted(result, key=lambda item: item.congratulation_date)

    def _filter(self, predicate, query: str) -> list[Contact]:
        """Return contacts matching a normalized query."""
        value = self._search_key(query)
        result = [
            contact
            for contact in self._data.values()
            if value and predicate(contact, value)
        ]

        return result

    def _matches_any(self, contact: Contact, query: str) -> bool:
        """Return ``True`` if any searchable contact field matches."""
        searchable = [
            contact.name.value,
            *(item.value for item in contact.phones),
            *(str(item) for item in contact.phones),
            *(item.value for item in contact.emails),
            contact.formatted_address if contact.address is not None else "",
            str(contact.birthday) if contact.birthday is not None else "",
            contact.note if contact.note != SystemValue.EMPTY_TEXT.value else "",
            *contact.tags,
        ]
        result = any(query in self._search_key(value) for value in searchable)

        return result
