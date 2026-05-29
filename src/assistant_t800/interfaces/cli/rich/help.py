"""Rich help screen rendering."""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Final

from rich.console import Group

from assistant_t800.application.commands import Command
from assistant_t800.interfaces.cli.metrics import (
    get_actual_width,
    get_half_actual_width,
    is_narrow_layout,
    DEFAULT_PAD,
)
from assistant_t800.localization import Message

if TYPE_CHECKING:
    from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter

CONTACT_EXCLUDED_TAGS: Final[tuple[str, ...]] = (
    "note",
    "tag",
    "birthdays",
    "help",
    "exit",
)
NOTES_TAGS: Final[tuple[str, ...]] = ("note", "tag")
BIRTHDAYS_TAGS: Final[tuple[str, ...]] = ("birthdays",)
OTHER_TAGS: Final[tuple[str, ...]] = ("help", "exit")


def display_help(
    presenter: "RichCliPresenter",
    registry: dict[str, Command],
) -> None:
    """Display Rich command help."""
    presenter.display_results_header()
    presenter.display_results_title(Message.HELP)
    presenter.console.print(build_help_view(presenter, registry))


def build_help_view(
    presenter: "RichCliPresenter",
    registry: dict[str, Command],
) -> Group:
    """Build adaptive Rich command help view."""
    actual_width = get_actual_width()
    contacts = _build_help_panel(
        presenter=presenter,
        title=str(Message.HELP_CONTACTS),
        commands=_filter_commands(registry, tags_ex=CONTACT_EXCLUDED_TAGS),
        width=actual_width,
    )

    if is_narrow_layout():
        result = Group(
            contacts,
            _build_help_panel(
                presenter=presenter,
                title=str(Message.HELP_NOTES),
                commands=_filter_commands(registry, tags_in=NOTES_TAGS),
                width=actual_width,
            ),
            _build_help_panel(
                presenter=presenter,
                title=str(Message.HELP_BIRTHDAYS),
                commands=_filter_commands(registry, tags_in=BIRTHDAYS_TAGS),
                width=actual_width,
            ),
            _build_help_panel(
                presenter=presenter,
                title=str(Message.HELP_OTHER),
                commands=_filter_commands(registry, tags_in=OTHER_TAGS),
                width=actual_width,
            ),
        )
    else:
        result = _build_two_column_help(
            presenter=presenter,
            contacts=contacts,
            registry=registry,
        )

    return result


def _build_two_column_help(
    *,
    presenter: "RichCliPresenter",
    contacts,
    registry: dict[str, Command],
) -> Group:
    """Build two-column Rich help layout."""
    half_width = get_half_actual_width()
    bottom = presenter.table_cls.grid(padding=(0, 1))
    bottom.add_column(width=half_width)
    bottom.add_column(width=half_width)

    right = Group(
        _build_help_panel(
            presenter=presenter,
            title=str(Message.HELP_BIRTHDAYS),
            commands=_filter_commands(registry, tags_in=BIRTHDAYS_TAGS),
            width=half_width,
        ),
        presenter.text_cls(""),
        _build_help_panel(
            presenter=presenter,
            title=str(Message.HELP_OTHER),
            commands=_filter_commands(registry, tags_in=OTHER_TAGS),
            width=half_width,
        ),
    )

    bottom.add_row(
        _build_help_panel(
            presenter=presenter,
            title=str(Message.HELP_NOTES),
            commands=_filter_commands(registry, tags_in=NOTES_TAGS),
            width=half_width,
        ),
        right,
    )

    result = Group(
        contacts,
        bottom,
    )

    return result


def _filter_commands(
    registry: dict[str, Command],
    *,
    tags_in: tuple[str, ...] = (),
    tags_ex: tuple[str, ...] = (),
) -> tuple[Command, ...]:
    """Return unique commands filtered by command-name tags."""
    seen: set[str] = set()

    if tags_in:
        result = tuple(
            command
            for command in registry.values()
            if any(tag in command.name for tag in tags_in)
            and command.name not in seen
            and not seen.add(command.name)
        )
    elif tags_ex:
        result = tuple(
            command
            for command in registry.values()
            if not any(tag in command.name for tag in tags_ex)
            and command.name not in seen
            and not seen.add(command.name)
        )
    else:
        result = tuple(
            command
            for command in registry.values()
            if command.name not in seen and not seen.add(command.name)
        )

    return result


def _build_help_panel(
    *,
    presenter: "RichCliPresenter",
    title: str,
    commands: Iterable[Command],
    width: int,
):
    """Build one Rich command help panel."""
    command_rows = tuple(
        (command.syntax, command.description.text) for command in commands
    )
    command_width = max((len(syntax) for syntax, _ in command_rows), default=0)

    table = presenter.table_cls.grid(padding=(0, DEFAULT_PAD))
    table.add_column(no_wrap=False, width=command_width)
    table.add_column(width=max(width - command_width - 6, 20))

    for syntax, description in command_rows:
        table.add_row(
            presenter.text_cls(syntax, style="bold green"),
            presenter.text_cls(description, style="white"),
        )

    result = presenter.panel_cls(
        table,
        title=presenter.text_cls(title, style="bold cyan"),
        border_style="dim",
        width=width,
        padding=(0, 1),
    )

    return result
