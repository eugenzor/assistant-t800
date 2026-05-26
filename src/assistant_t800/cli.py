"""Package console entry point."""

from sys import argv
from dotenv import load_dotenv
from assistant_t800.interfaces.launcher import launch


def main() -> None:
    """Run the package command-line entry point."""

    # Export variables from `.env` into `os.environ` for third-party libraries
    # that access environment variables directly.

    load_dotenv()

    raise SystemExit(launch(argv[1:], pickle_db=".data/address_book.pkl"))
