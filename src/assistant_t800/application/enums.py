"""Application-level enums and system constants."""

from enum import Enum


class SystemValue(Enum):
    """Shared low-level system values."""

    EMPTY_TEXT = "\u200b"
    MULTI_VALUE_SEPARATORS = ";,"
    DATE_VALUE_SEPARATORS = "-/."


class InterfaceMode(Enum):
    """Supported application interface modes."""

    CLI = "cli"
    TUI = "tui"
