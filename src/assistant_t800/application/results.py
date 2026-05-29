"""Structured application results."""

from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import TypeAlias

from assistant_t800.localization import ErrorCode, Message

MessageParams: TypeAlias = dict[str, object]
MessageKey: TypeAlias = Message | ErrorCode


class ResultStatus(StrEnum):
    """Application result status."""

    SUCCESS = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()


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
    status: ResultStatus = ResultStatus.SUCCESS

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
            status=ResultStatus.SUCCESS,
        )

        return result

    @classmethod
    def fail(
        cls,
        code: ErrorCode,
        *,
        data: object | None = None,
        **params: object,
    ) -> "AppResult":
        """Build a failed result."""
        result = cls(
            success=False,
            message=AppMessage(code, params),
            data=data,
            status=ResultStatus.ERROR,
        )

        return result

    @classmethod
    def info(
        cls,
        code: Message | ErrorCode,
        *,
        data: object | None = None,
        **params: object,
    ) -> "AppResult":
        """Build informational result."""
        result = cls(
            success=False,
            message=AppMessage(code, params),
            data=data,
            status=ResultStatus.INFO,
        )

        return result

    @classmethod
    def warning(
        cls,
        code: Message | ErrorCode,
        *,
        data: object | None = None,
        **params: object,
    ) -> "AppResult":
        """Build warning result."""
        result = cls(
            success=False,
            message=AppMessage(code, params),
            data=data,
            status=ResultStatus.WARNING,
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
            status=ResultStatus.WARNING,
        )

        return result
