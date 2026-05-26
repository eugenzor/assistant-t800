"""Application command definitions."""

from collections.abc import Callable
from dataclasses import dataclass, field

from assistant_t800.application.context import AppContext
from assistant_t800.application.results import AppResult
from assistant_t800.localization import Message

Handler = Callable[[AppContext], AppResult]


@dataclass(frozen=True)
class Command:
    """Command metadata and handler binding."""

    name: str
    handler: Handler
    description: Message
    args: tuple[str, ...] = ()
    optional_args: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    defaults: dict[str, str] = field(default_factory=dict)
    usage: str | None = None
    parse_args: bool = True

    @property
    def syntax(self) -> str:
        """Return human-readable command syntax."""
        if self.usage is not None:
            result = self.usage
        else:
            required = (f"<{arg}>" for arg in self.args)
            optional = (f"[{arg}]" for arg in self.optional_args)
            result = " ".join((self.name, *required, *optional)).strip()

        return result
