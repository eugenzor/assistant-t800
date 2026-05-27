"""Unit tests for ``CommandRegistry`` in ``assistant_t800.suggestions.registry``."""

from dataclasses import dataclass

from assistant_t800.suggestions.models import CommandInfo
from assistant_t800.suggestions.registry import CommandRegistry


@dataclass
class _FakeForeignCommand:
    """Foreign command stand-in for ``from_mapping`` tests."""

    name: str
    description: str = ""
    syntax: str = ""
    args: tuple[str, ...] = ()
    optional_args: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()


# ---------- add / get ----------


def test_add_stores_command_metadata():
    registry = CommandRegistry()

    registry.add(
        name="help",
        description="Show help",
        syntax="help",
        aliases=("?",),
    )

    command = registry.get("help")
    assert command is not None
    assert command.name == "help"
    assert command.description == "Show help"
    assert command.aliases == ("?",)


def test_add_returns_self_for_chaining():
    registry = CommandRegistry()

    result = registry.add(name="help").add(name="exit")

    assert result is registry
    assert registry.get("help") is not None
    assert registry.get("exit") is not None


def test_get_is_case_insensitive():
    registry = CommandRegistry()
    registry.add(name="Help")

    assert registry.get("HELP") is not None
    assert registry.get("help") is not None


def test_get_returns_none_for_unknown_command():
    registry = CommandRegistry()

    assert registry.get("nosuch") is None


def test_add_strips_and_normalizes_lookup_key():
    registry = CommandRegistry()
    registry.add(name="  Help  ")

    assert registry.get("help") is not None


def test_add_defaults_args_and_optional_args_to_empty_tuples():
    registry = CommandRegistry()

    registry.add(name="help")

    command = registry.get("help")
    assert command is not None
    assert command.args == ()
    assert command.optional_args == ()
    assert command.aliases == ()


# ---------- extend ----------


def test_extend_adds_many_commands():
    registry = CommandRegistry()
    commands = [
        CommandInfo(name="help"),
        CommandInfo(name="exit"),
    ]

    registry.extend(commands)

    assert registry.get("help") is not None
    assert registry.get("exit") is not None


def test_extend_overwrites_existing_command():
    registry = CommandRegistry()
    registry.add(name="help", description="old")

    registry.extend([CommandInfo(name="help", description="new")])

    command = registry.get("help")
    assert command is not None
    assert command.description == "new"


# ---------- all / names ----------


def test_all_returns_empty_for_empty_registry():
    assert CommandRegistry().all() == ()


def test_all_returns_all_commands_in_insertion_order():
    registry = CommandRegistry()
    registry.add(name="help").add(name="exit")

    all_commands = registry.all()

    assert [command.name for command in all_commands] == ["help", "exit"]


def test_names_returns_registered_names():
    registry = CommandRegistry()
    registry.add(name="help").add(name="exit")

    assert registry.names() == ("help", "exit")


# ---------- from_mapping ----------


def test_from_mapping_builds_registry_from_foreign_commands():
    foreign_commands = {
        "help": _FakeForeignCommand(
            name="help",
            description="Show help",
            syntax="help",
            aliases=("?",),
        ),
        "exit": _FakeForeignCommand(name="exit", description="Quit"),
    }

    registry = CommandRegistry.from_mapping(foreign_commands)

    help_command = registry.get("help")
    assert help_command is not None
    assert help_command.description == "Show help"
    assert help_command.aliases == ("?",)
    exit_command = registry.get("exit")
    assert exit_command is not None
    assert exit_command.description == "Quit"


def test_from_mapping_uses_custom_text_getters():
    foreign_commands = {"help": object()}

    registry = CommandRegistry.from_mapping(
        foreign_commands,
        name=lambda _: "help",
        description=lambda _: "Show help",
    )

    command = registry.get("help")
    assert command is not None
    assert command.description == "Show help"


def test_from_mapping_uses_custom_iterable_getters():
    foreign_commands = {"help": object()}

    registry = CommandRegistry.from_mapping(
        foreign_commands,
        name=lambda _: "help",
        aliases=lambda _: ("?", "h"),
    )

    command = registry.get("help")
    assert command is not None
    assert command.aliases == ("?", "h")


def test_from_mapping_falls_back_to_mapping_key_when_attribute_missing():
    """When the foreign command has no ``name`` attribute, the mapping key is used."""
    foreign_commands = {"help": object()}

    registry = CommandRegistry.from_mapping(foreign_commands)

    command = registry.get("help")
    assert command is not None
    assert command.name == "help"


def test_from_mapping_defaults_syntax_to_resolved_name():
    """Without a ``syntax`` attribute, syntax defaults to the resolved name."""
    foreign_commands = {"help": _FakeForeignCommand(name="help")}

    registry = CommandRegistry.from_mapping(foreign_commands)

    command = registry.get("help")
    assert command is not None
    assert command.syntax == "help"