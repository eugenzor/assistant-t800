"""Message history helpers for safe replay to tool-calling models."""

from dataclasses import replace

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ToolReturnPart,
    UserPromptPart,
)

from assistant_t800.ai.results import DisplayPayload


def _is_user_turn_start(message: ModelMessage) -> bool:
    """Return whether a message begins a new user turn."""
    if not isinstance(message, ModelRequest):
        return False

    return any(isinstance(part, UserPromptPart) for part in message.parts)


def cap_message_history(
    messages: list[ModelMessage],
    max_messages: int,
) -> list[ModelMessage]:
    """Return a suffix of messages capped to ``max_messages``.

    The slice is aligned to a user-turn boundary so replayed history never
    starts with an orphaned tool return or mid-cycle model response. Gemini
    and similar providers require each function response to follow its call.
    """
    if max_messages <= 0:
        return []

    if len(messages) <= max_messages:
        return list(messages)

    start = len(messages) - max_messages
    aligned = next(
        (i for i in range(start, len(messages)) if _is_user_turn_start(messages[i])),
        len(messages),
    )
    return list(messages[aligned:])


def strip_display_metadata(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Remove UI display payloads from stored tool returns.

    Display metadata is consumed by ``apply_display`` during the same run and
    is not needed for LLM replay. Stripping it keeps stored history lightweight.
    """
    stripped: list[ModelMessage] = []

    for message in messages:
        if not isinstance(message, ModelRequest):
            stripped.append(message)
            continue

        new_parts: list[object] = []
        changed = False

        for part in message.parts:
            if isinstance(part, ToolReturnPart) and isinstance(
                part.metadata, DisplayPayload
            ):
                new_parts.append(replace(part, metadata=None))
                changed = True
            else:
                new_parts.append(part)

        if changed:
            stripped.append(replace(message, parts=new_parts))
        else:
            stripped.append(message)

    return stripped
