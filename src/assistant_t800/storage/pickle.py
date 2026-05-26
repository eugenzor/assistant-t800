"""Pickle-based address book storage."""

import pickle
from pathlib import Path
from typing import ClassVar

from assistant_t800.repositories.contacts import ContactsRepository


class AssistantStorage:
    """Persist the contacts repository to disk using pickle."""

    DEFAULT_PATH: ClassVar[Path] = Path(".address_book.pkl")

    def __init__(self, path: str | Path = DEFAULT_PATH) -> None:
        self._path = Path(path)
        self._data: ContactsRepository | None = None

    @property
    def path(self) -> Path:
        """Return storage file path."""
        return self._path

    def load(self) -> ContactsRepository:
        """Load contacts repository from disk."""
        try:
            with self.path.open("rb") as file:
                data = pickle.load(file)

            if not isinstance(data, ContactsRepository):
                data = ContactsRepository()

        except (
            FileNotFoundError,
            EOFError,
            pickle.PickleError,
            AttributeError,
            TypeError,
        ):
            data = ContactsRepository()

        return data

    def save(self) -> bool:
        """Save current contacts repository state."""
        if self._data is None:
            result = False
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)

            with self.path.open("wb") as file:
                pickle.dump(self._data, file)

            result = True

        return result

    def __enter__(self) -> ContactsRepository:
        """Load repository and enter context manager."""
        self._data = self.load()

        return self._data

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Save repository on context exit."""
        self.save()

        return False
