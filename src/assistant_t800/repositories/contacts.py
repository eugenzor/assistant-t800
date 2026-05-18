"""Репозиторій контактів: сховище у пам'яті процесу.

Реалізація на основі словника. Ключем виступає ім'я контакту,
приведене до нижнього регістру (з обрізаними пробілами), що дозволяє
шукати контакти без урахування регістру.
"""

from typing import Optional

from assistant_t800.domain.contacts import Contact


class ContactsRepository:
    """Просте in-memory сховище контактів.

    Інкапсулює доступ до внутрішнього словника та забезпечує
    нечутливий до регістру пошук за ім'ям.
    """

    def __init__(self) -> None:
        """Створює порожнє сховище контактів."""
        # Внутрішнє сховище: ключ — нормалізоване ім'я, значення — контакт
        self._data: dict[str, Contact] = {}

    @staticmethod
    def _key(name: str) -> str:
        """Нормалізує ім'я контакту для використання у якості ключа сховища."""
        return name.strip().lower()

    def add(self, contact: Contact) -> None:
        """Додає контакт до сховища.

        Кидає ``ValueError``, якщо контакт із таким ім'ям вже існує.
        """
        key = self._key(contact.name.value)
        if key in self._data:
            raise ValueError(f"Контакт «{contact.name.value}» вже існує")
        self._data[key] = contact

    def get(self, name: str) -> Optional[Contact]:
        """Повертає контакт за ім'ям або ``None``, якщо його немає."""
        return self._data.get(self._key(name))


    def exists(self, name: str) -> bool:
        """Перевіряє, чи зберігається у сховищі контакт з таким ім'ям."""
        return self._key(name) in self._data

    def all(self) -> list[Contact]:
        """Повертає список усіх збережених контактів."""
        return list(self._data.values())
