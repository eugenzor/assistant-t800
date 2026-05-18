"""Залежності AI-агента: інтерфейс презентера та контейнер залежностей.

Цей модуль визначає протокол ``Presenter`` для виведення інформації
у користувацький інтерфейс та структуру ``AgentDeps``, яку отримує
агент під час виконання інструментів.
"""

from dataclasses import dataclass
from typing import Protocol

from assistant_t800.domain.contacts import Contact
from assistant_t800.services.contacts import ContactsService


class Presenter(Protocol):
    """Протокол презентера для виведення даних користувачу.

    Реалізації повинні підтримувати оновлення списку контактів
    та виведення довільного текстового повідомлення.
    """

    def refresh_contacts(self, contacts: list[Contact]) -> None:
        """Оновлює відображення списком контактів."""
        ...

    def print(self, text: str) -> None:
        """Виводить довільний текст у панель відображення."""
        ...


@dataclass
class AgentDeps:
    """Контейнер залежностей, які передаються AI-агенту під час виклику.

    Атрибути:
        contacts_service: сервіс для роботи з контактами.
        presenter: об'єкт для виведення інформації у UI.
    """

    contacts_service: ContactsService
    presenter: Presenter
