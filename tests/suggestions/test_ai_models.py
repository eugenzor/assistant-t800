"""Unit tests for ``AICommandSuggestion`` pydantic model.

The model wraps the structured AI output and validates ranges (``confidence``
must be between 0 and 100 inclusive).
"""

import pytest
from pydantic import ValidationError

from assistant_t800.suggestions.ai_models import AICommandSuggestion


# ---------- construction ----------


def test_ai_command_suggestion_minimal_fields():
    suggestion = AICommandSuggestion(command="help", confidence=80.0)

    assert suggestion.command == "help"
    assert suggestion.confidence == 80.0
    assert suggestion.arguments == ""
    assert suggestion.reason == ""


def test_ai_command_suggestion_stores_all_fields():
    suggestion = AICommandSuggestion(
        command="remove",
        arguments="Іван",
        confidence=95.5,
        reason="Closest semantic match",
    )

    assert suggestion.arguments == "Іван"
    assert suggestion.reason == "Closest semantic match"
    assert suggestion.confidence == 95.5


# ---------- confidence range validation ----------


def test_ai_command_suggestion_confidence_accepts_zero():
    suggestion = AICommandSuggestion(command="help", confidence=0.0)

    assert suggestion.confidence == 0.0


def test_ai_command_suggestion_confidence_accepts_one_hundred():
    suggestion = AICommandSuggestion(command="help", confidence=100.0)

    assert suggestion.confidence == 100.0


def test_ai_command_suggestion_rejects_negative_confidence():
    with pytest.raises(ValidationError):
        AICommandSuggestion(command="help", confidence=-0.1)


def test_ai_command_suggestion_rejects_confidence_above_one_hundred():
    with pytest.raises(ValidationError):
        AICommandSuggestion(command="help", confidence=100.1)


# ---------- required fields ----------


def test_ai_command_suggestion_requires_command():
    with pytest.raises(ValidationError):
        AICommandSuggestion(confidence=50.0)  # type: ignore[call-arg]


def test_ai_command_suggestion_requires_confidence():
    with pytest.raises(ValidationError):
        AICommandSuggestion(command="help")  # type: ignore[call-arg]
