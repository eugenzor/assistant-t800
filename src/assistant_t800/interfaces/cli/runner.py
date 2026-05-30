"""Classic CLI input loop."""

from collections.abc import Callable

from assistant_t800.application.dispatcher import CommandDispatcher
from assistant_t800.application.results import AppResult
from assistant_t800.interfaces.cli.edit_resolvers import (
    NoteEditResolver,
    SuggestTagsResolver,
    TagEditResolver,
)
from assistant_t800.interfaces.cli.prompting import (
    InputFunc,
    EditableInputFunc,
    TextInputFunc,
)
from assistant_t800.interfaces.cli.presenter import CliPresenter
from assistant_t800.localization import ErrorCode, Message
from assistant_t800.suggestions import SuggestionService

OutputFunc = Callable[[str], None]


class CliRunner:
    """Run the classic command-line interface."""

    def __init__(
        self,
        dispatcher: CommandDispatcher,
        presenter: CliPresenter,
        input_func: InputFunc = input,
        editable_func: EditableInputFunc | None = None,
        text_input_func: TextInputFunc | None = None,
        output_func: OutputFunc = print,
        suggestion_service: SuggestionService | None = None,
        force_suggestion_confirm: bool = True,
        force_removal_confirm: bool = True,
    ) -> None:
        self._dispatcher = dispatcher
        self._presenter = presenter
        self._input_func = input_func
        self._editable_func = editable_func
        self._text_input_func = text_input_func
        self._note_edit_resolver = NoteEditResolver(
            context=dispatcher.context,
            presenter=presenter,
            text_input_func=text_input_func,
        )
        self._tag_edit_resolver = TagEditResolver(
            context=dispatcher.context,
            presenter=presenter,
            editable_func=editable_func,
        )
        self._suggest_tags_resolver = SuggestTagsResolver(
            context=dispatcher.context,
            presenter=presenter,
            editable_func=editable_func,
        )
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

                if result is None:
                    continue

                if self._should_display_results_header(result):
                    self.presenter.display_results_header()

                self.presenter.display(result)

                if result.should_exit:
                    break
        except (KeyboardInterrupt, EOFError):
            self.presenter.display_goodbye()

    def _dispatch_input(self) -> AppResult | None:
        """Read, resolve, dispatch, and optionally confirm one input line."""
        raw_input = self._input_func(f"{Message.PROMPT} ")

        if not raw_input.strip():
            self.presenter.display_welcome()
            result = None
        else:
            command_input = self._resolve_interactive_input(raw_input)

            if isinstance(command_input, AppResult):
                result = command_input
            else:
                result = self.dispatcher.dispatch(command_input)

                if self._can_suggest(result):
                    suggested_input = self._get_confirmed_suggestion(raw_input)

                    if suggested_input is not None:
                        command_input = self._resolve_interactive_input(suggested_input)

                        if isinstance(command_input, AppResult):
                            result = command_input
                        else:
                            result = self.dispatcher.dispatch(command_input)

                if result.requires_confirmation:
                    result = self._confirm_and_dispatch(command_input, result)

        return result

    def _resolve_interactive_input(self, raw_input: str) -> str | AppResult:
        """Resolve interactive edit commands before dispatch."""
        note_input = self._note_edit_resolver.resolve(raw_input)

        if isinstance(note_input, AppResult):
            result = note_input
        else:
            tag_input = self._tag_edit_resolver.resolve(note_input)

            if isinstance(tag_input, AppResult):
                result = tag_input
            else:
                result = self._suggest_tags_resolver.resolve(tag_input)

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

    @staticmethod
    def _should_display_results_header(result: AppResult) -> bool:
        """Return whether results header should be displayed."""
        should_display = not result.should_exit and not result.requires_confirmation

        return should_display

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
