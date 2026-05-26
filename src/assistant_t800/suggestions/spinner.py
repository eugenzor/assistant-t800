"""Minimal CLI spinner."""

from itertools import cycle
from threading import Event, Thread
from time import sleep
from typing import Final

LOADER_FRAMES: Final[str] = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class Spinner:
    """Animated terminal spinner."""

    def __init__(
        self,
        text: str = "AI resolving command...",
        delay: float = 0.08,
    ) -> None:
        self.text = text
        self.delay = delay
        self._stop = Event()
        self._thread = Thread(target=self._spin, daemon=True)

    def start(self) -> None:
        """Start spinner animation."""
        self._thread.start()

    def stop(self) -> None:
        """Stop spinner animation and clear line."""
        self._stop.set()
        self._thread.join()

        print("\r\033[2K", end="", flush=True)

    def _spin(self) -> None:
        """Render animated spinner."""
        for frame in cycle(LOADER_FRAMES):
            if self._stop.is_set():
                break

            print(
                f"\r{frame} ",
                end="",
                flush=True,
            )

            sleep(self.delay)
