"""Command-line base input implementation."""

from pathlib import Path
from typing import Callable, Sequence

from assistant_t800.interfaces.cli.prompts.history import cleanup_history_file

InputFunc = Callable[[str], str]


class BaseInput:
    """Create single-line command input with history and completion."""

    def __init__(
        self,
        *,
        history_file: str | Path = ".commands_history",
        max_history_entries: int = 100,
    ) -> None:
        self.history_file = Path(history_file)
        self.max_history_entries = max_history_entries

    def cleanup_history(self) -> None:
        """Trim prompt_toolkit history file to the last max_history_entries commands."""
        cleanup_history_file(
            path=self.history_file,
            max_entries=self.max_history_entries,
        )

    def create(self, completion_words: Sequence[str]) -> InputFunc:
        """Create prompt_toolkit command input function."""
        from prompt_toolkit import PromptSession
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.shortcuts import CompleteStyle

        completer = WordCompleter(
            completion_words,
            ignore_case=True,
            match_middle=True,
            sentence=True,
        )

        self.cleanup_history()

        session = PromptSession(
            history=FileHistory(self.history_file),
            auto_suggest=AutoSuggestFromHistory(),
            completer=completer,
            complete_while_typing=False,
            complete_style=CompleteStyle.READLINE_LIKE,
        )

        result = session.prompt

        return result
