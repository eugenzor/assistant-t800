"""CLI entry point for the T800 assistant."""

import argparse

# Load environment variables before initializing AI-related modules.
from assistant_t800 import config  # noqa: F401


def main() -> None:
    """Parse CLI arguments and start the selected application mode."""
    parser = argparse.ArgumentParser(
        prog="assistant-t800",
        description="Особистий асистент T800.",
    )

    parser.add_argument(
        "--enable-ai",
        action="store_true",
        help="Запустити Textual TUI з підтримкою ШІ.",
    )

    args = parser.parse_args()

    if args.enable_ai:
        # Import lazily to avoid loading heavy UI dependencies unnecessarily.
        from assistant_t800.interfaces.textual.app import run_textual

        run_textual()
    else:
        print(
            "Звичайний режим ще не реалізовано. "
            "Використовуйте --enable-ai."
        )
