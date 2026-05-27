"""INI-based localization helpers."""

from configparser import ConfigParser
from enum import Enum
from locale import getlocale
from pathlib import Path
from sys import platform
from typing import ClassVar


class MultiLang:
    """Provide lazy-loaded localization by enum keys."""

    DEFAULT_LANGUAGE: ClassVar[str] = "en"
    LOCALE_DIR: ClassVar[Path] = Path(__file__).parent / "locales"

    _storage: ClassVar[dict[str, ConfigParser]] = {}

    @classmethod
    def get(cls, source: Enum) -> str:
        """Return localized text for an enum item."""
        language = cls._detect_language()
        config = cls._load(language)
        section = source.__class__.__name__
        key = source.name
        result = (
            cls._get_value(config, section, key)
            .replace(r"\n", "\n")
            .replace(r"\t", "    ")
        )

        return result

    @classmethod
    def _load(cls, language: str) -> ConfigParser:
        """Load locale config with fallback to default language."""
        if language not in cls._storage:
            config = ConfigParser()
            config.optionxform = str
            config.read(
                cls.LOCALE_DIR / f"{cls.DEFAULT_LANGUAGE}.ini", encoding="utf-8"
            )

            if language != cls.DEFAULT_LANGUAGE:
                config.read(cls.LOCALE_DIR / f"{language}.ini", encoding="utf-8")

            cls._storage[language] = config

        return cls._storage[language]

    @staticmethod
    def _get_value(config: ConfigParser, section: str, key: str) -> str:
        """Return one localized value or a visible fallback."""
        result = config.get(section, key, fallback=f"{section}.{key}")

        return result

    @classmethod
    def _detect_language(cls) -> str:
        """Return supported UI language code."""
        detected = (
            cls._detect_windows_language()
            if platform.startswith("win")
            else cls._detect_posix_language()
        )

        result = (
            detected
            if (cls.LOCALE_DIR / f"{detected}.ini").is_file()
            else cls.DEFAULT_LANGUAGE
        )

        return result

    @staticmethod
    def _detect_windows_language() -> str:
        """Return Windows UI language code."""
        try:
            import ctypes

            language_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            result = {0x0422: "uk", 0x0419: "ru"}.get(language_id, "en")
        except Exception:
            result = "en"

        return result

    @staticmethod
    def _detect_posix_language() -> str:
        """Return POSIX locale language code."""
        language = getlocale()[0] or ""
        result = language.split("_", maxsplit=1)[0] or "en"

        return result


def render_message(message: object | None) -> str:
    """Render an application message."""
    if message is None:
        result = ""
    else:
        result = message.code.render(**message.params)

    return result
