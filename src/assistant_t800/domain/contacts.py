"""Доменна модель ``Contact``: контакт із полями телефонів, e-mail тощо.

Містить клас контакту з методами для керування його полями та
валідацією через відповідні доменні типи з модуля ``fields``.
"""

from typing import Optional

from assistant_t800.domain.fields import Address, Birthday, Email, Name, Phone


class Contact:
    """Доменний об'єкт «Контакт».

    Атрибути:
        name: ім'я (обов'язкове).
        phones: список телефонів.
        emails: список електронних адрес.
        address: фізична адреса (необов'язкова).
        birthday: день народження (необов'язковий).
    """

    def __init__(self, name: Name) -> None:
        """Створює контакт із заданим іменем і порожніми колекціями."""
        self.name: Name = name
        self.phones: list[Phone] = []
        self.emails: list[Email] = []
        self.address: Optional[Address] = None
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone: str) -> None:
        """Додає телефон до контакту.

        Кидає ``ValueError``, якщо такий телефон вже присутній.
        """
        new_phone = Phone(phone)
        # Перевіряємо, чи такий номер уже є серед телефонів контакту
        if self.find_phone(new_phone.value) is not None:
            raise ValueError(f"Телефон {new_phone.value} вже існує")
        self.phones.append(new_phone)

    def find_phone(self, phone: str) -> Optional[Phone]:
        """Шукає телефон за точним значенням і повертає його або ``None``."""
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_email(self, email: str) -> None:
        """Додає електронну адресу до контакту.

        Кидає ``ValueError``, якщо така адреса вже присутня.
        """
        new_email = Email(email)
        if self.find_email(new_email.value) is not None:
            raise ValueError(f"E-mail {new_email.value} вже існує")
        self.emails.append(new_email)

    def set_address(self, address: str) -> None:
        """Встановлює або замінює адресу контакту."""
        self.address = Address(address)

    def set_birthday(self, birthday: str) -> None:
        """Встановлює або замінює день народження (DD.MM.YYYY)."""
        self.birthday = Birthday(birthday)

    def __str__(self) -> str:
        """Повертає рядкове представлення контакту українською мовою."""
        # Збираємо частини рядка відповідно до наявних полів
        parts = [f"Ім'я контакту: {self.name.value}"]
        if self.phones:
            parts.append("телефони: " + "; ".join(p.value for p in self.phones))
        if self.emails:
            parts.append("e-mail: " + "; ".join(e.value for e in self.emails))
        if self.address is not None:
            parts.append(f"адреса: {self.address.value}")
        if self.birthday is not None:
            parts.append(f"день народження: {self.birthday}")
        return ", ".join(parts)
