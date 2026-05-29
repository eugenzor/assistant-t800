"""Rich inline editable field rendering."""

from typing import TYPE_CHECKING

from assistant_t800.domain.contacts import Contact
from assistant_t800.interfaces.rich.contact_card import display_contact_card
from assistant_t800.interfaces.rich.inline_hint import display_inline_hint
from assistant_t800.localization import Message

if TYPE_CHECKING:
    from assistant_t800.interfaces.cli.prompting import EditableInputFunc, TextInputFunc
    from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter


def request_note_edit(
    presenter: "RichCliPresenter",
    *,
    contact: Contact,
    current_note: str,
    text_input_func: "TextInputFunc",
) -> str | None:
    """Request multiline note text under the contact details."""
    presenter.display_results_header()
    display_contact_card(presenter, contact)
    display_inline_hint(presenter, str(Message.EDIT_NOTE_INPUT_HINT))
    result = text_input_func(
        f"{Message.EDITABLE_PROMPT} ",
        current_note,
    )

    return result


def request_tag_edit(
    presenter: "RichCliPresenter",
    *,
    contact: Contact,
    current_tags: str,
    editable_func: "EditableInputFunc",
) -> str | None:
    """Request comma-separated tags under the contact details."""
    presenter.display_results_header()
    display_contact_card(presenter, contact)
    display_inline_hint(presenter, str(Message.EDIT_TAGS_INPUT_HINT))
    result = editable_func(
        f"{Message.EDITABLE_PROMPT} ",
        current_tags,
    )

    return result
