"""Rich header rendering."""

from typing import TYPE_CHECKING

from rich.console import Group

from assistant_t800.interfaces.cli.metrics import (
    get_actual_width,
    get_ascii_logo_width,
    DEFAULT_PAD,
)
from assistant_t800.localization import APP_VERSION, ASCII_APP_LOGO, Message

if TYPE_CHECKING:
    from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter


def display_welcome_header(presenter: "RichCliPresenter") -> None:
    """Display Rich welcome header."""
    presenter.clear()

    header_width = get_actual_width()
    logo_width = get_ascii_logo_width()
    title_width = header_width - logo_width - header_width // 8

    header = presenter.table_cls.grid(padding=(0, DEFAULT_PAD))
    header.add_column(no_wrap=True, width=logo_width)
    header.add_column(width=title_width)

    title = Group(
        presenter.text_cls(),
        presenter.text_cls(
            str(Message.WELCOME_TITLE),
            justify="center",
            style="bold green",
        ),
        presenter.text_cls(""),
        presenter.text_cls(
            str(Message.WELCOME_SUBTITLE),
            justify="center",
            style="white",
        ),
        presenter.text_cls("\n\n"),
        presenter.text_cls(
            f"v. {APP_VERSION}",
            justify="right",
            style="dim",
        ),
    )

    header.add_row(
        presenter.text_cls(ASCII_APP_LOGO, style="bold green"),
        title,
    )

    presenter.console.print(
        presenter.panel_cls(
            header,
            border_style="green",
            width=header_width,
        ),
        presenter.text_cls(""),
    )


def display_results_header(presenter: "RichCliPresenter") -> None:
    """Display compact Rich results header."""
    presenter.clear()

    header = presenter.table_cls.grid(expand=True)
    header.add_column(ratio=1)
    header.add_column(justify="right", no_wrap=True)

    version = f"v. {APP_VERSION}"

    header.add_row(
        presenter.text_cls(
            " " * len(version) + f"{Message.WELCOME_TITLE}",
            style="bold green",
            justify="center",
        ),
        presenter.text_cls(
            version,
            style="dim",
        ),
    )

    presenter.console.print(
        presenter.panel_cls(
            header,
            border_style="green",
            width=get_actual_width(),
            padding=(0, 1),
        ),
        presenter.text_cls(""),
    )


def display_results_title(
    presenter: "RichCliPresenter",
    text: str | Message,
) -> None:
    """Display command execution results title."""

    container = presenter.table_cls.grid()
    container.add_column(width=get_actual_width())

    container.add_row(
        presenter.text_cls(
            f"{str(text).upper()}",
            style="bold cyan",
            justify="center",
        )
    )

    presenter.console.print(container, presenter.text_cls(""))
