"""Application configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and `.env`.
    ``assistant_t800_model`` -> ``ASSISTANT_T800_MODEL``
    ``max_history_messages`` -> ``ASSISTANT_T800_MAX_HISTORY_MESSAGES``
    ``max_contacts_in_tool_return`` -> ``ASSISTANT_T800_MAX_CONTACTS_IN_TOOL_RETURN``
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    assistant_t800_model: str = "google:gemini-3.1-flash-lite"
    max_history_messages: int = 10
    max_contacts_in_tool_return: int = 25


settings = Settings()
