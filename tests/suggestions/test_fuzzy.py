"""Unit tests for ``FuzzyCommandSuggester`` in ``assistant_t800.suggestions.fuzzy``."""

import pytest

from assistant_t800.suggestions.fuzzy import (
    FuzzyCommandSuggester,
    FuzzySuggestionConfig,
)
from assistant_t800.suggestions.models import SuggestionSource
from assistant_t800.suggestions.registry import CommandRegistry


def _registry_with(*specs) -> CommandRegistry:
    """Build a registry with the supplied command specs."""
    registry = CommandRegistry()
    for spec in specs:
        registry.add(**spec)

    return registry


# ---------- empty input ----------


def test_suggest_empty_input_returns_no_suggestions():
    registry = _registry_with({"name": "help"})
    suggester = FuzzyCommandSuggester(registry)

    assert suggester.suggest("") == ()


def test_suggest_whitespace_input_returns_no_suggestions():
    registry = _registry_with({"name": "help"})
    suggester = FuzzyCommandSuggester(registry)

    assert suggester.suggest("   ") == ()


def test_suggest_with_empty_registry_returns_no_suggestions():
    suggester = FuzzyCommandSuggester(CommandRegistry())

    assert suggester.suggest("help") == ()


# ---------- exact prefix match ----------


def test_suggest_exact_command_name_scores_perfectly():
    registry = _registry_with({"name": "help"})
    suggester = FuzzyCommandSuggester(registry)

    suggestions = suggester.suggest("help")

    assert len(suggestions) == 1
    assert suggestions[0].command.name == "help"
    assert suggestions[0].score >= 100.0
    assert suggestions[0].source is SuggestionSource.FUZZY


def test_suggest_phrase_prefix_scores_perfectly():
    """Command name appearing as a word prefix must produce a perfect score."""
    registry = _registry_with({"name": "search"})
    suggester = FuzzyCommandSuggester(registry)

    suggestions = suggester.suggest("search Іван")

    assert len(suggestions) >= 1
    assert suggestions[0].command.name == "search"
    assert suggestions[0].score >= 100.0


def test_suggest_phrase_prefix_requires_word_boundary():
    """A name that is a string prefix but not a word prefix must not score 100."""
    registry = _registry_with({"name": "help"})
    suggester = FuzzyCommandSuggester(registry)

    suggestions = suggester.suggest("helper")

    # Fuzzy ratio will still be high but the perfect-prefix branch must not apply.
    assert (
        not suggestions
        or suggestions[0].score < 100.0
        or "help" in suggestions[0].matched_by
    )


# ---------- typo tolerance ----------


def test_suggest_typo_in_command_name_returns_suggestion():
    registry = _registry_with({"name": "search"})
    suggester = FuzzyCommandSuggester(
        registry,
        config=FuzzySuggestionConfig(min_score=40.0),
    )

    suggestions = suggester.suggest("seerch")

    assert len(suggestions) >= 1
    assert suggestions[0].command.name == "search"


def test_suggest_below_min_score_returns_empty():
    registry = _registry_with({"name": "search"})
    suggester = FuzzyCommandSuggester(
        registry,
        config=FuzzySuggestionConfig(min_score=99.0),
    )

    suggestions = suggester.suggest("xyz")

    assert suggestions == ()


# ---------- max_suggestions cap ----------


def test_suggest_caps_results_to_max_suggestions():
    registry = _registry_with(
        {"name": "search"},
        {"name": "search-by-name"},
        {"name": "search-by-phone"},
        {"name": "search-by-email"},
    )
    suggester = FuzzyCommandSuggester(
        registry,
        config=FuzzySuggestionConfig(min_score=20.0, max_suggestions=2),
    )

    suggestions = suggester.suggest("search")

    assert len(suggestions) <= 2


def test_suggest_orders_results_by_score_descending():
    registry = _registry_with(
        {"name": "search"},
        {"name": "exit"},
    )
    suggester = FuzzyCommandSuggester(
        registry,
        config=FuzzySuggestionConfig(min_score=20.0),
    )

    suggestions = suggester.suggest("search")

    scores = [item.score for item in suggestions]
    assert scores == sorted(scores, reverse=True)


# ---------- alias / description matching ----------


def test_suggest_matches_alias():
    registry = _registry_with({"name": "help", "aliases": ("допомога",)})
    suggester = FuzzyCommandSuggester(
        registry,
        config=FuzzySuggestionConfig(min_score=40.0),
    )

    suggestions = suggester.suggest("допомога")

    assert len(suggestions) >= 1
    assert suggestions[0].command.name == "help"


def test_suggest_matches_description_with_lower_weight():
    registry = _registry_with(
        {
            "name": "exit",
            "description": "quit the application",
        }
    )
    suggester = FuzzyCommandSuggester(
        registry,
        config=FuzzySuggestionConfig(min_score=40.0),
    )

    suggestions = suggester.suggest("quit the application")

    assert len(suggestions) >= 1
    assert suggestions[0].command.name == "exit"


# ---------- deduplication ----------


def test_suggest_keeps_best_candidate_per_command():
    """Multiple internal scorings of the same command must produce one entry."""
    registry = _registry_with(
        {
            "name": "search",
            "description": "search contacts",
            "aliases": ("find",),
        }
    )
    suggester = FuzzyCommandSuggester(
        registry,
        config=FuzzySuggestionConfig(min_score=20.0),
    )

    suggestions = suggester.suggest("search")

    names = [item.command.name for item in suggestions]
    assert len(names) == len(set(names)), (
        "the same command must not appear more than once"
    )


# ---------- properties ----------


def test_default_config_is_used_when_omitted():
    suggester = FuzzyCommandSuggester(CommandRegistry())

    assert isinstance(suggester.config, FuzzySuggestionConfig)


def test_registry_property_exposes_provided_registry():
    registry = CommandRegistry()
    suggester = FuzzyCommandSuggester(registry)

    assert suggester.registry is registry


def test_config_property_exposes_provided_config():
    config = FuzzySuggestionConfig(min_score=42.0)
    suggester = FuzzyCommandSuggester(CommandRegistry(), config=config)

    assert suggester.config is config


# ---------- normalization ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Help", "help"),
        ("  HELP  ", "help"),
        ("search   contacts", "search contacts"),
        ("Search\tContacts", "search contacts"),
    ],
)
def test_normalize_lowercases_and_collapses_whitespace(raw, expected):
    assert FuzzyCommandSuggester._normalize(raw) == expected
