"""Rich welcome screen rendering."""

from typing import TYPE_CHECKING

from assistant_t800.localization import Message

if TYPE_CHECKING:
    from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter


def display_welcome(presenter: "RichCliPresenter") -> None:
    """Display Rich welcome screen."""
    presenter.display_welcome_header()

    hints = presenter.text_cls("")
    hints.append(f"{Message.WELCOME_HINTS_TITLE}:\n", style="bold cyan")
    hints.append("  • ", style="cyan")
    hints.append(f"{Message.WELCOME_QUOTES_HINT}\n", style="white")
    hints.append(
        '    add "John Smith" +17739992233 "USA, New York, 77th Street"\n', style="dim"
    )
    hints.append("  • ", style="cyan")
    hints.append(f"{Message.WELCOME_MULTI_VALUE_HINT}\n", style="white")
    hints.append("    add-phone John 17739992233;0509992233\n", style="dim")
    hints.append("  • ", style="cyan")
    hints.append(f"{Message.WELCOME_REMOVE_HINT}\n", style="white")
    hints.append("  • ", style="cyan")
    hints.append(f"{Message.WELCOME_HELP_HINT}", style="white")

    presenter.console.print(hints)
