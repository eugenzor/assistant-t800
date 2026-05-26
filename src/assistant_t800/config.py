"""Application configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and `.env`.
    ``assistant_t800_model`` -> ``ASSISTANT_T800_MODEL``
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    assistant_t800_model: str = "google-gla:gemini-3.1-flash-lite"


settings = Settings()
