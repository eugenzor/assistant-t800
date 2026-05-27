"""Optional Rich-based CLI presenter."""

from typing import Final

from rich.console import Group

from assistant_t800.interfaces.cli.presenter import CliPresenter
from assistant_t800.localization import APP_VERSION, Message


class RichCliPresenter:
    """Rich presenter with plain presenter fallback."""

    HEADER_WIDTH: Final[int] = 80
    FACE_WIDTH: Final[int] = 20
    TITLE_WIDTH: Final[int] = 50

    TERMINATOR_FACE: Final[str] = r"""       ______   
     <((((((\\\ 
     /      . }\
     ;--..--._|}
     '--/\--'  )
     | '-'  :'| 
     . -==- .-| 
      \.__.'    
                """

    def __init__(self, fallback: CliPresenter) -> None:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        self._console = Console()
        self._panel_cls = Panel
        self._table_cls = Table
        self._text_cls = Text
        self._fallback = fallback

    def display_header(self) -> None:
        """Display Rich header."""
        self.clear()

        header = self._table_cls.grid(padding=(0, 0))
        header.add_column(no_wrap=True, width=self.FACE_WIDTH)
        header.add_column(width=self.TITLE_WIDTH)

        title = Group(
            self._text_cls(),
            self._text_cls(
                str(Message.WELCOME_TITLE),
                justify="center",
                style="bold green",
            ),
            self._text_cls(""),
            self._text_cls(
                str(Message.WELCOME_SUBTITLE),
                justify="center",
                style="white",
            ),
            self._text_cls("\n\n"),
            self._text_cls(
                f"v. {APP_VERSION}",
                justify="right",
                style="dim",
            ),
        )

        header.add_row(
            self._text_cls(self.TERMINATOR_FACE, style="bold green"),
            title,
        )

        self._console.print(
            self._panel_cls(
                header,
                border_style="green",
                width=self.HEADER_WIDTH,
            )
        )

        self._console.print(self._text_cls(""))

    def display_welcome(self) -> None:
        """Display Rich welcome screen."""
        self.display_header()

        hints = self._text_cls("")
        hints.append(f"{Message.WELCOME_HINTS_TITLE}:\n", style="bold cyan")
        hints.append("  • ", style="cyan")
        hints.append(f"{Message.WELCOME_QUOTES_HINT}\n", style="white")
        hints.append('    add "John Smith" 0991112233 "New York"\n', style="dim")
        hints.append("  • ", style="cyan")
        hints.append(f"{Message.WELCOME_MULTI_VALUE_HINT}\n", style="white")
        hints.append("    add-phone John 0991112233;0992223344\n", style="dim")
        hints.append("  • ", style="cyan")
        hints.append(f"{Message.WELCOME_REMOVE_HINT}\n", style="white")
        hints.append("  • ", style="cyan")
        hints.append(f"{Message.WELCOME_HELP_HINT}\n", style="white")

        self._console.print(hints)

    def display_goodbye(self) -> None:
        """Display goodbye message."""
        self._fallback.display_goodbye()

    def display(self, result) -> None:
        """Display one application result."""
        self._fallback.display(result)

    def clear(self) -> None:
        """Clear terminal screen."""
        self._console.clear()
