"""Unit tests for ``ResolutionService`` in ``assistant_t800.suggestions.resolution``."""

from assistant_t800.suggestions.models import (
    CommandInfo,
    CommandSuggestion,
    SuggestionSource,
)
from assistant_t800.suggestions.resolution import ResolutionService


def _suggestion(
    *,
    name: str = "get",
    args: tuple[str, ...] = ("name",),
    optional_args: tuple[str, ...] = (),
    source: SuggestionSource = SuggestionSource.FUZZY,
    suggested_input: str = "get Іван",
) -> CommandSuggestion:
    """Build a suggestion for resolution-service testing."""
    return CommandSuggestion(
        command=CommandInfo(name=name, args=args, optional_args=optional_args),
        score=80.0,
        source=source,
        matched_by=name,
        suggested_input=suggested_input,
    )


def _identity_refiner(suggestion: CommandSuggestion):
    """Build an AI refiner returning a sentinel suggestion."""

    def refiner(raw_input: str) -> CommandSuggestion | None:
        return suggestion

    return refiner


def _null_refiner(raw_input: str) -> CommandSuggestion | None:
    """AI refiner that always returns ``None``."""
    return None


# ---------- no refinement needed ----------


def test_resolve_returns_suggestion_when_argument_count_matches():
    suggestion = _suggestion(args=("name",), suggested_input="get Іван")
    service = ResolutionService(ai_refiner=_null_refiner)

    result = service.resolve("get Іван", suggestion)

    assert result is suggestion


def test_resolve_returns_suggestion_when_argument_count_below_max():
    suggestion = _suggestion(
        args=("name",),
        optional_args=("extra",),
        suggested_input="get Іван",
    )
    service = ResolutionService(ai_refiner=_null_refiner)

    result = service.resolve("get Іван", suggestion)

    assert result is suggestion


def test_resolve_does_not_refine_ai_suggestions():
    suggestion = _suggestion(
        source=SuggestionSource.AI,
        suggested_input="get Іван extra extra extra",
    )
    refined = _suggestion(suggested_input="refined")
    service = ResolutionService(ai_refiner=_identity_refiner(refined))

    result = service.resolve("get Іван extra extra extra", suggestion)

    assert result is suggestion, (
        "non-fuzzy suggestions must not be passed to the AI refiner"
    )


def test_resolve_does_not_refine_exact_suggestions():
    suggestion = _suggestion(
        source=SuggestionSource.EXACT,
        suggested_input="get Іван extra extra extra",
    )
    refined = _suggestion(suggested_input="refined")
    service = ResolutionService(ai_refiner=_identity_refiner(refined))

    result = service.resolve("get Іван extra extra extra", suggestion)

    assert result is suggestion


# ---------- refinement triggered ----------


def test_resolve_calls_ai_when_fuzzy_has_too_many_args():
    suggestion = _suggestion(
        args=("name",),
        suggested_input="get Іван extra extra",
    )
    refined = _suggestion(suggested_input="refined")
    service = ResolutionService(ai_refiner=_identity_refiner(refined))

    result = service.resolve("get Іван extra extra", suggestion)

    assert result is refined


def test_resolve_keeps_original_when_ai_returns_none():
    suggestion = _suggestion(
        args=("name",),
        suggested_input="get Іван extra extra",
    )
    service = ResolutionService(ai_refiner=_null_refiner)

    result = service.resolve("get Іван extra extra", suggestion)

    assert result is suggestion, (
        "AI returning None must not discard the original fuzzy suggestion"
    )


def test_resolve_passes_raw_input_to_ai_refiner():
    captured: dict[str, str] = {}

    def refiner(raw_input: str) -> CommandSuggestion | None:
        captured["raw_input"] = raw_input
        return None

    suggestion = _suggestion(
        args=("name",),
        suggested_input="get Іван extra extra",
    )
    service = ResolutionService(ai_refiner=refiner)

    service.resolve("the raw user input", suggestion)

    assert captured["raw_input"] == "the raw user input"
