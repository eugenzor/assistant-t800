"""Модуль AI-агента, який керує контактами користувача через інструменти.

Конструктор агента на базі ``pydantic_ai``. Функції-інструменти
визначені у модулі :mod:`assistant_t800.ai.tools`. Усі повідомлення,
які агент повертає у чат, написані українською мовою.
"""

import os
from functools import lru_cache

from pydantic_ai import Agent

from assistant_t800.ai.deps import AgentDeps
from assistant_t800.ai.tools import (
    add_contact,
    add_email,
    add_phone,
    list_contacts,
    print_to_display,
    set_address,
    set_birthday,
)

# Назва моделі за замовчуванням. Можна перевизначити змінною середовища.
DEFAULT_MODEL = "google-gla:gemini-3.1-flash-lite"

# Системний промпт українською — задає роль та правила поведінки агента.
SYSTEM_PROMPT = (
    "Ти — T800, особистий асистент. Ти керуєш контактами користувача. "
    "Контакт має ім'я, телефони (по 10 цифр кожен), електронні адреси, "
    "адресу та день народження у форматі DD.MM.YYYY. "
    "Використовуй доступні інструменти, щоб додавати, редагувати, шукати, "
    "перелічувати та видаляти контакти, а також переглядати найближчі дні "
    "народження. Коротко підтверджуй виконані дії у чаті. "
    "Коли користувач просить показати контакти, завжди викликай "
    "list_contacts, щоб оновити панель відображення. "
    "Використовуй print_to_display, коли потрібно показати довільну "
    "інформацію (нотатки, підсумки, пояснення тощо) у лівій панелі."
)


@lru_cache(maxsize=1)
def _get_agent() -> Agent[AgentDeps, str]:
    """Створює (один раз) та повертає налаштованого AI-агента.

    Модель береться зі змінної середовища ``ASSISTANT_T800_MODEL``
    або використовується значення за замовчуванням ``DEFAULT_MODEL``.
    Усі функції-інструменти реєструються в агенті.
    """
    model = os.environ.get("ASSISTANT_T800_MODEL", DEFAULT_MODEL)
    agent: Agent[AgentDeps, str] = Agent(
        model,
        deps_type=AgentDeps,
        system_prompt=SYSTEM_PROMPT,
    )
    # Реєструємо всі доступні агенту інструменти
    agent.tool(add_contact)
    agent.tool(add_phone)
    agent.tool(add_email)
    agent.tool(set_address)
    agent.tool(set_birthday)
    agent.tool(list_contacts)
    agent.tool(print_to_display)
    return agent


def run_chat(message: str, deps: AgentDeps) -> str:
    """Синхронно надсилає повідомлення агенту та повертає його відповідь."""
    result = _get_agent().run_sync(message, deps=deps)
    return result.output
