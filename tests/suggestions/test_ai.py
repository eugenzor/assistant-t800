"""Unit tests for AI command suggester in ``assistant_t800.suggestions.ai``.

External AI calls are mocked; no real network access is performed.
"""

import sys
import types

import pytest

from assistant_t800.suggestions import ai as ai_module
from assistant_t800.suggestions.ai import (
    AICommandSuggester,
    AICommandSuggesterConfig,
)
from assistant_t800.suggestions.ai_models import AICommandSuggestion
from assistant_t800.suggestions.models import (
    CommandSuggestion,
    SuggestionSource,
)
from assistant_t800.suggestions.registry import CommandRegistry


# ---------- helpers ----------


def _registry() -> CommandRegistry:
    """Build a small registry with a few commands."""
    registry = CommandRegistry()
    registry.add(
        name="help",
        description="Show help",
        syntax="help",
        aliases=("?",),
    )
    registry.add(
        name="remove",
        description="Remove contact",
        syntax="remove <name>",
        aliases=("delete",),
    )

    return registry


class _StubAgentResponse:
    """Stand-in for ``Agent.run_sync`` response."""

    def __init__(self, output: AICommandSuggestion) -> None:
        self.output = output


class _StubAgent:
    """Capture-only Agent stand-in used to bypass real AI calls.

    Instances expose the same surface ``AICommandSuggester._suggest`` relies on:
    ``run_sync`` returning an object with ``.output``.
    """

    last_init_kwargs: dict = {}
    response: AICommandSuggestion | None = None
    raise_on_run: Exception | None = None

    def __init__(self, model, *, output_type, system_prompt):
        _StubAgent.last_init_kwargs = {
            "model": model,
            "output_type": output_type,
            "system_prompt": system_prompt,
        }

    def run_sync(self, user_prompt):  # type: ignore[no-untyped-def]
        if _StubAgent.raise_on_run is not None:
            raise _StubAgent.raise_on_run

        return _StubAgentResponse(_StubAgent.response)


@pytest.fixture(autouse=True)
def _reset_stub_state():
    """Reset shared stub state between tests."""
    _StubAgent.last_init_kwargs = {}
    _StubAgent.response = None
    _StubAgent.raise_on_run = None
    yield
    _StubAgent.last_init_kwargs = {}
    _StubAgent.response = None
    _StubAgent.raise_on_run = None


@pytest.fixture(autouse=True)
def _isolate_dotenv(monkeypatch):
    """Prevent ``AICommandSuggesterConfig.__post_init__`` from reading a real .env.

    Otherwise a developer-local ``.env`` with API keys would override the
    ``monkeypatch.delenv`` calls in tests that expect "no key configured".
    """
    monkeypatch.setattr(
        AICommandSuggesterConfig,
        "_load_dotenv",
        staticmethod(lambda: None),
    )


@pytest.fixture
def patch_pydantic_ai(monkeypatch):
    """Install a fake ``pydantic_ai`` module exposing the stub Agent."""
    fake_module = types.ModuleType("pydantic_ai")
    fake_module.Agent = _StubAgent  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pydantic_ai", fake_module)
    return fake_module


@pytest.fixture
def patch_spinner(monkeypatch):
    """Replace ``Spinner`` with a no-op stand-in to avoid threads and stdout."""

    class _NoOpSpinner:
        def __init__(self, *args, **kwargs):
            self.started = False
            self.stopped = False

        def start(self):
            self.started = True

        def stop(self):
            self.stopped = True

    monkeypatch.setattr(ai_module, "Spinner", _NoOpSpinner)
    return _NoOpSpinner


# ---------- AICommandSuggesterConfig ----------


def test_config_default_min_confidence():
    config = AICommandSuggesterConfig()

    assert config.min_confidence == 70.0


def test_config_custom_min_confidence():
    config = AICommandSuggesterConfig(min_confidence=50.0)

    assert config.min_confidence == 50.0


def test_config_model_uses_google_when_google_api_key_set(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_MODEL", raising=False)

    config = AICommandSuggesterConfig()

    assert config.model == "google:gemini-3.1-flash-lite"


def test_config_model_uses_google_api_model_override(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    monkeypatch.setenv("GOOGLE_API_MODEL", "google:custom-model")

    config = AICommandSuggesterConfig()

    assert config.model == "google:custom-model"


def test_config_model_uses_openai_when_only_openai_key_set(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    monkeypatch.delenv("OPENAI_API_MODEL", raising=False)

    config = AICommandSuggesterConfig()

    assert config.model == "openai-chat:gpt-4o-mini"


def test_config_model_uses_openai_api_model_override(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    monkeypatch.setenv("OPENAI_API_MODEL", "openai-chat:custom")

    config = AICommandSuggesterConfig()

    assert config.model == "openai-chat:custom"


def test_config_model_prefers_google_over_openai_when_both_set(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-google")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai")
    monkeypatch.delenv("GOOGLE_API_MODEL", raising=False)

    config = AICommandSuggesterConfig()

    assert config.model.startswith("google:")


def test_config_model_returns_empty_when_no_keys(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = AICommandSuggesterConfig()

    assert config.model == ""


# ---------- AICommandSuggester: properties ----------


def test_suggester_exposes_registry_and_config():
    registry = _registry()
    config = AICommandSuggesterConfig(min_confidence=50.0)

    suggester = AICommandSuggester(registry, config=config)

    assert suggester.registry is registry
    assert suggester.config is config


def test_suggester_uses_default_config_when_none_supplied():
    suggester = AICommandSuggester(_registry())

    assert isinstance(suggester.config, AICommandSuggesterConfig)


# ---------- AICommandSuggester.available ----------


def test_available_false_when_no_model_configured(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    suggester = AICommandSuggester(_registry())

    assert suggester.available is False


def test_available_true_when_model_configured_and_pydantic_ai_present(
    monkeypatch,
    patch_pydantic_ai,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    suggester = AICommandSuggester(_registry())

    assert suggester.available is True


# ---------- AICommandSuggester.suggest: gating ----------


def test_suggest_returns_none_when_not_available(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    suggester = AICommandSuggester(_registry())

    assert suggester.suggest("anything") is None


# ---------- AICommandSuggester.suggest: success ----------


def test_suggest_returns_command_suggestion_on_success(
    monkeypatch,
    patch_pydantic_ai,
    patch_spinner,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.response = AICommandSuggestion(
        command="remove",
        arguments="Іван",
        confidence=90.0,
        reason="Semantic match",
    )

    suggester = AICommandSuggester(_registry())

    result = suggester.suggest("видали Іван")

    assert isinstance(result, CommandSuggestion)
    assert result.command.name == "remove"
    assert result.score == 90.0
    assert result.source is SuggestionSource.AI
    assert result.matched_by == "видали Іван"
    assert result.reason == "Semantic match"
    assert result.suggested_input == "remove Іван"


def test_suggest_includes_command_name_only_when_arguments_empty(
    monkeypatch,
    patch_pydantic_ai,
    patch_spinner,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.response = AICommandSuggestion(
        command="help",
        arguments="",
        confidence=95.0,
    )

    suggester = AICommandSuggester(_registry())

    result = suggester.suggest("допомога")

    assert result is not None
    assert result.suggested_input == "help"


def test_suggest_strips_whitespace_from_arguments(
    monkeypatch,
    patch_pydantic_ai,
    patch_spinner,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.response = AICommandSuggestion(
        command="remove",
        arguments="   Іван   ",
        confidence=90.0,
    )

    suggester = AICommandSuggester(_registry())

    result = suggester.suggest("видали Іван")

    assert result is not None
    assert result.suggested_input == "remove Іван"


# ---------- AICommandSuggester.suggest: rejections ----------


def test_suggest_returns_none_for_unknown_command(
    monkeypatch,
    patch_pydantic_ai,
    patch_spinner,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.response = AICommandSuggestion(
        command="non-existent-command",
        confidence=99.0,
    )

    suggester = AICommandSuggester(_registry())

    assert suggester.suggest("anything") is None


def test_suggest_returns_none_when_confidence_below_threshold(
    monkeypatch,
    patch_pydantic_ai,
    patch_spinner,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.response = AICommandSuggestion(
        command="remove",
        confidence=50.0,
    )

    suggester = AICommandSuggester(
        _registry(),
        config=AICommandSuggesterConfig(min_confidence=70.0),
    )

    assert suggester.suggest("anything") is None


def test_suggest_accepts_confidence_equal_to_min_threshold(
    monkeypatch,
    patch_pydantic_ai,
    patch_spinner,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.response = AICommandSuggestion(
        command="remove",
        confidence=70.0,
    )

    suggester = AICommandSuggester(
        _registry(),
        config=AICommandSuggesterConfig(min_confidence=70.0),
    )

    assert suggester.suggest("anything") is not None


# ---------- AICommandSuggester.suggest: error handling ----------


def test_suggest_returns_none_when_agent_raises_runtime_error(
    monkeypatch,
    patch_pydantic_ai,
    patch_spinner,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.raise_on_run = RuntimeError("boom")

    suggester = AICommandSuggester(_registry())

    assert suggester.suggest("anything") is None


def test_suggest_returns_none_when_agent_raises_value_error(
    monkeypatch,
    patch_pydantic_ai,
    patch_spinner,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.raise_on_run = ValueError("bad data")

    suggester = AICommandSuggester(_registry())

    assert suggester.suggest("anything") is None


def test_suggest_returns_none_when_agent_raises_timeout_error(
    monkeypatch,
    patch_pydantic_ai,
    patch_spinner,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.raise_on_run = TimeoutError("slow")

    suggester = AICommandSuggester(_registry())

    assert suggester.suggest("anything") is None


# ---------- Spinner lifecycle ----------


def test_suggest_starts_and_stops_spinner(
    monkeypatch,
    patch_pydantic_ai,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.response = AICommandSuggestion(
        command="help",
        confidence=95.0,
    )

    spinner_calls: list[str] = []

    class _RecordingSpinner:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            spinner_calls.append("start")

        def stop(self):
            spinner_calls.append("stop")

    monkeypatch.setattr(ai_module, "Spinner", _RecordingSpinner)

    suggester = AICommandSuggester(_registry())
    suggester.suggest("anything")

    assert spinner_calls == ["start", "stop"]


def test_suggest_stops_spinner_even_when_agent_raises(
    monkeypatch,
    patch_pydantic_ai,
):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    _StubAgent.raise_on_run = RuntimeError("boom")

    spinner_calls: list[str] = []

    class _RecordingSpinner:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            spinner_calls.append("start")

        def stop(self):
            spinner_calls.append("stop")

    monkeypatch.setattr(ai_module, "Spinner", _RecordingSpinner)

    suggester = AICommandSuggester(_registry())
    suggester.suggest("anything")

    assert spinner_calls == ["start", "stop"]


# ---------- _system_prompt / _user_prompt ----------


def test_system_prompt_lists_registered_commands():
    suggester = AICommandSuggester(_registry())

    prompt = suggester._system_prompt()

    assert "help" in prompt
    assert "remove" in prompt
    assert "Show help" in prompt
    assert "Remove contact" in prompt


def test_system_prompt_includes_aliases():
    suggester = AICommandSuggester(_registry())

    prompt = suggester._system_prompt()

    assert "?" in prompt
    assert "delete" in prompt


def test_user_prompt_wraps_input():
    prompt = AICommandSuggester._user_prompt("видали Іван")

    assert "видали Іван" in prompt
    assert prompt.startswith("User input:")
