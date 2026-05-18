"""Функції-інструменти AI-агента для роботи з контактами.

Кожна функція приймає ``RunContext[AgentDeps]`` і повертає рядок,
який агент може використати у відповіді користувачу. Усі повідомлення
написані українською мовою.
"""

from typing import Optional

from pydantic_ai import RunContext

from assistant_t800.ai.deps import AgentDeps


def add_contact(
    ctx: RunContext[AgentDeps],
    name: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
    birthday: Optional[str] = None,
) -> str:
    """Додає новий контакт.

    Необов'язкові поля: телефон, e-mail, адреса, день народження
    (у форматі DD.MM.YYYY).
    """
    try:
        contact = ctx.deps.contacts_service.add_contact(
            name,
            phone=phone,
            email=email,
            address=address,
            birthday=birthday,
        )
    except ValueError as exc:
        # Повертаємо помилку у читабельному вигляді українською
        return f"Не вдалося додати контакт: {exc}"
    # Оновлюємо панель відображення після зміни даних
    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())
    return f"Контакт «{contact.name.value}» додано."


def add_phone(ctx: RunContext[AgentDeps], name: str, phone: str) -> str:
    """Додає номер телефону до наявного контакту."""
    try:
        ctx.deps.contacts_service.add_phone(name, phone)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося додати телефон: {exc}"
    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())
    return f"Телефон {phone} додано до контакту «{name}»."


def edit_phone(
    ctx: RunContext[AgentDeps], name: str, old_phone: str, new_phone: str
) -> str:
    """Замінює існуючий номер телефону у контакті на новий."""
    try:
        ctx.deps.contacts_service.edit_phone(name, old_phone, new_phone)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося змінити телефон: {exc}"
    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())
    return f"Телефон контакту «{name}» оновлено."


def add_email(ctx: RunContext[AgentDeps], name: str, email: str) -> str:
    """Додає електронну адресу до наявного контакту."""
    try:
        ctx.deps.contacts_service.add_email(name, email)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося додати e-mail: {exc}"
    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())
    return f"E-mail {email} додано до контакту «{name}»."


def set_address(ctx: RunContext[AgentDeps], name: str, address: str) -> str:
    """Встановлює або змінює адресу наявного контакту."""
    try:
        ctx.deps.contacts_service.set_address(name, address)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося встановити адресу: {exc}"
    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())
    return f"Адресу контакту «{name}» оновлено."


def set_birthday(ctx: RunContext[AgentDeps], name: str, birthday: str) -> str:
    """Встановлює або змінює день народження (DD.MM.YYYY) контакту."""
    try:
        ctx.deps.contacts_service.set_birthday(name, birthday)
    except (KeyError, ValueError) as exc:
        return f"Не вдалося встановити день народження: {exc}"
    ctx.deps.presenter.refresh_contacts(ctx.deps.contacts_service.list_contacts())
    return f"День народження контакту «{name}» оновлено."


def search_contacts(ctx: RunContext[AgentDeps], query: str) -> str:
    """Шукає контакти за підрядком в імені, телефоні, e-mail або адресі."""
    matches = ctx.deps.contacts_service.search_contacts(query)
    ctx.deps.presenter.refresh_contacts(matches)
    if not matches:
        return f"Жоден контакт не відповідає запиту «{query}»."
    return f"Знайдено контактів за запитом «{query}»: {len(matches)}."


def list_contacts(ctx: RunContext[AgentDeps]) -> str:
    """Перелічує всі збережені контакти та оновлює панель відображення."""
    contacts = ctx.deps.contacts_service.list_contacts()
    ctx.deps.presenter.refresh_contacts(contacts)
    if not contacts:
        return "Контактів поки немає. Панель відображення порожня."
    return f"У панелі відображення показано контактів: {len(contacts)}."


def print_to_display(ctx: RunContext[AgentDeps], text: str) -> str:
    """Виводить довільний текст у ліву панель відображення."""
    ctx.deps.presenter.print(text)
    return "Текст виведено у панель відображення."
