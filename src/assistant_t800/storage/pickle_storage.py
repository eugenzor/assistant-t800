"""Pickle-based local storage."""

import pickle
from pathlib import Path
from typing import Any


class PickleStorage:
    """Save and load application data using pickle."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, data: Any) -> None:
        """Save data to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("wb") as file:
            pickle.dump(data, file)

    def load(self, default: Any = None) -> Any:
        """Load data from disk, or return default if file does not exist."""
        if not self.path.exists():
            return default

        with self.path.open("rb") as file:
            return pickle.load(file)
