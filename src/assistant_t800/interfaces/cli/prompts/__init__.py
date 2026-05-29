"""CLI prompt implementations."""

from assistant_t800.interfaces.cli.prompts.base_input import BaseInput, InputFunc
from assistant_t800.interfaces.cli.prompts.editable_input import (
    EditableInput,
    EditableInputFunc,
)
from assistant_t800.interfaces.cli.prompts.text_input import TextInput, TextInputFunc

__all__ = (
    "BaseInput",
    "InputFunc",
    "EditableInput",
    "EditableInputFunc",
    "TextInput",
    "TextInputFunc",
)
