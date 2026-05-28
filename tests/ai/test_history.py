"""Unit tests for message-history helpers in ``assistant_t800.ai.history``."""

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolReturnPart,
    UserPromptPart,
)

from assistant_t800.ai.history import cap_message_history, strip_display_metadata
from assistant_t800.ai.results import DisplayPayload


def _user_turn(prompt: str = "hi") -> ModelRequest:
    """Build a ``ModelRequest`` that begins a user turn."""
    return ModelRequest(parts=[UserPromptPart(content=prompt)])


def _tool_return_turn(
    *,
    tool_name: str = "list_contacts",
    metadata: object = None,
) -> ModelRequest:
    """Build a ``ModelRequest`` that carries a tool return (not a user prompt)."""
    return ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name=tool_name,
                content="ok",
                tool_call_id="call-1",
                metadata=metadata,
            )
        ]
    )


def _assistant_response() -> ModelResponse:
    """Build a plain assistant response."""
    return ModelResponse(parts=[TextPart(content="ok")])


# ---------- cap_message_history ----------


def test_cap_message_history_zero_max_returns_empty():
    messages = [_user_turn(), _assistant_response()]

    assert cap_message_history(messages, max_messages=0) == []


def test_cap_message_history_negative_max_returns_empty():
    messages = [_user_turn(), _assistant_response()]

    assert cap_message_history(messages, max_messages=-1) == []


def test_cap_message_history_below_limit_returns_all_messages():
    messages = [_user_turn(), _assistant_response()]

    result = cap_message_history(messages, max_messages=10)

    assert result == messages


def test_cap_message_history_returns_a_list_copy_below_limit():
    messages = [_user_turn(), _assistant_response()]

    result = cap_message_history(messages, max_messages=10)

    assert result is not messages, "cap must return a fresh list, not the input"


def test_cap_message_history_aligns_to_user_turn_boundary():
    messages = [
        _user_turn("first"),
        _assistant_response(),
        _tool_return_turn(),
        _user_turn("second"),
        _assistant_response(),
        _tool_return_turn(),
    ]

    result = cap_message_history(messages, max_messages=3)

    # First retained message must begin a user turn
    assert isinstance(result[0], ModelRequest)
    assert any(isinstance(part, UserPromptPart) for part in result[0].parts), (
        "the suffix must start at a user-turn boundary"
    )


def test_cap_message_history_aligned_to_first_user_turn_in_window():
    third = _user_turn("third")
    messages = [
        _user_turn("first"),
        _assistant_response(),
        _tool_return_turn(),
        third,
        _assistant_response(),
    ]

    result = cap_message_history(messages, max_messages=3)

    assert result[0] is third


def test_cap_message_history_returns_empty_when_no_user_turn_in_window():
    messages = [
        _user_turn("first"),
        _assistant_response(),
        _assistant_response(),
        _assistant_response(),
        _tool_return_turn(),
    ]

    result = cap_message_history(messages, max_messages=2)

    assert result == [], (
        "without a user-turn boundary in the suffix, the result must be empty"
    )


# ---------- strip_display_metadata ----------


def test_strip_display_metadata_removes_display_payload():
    payload = DisplayPayload(kind="text", text="hello")
    messages = [_tool_return_turn(metadata=payload)]

    stripped = strip_display_metadata(messages)

    assert isinstance(stripped[0], ModelRequest)
    parts = stripped[0].parts
    assert any(isinstance(part, ToolReturnPart) for part in parts)
    tool_return = next(part for part in parts if isinstance(part, ToolReturnPart))
    assert tool_return.metadata is None


def test_strip_display_metadata_preserves_non_display_metadata():
    messages = [_tool_return_turn(metadata={"custom": "value"})]

    stripped = strip_display_metadata(messages)

    tool_return = next(
        part for part in stripped[0].parts if isinstance(part, ToolReturnPart)
    )
    assert tool_return.metadata == {"custom": "value"}, (
        "only DisplayPayload metadata must be stripped"
    )


def test_strip_display_metadata_passes_through_non_model_requests():
    response = _assistant_response()
    messages = [response]

    stripped = strip_display_metadata(messages)

    assert stripped == [response]


def test_strip_display_metadata_returns_original_message_when_no_changes():
    """Unchanged messages must not be rebuilt unnecessarily."""
    messages = [_user_turn("hi"), _assistant_response()]

    stripped = strip_display_metadata(messages)

    assert stripped[0] is messages[0]
    assert stripped[1] is messages[1]


def test_strip_display_metadata_preserves_other_parts_in_same_request():
    payload = DisplayPayload(kind="text", text="hello")
    user_part = UserPromptPart(content="hi")
    request = ModelRequest(
        parts=[
            user_part,
            ToolReturnPart(
                tool_name="list_contacts",
                content="ok",
                tool_call_id="call-1",
                metadata=payload,
            ),
        ]
    )

    stripped = strip_display_metadata([request])

    parts = stripped[0].parts
    assert any(part is user_part for part in parts), (
        "non-tool-return parts must be preserved unchanged"
    )


def test_strip_display_metadata_returns_empty_for_empty_input():
    assert strip_display_metadata([]) == []