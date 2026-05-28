"""Unit tests for ``AppContext`` in ``assistant_t800.application.context``."""

from assistant_t800.application.context import AppContext
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService


def _service() -> ContactsService:
    return ContactsService(ContactsRepository())


# ---------- defaults ----------


def test_app_context_defaults_args_to_empty_dict():
    context = AppContext(contacts=_service())

    assert context.args == {}


def test_app_context_defaults_raw_args_to_empty_tuple():
    context = AppContext(contacts=_service())

    assert context.raw_args == ()


def test_app_context_defaults_registry_to_empty_dict():
    context = AppContext(contacts=_service())

    assert context.registry == {}


def test_app_context_defaults_confirmed_to_false():
    context = AppContext(contacts=_service())

    assert context.confirmed is False


# ---------- explicit values ----------


def test_app_context_stores_supplied_args():
    context = AppContext(
        contacts=_service(),
        args={"name": "Іван"},
    )

    assert context.args == {"name": "Іван"}


def test_app_context_stores_supplied_raw_args():
    context = AppContext(
        contacts=_service(),
        raw_args=("Іван", "1234567890"),
    )

    assert context.raw_args == ("Іван", "1234567890")


def test_app_context_stores_supplied_registry():
    registry = {"help": object()}
    context = AppContext(contacts=_service(), registry=registry)

    assert context.registry is registry


def test_app_context_stores_supplied_confirmed_flag():
    context = AppContext(contacts=_service(), confirmed=True)

    assert context.confirmed is True


# ---------- mutability ----------


def test_app_context_allows_mutation_of_args_after_construction():
    context = AppContext(contacts=_service())

    context.args["name"] = "Іван"

    assert context.args == {"name": "Іван"}


def test_app_context_allows_mutation_of_confirmed_flag():
    context = AppContext(contacts=_service())

    context.confirmed = True

    assert context.confirmed is True


# ---------- defaults isolation ----------


def test_app_context_default_args_are_isolated_between_instances():
    first = AppContext(contacts=_service())
    second = AppContext(contacts=_service())

    first.args["name"] = "Іван"

    assert second.args == {}


def test_app_context_default_registry_is_isolated_between_instances():
    first = AppContext(contacts=_service())
    second = AppContext(contacts=_service())

    first.registry["help"] = object()

    assert second.registry == {}
