"""Application object construction."""

from dataclasses import dataclass
from pathlib import Path

from assistant_t800.application.context import AppContext
from assistant_t800.application.dispatcher import CommandDispatcher
from assistant_t800.interfaces.cli.commands import build_registry
from assistant_t800.interfaces.cli.presenter_factory import create_cli_presenter
from assistant_t800.interfaces.cli.prompting import InputFactory
from assistant_t800.interfaces.cli.runner import CliRunner
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService
from assistant_t800.storage import AssistantStorage
from assistant_t800.suggestions import CommandRegistry as SuggestionCommandRegistry
from assistant_t800.suggestions import SuggestionService


CLI_HISTORY_FILE = Path(".data/cli_commands_history")


@dataclass(frozen=True)
class CliApplication:
    """Classic CLI runtime container."""

    storage: AssistantStorage

    def run(self) -> None:
        """Run the CLI application."""
        with self.storage as repository:
            runner = _build_cli_runner(repository)
            runner.run()


def build_cli_application(pickle_db: Path) -> CliApplication:
    """Build the classic CLI application runtime."""

    result = CliApplication(
        storage=AssistantStorage(path=pickle_db),
    )

    return result


def _build_cli_runner(repository: ContactsRepository) -> CliRunner:
    """Build CLI runner for the provided contacts repository."""
    registry = build_registry()
    context = AppContext(
        contacts=ContactsService(repository),
        registry=registry,
    )
    dispatcher = CommandDispatcher(context)
    presenter = create_cli_presenter()

    CLI_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    input_factory = InputFactory(history_file=CLI_HISTORY_FILE)
    input_func = input_factory.create(registry)
    note_input_func = input_factory.create_note_input()

    suggestion_registry = SuggestionCommandRegistry.from_mapping(registry)
    suggestion_service = SuggestionService(suggestion_registry)

    result = CliRunner(
        dispatcher=dispatcher,
        presenter=presenter,
        input_func=input_func,
        note_input_func=note_input_func,
        suggestion_service=suggestion_service,
        force_suggestion_confirm=False,
        force_removal_confirm=True,
    )

    return result
