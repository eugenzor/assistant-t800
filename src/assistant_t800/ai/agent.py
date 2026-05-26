"""AI agent module for managing user contacts through tools.

Builds a ``pydantic_ai``-based agent. Tool functions are defined in
:mod:`assistant_t800.ai.tools`.
"""

import os
from functools import lru_cache

from pydantic_ai import Agent

from assistant_t800.ai.deps import AgentDeps
from assistant_t800.ai.tools import (
    add_contact,
    add_emails,
    add_phones,
    get_contact,
    list_contacts,
    print_to_display,
    remove_address,
    remove_all_emails,
    remove_all_phones,
    remove_birthday,
    remove_contact,
    remove_emails,
    remove_phones,
    search_contacts,
    search_contacts_by_email,
    search_contacts_by_name,
    search_contacts_by_note,
    search_contacts_by_phone,
    search_contacts_by_tag,
    search_upcoming_birthdays,
    set_address,
    set_birthday,
)

# Default AI model name. Can be overridden via environment variable.
DEFAULT_MODEL = "google-gla:gemini-3.1-flash-lite"

# System prompt that defines the assistant role and behavior.
SYSTEM_PROMPT = """\
Ти — Арні, персональний асистент для керування контактами користувача.

Твій стиль спілкування:
- говори коротко, чітко й впевнено;
- використовуй холодний, лаконічний, “кібернетичний” тон;
- звуч як бойовий андроїд-асистент: без зайвих емоцій, без довгих пояснень;
- іноді можеш додавати короткі фрази у стилі “Завдання виконано”,
“Контакт ідентифіковано”, “Команду прийнято”;
- не перебільшуй стиль настільки, щоб це заважало користувачу.
- допустимо використовувати доречний гумор

Твоя задача — керувати контактами користувача.

Контакт містить:
- ім’я;
- телефони — кожен телефон має складатися рівно з 10 цифр;
- електронні адреси;
- адресу;
- день народження у форматі DD.MM.YYYY.

Використовуй доступні інструменти для таких дій:
- додавання контактів;
- додавання та видалення телефонів і e-mail у існуючих контактів;
- встановлення та видалення адреси і дня народження;
- пошуку контактів — як загального, так і за окремими полями (ім’я, телефон, e-mail,
нотатка, тег);
- перегляду списку контактів та отримання одного контакту за іменем;
- видалення контактів;
- перегляду найближчих днів народження.

Правила роботи:
1. Якщо користувач просить показати контакти, завжди викликай `list_contacts`, щоб
оновити панель відображення.
2. Якщо потрібно показати довільну інформацію у лівій панелі — нотатки, підсумки,
пояснення або результати аналізу — використовуй `print_to_display`.
3. Після виконання дії коротко підтверджуй результат у чаті.
4. Якщо даних недостатньо для виконання команди, коротко запитай лише те, чого бракує.
5. Перед додаванням або редагуванням перевіряй формат телефону та дати народження.
6. Якщо телефон має не 10 цифр або дата народження не відповідає формату DD.MM.YYYY,
повідом користувача про помилку і попроси виправити дані.

Приклади стилю відповідей:
- “Команду прийнято. Контакт додано.”
- “Контакт знайдено.”
- “Помилка формату. Телефон має містити 10 цифр.”
- “Видалення завершено.”
- “Найближчі дні народження виведено на панель.”
"""


@lru_cache(maxsize=1)
def _get_agent() -> Agent[AgentDeps, str]:
    """Create and return a configured singleton AI agent.

    The model name is loaded from the ``ASSISTANT_T800_MODEL``
    environment variable or falls back to ``DEFAULT_MODEL``.
    All available tool functions are registered in the agent.
    """
    model = os.environ.get("ASSISTANT_T800_MODEL", DEFAULT_MODEL)
    agent: Agent[AgentDeps, str] = Agent(
        model,
        deps_type=AgentDeps,
        system_prompt=SYSTEM_PROMPT,
    )
    # Register all available agent tools.
    agent.tool(add_contact)
    agent.tool(get_contact)
    agent.tool(list_contacts)
    agent.tool(search_contacts)
    agent.tool(search_contacts_by_name)
    agent.tool(search_contacts_by_phone)
    agent.tool(search_contacts_by_email)
    agent.tool(search_contacts_by_note)
    agent.tool(search_contacts_by_tag)
    agent.tool(search_upcoming_birthdays)
    agent.tool(set_address)
    agent.tool(set_birthday)
    agent.tool(add_phones)
    agent.tool(add_emails)
    agent.tool(remove_contact)
    agent.tool(remove_address)
    agent.tool(remove_birthday)
    agent.tool(remove_phones)
    agent.tool(remove_all_phones)
    agent.tool(remove_emails)
    agent.tool(remove_all_emails)
    agent.tool(print_to_display)
    return agent


def run_chat(message: str, deps: AgentDeps) -> str:
    """Send a synchronous message to the AI agent.

    Args:
        message: User message for the agent.
        deps: Runtime dependencies container.

    Returns:
        Agent response text.
    """
    result = _get_agent().run_sync(message, deps=deps)

    return result.output
