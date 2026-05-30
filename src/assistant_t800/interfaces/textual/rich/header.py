"""Rich welcome header rendering for the Textual interface."""

from rich.console import Group

from assistant_t800.interfaces.cli.metrics import DEFAULT_PAD, get_ascii_logo_width
from assistant_t800.localization.messages import APP_VERSION, ASCII_APP_LOGO


def build_welcome_header(*, text_cls, table_cls, width: int):
    """Build the welcome header sized to ``width``.

    ``text_cls`` and ``table_cls`` are the Rich ``Text`` and ``Table`` classes,
    injected by the caller so this module stays decoupled from any presenter.
    Rendered without a surrounding panel/border.
    """
    logo_width = get_ascii_logo_width()
    title_width = max(1, width - logo_width - width // 8)

    header = table_cls.grid(padding=(0, DEFAULT_PAD))
    header.add_column(no_wrap=True, width=logo_width)
    header.add_column(width=title_width)

    title = Group(
        text_cls(),
        text_cls(
            "ASSISTANT T800",
            justify="center",
            style="bold green",
        ),
        text_cls(""),
        text_cls(
            "Персональний CLI асистент\nдля контактів, нотаток та тегів",
            justify="center",
            style="white",
        ),
        text_cls("\n\n"),
        text_cls(
            f"v. {APP_VERSION}",
            justify="right",
            style="dim",
        ),
    )

    header.add_row(
        text_cls(ASCII_APP_LOGO, style="bold green"),
        title,
    )

    return header
