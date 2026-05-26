from dataclasses import dataclass, field
from enum import Enum, auto


class SuggestionSource(Enum):
    """Suggestion source type."""

    EXACT = auto()
    FUZZY = auto()
    AI = auto()


@dataclass(frozen=True)
class CommandInfo:
    """Portable command metadata for suggestions."""

    name: str
    description: str = ""
    syntax: str = ""
    args: tuple[str, ...] = ()
    optional_args: tuple[str, ...] = ()
    aliases: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CommandSuggestion:
    """Suggested command candidate."""

    command: CommandInfo
    score: float
    source: SuggestionSource
    matched_by: str = ""
    reason: str = ""
    suggested_input: str = ""


@dataclass(frozen=True)
class SuggestionResult:
    """Command suggestion result."""

    understood: bool
    command: CommandInfo | None = None
    suggestions: tuple[CommandSuggestion, ...] = ()
