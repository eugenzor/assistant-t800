"""Multiline text input implementation."""

from collections.abc import Callable

TextInputFunc = Callable[[str, str], str | None]


class TextInput:
    """Create multiline text input without history or suggestions."""

    def create(self) -> TextInputFunc:
        """Create prompt_toolkit multiline text input function."""
        from prompt_toolkit import PromptSession
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.keys import Keys

        bindings = KeyBindings()

        @bindings.add("enter")
        def _(event) -> None:
            event.current_buffer.insert_text("\n")

        @bindings.add("c-s")
        def _(event) -> None:
            event.app.current_buffer.validate_and_handle()

        @bindings.add(Keys.Escape)
        def _(event) -> None:
            event.app.exit(exception=KeyboardInterrupt)

        session = PromptSession(
            multiline=True,
            key_bindings=bindings,
            history=None,
            auto_suggest=None,
            completer=None,
            complete_while_typing=False,
            wrap_lines=True,
        )

        def text_input(prompt: str, default: str) -> str | None:
            try:
                result = session.prompt(
                    f"{prompt}\n",
                    default=default,
                    multiline=True,
                    wrap_lines=True,
                )
            except KeyboardInterrupt:
                result = None

            return result

        return text_input
