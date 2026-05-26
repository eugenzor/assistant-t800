from dataclasses import dataclass

from assistant_t800.suggestions.fuzzy import (
    FuzzyCommandSuggester,
    FuzzySuggestionConfig,
)
from assistant_t800.suggestions.models import (
    CommandSuggestion,
    SuggestionResult,
    SuggestionSource,
)
from assistant_t800.suggestions.registry import CommandRegistry
from assistant_t800.suggestions.ai import AICommandSuggester
from assistant_t800.suggestions.resolution import ResolutionService


@dataclass(frozen=True)
class SuggestionServiceConfig:
    """Suggestion service configuration."""

    auto_understand_score: float = 95.0
    full_input_fallback_score: float = 70.0
    ai_fallback_score: float = 80.0
    min_ai_input_length: int = 8
    min_ai_word_count: int = 2


class SuggestionService:
    """Resolve command understanding and suggestions."""

    def __init__(
        self,
        registry: CommandRegistry,
        fuzzy_config: FuzzySuggestionConfig | None = None,
        config: SuggestionServiceConfig | None = None,
    ) -> None:
        self._registry = registry
        self._fuzzy = FuzzyCommandSuggester(
            registry=registry,
            config=fuzzy_config,
        )
        self._config = config or SuggestionServiceConfig()
        self._ai = AICommandSuggester(registry)
        self._resolution = ResolutionService(
            ai_refiner=self.refine_with_ai,
        )

    @property
    def registry(self) -> CommandRegistry:
        """Return command registry."""
        return self._registry

    @property
    def config(self) -> SuggestionServiceConfig:
        """Return service configuration."""
        return self._config

    def suggest(self, user_input: str) -> SuggestionResult:
        """Return command understanding or suggestions."""
        command_name, command_tail = self._split_input(user_input)
        exact = self.registry.get(command_name)

        if exact is not None:
            result = SuggestionResult(
                understood=True,
                command=exact,
                suggestions=(
                    CommandSuggestion(
                        command=exact,
                        score=100.0,
                        source=SuggestionSource.EXACT,
                        matched_by=command_name,
                        suggested_input=user_input.strip(),
                    ),
                ),
            )
        else:
            suggestions = self._build_fuzzy_suggestions(
                user_input=user_input,
                command_name=command_name,
                command_tail=command_tail,
            )
            best = suggestions[0] if suggestions else None

            result = SuggestionResult(
                understood=(
                    best is not None and best.score >= self.config.auto_understand_score
                ),
                command=(
                    best.command
                    if best is not None
                    and best.score >= self.config.auto_understand_score
                    else None
                ),
                suggestions=suggestions,
            )

        return result

    def refine_with_ai(
        self,
        user_input: str,
    ) -> CommandSuggestion | None:
        """Force AI command refinement."""
        return self._ai.suggest(user_input)

    def _build_fuzzy_suggestions(
        self,
        user_input: str,
        command_name: str,
        command_tail: str,
    ) -> tuple[CommandSuggestion, ...]:
        """Build fuzzy or AI suggestions with executable input."""
        suggestions = self._fuzzy.suggest(user_input)
        fallback_tail = ""

        best = suggestions[0] if suggestions else None

        if best is None or best.score < self.config.full_input_fallback_score:
            suggestions = self._fuzzy.suggest(command_name)
            fallback_tail = command_tail

        best = suggestions[0] if suggestions else None

        if self._can_use_ai(user_input) and (
            best is None or best.score < self.config.ai_fallback_score
        ):
            ai_suggestion = self._ai.suggest(user_input)

            if ai_suggestion is not None:
                suggestions = (ai_suggestion,)

        result = tuple(
            self._with_suggested_input(
                suggestion=suggestion,
                user_input=user_input,
                fallback_tail=fallback_tail,
            )
            for suggestion in suggestions
        )

        if result:
            result = (
                self._resolution.resolve(
                    raw_input=user_input,
                    suggestion=result[0],
                ),
                *result[1:],
            )

        return result

    def _can_use_ai(self, user_input: str) -> bool:
        """Return whether AI fallback makes sense."""
        normalized = " ".join(user_input.strip().split())

        result = (
            len(normalized) >= self.config.min_ai_input_length
            and len(normalized.split()) >= self.config.min_ai_word_count
        )

        return result

    @staticmethod
    def _with_suggested_input(
        suggestion: CommandSuggestion,
        user_input: str,
        fallback_tail: str,
    ) -> CommandSuggestion:
        """Return suggestion with executable command input."""
        if suggestion.suggested_input:
            return suggestion

        tail = SuggestionService._extract_tail_by_match(
            user_input=user_input,
            matched_by=suggestion.matched_by,
            fallback_tail=fallback_tail,
        )

        return CommandSuggestion(
            command=suggestion.command,
            score=suggestion.score,
            source=suggestion.source,
            matched_by=suggestion.matched_by,
            reason=suggestion.reason,
            suggested_input=" ".join(
                [
                    suggestion.command.name,
                    tail,
                ]
            ).strip(),
        )

    @staticmethod
    def _extract_tail_by_match(
        user_input: str,
        matched_by: str,
        fallback_tail: str,
    ) -> str:
        """Return user input tail after matched phrase."""
        normalized_input = user_input.strip()
        normalized_match = matched_by.strip()

        if normalized_input.casefold().startswith(normalized_match.casefold()):
            result = normalized_input[len(normalized_match) :].strip()
        else:
            result = fallback_tail

        return result

    @staticmethod
    def _split_input(user_input: str) -> tuple[str, str]:
        """Split command and tail."""
        parts = user_input.strip().split(
            maxsplit=1,
        )

        result = (
            (parts[0], parts[1])
            if len(parts) > 1
            else (parts[0], "")
            if parts
            else ("", "")
        )

        return result
