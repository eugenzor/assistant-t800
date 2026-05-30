"""AI agent module for managing user contacts through tools.

Builds a ``pydantic_ai``-based agent. Tool functions are defined in
:mod:`assistant_t800.ai.tools`.
"""

import os
from functools import lru_cache

from pydantic_ai import Agent

from assistant_t800.ai.deps import AgentDeps
from assistant_t800.ai.display import apply_display, extract_display_payloads
from assistant_t800.ai.history import cap_message_history, strip_display_metadata
from assistant_t800.config import settings
from assistant_t800.ai.tools import (
    add_contact,
    add_emails,
    add_phones,
    clear_tags,
    get_contact,
    list_contacts,
    remove_address,
    remove_all_emails,
    remove_all_phones,
    remove_birthday,
    remove_contact,
    remove_emails,
    remove_note,
    remove_phones,
    set_tags_from_text,
    search_contacts,
    search_contacts_by_email,
    search_contacts_by_name,
    search_contacts_by_note,
    search_contacts_by_phone,
    search_contacts_by_tag,
    search_upcoming_birthdays,
    set_address,
    set_birthday,
    set_note,
)

# Default AI model name. Can be overridden via environment variable.
DEFAULT_MODEL = "google:gemini-3.1-flash-lite"

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
- телефони — кожен телефон зберігається у міжнародному форматі
+<код країни><номер>, напр. +380501234567;
- електронні адреси;
- адресу — структурований запис із полів country, city, line (всі три
обов'язкові), та опціональних zip і region;
- день народження у форматі DD.MM.YYYY;
- нотатку;
- теги (нормалізуються до нижнього регістру).

Використовуй доступні інструменти для таких дій:
- додавання контактів;
- додавання та видалення телефонів і e-mail у існуючих контактів;
- встановлення та видалення адреси і дня народження;
- встановлення та видалення нотатки контакту;
- встановлення (заміна) та очищення тегів контакту;
- пошуку контактів — як загального, так і за окремими полями (ім’я, телефон, e-mail,
нотатка, тег);
- перегляду списку контактів та отримання одного контакту за іменем;
- видалення контактів;
- перегляду найближчих днів народження.

Правила роботи:
1. Панель відображення оновлюється автоматично після виконання інструментів — не потрібно
окремо викликати інструменти лише для оновлення панелі.
2. Після виконання дії коротко підтверджуй результат у чаті.
3. Якщо даних недостатньо для виконання команди, коротко запитай лише те, чого бракує.
4. Перед додаванням або редагуванням перевіряй формат телефону та дати народження.
5. Якщо номер телефону або дату народження не вдається розпізнати повідом користувача 
про помилку і попроси виправити дані.

Приклади стилю відповідей:
- “Команду прийнято. Контакт додано.”
- “Контакт знайдено.”
- “Помилка формату. Не вдалося розпізнати номер телефону.”
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
    agent.tool(set_note)
    agent.tool(add_phones)
    agent.tool(add_emails)
    agent.tool(remove_contact)
    agent.tool(remove_address)
    agent.tool(remove_birthday)
    agent.tool(remove_note)
    agent.tool(remove_phones)
    agent.tool(remove_all_phones)
    agent.tool(remove_emails)
    agent.tool(remove_all_emails)
    agent.tool(set_tags_from_text)
    agent.tool(clear_tags)
    return agent


def run_chat(message: str, deps: AgentDeps) -> str:
    """Send a synchronous message to the AI agent.

    Replays ``deps.message_history`` so the agent has context from prior turns,
    then stores the updated, capped history back on ``deps`` for the next call.

    Args:
        message: User message for the agent.
        deps: Runtime dependencies container.

    Returns:
        Agent response text.
    """
    result = _get_agent().run_sync(
        message,
        deps=deps,
        message_history=deps.message_history,
    )

    apply_display(deps.presenter, extract_display_payloads(result.new_messages()))

    max_messages = settings.max_history_messages
    deps.message_history = strip_display_metadata(
        cap_message_history(list(result.all_messages()), max_messages)
    )

    return result.output


# System prompt for the one-shot tag-suggestion agent.
_TAG_SUGGESTION_PROMPT = """\
Ти — спеціалізований класифікатор контактів. Тобі надсилають JSON-знімок контакту,
а ти повертаєш короткі теги для його категоризації.

Формат відповіді:
- Поверни лише JSON, що відповідає схемі: {"tags": ["...", "..."]}.
- Без коментарів, пояснень або тексту поза JSON.

Правила для тегів:
1. Максимум 5 тегів. Менше — теж добре, якщо вхідних сигналів небагато.
2. Кожен тег — 1–2 слова, у нижньому регістрі.
3. Без знаків пунктуації, лапок, емоджі. Дозволено дефіс для складених тегів
(наприклад, kyiv-office, family-friend).
4. Тег має описувати ТЕМУ АБО КАТЕГОРІЮ (робота, клієнт, сім'я, friend, college),
а не факти про дані (+380, має-телефон, день-народження-травень).
5. Якщо у вхідному полі "tags" вже є теги — НЕ повторюй їх і дотримуйся їхнього стилю
(якщо існуючі однослівні — твої теж однослівні; якщо з дефісами — твої також з дефісами).

Мова:
- Виводь теги тією ж мовою, що домінує у вхідних даних (насамперед у полі "note";
якщо "note" відсутній — за полем "name").
- Якщо вхід змішаний — орієнтуйся на мову "note".
- Якщо сигналу мови немає — за замовчуванням українська.

Якщо вхідні дані не містять корисного сигналу (немає note, немає інформативної адреси,
немає інформативних існуючих тегів) — поверни порожній масив: {"tags": []}.

Приклади:

Вхід: {"name": "Аліса", "note": "Менеджер з продажів у B2B-стартапі", "tags": ["клієнт"]}
Вихід: {"tags": ["продажі", "b2b", "менеджер", "стартап"]}

Вхід: {"name": "John Smith", "note": "Family friend from college, lives in NYC", "tags": []}
Вихід: {"tags": ["family", "friend", "college", "nyc"]}

Вхід: {"name": "Боб"}
Вихід: {"tags": []}
"""
