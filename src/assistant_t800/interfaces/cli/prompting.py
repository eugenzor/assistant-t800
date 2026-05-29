"""CLI input factory."""

from pathlib import Path
from typing import TypeVar, Sequence

from assistant_t800.interfaces.cli.prompts.base_input import BaseInput, InputFunc
from assistant_t800.interfaces.cli.prompts.editable_input import (
    EditableInput,
    EditableInputFunc,
)
from assistant_t800.interfaces.cli.prompts.platform import patch_windows_asyncio
from assistant_t800.interfaces.cli.prompts.text_input import TextInput, TextInputFunc

InputFunc = InputFunc
EditableInputFunc = EditableInputFunc
TextInputFunc = TextInputFunc
PromptFunc = TypeVar("PromptFunc")


class InputFactory:
    """Create CLI input functions with optional prompt_toolkit support."""

    def __init__(
        self,
        fallback_to_input: bool = True,
        show_fallback_reason: bool = False,
    ) -> None:
        self.fallback_to_input = fallback_to_input
        self.show_fallback_reason = show_fallback_reason
        self._prompt_toolkit_error: Exception | None = None
        self._prompt_toolkit_available = self._detect_prompt_toolkit()

    def create_base(
        self,
        completion_words: Sequence[str],
        history_file: str | Path = ".commands_history",
        max_history_entries: int = 100,
    ) -> InputFunc:
        """Create command input with history, completion, and auto-suggestions."""
        result = self._try_prompt(
            prompt=BaseInput(
                history_file=history_file,
                max_history_entries=max_history_entries,
            ),
            fallback=input,
            completion_words=completion_words,
        )

        return result

    def create_editable(self) -> EditableInputFunc:
        """Create single-line editable input without history or suggestions."""
        result = self._try_prompt(
            prompt=EditableInput(),
            fallback=self._create_editable_fallback(),
        )

        return result

    def create_text(self) -> TextInputFunc:
        """Create multiline text input without history or suggestions."""
        result = self._try_prompt(
            prompt=TextInput(),
            fallback=self._create_text_fallback(),
        )

        return result

    def _detect_prompt_toolkit(self) -> bool:
        """Return whether prompt_toolkit can be used."""
        result = False

        try:
            import sys

            if not sys.stdin.isatty():
                raise OSError("stdin is not interactive")

            patch_windows_asyncio()

            import prompt_toolkit  # noqa: F401

            result = True
        except (ImportError, OSError, Exception) as error:
            self._prompt_toolkit_error = error

        return result

    def _try_prompt(
        self,
        *,
        prompt,
        fallback: PromptFunc,
        **params: object,
    ) -> PromptFunc:
        """Create prompt function or fallback."""
        result: PromptFunc | None = None
        error = self._prompt_toolkit_error

        if self._prompt_toolkit_available:
            try:
                result = prompt.create(**params)
            except (OSError, Exception) as prompt_error:
                error = prompt_error

        if result is None:
            if not self.fallback_to_input:
                raise RuntimeError("Prompt toolkit is not available.") from error

            if self.show_fallback_reason and error is not None:
                print(f"Prompt toolkit disabled: {error}")

            result = fallback

        return result

    @staticmethod
    def _create_editable_fallback() -> EditableInputFunc:
        """Create simple editable input fallback."""

        def editable_input(prompt: str, default: str) -> str | None:
            current = f" [{default}]" if default else ""
            result = input(f"{prompt}{current}\n> ")

            return result

        return editable_input

    @staticmethod
    def _create_text_fallback() -> TextInputFunc:
        """Create simple text input fallback."""

        def text_input(prompt: str, default: str) -> str:
            current = f" [{default}]" if default else ""
            result = input(f"{prompt}{current}\n> ") or default

            return result

        return text_input
