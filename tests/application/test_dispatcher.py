"""Unit tests for ``CommandDispatcher`` in ``assistant_t800.application.dispatcher``."""


from assistant_t800.application.commands import Command
from assistant_t800.application.context import AppContext
from assistant_t800.application.dispatcher import CommandDispatcher
from assistant_t800.application.errors import AppError, CommandError
from assistant_t800.application.results import AppResult
from assistant_t800.localization import ErrorCode, Message
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService


def _ok_handler(context: AppContext) -> AppResult:
    """Return the parsed args dict as a successful result payload."""
    return AppResult.ok(Message.HELP, data=dict(context.args))


def _raise_app_error(context: AppContext) -> AppResult:
    """Raise an ``AppError`` to verify dispatcher error translation."""
    raise AppError(ErrorCode.CONTACT_NOT_FOUND, name="Іван")


def _raise_unexpected_error(context: AppContext) -> AppResult:
    """Raise a generic exception to verify the catch-all branch."""
    raise RuntimeError("boom")


def _registry(*commands: Command) -> dict[str, Command]:
    """Build a registry keyed by lowercase command name and aliases."""
    result: dict[str, Command] = {}

    for command in commands:
        result[command.name.lower()] = command
        for alias in command.aliases:
            result[alias.lower()] = command

    return result


def _context(registry: dict[str, Command]) -> AppContext:
    """Build an application context backed by an empty in-memory service."""
    return AppContext(
        contacts=ContactsService(ContactsRepository()),
        registry=registry,
    )


# ---------- parsing ----------


def test_dispatch_empty_input_fails_with_empty_command():
    context = _context({})
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("")

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.EMPTY_COMMAND


def test_dispatch_whitespace_only_input_fails_with_empty_command():
    context = _context({})
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("   ")

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.EMPTY_COMMAND


def test_dispatch_unbalanced_quotes_fails_with_invalid_syntax():
    context = _context({})
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch('add "Іван')

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.INVALID_COMMAND_SYNTAX


def test_dispatch_unknown_command_fails_with_unknown_command():
    context = _context({})
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("nosuch")

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.UNKNOWN_COMMAND
    assert result.message.params == {"command": "nosuch"}


# ---------- positional argument binding ----------


def test_dispatch_binds_required_args_by_name():
    command = Command(
        name="get",
        handler=_ok_handler,
        description=Message.GET_DESCRIPTION,
        args=("name",),
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("get Іван")

    assert result.success is True
    assert result.data == {"name": "Іван"}


def test_dispatch_binds_optional_args_when_provided():
    command = Command(
        name="birthdays",
        handler=_ok_handler,
        description=Message.BIRTHDAYS_DESCRIPTION,
        optional_args=("days",),
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("birthdays 10")

    assert result.data == {"days": "10"}


def test_dispatch_applies_defaults_for_missing_optional_args():
    command = Command(
        name="birthdays",
        handler=_ok_handler,
        description=Message.BIRTHDAYS_DESCRIPTION,
        optional_args=("days",),
        defaults={"days": "7"},
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("birthdays")

    assert result.data == {"days": "7"}


def test_dispatch_missing_required_args_fails_with_invalid_syntax():
    command = Command(
        name="get",
        handler=_ok_handler,
        description=Message.GET_DESCRIPTION,
        args=("name",),
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("get")

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.INVALID_COMMAND_SYNTAX


def test_dispatch_too_many_args_fails_with_invalid_syntax():
    command = Command(
        name="get",
        handler=_ok_handler,
        description=Message.GET_DESCRIPTION,
        args=("name",),
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("get Іван extra")

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.INVALID_COMMAND_SYNTAX


def test_dispatch_quoted_argument_preserves_spaces():
    command = Command(
        name="set-address",
        handler=_ok_handler,
        description=Message.SET_ADDRESS_DESCRIPTION,
        args=("name", "address"),
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch('set-address Іван "Київ, Хрещатик 1"')

    assert result.data == {"name": "Іван", "address": "Київ, Хрещатик 1"}


def test_dispatch_passes_raw_args_as_tuple():
    captured: dict[str, tuple[str, ...]] = {}

    def handler(context: AppContext) -> AppResult:
        captured["raw_args"] = context.raw_args
        return AppResult.ok()

    command = Command(
        name="add",
        handler=handler,
        description=Message.ADD_DESCRIPTION,
        parse_args=False,
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    dispatcher.dispatch("add Іван 0501234567 ivan@example.com")

    assert captured["raw_args"] == ("Іван", "0501234567", "ivan@example.com")


def test_dispatch_parse_args_false_leaves_args_empty():
    captured: dict[str, dict[str, str]] = {}

    def handler(context: AppContext) -> AppResult:
        captured["args"] = dict(context.args)
        return AppResult.ok()

    command = Command(
        name="add",
        handler=handler,
        description=Message.ADD_DESCRIPTION,
        parse_args=False,
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    dispatcher.dispatch("add Іван 0501234567")

    assert captured["args"] == {}


# ---------- multi-word and alias resolution ----------


def test_dispatch_resolves_longest_matching_command_prefix():
    short = Command(
        name="search",
        handler=_ok_handler,
        description=Message.SEARCH_DESCRIPTION,
        args=("query",),
    )
    long_form = Command(
        name="search by name",
        handler=_ok_handler,
        description=Message.SEARCH_NAME_DESCRIPTION,
        args=("query",),
    )
    context = _context(_registry(short, long_form))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("search by name Іван")

    assert result.data == {"query": "Іван"}, (
        "the longest matching command prefix must win"
    )


def test_dispatch_resolves_alias_to_command():
    command = Command(
        name="help",
        handler=_ok_handler,
        description=Message.HELP_DESCRIPTION,
        aliases=("?",),
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("?")

    assert result.success is True


def test_dispatch_is_case_insensitive_for_command_name():
    command = Command(
        name="help",
        handler=_ok_handler,
        description=Message.HELP_DESCRIPTION,
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("HELP")

    assert result.success is True


# ---------- confirmation flag ----------


def test_dispatch_propagates_confirmed_flag_to_context():
    captured: dict[str, bool] = {}

    def handler(context: AppContext) -> AppResult:
        captured["confirmed"] = context.confirmed
        return AppResult.ok()

    command = Command(
        name="remove",
        handler=handler,
        description=Message.REMOVE_DESCRIPTION,
        args=("name",),
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    dispatcher.dispatch("remove Іван", confirmed=True)

    assert captured["confirmed"] is True


def test_dispatch_defaults_confirmed_to_false():
    captured: dict[str, bool] = {}

    def handler(context: AppContext) -> AppResult:
        captured["confirmed"] = context.confirmed
        return AppResult.ok()

    command = Command(
        name="remove",
        handler=handler,
        description=Message.REMOVE_DESCRIPTION,
        args=("name",),
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    dispatcher.dispatch("remove Іван")

    assert captured["confirmed"] is False


# ---------- handler error translation ----------


def test_dispatch_translates_app_error_to_failed_result():
    command = Command(
        name="boom",
        handler=_raise_app_error,
        description=Message.HELP_DESCRIPTION,
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("boom")

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.CONTACT_NOT_FOUND
    assert result.message.params == {"name": "Іван"}


def test_dispatch_translates_unexpected_error_to_failed_result():
    command = Command(
        name="boom",
        handler=_raise_unexpected_error,
        description=Message.HELP_DESCRIPTION,
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("boom")

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.UNEXPECTED_ERROR
    assert result.message.params == {"reason": "boom"}


def test_dispatch_translates_command_error_subclass_to_failed_result():
    def handler(context: AppContext) -> AppResult:
        raise CommandError(ErrorCode.INVALID_COMMAND_SYNTAX, reason="bad")

    command = Command(
        name="boom",
        handler=handler,
        description=Message.HELP_DESCRIPTION,
    )
    context = _context(_registry(command))
    dispatcher = CommandDispatcher(context)

    result = dispatcher.dispatch("boom")

    assert result.success is False
    assert result.message is not None
    assert result.message.code is ErrorCode.INVALID_COMMAND_SYNTAX


# ---------- dispatcher context exposure ----------


def test_dispatcher_exposes_context_property():
    context = _context({})
    dispatcher = CommandDispatcher(context)

    assert dispatcher.context is context