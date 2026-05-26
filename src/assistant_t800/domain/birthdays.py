"""Birthday list projection models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BirthdaysListContact:
    """Contact data prepared for upcoming birthday rendering."""

    name: str
    birthday: str
    age: str
    congratulation_date: str
