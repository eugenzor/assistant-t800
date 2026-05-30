"""Narrow AI tag suggestion module."""

import json
import os
from typing import Final

from pydantic import BaseModel
from pydantic_ai import Agent

from assistant_t800.config import settings

DEFAULT_MODEL: Final[str] = "google:gemini-3.1-flash-lite"

MAX_SUGGESTED_TAGS = 7

TAG_SUGGESTION_SYSTEM_PROMPT: Final[str] = f"""\
You are a strict contact tag suggestion engine.

Return ONLY structured output matching the requested schema.
Do not explain anything.
Do not include markdown.
Do not include comments.
Do not invent private or sensitive facts.

Task:
Return the best final tag set for a contact profile.

The command means:
"Suggest the {MAX_SUGGESTED_TAGS} most relevant tags for this contact."

It does NOT mean:
- suggest only new tags;
- suggest only tags different from existing tags;
- append tags to existing tags;
- avoid existing tags.

Input may contain:
- name
- country
- city
- note
- existing tags

Rules:
1. Existing tags are context only.
2. Existing tags may be reused freely.
3. Existing tags are not forbidden.
4. Existing tags are not automatically included.
5. Choose tags only by relevance to the contact profile.
6. Return the best final tag set, not additional tags.
7. Do not return an empty list only because suitable tags already exist.
8. If existing tags are already the best tags, return them.
9. If better tags can be derived from the profile, return the better tags.
10. Return up to {MAX_SUGGESTED_TAGS} tags total.

11. Tags must be meaningful keywords.
12. Tags must help categorize, search, or identify the contact later.
13. Prefer concepts, places, activities, interests, relationships, professions, organizations, projects, or useful categories.
14. Do not generate random frequent words from the note.
15. Avoid tag spam.
16. Avoid duplicates.
17. Avoid near-duplicates.
18. Avoid many broader/narrower variants of the same concept.

19. Preserve the language of the source data.
20. Do not translate words from notes, address, city, country, or existing tags.
21. If a useful tag comes from Ukrainian text, return it in Ukrainian.
22. If a useful tag comes from English text, return it in English.
23. Do not convert Ukrainian tags into English.
24. Do not convert English tags into Ukrainian.

25. Use lowercase tags where reasonable.
26. Avoid full sentences.
27. Avoid explanations.
28. Avoid personal assumptions.
29. Do not invent facts not present in the provided data.
30. Return an empty list only when the contact profile has no meaningful taggable information.

Output:
Return a list named "tags".
The list must contain the proposed final tags for this contact.
"""


class _TagSuggestion(BaseModel):
    """Structured output schema for tag suggestions."""

    tags: list[str]


def _get_agent() -> Agent[None, _TagSuggestion]:
    """Create a narrow AI agent for tag suggestions only."""
    model = os.environ.get("ASSISTANT_T800_MODEL", settings.assistant_t800_model)
    agent: Agent[None, _TagSuggestion] = Agent(
        model or DEFAULT_MODEL,
        output_type=_TagSuggestion,
        system_prompt=TAG_SUGGESTION_SYSTEM_PROMPT,
    )

    return agent


def suggest_tags(snapshot: dict[str, object]) -> list[str]:
    """Return AI tag suggestions for a contact snapshot."""
    prompt = _build_prompt(snapshot)
    result = _get_agent().run_sync(prompt)

    return result.output.tags


def _build_prompt(snapshot: dict[str, object]) -> str:
    """Build deterministic JSON prompt payload."""
    payload = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
    )

    result = (
        "Contact profile JSON:\n"
        f"{payload}\n\n"
        f"Return up to {MAX_SUGGESTED_TAGS} best final tags for this contact. "
        "Existing tags are context and may be reused. "
        "Do not return only new tags."
    )

    return result
