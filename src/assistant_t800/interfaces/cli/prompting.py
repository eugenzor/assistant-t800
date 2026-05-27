from pathlib import Path
from typing import Callable

from assistant_t800.application.commands import Command


class InputFactory:
    """Create CLI input function with optional prompt_toolkit support."""

    def __init__(
        self,
        history_file: str | Path = ".commands_history",
        max_history_entries: int = 100,
        fallback_to_input: bool = True,
        show_fallback_reason: bool = False,
    ) -> None:
        self.history_file = Path(history_file)
        self.max_history_entries = max_history_entries
        self.fallback_to_input = fallback_to_input
        self.show_fallback_reason = show_fallback_reason

    def cleanup_history(self) -> None:
        """Trim prompt_toolkit history file to the last max_history_entries commands."""
        path = Path(self.history_file)

        if not path.is_file():
            return

        lines = path.read_text(encoding="utf-8").splitlines()

        entries: list[list[str]] = []
        current: list[str] = []

        for line in lines:
            # Each history entry starts with a timestamp comment:
            #   # 2026-05-10 20:50:26.159230
            #   +command
            if line.startswith("# "):
                if current:
                    entries.append(current)

                current = [line]
            elif current:
                current.append(line)

        if current:
            entries.append(current)

        if len(entries) > self.max_history_entries:
            trimmed_entries = entries[-self.max_history_entries :]

            content = "\n".join("\n".join(entry) for entry in trimmed_entries)

            path.write_text(
                f"\n{content}\n",
                encoding="utf-8",
                newline="\n",
            )

    def create(self, registry: dict[str, Command]) -> Callable[[str], str]:
        """
        Create interactive input function.

        If prompt_toolkit is available, enables:
        - persistent history
        - command completion
        - auto-suggestions

        Falls back to standard input() otherwise.
        """
        result: Callable[[str], str] = input

        import sys

        if not sys.stdin.isatty():
            return input

        try:
            # prevent selector event loop on Windows
            self._patch_windows_asyncio()

            from prompt_toolkit import PromptSession
            from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
            from prompt_toolkit.completion import WordCompleter
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.shortcuts import CompleteStyle

            completer = WordCompleter(
                sorted(registry),
                ignore_case=True,
                # Allow matching command fragments:
                # "birth" -> "birthdays"
                match_middle=True,
                sentence=True,
            )

            # Keep history file size under control.
            self.cleanup_history()

            session = PromptSession(
                history=FileHistory(self.history_file),
                # Suggest previously used commands from history.
                auto_suggest=AutoSuggestFromHistory(),
                completer=completer,
                # Completion is triggered only by TAB,
                # similar to classic shell behavior.
                complete_while_typing=False,
                # Disable dropdown-like completion menu.
                complete_style=CompleteStyle.READLINE_LIKE,
            )

            result = session.prompt

        except (
            # prompt_toolkit is not installed
            ImportError,
            OSError,
            # prompt_toolkit may be installed but unavailable
            # in IDE consoles, especially on Windows when there
            # is no real console screen buffer.
            Exception,
        ) as error:
            if not self.fallback_to_input:
                raise

            if self.show_fallback_reason:
                print(f"Prompt toolkit disabled: {error}")

            result = input

        return result

    def create_note_input(self) -> Callable[[str, str], str]:
        """Create note input function."""
        import sys

        # prompt_toolkit needs an interactive terminal.
        if not sys.stdin.isatty():
            # fallback function to use simple input(), second argument for return type compatibility
            def fallback_note_input(prompt: str, default: str) -> str:
                return input(prompt)

            return fallback_note_input

        try:
            # prevent selector event loop on Windows
            self._patch_windows_asyncio()

            from prompt_toolkit import PromptSession

            session = PromptSession()

            def note_input(prompt: str, default: str) -> str:
                return session.prompt(prompt, default=default)

            return note_input

        except (ImportError, OSError, Exception) as error:
            if not self.fallback_to_input:
                raise

            if self.show_fallback_reason:
                print(f"Prompt toolkit note input disabled: {error}")

            # fall back to simple input without prompt_toolkit
            def fallback_note_input(prompt: str, default: str) -> str:
                return input(prompt)

            return fallback_note_input

    @staticmethod
    def _patch_windows_asyncio() -> None:
        """Use selector event loop on Windows for prompt_toolkit stability."""
        import asyncio
        import sys

        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
