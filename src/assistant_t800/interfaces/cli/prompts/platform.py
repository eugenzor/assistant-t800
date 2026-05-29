"""Shared prompt_toolkit platform helpers."""


def patch_windows_asyncio() -> None:
    """Use selector event loop on Windows for prompt_toolkit stability."""
    import asyncio
    import sys

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
