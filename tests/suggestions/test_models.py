"""Unit tests for suggestion data models in ``assistant_t800.suggestions.models``."""

import dataclasses

import pytest

from assistant_t800.suggestions.models import (
    CommandInfo,
    CommandSuggestion,
    SuggestionResult,
    SuggestionSource,
)


# ---------- SuggestionSource ----------


def test_suggestion_source_has_three_members():
    assert {member.name for member in SuggestionSource} == {"EXACT", "FUZZY", "AI"}


def test_suggestion_source_members_have_distinct_values():
    values = {member.value for member in SuggestionSource}

    assert len(values) == 3


# ---------- CommandInfo ----------


def test_command_info_defaults():
    info = CommandInfo(name="help")

    assert info.name == "help"
    assert info.description == ""
    assert info.syntax == ""
    assert info.args == ()
    assert info.optional_args == ()
    assert info.aliases == ()


def test_command_info_stores_all_fields():
    info = CommandInfo(
        name="add",
        description="Add a contact",
        syntax="add <name>",
        args=("name",),
        optional_args=("phone",),
        aliases=("create",),
    )

    assert info.description == "Add a contact"
    assert info.syntax == "add <name>"
    assert info.args == ("name",)
    assert info.optional_args == ("phone",)
    assert info.aliases == ("create",)


def test_command_info_is_frozen():
    info = CommandInfo(name="help")

    with pytest.raises(dataclasses.FrozenInstanceError):
        info.name = "exit"  # type: ignore[misc]


def test_command_info_equality_by_value():
    first = CommandInfo(name="help", description="Show help")
    second = CommandInfo(name="help", description="Show help")

    assert first == second


def test_command_info_inequality_by_name():
    first = CommandInfo(name="help")
    second = CommandInfo(name="exit")

    assert first != second


def test_command_info_default_aliases_are_isolated_between_instances():
    first = CommandInfo(name="a")
    second = CommandInfo(name="b")

    assert first.aliases == ()
    assert second.aliases == ()


# ---------- CommandSuggestion ----------


def test_command_suggestion_defaults_optional_fields():
    info = CommandInfo(name="help")
    suggestion = CommandSuggestion(
        command=info,
        score=42.0,
        source=SuggestionSource.FUZZY,
    )

    assert suggestion.command is info
    assert suggestion.score == 42.0
    assert suggestion.source is SuggestionSource.FUZZY
    assert suggestion.matched_by == ""
    assert suggestion.reason == ""
    assert suggestion.suggested_input == ""


def test_command_suggestion_stores_all_fields():
    info = CommandInfo(name="remove")
    suggestion = CommandSuggestion(
        command=info,
        score=85.5,
        source=SuggestionSource.AI,
        matched_by="видали",
        reason="Closest semantic match",
        suggested_input="remove Іван",
    )

    assert suggestion.matched_by == "видали"
    assert suggestion.reason == "Closest semantic match"
    assert suggestion.suggested_input == "remove Іван"


def test_command_suggestion_is_frozen():
    info = CommandInfo(name="help")
    suggestion = CommandSuggestion(
        command=info,
        score=42.0,
        source=SuggestionSource.FUZZY,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        suggestion.score = 50.0  # type: ignore[misc]


# ---------- SuggestionResult ----------


def test_suggestion_result_defaults():
    result = SuggestionResult(understood=False)

    assert result.understood is False
    assert result.command is None
    assert result.suggestions == ()


def test_suggestion_result_stores_command_and_suggestions():
    info = CommandInfo(name="help")
    suggestion = CommandSuggestion(
        command=info,
        score=100.0,
        source=SuggestionSource.EXACT,
    )

    result = SuggestionResult(
        understood=True,
        command=info,
        suggestions=(suggestion,),
    )

    assert result.understood is True
    assert result.command is info
    assert result.suggestions == (suggestion,)


def test_suggestion_result_is_frozen():
    result = SuggestionResult(understood=False)

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.understood = True  # type: ignore[misc]
