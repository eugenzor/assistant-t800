from pydantic import BaseModel, Field


class AICommandSuggestion(BaseModel):
    """Structured AI command suggestion."""

    command: str = Field(
        description="Command name from the provided command list.",
    )
    arguments: str = Field(
        default="",
        description="Command arguments without command name.",
    )
    confidence: float = Field(
        ge=0.0,
        le=100.0,
        description="Suggestion confidence from 0 to 100.",
    )
    reason: str = Field(
        default="",
        description="Short reason for this suggestion.",
    )
