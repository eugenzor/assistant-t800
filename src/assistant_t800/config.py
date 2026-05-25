"""Application configuration management."""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Export variables from `.env` into `os.environ` for third-party libraries
# that access environment variables directly.
load_dotenv()


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
