"""Pickle-based address book storage."""

import os
import pickle
import shutil
import tempfile
from pathlib import Path
from typing import ClassVar

from assistant_t800.repositories.contacts import ContactsRepository


class AssistantStorage:
    """Persist the contacts repository to disk using pickle."""

    DEFAULT_PATH: ClassVar[Path] = Path(".address_book.pkl")
    BACKUP_SUFFIX: ClassVar[str] = ".bak"
    WARNING_COLOR: ClassVar[str] = "\033[31m"
    RESET_COLOR: ClassVar[str] = "\033[0m"

    def __init__(self, path: str | Path = DEFAULT_PATH) -> None:
        self._path = Path(path)
        self._data: ContactsRepository | None = None

    @property
    def path(self) -> Path:
        """Return storage file path."""
        return self._path

    @property
    def backup_path(self) -> Path:
        """Return backup storage file path."""
        result = self.path.with_name(f"{self.path.name}{self.BACKUP_SUFFIX}")

        return result

    def load(self) -> ContactsRepository:
        """Load contacts repository from disk with backup recovery."""
        data = self._load_from_path(self.path)

        if data is None:
            data = self._load_from_path(self.backup_path)

        if data is None:
            data = ContactsRepository()

        return data

    def save(self) -> bool:
        """Save current contacts repository state atomically."""
        if self._data is None:
            result = False
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self._dump_to_temp_file(self._data)

            try:
                temp_path.replace(self.path)
                result = True
            finally:
                if temp_path.exists():
                    temp_path.unlink()

        return result

    def _load_from_path(self, path: Path) -> ContactsRepository | None:
        """Load repository from one path or return None when it is unusable."""
        result: ContactsRepository | None = None

        try:
            if not path.is_file() or path.stat().st_size == 0:
                raise EOFError

            with path.open("rb") as file:
                data = pickle.load(file)

            if isinstance(data, ContactsRepository):
                result = data

        except (
            FileNotFoundError,
            EOFError,
            pickle.PickleError,
            AttributeError,
            TypeError,
            OSError,
        ):
            result = None

        return result

    def _dump_to_temp_file(self, data: ContactsRepository) -> Path:
        """Dump repository to a temporary file in the storage directory."""
        with tempfile.NamedTemporaryFile(
            mode="wb",
            delete=False,
            dir=self.path.parent,
        ) as file:
            pickle.dump(data, file)
            file.flush()
            os.fsync(file.fileno())
            result = Path(file.name)

        return result

    def _backup_current_file(self) -> None:
        """Create a backup copy of the current valid storage file."""
        if self._load_from_path(self.path) is not None:
            shutil.copy2(self.path, self.backup_path)

    def _recover_empty_storage_file(self) -> None:
        """Offer startup recovery when main storage is empty and backup exists."""
        if self._should_offer_backup_recovery() and self._confirm_backup_recovery():
            shutil.copy2(self.backup_path, self.path)

    def _should_offer_backup_recovery(self) -> bool:
        """Return whether startup backup recovery should be offered."""
        result = (
            self.path.is_file()
            and self.path.stat().st_size == 0
            and self._load_from_path(self.backup_path) is not None
        )

        return result

    def _confirm_backup_recovery(self) -> bool:
        """Ask user whether to restore storage from backup."""
        prompt = (
            f"{self.WARNING_COLOR}"
            f"Storage file is corrypted: {self.path}\n"
            f"Valid backup found: {self.backup_path}\n"
            "Restore database from backup? [y/N]: "
            f"{self.RESET_COLOR}"
        )

        try:
            answer = input(prompt)
            result = answer.strip().lower() in {"y", "yes"}
        except (KeyboardInterrupt, EOFError):
            result = False

        return result

    def __enter__(self) -> ContactsRepository:
        """Recover empty storage, create startup backup, and load repository."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._recover_empty_storage_file()
        self._backup_current_file()
        self._data = self.load()

        return self._data

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Save repository on context exit."""
        self.save()

        return False
