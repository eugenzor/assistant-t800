import os
from dataclasses import dataclass

from assistant_t800.suggestions.spinner import Spinner
from assistant_t800.suggestions.ai_models import AICommandSuggestion
from assistant_t800.suggestions.models import (
    CommandSuggestion,
    SuggestionSource,
)
from assistant_t800.suggestions.registry import CommandRegistry

try:
    from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
except ImportError:
    ModelHTTPError = RuntimeError
    UnexpectedModelBehavior = RuntimeError


@dataclass(frozen=True)
class AICommandSuggesterConfig:
    """AI command suggester configuration."""

    min_confidence: float = 70.0

    def __post_init__(self) -> None:
        """Load environment variables from .env if available."""
        self._load_dotenv()

    @property
    def model(self) -> str:
        """Return configured AI model."""
        if os.getenv("GOOGLE_API_KEY"):
            result = os.getenv(
                "GOOGLE_API_MODEL",
                "google:gemini-3.1-flash-lite",
            )
        elif os.getenv("OPENAI_API_KEY"):
            result = os.getenv(
                "OPENAI_API_MODEL",
                "openai-chat:gpt-4o-mini",
            )
        else:
            result = ""

        return result

    @staticmethod
    def _load_dotenv() -> None:
        """Load .env file if python-dotenv is installed."""
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass


class AICommandSuggester:
    """Suggest command using optional Pydantic AI integration."""

    def __init__(
        self,
        registry: CommandRegistry,
        config: AICommandSuggesterConfig | None = None,
    ) -> None:
        self._registry = registry
        self._config = config or AICommandSuggesterConfig()

    @property
    def registry(self) -> CommandRegistry:
        """Return command registry."""
        return self._registry

    @property
    def config(self) -> AICommandSuggesterConfig:
        """Return config."""
        return self._config

    @property
    def available(self) -> bool:
        """Return whether AI suggestion can be used."""
        result = bool(self.config.model) and self._has_pydantic_ai()

        return result

    def suggest(self, user_input: str) -> CommandSuggestion | None:
        """Return AI command suggestion or None."""
        if not self.available:
            return None

        try:
            result = self._suggest(user_input)
        except (
            ModelHTTPError,
            UnexpectedModelBehavior,
            RuntimeError,
            ValueError,
            TimeoutError,
        ):
            result = None

        return result

    def _suggest(self, user_input: str) -> CommandSuggestion | None:
        """Run AI suggestion."""
        from pydantic_ai import Agent

        agent = Agent(
            self.config.model,
            output_type=AICommandSuggestion,
            system_prompt=self._system_prompt(),
        )

        spinner = Spinner()

        try:
            spinner.start()
            response = agent.run_sync(
                self._user_prompt(user_input),
            )
        finally:
            spinner.stop()

        ai_result = response.output
        command = self.registry.get(ai_result.command)

        if command is None or ai_result.confidence < self.config.min_confidence:
            result = None
        else:
            suggested_input = " ".join(
                [
                    command.name,
                    ai_result.arguments.strip(),
                ]
            ).strip()

            result = CommandSuggestion(
                command=command,
                score=ai_result.confidence,
                source=SuggestionSource.AI,
                matched_by=user_input,
                reason=ai_result.reason,
                suggested_input=suggested_input,
            )

        return result

    def _system_prompt(self) -> str:
        """Return AI system prompt."""
        commands = "\n".join(
            (
                f"- {command.name}: "
                f"{command.description}; "
                f"syntax: {command.syntax}; "
                f"aliases: {', '.join(command.aliases)}"
            )
            for command in self.registry.all()
        )

        return (
            "You are a command suggestion engine for a CLI personal assistant.\n"
            "Your task is to map user input to exactly one known command.\n"
            "Return only a structured result matching the schema.\n"
            "Do not invent commands.\n"
            "If arguments are present in user input, preserve them.\n\n"
            f"Available commands:\n{commands}"
        )

    @staticmethod
    def _user_prompt(user_input: str) -> str:
        """Return AI user prompt."""
        return f"User input: {user_input}"

    @staticmethod
    def _has_pydantic_ai() -> bool:
        """Return whether pydantic_ai is installed."""
        try:
            import pydantic_ai  # noqa: F401

            result = True
        except ImportError:
            result = False

        return result
