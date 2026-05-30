"""Tests for AI tag suggestion module."""

from unittest.mock import Mock, patch

from assistant_t800.ai.tag_suggester import (
    MAX_SUGGESTED_TAGS,
    _build_prompt,
    suggest_tags,
)


def test_build_prompt_contains_contact_data() -> None:
    """Prompt must contain contact snapshot data."""
    snapshot = {
        "name": "Alice",
        "country": "USA",
        "city": "New York",
        "note": "Railroad trip",
        "tags": ["travel"],
    }

    prompt = _build_prompt(snapshot)

    assert "Alice" in prompt
    assert "USA" in prompt
    assert "New York" in prompt
    assert "Railroad trip" in prompt
    assert "travel" in prompt


def test_build_prompt_mentions_final_tags_mode() -> None:
    """Prompt must explain final tag set behaviour."""
    prompt = _build_prompt(
        {
            "name": "Alice",
            "tags": [],
        }
    )

    assert "best final tags" in prompt
    assert str(MAX_SUGGESTED_TAGS) in prompt


@patch("assistant_t800.ai.tag_suggester._get_agent")
def test_suggest_tags_returns_ai_tags(mock_get_agent: Mock) -> None:
    """AI tags must be returned unchanged."""
    response = Mock()
    response.output.tags = [
        "подорож",
        "коннектикут",
        "залізниця",
    ]

    agent = Mock()
    agent.run_sync.return_value = response

    mock_get_agent.return_value = agent

    result = suggest_tags(
        {
            "name": "Alice",
            "tags": ["старий-тег"],
        }
    )

    assert result == [
        "подорож",
        "коннектикут",
        "залізниця",
    ]


@patch("assistant_t800.ai.tag_suggester._get_agent")
def test_suggest_tags_allows_existing_tags(mock_get_agent: Mock) -> None:
    """Existing tags may appear in final AI result."""
    response = Mock()
    response.output.tags = [
        "подорож",
        "коннектикут",
    ]

    agent = Mock()
    agent.run_sync.return_value = response

    mock_get_agent.return_value = agent

    result = suggest_tags(
        {
            "name": "Alice",
            "tags": [
                "подорож",
                "коннектикут",
            ],
        }
    )

    assert result == [
        "подорож",
        "коннектикут",
    ]


@patch("assistant_t800.ai.tag_suggester._get_agent")
def test_suggest_tags_supports_empty_result(mock_get_agent: Mock) -> None:
    """Empty AI result must be handled."""
    response = Mock()
    response.output.tags = []

    agent = Mock()
    agent.run_sync.return_value = response

    mock_get_agent.return_value = agent

    result = suggest_tags(
        {
            "name": "Alice",
            "tags": [],
        }
    )

    assert result == []


@patch("assistant_t800.ai.tag_suggester._get_agent")
def test_suggest_tags_passes_prompt_to_agent(mock_get_agent: Mock) -> None:
    """Generated prompt must be passed to AI agent."""
    response = Mock()
    response.output.tags = []

    agent = Mock()
    agent.run_sync.return_value = response

    mock_get_agent.return_value = agent

    snapshot = {
        "name": "Alice",
        "country": "USA",
    }

    suggest_tags(snapshot)

    prompt = agent.run_sync.call_args.args[0]

    assert "Alice" in prompt
    assert "USA" in prompt

@patch("assistant_t800.ai.tag_suggester._get_agent")
def test_suggest_tags_does_not_remove_existing_tags_from_ai_result(
    mock_get_agent: Mock,
) -> None:
    """AI result must not be filtered against existing tags."""
    response = Mock()
    response.output.tags = [
        "подорож",
        "коннектикут",
    ]

    agent = Mock()
    agent.run_sync.return_value = response

    mock_get_agent.return_value = agent

    result = suggest_tags(
        {
            "tags": [
                "подорож",
                "коннектикут",
            ],
        }
    )

    assert result == [
        "подорож",
        "коннектикут",
    ]