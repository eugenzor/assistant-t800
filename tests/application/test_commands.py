"""Unit tests for command metadata in ``assistant_t800.application.commands``."""

from assistant_t800.application.commands import Command
from assistant_t800.application.context import AppContext
from assistant_t800.application.results import AppResult
from assistant_t800.localization import Message


def _noop_handler(context: AppContext) -> AppResult:
    """Return an empty successful result for handler stub purposes."""
    return AppResult.ok()


# ---------- syntax ----------


def test_syntax_without_args_returns_command_name():
    command = Command(
        name="exit",
        handler=_noop_handler,
        description=Message.EXIT_DESCRIPTION,
    )

    assert command.syntax == "exit"


def test_syntax_renders_required_args_in_angle_brackets():
    command = Command(
        name="get",
        handler=_noop_handler,
        description=Message.GET_DESCRIPTION,
        args=("name",),
    )

    assert command.syntax == "get <name>"


def test_syntax_renders_optional_args_in_square_brackets():
    command = Command(
        name="remove-phone",
        handler=_noop_handler,
        description=Message.REMOVE_PHONE_DESCRIPTION,
        args=("name",),
        optional_args=("phone",),
    )

    assert command.syntax == "remove-phone <name> [phone]"


def test_syntax_uses_explicit_usage_override():
    command = Command(
        name="add",
        handler=_noop_handler,
        description=Message.ADD_DESCRIPTION,
        usage="add <name> [phone] [email] [address] [birthday]",
    )

    assert command.syntax == "add <name> [phone] [email] [address] [birthday]"