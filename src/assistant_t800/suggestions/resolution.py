from collections.abc import Callable
from dataclasses import dataclass

from assistant_t800.suggestions.models import (
    CommandSuggestion,
    SuggestionSource,
)

AIRefiner = Callable[[str], CommandSuggestion | None]


@dataclass(frozen=True)
class ResolutionService:
    """Resolve final suggestion candidate."""

    ai_refiner: AIRefiner

    def resolve(
        self,
        raw_input: str,
        suggestion: CommandSuggestion,
    ) -> CommandSuggestion:
        """Return final suggestion candidate."""
        result = suggestion

        if self._needs_ai_refinement(suggestion):
            refined = self.ai_refiner(raw_input)

            if refined is not None:
                result = refined

        return result

    @staticmethod
    def _needs_ai_refinement(
        suggestion: CommandSuggestion,
    ) -> bool:
        """Return whether fuzzy suggestion should be refined by AI."""
        if suggestion.source != SuggestionSource.FUZZY:
            result = False
        else:
            args_count = len(suggestion.suggested_input.split()[1:])
            max_args = len(suggestion.command.args) + len(
                suggestion.command.optional_args
            )

            result = args_count > max_args

        return result
