"""CLI presenter factory."""

from collections.abc import Callable

from assistant_t800.interfaces.cli.presenter import CliPresenter

OutputFunc = Callable[[str], None]


def create_cli_presenter(output_func: OutputFunc = print):
    """Create the best available CLI presenter."""
    fallback = CliPresenter(output_func=output_func)

    try:
        from assistant_t800.interfaces.cli.rich_presenter import RichCliPresenter

        result = RichCliPresenter(fallback=fallback)
    except ImportError:
        result = fallback

    return result
