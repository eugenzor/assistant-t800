"""Конфігурація застосунку, що читається з ``.env`` через ``pydantic-settings``.

Налаштування експонуються через екземпляр ``settings`` і використовуються
іншими модулями (наприклад, AI-агентом) замість прямого читання
змінних середовища.
"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Експортуємо змінні з ``.env`` у ``os.environ``, щоб бібліотеки, які
# читають env-змінні напряму (наприклад, провайдер Google у pydantic-ai),
# бачили їх без додаткового експорту в оболонці.
load_dotenv()


class Settings(BaseSettings):
    """Налаштування застосунку Assistant T800.

    Значення підвантажуються зі змінних середовища або з файлу ``.env``
    у корені проєкту. Зіставлення імен — регістронезалежне: атрибут
    ``assistant_t800_model`` відповідає змінній ``ASSISTANT_T800_MODEL``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    assistant_t800_model: str = "google-gla:gemini-3.1-flash-lite"


settings = Settings()
