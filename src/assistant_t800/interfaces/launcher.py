"""Application interface launcher."""

from collections.abc import Sequence
from pathlib import Path

from assistant_t800.application.enums import InterfaceMode
from assistant_t800.application.results import AppMessage
from assistant_t800.localization import ErrorCode, render_message

_MODE_ALIASES: dict[str, InterfaceMode] = {
    "": InterfaceMode.CLI,
    "cli": InterfaceMode.CLI,
    "run": InterfaceMode.CLI,
    "tui": InterfaceMode.TUI,
    "--tui": InterfaceMode.TUI,
    "--enable-ai": InterfaceMode.TUI,
}


def launch(argv: Sequence[str], pickle_db: str = None) -> int:
    """Launch the selected application interface."""
    mode, exit_code = _resolve_mode(argv)

    pickle_db_path = Path(pickle_db or ".data/address_book.pkl")
    pickle_db_path.parent.mkdir(parents=True, exist_ok=True)

    if exit_code == 0:
        if mode is InterfaceMode.TUI:
            _run_tui(pickle_db_path)
        else:
            _run_cli(pickle_db_path)

    return exit_code


def _resolve_mode(argv: Sequence[str]) -> tuple[InterfaceMode, int]:
    """Resolve interface mode from raw CLI arguments."""
    raw_mode = argv[0].strip().lower() if argv else ""
    mode = _MODE_ALIASES.get(raw_mode)

    if mode is None:
        print(
            render_message(
                AppMessage(
                    ErrorCode.UNKNOWN_INTERFACE_MODE,
                    {"mode": raw_mode},
                )
            )
        )
        result = InterfaceMode.CLI, 2
    else:
        result = mode, 0

    return result


def _run_cli(pickle_db: Path) -> None:
    """Run the classic CLI interface."""
    from assistant_t800.bootstrap import build_cli_application

    build_cli_application(pickle_db).run()


def _run_tui(pickle_db: Path) -> None:
    """Run the Textual AI sandbox interface."""
    from assistant_t800 import config  # noqa: F401
    from assistant_t800.interfaces.textual.app import run_textual

    run_textual(pickle_db)
