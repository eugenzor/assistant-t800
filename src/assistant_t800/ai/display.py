"""Extract and apply display payloads from agent tool results."""

from pydantic_ai.messages import ModelMessage, ModelRequest, ToolReturnPart

from assistant_t800.ai.deps import Presenter
from assistant_t800.ai.results import DisplayPayload


def extract_display_payloads(messages: list[ModelMessage]) -> list[DisplayPayload]:
    """Collect display payloads from tool return metadata in agent messages."""
    payloads: list[DisplayPayload] = []

    for message in messages:
        if not isinstance(message, ModelRequest):
            continue

        for part in message.parts:
            if isinstance(part, ToolReturnPart) and isinstance(
                part.metadata, DisplayPayload
            ):
                payloads.append(part.metadata)

    return payloads


def apply_display(presenter: Presenter, payloads: list[DisplayPayload]) -> None:
    """Apply the last display payload to the presenter."""
    if not payloads:
        return

    payload = payloads[-1]

    if payload.kind == "contacts":
        presenter.refresh_contacts(payload.contacts or [])
    elif payload.kind == "birthdays":
        presenter.refresh_birthdays(payload.birthdays or [])
    elif payload.kind == "text":
        presenter.print(payload.text or "")
