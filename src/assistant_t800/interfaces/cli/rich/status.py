"""Rich status rendering."""

from typing import TYPE_CHECKING

from assistant_t800.application.results import ResultStatus, AppResult
from assistant_t800.interfaces.cli.metrics import get_actual_width
from assistant_t800.localization.multilang import render_message

if TYPE_CHECKING:
    from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter


STATUS_STYLES = {
    ResultStatus.SUCCESS: ("cyan", "✓"),
    ResultStatus.INFO: ("white", "ℹ"),
    ResultStatus.WARNING: ("yellow", "⚠"),
    ResultStatus.ERROR: ("red", "✖"),
}


def display_status(
    presenter: "RichCliPresenter",
    result: AppResult,
) -> None:
    """Display Rich status panel."""
    if result.message is None:
        return

    rendered = render_message(result.message)

    if not rendered:
        return

    color, icon = STATUS_STYLES[result.status]

    presenter.console.print(
        presenter.panel_cls(
            presenter.text_cls(
                f"{icon} {rendered}",
                style=f"bold {color}",
            ),
            border_style=color,
            padding=(0, 1),
            width=get_actual_width(),
        ),
    )
