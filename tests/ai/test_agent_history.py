"""Tests for chat-history handling in ``run_chat``.

The agent itself is patched so these tests run without calling an LLM —
they verify that history is replayed, updated, and capped correctly.
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from assistant_t800.ai import agent as agent_module
from assistant_t800.ai.deps import AgentDeps


def _user_request(text: str) -> ModelRequest:
    return ModelRequest(parts=[UserPromptPart(content=text)])


def _assistant_text(text: str) -> ModelResponse:
    return ModelResponse(parts=[TextPart(content=text)])


@dataclass
class _StubResult:
    """Mimics ``AgentRunResult`` for the fields ``run_chat`` consumes."""

    output: str
    messages: list[Any]

    def all_messages(self) -> list[Any]:
        return self.messages


@pytest.fixture
def patched_agent(monkeypatch):
    """Replace the cached pydantic-ai agent with a mock and expose its run_sync."""
    fake_agent = MagicMock()
    monkeypatch.setattr(agent_module, "_get_agent", lambda: fake_agent)
    return fake_agent


def test_run_chat_passes_existing_history_to_agent(patched_agent, deps):
    prior = [_user_request("hi"), _assistant_text("hello")]
    deps.message_history = list(prior)
    patched_agent.run_sync.return_value = _StubResult(
        output="ok", messages=prior + [_user_request("how?"), _assistant_text("fine")]
    )

    agent_module.run_chat("how?", deps)

    call_kwargs = patched_agent.run_sync.call_args.kwargs
    assert call_kwargs["message_history"] == prior


def test_run_chat_stores_updated_history(patched_agent, deps):
    full = [_user_request("hi"), _assistant_text("hello")]
    patched_agent.run_sync.return_value = _StubResult(output="hello", messages=full)

    agent_module.run_chat("hi", deps)

    assert deps.message_history == full


def test_run_chat_caps_history_at_max(patched_agent, deps, monkeypatch):
    monkeypatch.setattr(agent_module.settings, "max_history_messages", 4)
    long_history = []
    for i in range(5):
        long_history.append(_user_request(f"q{i}"))
        long_history.append(_assistant_text(f"a{i}"))
    patched_agent.run_sync.return_value = _StubResult(
        output="a4", messages=long_history
    )

    agent_module.run_chat("q4", deps)

    assert deps.message_history == long_history[-4:]


def test_run_chat_returns_agent_output(patched_agent, deps):
    patched_agent.run_sync.return_value = _StubResult(
        output="response text", messages=[]
    )

    assert agent_module.run_chat("hi", deps) == "response text"


def test_agent_deps_starts_with_empty_history():
    deps = AgentDeps(contacts_service=MagicMock(), presenter=MagicMock())

    assert deps.message_history == []
