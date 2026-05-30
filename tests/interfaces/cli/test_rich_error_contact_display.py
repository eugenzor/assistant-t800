"""Tests for Rich presenter showing contact context after mutation errors."""

from dataclasses import dataclass, field

from assistant_t800.application.results import AppResult
from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter
from assistant_t800.localization import ErrorCode


@dataclass
class FakeFallback:
    """Fallback presenter stub."""

    displayed: list[AppResult] = field(default_factory=list)

    def display(self, result: AppResult) -> None:
        self.displayed.append(result)

    def display_goodbye(self) -> None:
        pass


def test_rich_presenter_displays_contact_card_for_error_payload():
    presenter = RichCliPresenter(FakeFallback())
    contact = Contact(Name("John"))
    result = AppResult.fail(
        ErrorCode.VALIDATION_ERROR,
        data=contact,
        reason="Invalid value",
    )

    presenter.display(result)
