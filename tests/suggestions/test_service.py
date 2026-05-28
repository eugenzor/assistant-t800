"""Unit tests for ``SuggestionService`` in ``assistant_t800.suggestions.service``.

The AI sub-suggester is monkeypatched so tests do not require network access.
"""

import pytest

from assistant_t800.suggestions.fuzzy import FuzzySuggestionConfig
from assistant_t800.suggestions.models import (
    CommandInfo,
    CommandSuggestion,
    SuggestionSource,
)
from assistant_t800.suggestions.registry import CommandRegistry
from assistant_t800.suggestions.service import (
    SuggestionService,
    SuggestionServiceConfig,
)


def _registry(*specs) -> CommandRegistry:
    """Build a registry with the supplied command specs."""
    registry = CommandRegistry()
    for spec in specs:
        registry.add(**spec)

    return registry


def _silence_ai(monkeypatch: pytest.MonkeyPatch, service: SuggestionService) -> None:
    """Replace AI suggester so tests stay deterministic and offline."""
    monkeypatch.setattr(service._ai, "suggest", lambda user_input: None)


# ---------- exact match ----------


def test_suggest_exact_match_marks_understood(monkeypatch):
    registry = _registry({"name": "help"})
    service = SuggestionService(registry)
    _silence_ai(monkeypatch, service)

    result = service.suggest("help")

    assert result.understood is True
    assert result.command is not None
    assert result.command.name == "help"
    assert len(result.suggestions) == 1
    assert result.suggestions[0].source is SuggestionSource.EXACT
    assert result.suggestions[0].score == 100.0


def test_suggest_exact_match_preserves_user_input_as_suggested_input(monkeypatch):
    registry = _registry({"name": "get", "args": ("name",)})
    service = SuggestionService(registry)
    _silence_ai(monkeypatch, service)

    result = service.suggest("get Іван")

    assert result.suggestions[0].suggested_input == "get Іван"


# ---------- understood threshold ----------


def test_suggest_fuzzy_above_threshold_marks_understood(monkeypatch):
    registry = _registry({"name": "search"})
    service = SuggestionService(
        registry,
        fuzzy_config=FuzzySuggestionConfig(min_score=40.0),
        config=SuggestionServiceConfig(
            auto_understand_score=95.0,
            full_input_fallback_score=70.0,
            ai_fallback_score=200.0,  # disable AI fallback
        ),
    )
    _silence_ai(monkeypatch, service)

    result = service.suggest("search Іван")

    assert result.understood is True
    assert result.command is not None
    assert result.command.name == "search"


def test_suggest_fuzzy_below_threshold_does_not_mark_understood(monkeypatch):
    registry = _registry({"name": "search"})
    service = SuggestionService(
        registry,
        fuzzy_config=FuzzySuggestionConfig(min_score=20.0),
        config=SuggestionServiceConfig(
            auto_understand_score=99.0,
            full_input_fallback_score=10.0,
            ai_fallback_score=200.0,
        ),
    )
    _silence_ai(monkeypatch, service)

    result = service.suggest("xyzqzqz")

    assert result.understood is False
    assert result.command is None


# ---------- suggested_input reconstruction ----------


def test_suggest_extracts_tail_after_matched_phrase(monkeypatch):
    registry = _registry({"name": "search", "args": ("query",)})
    service = SuggestionService(
        registry,
        fuzzy_config=FuzzySuggestionConfig(min_score=20.0),
        config=SuggestionServiceConfig(ai_fallback_score=200.0),
    )
    _silence_ai(monkeypatch, service)

    result = service.suggest("search Іван")

    assert result.suggestions[0].suggested_input.startswith("search")
    assert "Іван" in result.suggestions[0].suggested_input


def test_suggest_falls_back_to_command_only_when_input_does_not_start_with_match(
    monkeypatch,
):
    """Below the full-input fallback score, only the command name is re-scored."""
    registry = _registry({"name": "search", "args": ("query",)})
    service = SuggestionService(
        registry,
        fuzzy_config=FuzzySuggestionConfig(min_score=20.0),
        config=SuggestionServiceConfig(
            full_input_fallback_score=90.0,
            ai_fallback_score=200.0,
        ),
    )
    _silence_ai(monkeypatch, service)

    result = service.suggest("seerch Іван")

    assert result.suggestions, "fallback path must still produce suggestions"


# ---------- AI fallback ----------


def test_suggest_falls_back_to_ai_when_fuzzy_is_weak(monkeypatch):
    registry = _registry({"name": "search"})
    service = SuggestionService(
        registry,
        fuzzy_config=FuzzySuggestionConfig(min_score=20.0),
        config=SuggestionServiceConfig(
            ai_fallback_score=99.0,
            min_ai_input_length=1,
            min_ai_word_count=1,
        ),
    )

    ai_suggestion = CommandSuggestion(
        command=CommandInfo(name="search"),
        score=92.0,
        source=SuggestionSource.AI,
        matched_by="search by phone",
        suggested_input="search 0501234567",
    )
    monkeypatch.setattr(service._ai, "suggest", lambda user_input: ai_suggestion)

    result = service.suggest("find by phone")

    assert any(item.source is SuggestionSource.AI for item in result.suggestions)


def test_suggest_skips_ai_when_input_too_short(monkeypatch):
    registry = _registry({"name": "search"})
    service = SuggestionService(
        registry,
        fuzzy_config=FuzzySuggestionConfig(min_score=20.0),
        config=SuggestionServiceConfig(
            ai_fallback_score=99.0,
            min_ai_input_length=50,
            min_ai_word_count=10,
        ),
    )
    called: dict[str, int] = {"count": 0}

    def fake_ai(user_input: str):
        called["count"] += 1
        return None

    monkeypatch.setattr(service._ai, "suggest", fake_ai)

    service.suggest("hi")

    assert called["count"] == 0, "AI must not be called for short input"


# ---------- refine_with_ai ----------


def test_refine_with_ai_delegates_to_ai_suggester(monkeypatch):
    registry = _registry({"name": "search"})
    service = SuggestionService(registry)
    ai_suggestion = CommandSuggestion(
        command=CommandInfo(name="search"),
        score=88.0,
        source=SuggestionSource.AI,
    )
    monkeypatch.setattr(service._ai, "suggest", lambda user_input: ai_suggestion)

    result = service.refine_with_ai("find ivan")

    assert result is ai_suggestion


# ---------- properties ----------


def test_registry_property_exposes_provided_registry():
    registry = CommandRegistry()
    service = SuggestionService(registry)

    assert service.registry is registry


def test_config_property_defaults_to_default_config():
    service = SuggestionService(CommandRegistry())

    assert isinstance(service.config, SuggestionServiceConfig)


def test_config_property_returns_supplied_config():
    config = SuggestionServiceConfig(auto_understand_score=50.0)
    service = SuggestionService(CommandRegistry(), config=config)

    assert service.config is config


# ---------- _split_input ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", ("", "")),
        ("   ", ("", "")),
        ("help", ("help", "")),
        ("get Іван", ("get", "Іван")),
        ("  search by name  Іван  ", ("search", "by name  Іван")),
    ],
)
def test_split_input_separates_command_and_tail(raw, expected):
    assert SuggestionService._split_input(raw) == expected
