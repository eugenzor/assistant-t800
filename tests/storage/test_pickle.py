"""Unit tests for ``AssistantStorage`` safe pickle persistence."""

import pickle

from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.storage.pickle import AssistantStorage


def _repository_with(name: str) -> ContactsRepository:
    repository = ContactsRepository()
    repository.add(Contact(Name(name)))

    return repository


def _dump_repository(path, repository: ContactsRepository) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        pickle.dump(repository, file)


# ---------- load ----------


def test_load_returns_empty_repository_when_file_missing(tmp_path):
    storage = AssistantStorage(path=tmp_path / "missing.pkl")

    repository = storage.load()

    assert isinstance(repository, ContactsRepository)
    assert repository.all() == []


def test_load_returns_empty_repository_for_empty_file_without_backup(tmp_path):
    path = tmp_path / "empty.pkl"
    path.write_bytes(b"")
    storage = AssistantStorage(path=path)

    repository = storage.load()

    assert isinstance(repository, ContactsRepository)
    assert repository.all() == []


def test_load_returns_empty_repository_for_corrupted_file_without_backup(tmp_path):
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
    assert repository.all() == []


def test_load_restores_stored_repository(tmp_path):
    path = tmp_path / "data.pkl"
    _dump_repository(path, _repository_with("Іван"))
    storage = AssistantStorage(path=path)

    loaded = storage.load()

    assert loaded.exists("Іван")


def test_load_recovers_from_backup_when_main_file_is_empty(tmp_path):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)
    path.write_bytes(b"")
    _dump_repository(storage.backup_path, _repository_with("John Smith"))

    loaded = storage.load()

    assert loaded.exists("John Smith")


def test_load_recovers_from_backup_when_main_file_is_corrupted(tmp_path):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)
    path.write_bytes(b"broken")
    _dump_repository(storage.backup_path, _repository_with("Марія"))

    loaded = storage.load()

    assert loaded.exists("Марія")


def test_load_ignores_corrupted_backup_and_returns_empty_repository(tmp_path):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)
    path.write_bytes(b"broken")
    storage.backup_path.write_bytes(b"also broken")

    loaded = storage.load()

    assert isinstance(loaded, ContactsRepository)
    assert loaded.all() == []


# ---------- startup backup ----------


def test_enter_creates_backup_before_working_with_existing_valid_file(tmp_path):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)
    _dump_repository(path, _repository_with("John Smith"))

    with storage as repository:
        assert repository.exists("John Smith")
        repository.add(Contact(Name("Марія")))

    backup = storage._load_from_path(storage.backup_path)

    assert backup is not None
    assert backup.exists("John Smith")
    assert not backup.exists("Марія")


def test_enter_offers_recovery_when_main_file_is_empty_and_backup_is_valid(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)
    path.write_bytes(b"")
    _dump_repository(storage.backup_path, _repository_with("John Smith"))
    monkeypatch.setattr("builtins.input", lambda prompt: "y")

    with storage as repository:
        assert repository.exists("John Smith")

    assert AssistantStorage(path=path).load().exists("John Smith")


def test_enter_keeps_old_backup_when_empty_main_recovery_is_declined(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)
    path.write_bytes(b"")
    _dump_repository(storage.backup_path, _repository_with("Backup Contact"))
    monkeypatch.setattr("builtins.input", lambda prompt: "n")

    with storage as repository:
        assert repository.exists("Backup Contact")
        repository.add(Contact(Name("New Contact")))

    backup = storage._load_from_path(storage.backup_path)

    assert backup is not None
    assert backup.exists("Backup Contact")
    assert not backup.exists("New Contact")


def test_enter_does_not_offer_recovery_when_empty_main_has_no_valid_backup(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)
    path.write_bytes(b"")
    calls = []

    def fake_input(prompt):
        calls.append(prompt)

        return "y"

    monkeypatch.setattr("builtins.input", fake_input)

    with storage as repository:
        assert repository.all() == []

    assert calls == []


def test_empty_main_file_recovery_prompt_uses_red_warning_text(tmp_path, monkeypatch):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)
    path.write_bytes(b"")
    _dump_repository(storage.backup_path, _repository_with("John Smith"))
    prompts = []

    def fake_input(prompt):
        prompts.append(prompt)

        return "n"

    monkeypatch.setattr("builtins.input", fake_input)

    with storage:
        pass

    assert prompts
    assert prompts[0].startswith(AssistantStorage.WARNING_COLOR)
    assert prompts[0].endswith(AssistantStorage.RESET_COLOR)


def test_enter_does_not_backup_empty_file(tmp_path):
    path = tmp_path / "data.pkl"
    path.write_bytes(b"")
    storage = AssistantStorage(path=path)

    with storage:
        pass

    assert not storage.backup_path.exists()


# ---------- save ----------


def test_save_without_load_returns_false(tmp_path):
    storage = AssistantStorage(path=tmp_path / "data.pkl")

    saved = storage.save()

    assert saved is False


def test_save_persists_repository_state(tmp_path):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)

    with storage as repository:
        repository.add(Contact(Name("Іван")))
        repository.add(Contact(Name("John Smith")))

    assert path.exists()
    with path.open("rb") as file:
        loaded = pickle.load(file)
    assert isinstance(loaded, ContactsRepository)
    assert loaded.exists("Іван")
    assert loaded.exists("John Smith")


def test_save_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "data.pkl"
    storage = AssistantStorage(path=path)

    with storage as repository:
        repository.add(Contact(Name("Іван")))

    assert path.exists()
    assert path.parent.is_dir()


def test_save_uses_temporary_file_and_leaves_no_temp_files(tmp_path):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)

    with storage as repository:
        repository.add(Contact(Name("Іван")))

    temp_candidates = [
        item
        for item in tmp_path.iterdir()
        if item.is_file() and item.name not in {"data.pkl", "data.pkl.bak"}
    ]
    assert temp_candidates == []


# ---------- context manager ----------


def test_context_manager_yields_loaded_repository(tmp_path):
    storage = AssistantStorage(path=tmp_path / "data.pkl")

    with storage as repository:
        assert isinstance(repository, ContactsRepository)


def test_context_manager_propagates_exceptions_but_still_saves(tmp_path):
    path = tmp_path / "data.pkl"
    storage = AssistantStorage(path=path)

    try:
        with storage as repository:
            repository.add(Contact(Name("Іван")))
            raise RuntimeError("boom")
    except RuntimeError as error:
        assert str(error) == "boom"
    else:
        raise AssertionError("expected RuntimeError to propagate")

    assert AssistantStorage(path=path).load().exists("Іван")


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


def test_backup_path_appends_bak_suffix(tmp_path):
    storage = AssistantStorage(path=tmp_path / "address_book.pkl")

    assert storage.backup_path.name == "address_book.pkl.bak"


def test_default_path_is_relative_pickle_file():
    storage = AssistantStorage()

    assert storage.path.name == ".address_book.pkl"


def test_path_accepts_string_argument(tmp_path):
    storage = AssistantStorage(path=str(tmp_path / "data.pkl"))

    assert storage.path == tmp_path / "data.pkl"
