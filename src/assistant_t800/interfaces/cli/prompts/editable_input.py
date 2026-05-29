"""Single-line editable input implementation."""

from collections.abc import Callable

EditableInputFunc = Callable[[str, str], str | None]


class EditableInput:
    """Create single-line editable input without history or suggestions."""

    def create(self) -> EditableInputFunc:
        """Create prompt_toolkit editable input function."""
        from prompt_toolkit import PromptSession
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.keys import Keys

        bindings = KeyBindings()

        @bindings.add(Keys.Escape)
        def _(event) -> None:
            event.app.exit(result=None)

        session = PromptSession(
            history=None,
            auto_suggest=None,
            completer=None,
            complete_while_typing=False,
            key_bindings=bindings,
        )

        def editable_input(prompt: str, default: str) -> str | None:
            result = session.prompt(
                prompt,
                default=default,
            )

            return result

        return editable_input
