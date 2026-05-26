"""Command dispatcher for deterministic CLI execution."""

import shlex

from assistant_t800.application.commands import Command
from assistant_t800.application.context import AppContext
from assistant_t800.application.errors import AppError, CommandError
from assistant_t800.application.results import AppResult
from assistant_t800.localization import ErrorCode


class CommandDispatcher:
    """Dispatch raw command input to registered handlers."""

    def __init__(self, context: AppContext) -> None:
        self._context = context

    @property
    def context(self) -> AppContext:
        """Return application context."""
        return self._context

    def dispatch(self, raw_input: str, *, confirmed: bool = False) -> AppResult:
        """Parse and execute one raw command line."""
        try:
            command, raw_args = self._parse_input(raw_input)
            self.context.confirmed = confirmed
            self.context.raw_args = tuple(raw_args)
            self.context.args = self._build_args(command, raw_args)
            result = command.handler(self.context)
        except AppError as error:
            result = AppResult.fail(error.code, **error.params)
        except Exception as error:
            result = AppResult.fail(
                ErrorCode.UNEXPECTED_ERROR,
                reason=str(error),
            )

        return result

    def _parse_input(self, raw_input: str) -> tuple[Command, list[str]]:
        """Split raw command line and resolve the longest matching command prefix."""
        try:
            parts = shlex.split(raw_input)
        except ValueError as error:
            raise CommandError(
                ErrorCode.INVALID_COMMAND_SYNTAX,
                reason=str(error),
            ) from error

        if not parts:
            raise CommandError(ErrorCode.EMPTY_COMMAND)

        result = self._resolve_command(parts)

        return result

    def _resolve_command(self, parts: list[str]) -> tuple[Command, list[str]]:
        """Resolve command by the longest matching name or alias prefix."""
        command: Command | None = None
        command_parts_count = 0

        for index in range(len(parts), 0, -1):
            candidate = " ".join(parts[:index]).strip().lower()
            command = self.context.registry.get(candidate)

            if command is not None:
                command_parts_count = index
                break

        if command is None:
            raise CommandError(
                ErrorCode.UNKNOWN_COMMAND,
                command=parts[0].strip().lower(),
            )

        result = command, parts[command_parts_count:]

        return result

    @staticmethod
    def _build_args(command: Command, raw_args: list[str]) -> dict[str, str]:
        """Map positional arguments to command argument names."""
        if not command.parse_args:
            result: dict[str, str] = {}
        else:
            min_args = len(command.args)
            max_args = min_args + len(command.optional_args)

            if not min_args <= len(raw_args) <= max_args:
                raise CommandError(
                    ErrorCode.INVALID_COMMAND_SYNTAX,
                    command=command.name,
                    syntax=command.syntax,
                )

            arg_names = (*command.args, *command.optional_args)
            result = {
                **command.defaults,
                **dict(zip(arg_names, raw_args, strict=False)),
            }

        return result
