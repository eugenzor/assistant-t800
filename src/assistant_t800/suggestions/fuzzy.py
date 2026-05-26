from dataclasses import dataclass

from assistant_t800.suggestions.models import (
    CommandInfo,
    CommandSuggestion,
    SuggestionSource,
)
from assistant_t800.suggestions.registry import CommandRegistry

try:
    from rapidfuzz import fuzz

    HAS_RAPIDFUZZ = True
except ImportError:
    fuzz = None
    HAS_RAPIDFUZZ = False


@dataclass(frozen=True)
class FuzzySuggestionConfig:
    """Fuzzy suggestion configuration."""

    min_score: float = 65.0
    strong_score: float = 85.0
    max_suggestions: int = 3


class FuzzyCommandSuggester:
    """Suggest commands using fuzzy matching."""

    def __init__(
        self,
        registry: CommandRegistry,
        config: FuzzySuggestionConfig | None = None,
    ) -> None:
        self._registry = registry
        self._config = config or FuzzySuggestionConfig()

    @property
    def registry(self) -> CommandRegistry:
        """Return command registry."""
        return self._registry

    @property
    def config(self) -> FuzzySuggestionConfig:
        """Return fuzzy config."""
        return self._config

    def suggest(self, user_input: str) -> tuple[CommandSuggestion, ...]:
        """Return fuzzy command suggestions."""
        query = self._normalize(user_input)

        if not query:
            return ()

        candidates = [
            suggestion
            for command in self.registry.all()
            for suggestion in self._score_command(
                command=command,
                query=query,
            )
            if suggestion.score >= self.config.min_score
        ]

        best_by_command: dict[str, CommandSuggestion] = {}

        for suggestion in candidates:
            key = suggestion.command.name.casefold()
            current = best_by_command.get(key)

            if current is None or suggestion.score > current.score:
                best_by_command[key] = suggestion

        result = tuple(
            sorted(
                best_by_command.values(),
                key=lambda item: item.score,
                reverse=True,
            )[: self.config.max_suggestions]
        )

        return result

    def _score_command(
        self,
        command: CommandInfo,
        query: str,
    ) -> tuple[CommandSuggestion, ...]:
        """Score one command against query."""
        candidates = [
            (command.name, 1.15),
            (command.syntax, 1.00),
            (command.description, 0.85),
            *[(alias, 0.95) for alias in command.aliases],
        ]

        result = tuple(
            CommandSuggestion(
                command=command,
                score=self._score(
                    query,
                    self._normalize(candidate),
                )
                * weight,
                source=SuggestionSource.FUZZY,
                matched_by=candidate,
            )
            for candidate, weight in candidates
            if candidate
        )

        return result

    @staticmethod
    def _score(query: str, candidate: str) -> float:
        """Return similarity score."""
        if FuzzyCommandSuggester._is_phrase_prefix(
            query=query,
            candidate=candidate,
        ):
            result = 100.0
        elif HAS_RAPIDFUZZ:
            result = float(fuzz.ratio(query, candidate))
        else:
            result = FuzzyCommandSuggester._fallback_score(
                query=query,
                candidate=candidate,
            )

        return result

    @staticmethod
    def _is_phrase_prefix(
        query: str,
        candidate: str,
    ) -> bool:
        """Return whether candidate is a full phrase prefix of query."""
        if not query.startswith(candidate):
            result = False
        elif len(query) == len(candidate):
            result = True
        else:
            result = query[len(candidate)].isspace()

        return result

    @staticmethod
    def _fallback_score(
        query: str,
        candidate: str,
    ) -> float:
        """Return fallback similarity score without external dependencies."""
        from difflib import SequenceMatcher

        return (
            SequenceMatcher(
                None,
                query,
                candidate,
            ).ratio()
            * 100.0
        )

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize text before matching."""
        return " ".join(value.strip().casefold().split())
