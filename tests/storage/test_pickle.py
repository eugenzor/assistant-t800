"""Unit tests for ``AssistantStorage`` in ``assistant_t800.storage.pickle``."""

import pickle
from pathlib import Path

from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.storage.pickle import AssistantStorage


# ---------- load ----------


def test_load_returns_empty_repository_when_file_missing(tmp_path):
    storage = AssistantStorage(path=tmp_path / "missing.pkl")

    repository = storage.load()

    assert isinstance(repository, ContactsRepository)
    assert repository.all() == []


def test_load_returns_empty_repository_for_corrupted_file(tmp_path):
    path = tmp_path / "corrupted.pkl"
    path.write_bytes(b"not a pickle stream")
    storage = AssistantStorage(path=path)

    repository = storage.load()

    assert isinstance(repository, ContactsRepository)
    assert repository.all() == []


def test_load_returns_empty_repository_for_wrong_type(tmp_path):
    path = tmp_path / "wrong_type.pkl"
    with path.open("wb") as file:
        pickle.dump({"not": "a repo"}, file)
    storage = AssistantStorage(path=path)

    repository = storage.load()

    assert isinstance(repository, ContactsRepository)
    assert repository.all() == [], (
        "non-repository pickled data must fall back to an empty repository"
    )


def test_load_restores_stored_repository(tmp_path):
    path = tmp_path / "data.pkl"
    repository = ContactsRepository()
    repository.add(Contact(Name("Іван")))
    with path.open("wb") as file:
        pickle.dump(repository, file)
    storage = AssistantStorage(path=path)

    loaded = storage.load()

    assert loaded.exists("Іван")


# ---------- save ----------


def test_save_without_load_returns_false(tmp_path):
    storage = AssistantStorage(path=tmp_path / "data.pkl")

    saved = storage.save()

    assert saved is False, "save must be a no-op when no repository has been entered"


def test_save_persists_repository_state(tmp_path):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)

    with storage as repository:
        repository.add(Contact(Name("Іван")))

    assert path.exists(), "context exit must write the storage file"
    with path.open("rb") as file:
        loaded = pickle.load(file)
    assert isinstance(loaded, ContactsRepository)
    assert loaded.exists("Іван")


def test_save_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "data.pkl"
    storage = AssistantStorage(path=path)

    with storage as repository:
        repository.add(Contact(Name("Іван")))

    assert path.exists()
    assert path.parent.is_dir()


# ---------- context manager ----------


def test_context_manager_yields_loaded_repository(tmp_path):
    storage = AssistantStorage(path=tmp_path / "data.pkl")

    with storage as repository:
        assert isinstance(repository, ContactsRepository)


def test_context_manager_propagates_exceptions(tmp_path):
    storage = AssistantStorage(path=tmp_path / "data.pkl")

    try:
        with storage as repository:
            repository.add(Contact(Name("Іван")))
            raise RuntimeError("boom")
    except RuntimeError as error:
        assert str(error) == "boom"
    else:
        raise AssertionError("expected RuntimeError to propagate")


def test_context_manager_saves_on_exit_even_after_no_changes(tmp_path):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)

    with storage:
        pass

    assert path.exists()


# ---------- path ----------


def test_path_property_returns_configured_path(tmp_path):
    path = tmp_path / "custom.pkl"
    storage = AssistantStorage(path=path)

    assert storage.path == path


def test_default_path_is_relative_pickle_file():
    storage = AssistantStorage()

    assert isinstance(storage.path, Path)
    assert storage.path.name == ".address_book.pkl"


def test_path_accepts_string_argument(tmp_path):
    storage = AssistantStorage(path=str(tmp_path / "data.pkl"))

    assert isinstance(storage.path, Path)
