"""Модуль CLI для запуску застосунку Assistant T800.

Містить точку входу `main`, яка парсить аргументи командного рядка
та обирає режим роботи (наразі підтримується лише AI-режим у TUI).
"""

import argparse

# Імпорт ``config`` має відбутися першим: завантажує ``.env`` у
# ``os.environ`` до того, як будь-який клієнт зчитає API-ключі.
from assistant_t800 import config  # noqa: F401


def main() -> None:
    """Точка входу CLI.

    Розбирає аргументи командного рядка та запускає відповідний режим.
    ``--enable-ai`` і запускає Textual UI.
    """
    # Створюємо парсер аргументів командного рядка
    parser = argparse.ArgumentParser(
        prog="assistant-t800",
        description="Особистий асистент T800.",
    )
    parser.add_argument(
        "--enable-ai",
        action="store_true",
        help="Запустити Textual TUI з підтримкою ШІ.",
    )
    args = parser.parse_args()

    if args.enable_ai:
        # Імпортуємо тут, аби не тягнути залежності Textual без потреби
        from assistant_t800.interfaces.textual.app import run_textual

        run_textual()
    else:
        # Звичайний (не AI) режим поки не реалізовано
        print("Звичайний режим ще не реалізовано. Використовуйте --enable-ai.")
