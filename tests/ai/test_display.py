"""Unit tests for display-payload helpers in ``assistant_t800.ai.display``."""

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolReturnPart,
    UserPromptPart,
)

from assistant_t800.ai.display import apply_display, extract_display_payloads
from assistant_t800.ai.results import DisplayPayload
from assistant_t800.domain.birthdays import BirthdaysListContact
from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name


def _tool_return_request(metadata: object) -> ModelRequest:
    """Build a ``ModelRequest`` that carries a tool return with given metadata."""
    return ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name="any",
                content="ok",
                tool_call_id="call-1",
                metadata=metadata,
            )
        ]
    )


# ---------- extract_display_payloads ----------


def test_extract_display_payloads_collects_in_order():
    first = DisplayPayload(kind="contacts", contacts=[])
    second = DisplayPayload(kind="text", text="hello")
    messages = [_tool_return_request(first), _tool_return_request(second)]

    payloads = extract_display_payloads(messages)

    assert payloads == [first, second]


def test_extract_display_payloads_ignores_non_model_requests():
    payload = DisplayPayload(kind="text", text="hello")
    messages = [
        ModelResponse(parts=[TextPart(content="ok")]),
        _tool_return_request(payload),
    ]

    payloads = extract_display_payloads(messages)

    assert payloads == [payload]


def test_extract_display_payloads_skips_non_display_metadata():
    messages = [_tool_return_request({"not": "a payload"})]

    assert extract_display_payloads(messages) == []


def test_extract_display_payloads_skips_user_prompt_parts():
    messages = [ModelRequest(parts=[UserPromptPart(content="hi")])]

    assert extract_display_payloads(messages) == []


def test_extract_display_payloads_returns_empty_for_empty_input():
    assert extract_display_payloads([]) == []


# ---------- apply_display ----------


def test_apply_display_no_payloads_is_a_no_op(presenter):
    apply_display(presenter, [])

    assert presenter.refresh_calls == []
    assert presenter.refresh_birthdays_calls == []
    assert presenter.print_calls == []


def test_apply_display_uses_last_payload_only(presenter):
    earlier = DisplayPayload(kind="text", text="earlier")
    later = DisplayPayload(kind="text", text="later")

    apply_display(presenter, [earlier, later])

    assert presenter.print_calls == ["later"], (
        "only the most recent payload must be applied"
    )


def test_apply_display_contacts_refreshes_contact_panel(presenter):
    contact = Contact(Name("Іван"))
    payload = DisplayPayload(kind="contacts", contacts=[contact])

    apply_display(presenter, [payload])

    assert presenter.refresh_calls == [[contact]]
    assert presenter.refresh_contact_calls == []
    assert presenter.refresh_birthdays_calls == []
    assert presenter.print_calls == []


def test_apply_display_contact_refreshes_contact_card(presenter):
    contact = Contact(Name("Іван"))
    payload = DisplayPayload(kind="contact", contact=contact)

    apply_display(presenter, [payload])

    assert presenter.refresh_contact_calls == [contact]
    assert presenter.refresh_calls == []
    assert presenter.refresh_birthdays_calls == []
    assert presenter.print_calls == []


def test_apply_display_contacts_with_none_collection_passes_empty_list(presenter):
    payload = DisplayPayload(kind="contacts", contacts=None)

    apply_display(presenter, [payload])

    assert presenter.refresh_calls == [[]]


def test_apply_display_birthdays_refreshes_birthdays_panel(presenter):
    record = BirthdaysListContact(
        name="Іван",
        birthday="01.01.1990",
        age="36",
        congratulation_date="01.01.2026",
    )
    payload = DisplayPayload(kind="birthdays", birthdays=[record])

    apply_display(presenter, [payload])

    assert presenter.refresh_birthdays_calls == [[record]]
    assert presenter.refresh_calls == []


def test_apply_display_birthdays_with_none_collection_passes_empty_list(presenter):
    payload = DisplayPayload(kind="birthdays", birthdays=None)

    apply_display(presenter, [payload])

    assert presenter.refresh_birthdays_calls == [[]]


def test_apply_display_text_prints_value(presenter):
    payload = DisplayPayload(kind="text", text="hello")

    apply_display(presenter, [payload])

    assert presenter.print_calls == ["hello"]


def test_apply_display_text_none_falls_back_to_empty_string(presenter):
    payload = DisplayPayload(kind="text", text=None)

    apply_display(presenter, [payload])

    assert presenter.print_calls == [""]
