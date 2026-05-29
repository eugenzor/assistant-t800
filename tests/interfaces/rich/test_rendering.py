"""Unit tests for shared Rich renderers."""

from assistant_t800.application.results import AppResult, ResultStatus
from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.interfaces.cli.presenter import CliPresenter
from assistant_t800.interfaces.rich.birthdays import (
    is_birthdays_list,
)
from assistant_t800.interfaces.rich.contact_card import build_contact_panel, is_contact
from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter
from assistant_t800.localization import Message


def test_contact_card_detection_accepts_contact_only():
    contact = Contact(Name("John Smith"))

    assert is_contact(contact) is True
    assert is_contact([contact]) is False


def test_build_contact_panel_includes_contact_name():
    from rich.panel import Panel
    from rich.text import Text

    contact = Contact(Name("Alice"))

    panel = build_contact_panel(
        panel_cls=Panel,
        text_cls=Text,
        contact=contact,
        width=80,
    )

    assert isinstance(panel, Panel)
    assert "Alice" in panel.renderable.plain


def test_birthdays_list_detection_accepts_birthday_projection_only():
    birthdays = [
        BirthdaysListContact(
            name="Alice",
            birthday="29.05.2010",
            age="16",
            congratulation_date="29.05.2026",
        )
    ]

    assert is_birthdays_list(birthdays) is True
    assert is_birthdays_list([Contact(Name("Alice"))]) is False


def test_successful_contact_found_does_not_need_separate_status_panel():
    presenter = RichCliPresenter(CliPresenter())
    contact = Contact(Name("Аліса"))
    result = AppResult.ok(
        Message.CONTACT_FOUND,
        data=contact,
        name="Аліса",
    )

    assert (
        presenter._should_display_status(
            result,
            is_list=False,
            is_birthdays=False,
        )
        is False
    )


def test_successful_contact_update_with_data_keeps_status_panel():
    presenter = RichCliPresenter(CliPresenter())
    contact = Contact(Name("John Smith"))
    result = AppResult.ok(
        Message.CONTACT_UPDATED,
        data=contact,
        name="John Smith",
    )

    assert (
        presenter._should_display_status(
            result,
            is_list=False,
            is_birthdays=False,
        )
        is True
    )


def test_successful_birthdays_list_does_not_need_separate_status_panel():
    presenter = RichCliPresenter(CliPresenter())
    result = AppResult.ok(
        Message.BIRTHDAYS_FOUND,
        data=[
            BirthdaysListContact(
                name="Alice",
                birthday="29.05.2010",
                age="16",
                congratulation_date="29.05.2026",
            )
        ],
        days=7,
    )

    assert (
        presenter._should_display_status(
            result,
            is_list=False,
            is_birthdays=True,
        )
        is False
    )


def test_warning_result_keeps_status_panel():
    presenter = RichCliPresenter(CliPresenter())
    result = AppResult.warning(Message.OPERATION_CANCELLED)

    assert result.status is ResultStatus.WARNING
    assert (
        presenter._should_display_status(
            result,
            is_list=False,
            is_birthdays=False,
        )
        is True
    )
