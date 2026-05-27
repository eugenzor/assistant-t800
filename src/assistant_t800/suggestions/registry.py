from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Self

from assistant_t800.suggestions.models import CommandInfo

TextGetter = Callable[[Any], str]
IterTextGetter = Callable[[Any], Iterable[str]]


@dataclass
class CommandRegistry:
    """Portable command registry for suggestion engines."""

    _commands: dict[str, CommandInfo] = field(default_factory=dict)

    def add(
        self,
        name: str,
        description: str = "",
        syntax: str = "",
        args: Iterable[str] | None = None,
        optional_args: Iterable[str] | None = None,
        aliases: Iterable[str] | None = None,
    ) -> Self:
        """Add command metadata."""
        command = CommandInfo(
            name=name,
            description=description,
            syntax=syntax,
            args=tuple(args or ()),
            optional_args=tuple(optional_args or ()),
            aliases=tuple(aliases or ()),
        )

        self._commands[self._normalize(name)] = command

        return self

    def extend(
        self,
        commands: Iterable[CommandInfo],
    ) -> Self:
        """Add many command metadata objects."""
        for command in commands:
            self._commands[self._normalize(command.name)] = command

        return self

    def get(
        self,
        name: str,
    ) -> CommandInfo | None:
        """Return command by name."""
        return self._commands.get(
            self._normalize(name),
        )

    def all(self) -> tuple[CommandInfo, ...]:
        """Return all registered commands."""
        # type: ignore[arg-type]
        return tuple(self._commands.values())

    def names(self) -> tuple[str, ...]:
        """Return registered command names."""
        return tuple(command.name for command in self._commands.values())

    @classmethod
    def from_mapping(
        cls,
        registry: Mapping[str, Any],
        **getters: TextGetter | IterTextGetter,
    ) -> Self:
        """Build portable registry from foreign command mapping.

        Supported getter keys:
            name: Return command name as string.
            description: Return command description as string.
            syntax: Return command syntax as string.
            args: Return required command arguments.
            optional_args: Return optional command arguments.
            aliases: Return alternative command phrases.

        Missing getters fallback to matching command attributes.
        """
        result = cls()
        field_types = {
            "name": "text",
            "description": "text",
            "syntax": "text",
            "args": "iter",
            "optional_args": "iter",
            "aliases": "iter",
        }

        for key, command in registry.items():
            data: dict[str, str | tuple[str, ...]] = {}

            for field_name, field_type in field_types.items():
                getter = getters.get(field_name)
                default = (
                    str(key)
                    if field_name == "name"
                    else data["name"]
                    if field_name == "syntax"
                    else ""
                    if field_type == "text"
                    else ()
                )
                value = (
                    getter(command)
                    if getter is not None
                    else getattr(command, field_name, default)
                )

                if field_name == "syntax" and not value:
                    value = data["name"]

                data[field_name] = (
                    tuple(str(item) for item in value)
                    if field_type == "iter"
                    else str(value)
                )
            result.add(**data)

        return result

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize command lookup key."""
        return value.strip().casefold()
