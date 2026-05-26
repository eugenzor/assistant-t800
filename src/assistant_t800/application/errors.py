"""Application exceptions with structured error codes."""

from assistant_t800.localization import ErrorCode


class AppError(Exception):
    """Base application error with UI-renderable metadata."""

    def __init__(self, code: ErrorCode, **params: object) -> None:
        self.code = code
        self.params = params
        super().__init__(code.name)


class CommandError(AppError):
    """Command parsing or dispatching error."""
