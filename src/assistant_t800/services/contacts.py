"""Сервіс роботи з контактами.

Інкапсулює бізнес-логіку над репозиторієм контактів: додавання,
отримання та перелічення контактів. Сервіс не залежить від конкретного
сховища — він працює через інтерфейс ``ContactsRepository``.
"""

from typing import Optional

from assistant_t800.domain.contacts import Contact
from assistant_t800.domain.fields import Name
from assistant_t800.repositories.contacts import ContactsRepository


class ContactsService:
    """Сервіс-фасад над репозиторієм контактів.

    Надає зручні методи для створення та читання контактів, ховаючи
    деталі роботи зі сховищем за простим інтерфейсом.
    """

    def __init__(self, repo: ContactsRepository) -> None:
        """Ініціалізує сервіс із заданим репозиторієм контактів."""
        # Зберігаємо посилання на репозиторій для подальших операцій
        self._repo = repo

    def add_contact(
        self,
        name: str,
        *,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
        birthday: Optional[str] = None,
    ) -> Contact:
        """Створює та зберігає новий контакт.

        Аргументи:
            name: ім'я контакту (обов'язкове).
            phone: телефон у форматі 10 цифр (необов'язковий).
            email: електронна адреса (необов'язкова).
            address: фізична адреса (необов'язкова).
            birthday: день народження у форматі DD.MM.YYYY (необов'язковий).

        Повертає:
            Створений об'єкт ``Contact``.
        """
        # Створюємо контакт із обов'язковим ім'ям
        contact = Contact(Name(name))
        # Поступово додаємо вказані необов'язкові поля
        if phone:
            contact.add_phone(phone)
        if email:
            contact.add_email(email)
        if address:
            contact.set_address(address)
        if birthday:
            contact.set_birthday(birthday)
        # Зберігаємо контакт у сховищі
        self._repo.add(contact)
        return contact

    def get_contact(self, name: str) -> Contact:
        """Повертає контакт за ім'ям або кидає ``KeyError``, якщо немає."""
        contact = self._repo.get(name)
        if contact is None:
            # Сигналізуємо про відсутність контакту українським повідомленням
            raise KeyError(f"Контакт «{name}» не знайдено")
        return contact

    def list_contacts(self) -> list[Contact]:
        """Повертає список усіх збережених контактів."""
        return self._repo.all()
