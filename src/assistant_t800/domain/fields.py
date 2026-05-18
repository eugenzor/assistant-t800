"""Доменні типи полів контакту: ім'я, телефон, e-mail, адреса, день народження.

Кожен клас інкапсулює валідацію та нормалізацію свого значення.
Невалідні дані призводять до ``ValueError`` із повідомленням українською.
"""

import re
from datetime import date, datetime


class Field:
    """Базовий клас поля, що зберігає рядкове значення."""

    def __init__(self, value: str) -> None:
        """Зберігає вхідне значення без додаткової валідації."""
        self.value: str = value

    def __str__(self) -> str:
        """Повертає текстове представлення значення поля."""
        return str(self.value)


class Name(Field):
    """Ім'я контакту. Не може бути порожнім."""

    def __init__(self, value: str) -> None:
        """Валідує та зберігає ім'я, видаляючи зайві пробіли по краях."""
        if not value or not value.strip():
            # Порожнє ім'я неприпустиме
            raise ValueError("Ім'я не може бути порожнім")
        super().__init__(value.strip())


class Phone(Field):
    """Телефонний номер. Має містити рівно 10 цифр."""

    # Регулярний вираз для перевірки формату телефону (10 цифр)
    _PATTERN = re.compile(r"^\d{10}$")

    def __init__(self, value: str) -> None:
        """Валідує телефонний номер за патерном «10 цифр»."""
        normalized = (value or "").strip()
        if not self._PATTERN.fullmatch(normalized):
            raise ValueError("Номер телефону має містити рівно 10 цифр")
        super().__init__(normalized)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Повертає ``True``, якщо значення є валідним телефоном."""
        return isinstance(value, str) and bool(cls._PATTERN.fullmatch(value.strip()))


class Email(Field):
    """Електронна адреса. Перевіряється спрощеним регулярним виразом."""

    # Спрощений патерн для перевірки e-mail
    _PATTERN = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

    def __init__(self, value: str) -> None:
        """Валідує електронну адресу та зберігає її у нормалізованому вигляді."""
        normalized = (value or "").strip()
        if not self._PATTERN.fullmatch(normalized):
            raise ValueError("Некоректна електронна адреса")
        super().__init__(normalized)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Повертає ``True``, якщо значення є валідним e-mail."""
        return isinstance(value, str) and bool(cls._PATTERN.fullmatch(value.strip()))


class Address(Field):
    """Фізична адреса контакту. Не може бути порожньою."""

    def __init__(self, value: str) -> None:
        """Валідує адресу: вона має бути непорожнім рядком."""
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("Адреса не може бути порожньою")
        super().__init__(normalized)


class Birthday(Field):
    """День народження у форматі ``DD.MM.YYYY``.

    Не може бути в майбутньому.
    """

    # Формат дати, що використовується для парсингу та виведення
    DATE_FORMAT = "%d.%m.%Y"

    def __init__(self, value: str) -> None:
        """Парсить та валідує дату народження."""
        try:
            parsed = datetime.strptime((value or "").strip(), self.DATE_FORMAT).date()
        except (TypeError, ValueError):
            # Будь-яка помилка парсингу — некоректний формат
            raise ValueError("Некоректний формат дати. Використовуйте DD.MM.YYYY")
        if parsed > date.today():
            # День народження не може бути в майбутньому
            raise ValueError("День народження не може бути в майбутньому")
        super().__init__(parsed.strftime(self.DATE_FORMAT))
        # Зберігаємо також об'єкт ``date`` для зручних обчислень
        self.date: date = parsed

    def __str__(self) -> str:
        """Повертає дату у вигляді рядка формату ``DD.MM.YYYY``."""
        return self.date.strftime(self.DATE_FORMAT)
