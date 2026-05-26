"""Structured application results."""

from dataclasses import dataclass, field
from typing import TypeAlias

from assistant_t800.localization import ErrorCode, Message

MessageParams: TypeAlias = dict[str, object]
MessageKey: TypeAlias = Message | ErrorCode


@dataclass(frozen=True)
class AppMessage:
    """Message key with template parameters for interface rendering."""

    code: MessageKey
    params: MessageParams = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfirmation:
    """Confirmation request returned by destructive operations."""

    message: AppMessage


@dataclass(frozen=True)
class AppResult:
    """Application operation result returned by command handlers."""

    success: bool
    message: AppMessage | None = None
    data: object | None = None
    should_exit: bool = False
    confirmation: AppConfirmation | None = None

    @property
    def requires_confirmation(self) -> bool:
        """Return ``True`` when the interface must ask for confirmation."""
        return self.confirmation is not None

    @classmethod
    def ok(
        cls,
        code: Message | None = None,
        *,
        data: object | None = None,
        should_exit: bool = False,
        **params: object,
    ) -> "AppResult":
        """Build a successful result."""
        message = AppMessage(code, params) if code is not None else None
        result = cls(
            success=True,
            message=message,
            data=data,
            should_exit=should_exit,
        )

        return result

    @classmethod
    def fail(
        cls,
        code: ErrorCode,
        **params: object,
    ) -> "AppResult":
        """Build a failed result."""
        result = cls(
            success=False,
            message=AppMessage(code, params),
        )

        return result

    @classmethod
    def confirm(cls, code: Message, **params: object) -> "AppResult":
        """Build a result that requires interface-level confirmation."""
        message = AppMessage(code, params)
        result = cls(
            success=False,
            message=message,
            confirmation=AppConfirmation(message=message),
        )

        return result
