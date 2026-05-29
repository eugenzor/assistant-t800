"""Rich inline edit hint bar rendering."""

from typing import TYPE_CHECKING

from rich import box

from assistant_t800.interfaces.cli.metrics import get_actual_width

if TYPE_CHECKING:
    from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter


def display_inline_hint(
    presenter: "RichCliPresenter",
    text: str,
) -> None:
    """Display one-line hint bar for inline editors."""
    presenter.console.print(
        presenter.panel_cls(
            presenter.text_cls(
                text.replace("\n", "   "),
                style="grey50",
                no_wrap=True,
                overflow="ellipsis",
            ),
            box=box.SQUARE,
            border_style="grey50",
            style="white",
            padding=(0, 1),
            width=get_actual_width(),
        )
    )
