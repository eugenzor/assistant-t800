"""CLI layout helpers."""

from shutil import get_terminal_size
from typing import Final
from assistant_t800.localization import ASCII_APP_LOGO

MIN_LAYOUT_WIDTH: Final[int] = 80
MAX_LAYOUT_WIDTH: Final[int] = 105
NARROW_LAYOUT_WIDTH: Final[int] = 100

DEFAULT_PAD: Final[int] = 2

_ascii_logo_with: int = 0


def is_narrow_layout() -> bool:
    return NARROW_LAYOUT_WIDTH > get_actual_width()


def get_ascii_logo_width() -> int:
    """Return actual ASCII LOGO width."""
    global _ascii_logo_with

    if not _ascii_logo_with:
        if ASCII_APP_LOGO != "":
            _ascii_logo_with = len(ASCII_APP_LOGO.split("\n")[0])

    return _ascii_logo_with


def get_actual_width() -> int:
    """Return actual application layout width."""
    terminal_width = get_terminal_size().columns
    result = max(
        MIN_LAYOUT_WIDTH,
        min(terminal_width, MAX_LAYOUT_WIDTH),
    )
    return result


def get_half_actual_width() -> int:
    """Return half application layout width."""
    result = get_actual_width() // 2

    return result


def get_half_gap_with() -> int:
    """Return half application layout width."""
    result = get_actual_width() - get_half_actual_width() * 2 + DEFAULT_PAD * 2

    return result
