"""Classic CLI input loop."""
import shlex
from collections.abc import Callable

from assistant_t800.application.dispatcher import CommandDispatcher
from assistant_t800.application.results import AppResult
from assistant_t800.interfaces.cli.presenter import CliPresenter
from assistant_t800.localization import ErrorCode, Message
from assistant_t800.suggestions import SuggestionService
from assistant_t800.application.enums import SystemValue

InputFunc = Callable[[str], str]
NoteInputFunc = Callable[[str, str], str]
OutputFunc = Callable[[str], None]


class CliRunner:
    """Run the classic command-line interface."""

    def __init__(
        self,
        dispatcher: CommandDispatcher,
        presenter: CliPresenter,
        input_func: InputFunc = input,
        note_input_func: NoteInputFunc | None = None,
        output_func: OutputFunc = print,
        suggestion_service: SuggestionService | None = None,
        force_suggestion_confirm: bool = True,
        force_removal_confirm: bool = True,
    ) -> None:
        self._dispatcher = dispatcher
        self._presenter = presenter
        self._input_func = input_func
        self._note_input_func = note_input_func
        self._output_func = output_func
        self._suggestion_service = suggestion_service
        self._force_suggestion_confirm = force_suggestion_confirm
        self._force_removal_confirm = force_removal_confirm

    @property
    def dispatcher(self) -> CommandDispatcher:
        """Return command dispatcher."""
        return self._dispatcher

    @property
    def presenter(self) -> CliPresenter:
        """Return CLI presenter."""
        return self._presenter

    @property
    def suggestion_service(self) -> SuggestionService | None:
        """Return optional command suggestion service."""
        return self._suggestion_service

    def run(self) -> None:
        """Run the command processing loop."""
        self.presenter.display_welcome()

        try:
            while True:
                result = self._dispatch_input()
                self.presenter.display(result)

                if result.should_exit:
                    break
        except (KeyboardInterrupt, EOFError):
            self.presenter.display_goodbye()

    def _dispatch_input(self) -> AppResult:
        """Read, resolve, dispatch, and optionally confirm one input line."""
        raw_input = self._input_func(f"{Message.PROMPT} ")
        command_input = self._resolve_note_edit_input(raw_input)

        result = self.dispatcher.dispatch(command_input)

        if self._can_suggest(result):
            suggested_input = self._get_confirmed_suggestion(raw_input)

            if suggested_input is not None:
                command_input = suggested_input
                result = self.dispatcher.dispatch(command_input)

        if result.requires_confirmation:
            result = self._confirm_and_dispatch(command_input, result)

        return result

    def _confirm_and_dispatch(self, command_input: str, result: AppResult) -> AppResult:
        """Ask for confirmation and execute the resolved command when accepted."""

        if self._force_removal_confirm:
            confirmation = result.confirmation.message
            answer = confirmation.code.confirm_check(
                input(confirmation.code.confirm_render(**confirmation.params))
            )
        else:
            answer = True

        if answer:
            final_result = self.dispatcher.dispatch(command_input, confirmed=True)
        else:
            final_result = AppResult.ok(Message.OPERATION_CANCELLED)

        return final_result

    def _can_suggest(self, result: AppResult) -> bool:
        """Return whether command suggestions should be requested."""
        result_code = result.message.code if result.message is not None else None
        can_suggest = (
            self.suggestion_service is not None
            and not result.success
            and result_code is ErrorCode.UNKNOWN_COMMAND
        )

        return can_suggest

    def _get_confirmed_suggestion(self, raw_input: str) -> str | None:
        """Return a confirmed suggested command input."""
        suggestion_result = self.suggestion_service.suggest(raw_input)
        suggestion = (
            suggestion_result.suggestions[0] if suggestion_result.suggestions else None
        )

        if suggestion is None:
            result = None
        else:
            suggested_input = suggestion.suggested_input
            if self._force_suggestion_confirm:
                answer = input(
                    Message.COMMAND_SUGGESTION_CONFIRM.confirm_render(
                        command=suggested_input,
                    )
                )
                if not Message.COMMAND_SUGGESTION_CONFIRM.confirm_check(answer):
                    suggested_input = None
            else:
                print(Message.COMMAND_SUGGESTION_RUN.render(command=suggested_input))
            result = suggested_input

        return result

    def _resolve_note_edit_input(self, raw_input: str) -> str:
        """Resolve note edit input."""
        if self._note_input_func is None:
            return raw_input

        try:
            parts = shlex.split(raw_input)
        except ValueError:
            return raw_input

        if len(parts) != 2:
            return raw_input

        if parts[0] != "edit-note":
            return raw_input

        name = parts[1]

        # getting existing note content from contact
        try:
            contact = self.dispatcher.context.contacts.get_contact(name)
        except KeyError:
            return raw_input

        existing_note = contact.note
        if existing_note == SystemValue.EMPTY_TEXT.value:
            existing_note = ""

        edited_note = self._note_input_func(f"Note for {name}: ", existing_note)

        # we need to rebuild the command input with edited note content correctly i.e. (edit-note Alice "Call after demo")
        return f"edit-note {self._quote_arg(name)} {self._quote_arg(edited_note)}"

    @staticmethod
    def _quote_arg(value: str) -> str:
        """Quote one argument for dispatcher parsing."""
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
