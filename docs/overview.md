# Огляд проєкту Assistant T800

Assistant T800 — це персональний CLI/TUI помічник для керування контактами з опційним AI-режимом на базі Google Gemini. Цей документ дає відповідь на три питання: **як запустити**, **який функціонал є**, і **що загалом можна робити** в проєкті.

> Суміжні документи в теці: [architecture.md](architecture.md) — внутрішня будова, [commands-help.md](commands-help.md) — повний довідник команд, [notes.md](notes.md) — презентаційні слайди, [checklist.md](checklist.md) — статус вимог GoIT.

---

## 1. Як запустити

**Стек:** Python 3.13+, менеджер залежностей `uv` (рекомендовано) або pip. База даних не потрібна — сховище це pickle-файл `.data/address_book.pkl`, який створюється автоматично.

### Швидкий старт через `uv`

```bash
# 1. Встановити залежності
uv sync

# 2. Налаштувати оточення (тільки якщо потрібен AI)
cp .env.example .env
# відкрити .env і вписати GOOGLE_API_KEY
# (взяти ключ на https://aistudio.google.com/apikey)

# 3a. Запуск класичного CLI
uv run assistant-t800

# 3b. Запуск TUI з AI-чатом (потрібен GOOGLE_API_KEY)
uv run assistant-t800 tui
# або еквівалентно:
uv run assistant-t800 --enable-ai
```

### Альтернатива через pip

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-ai.txt   # base + pydantic-ai + google-genai
pip install -e .
assistant-t800
```

### Тести та якість коду

```bash
uv run pytest                                              # тести
uv run pytest --cov=src/assistant_t800 --cov-report=term-missing
uv run ruff check .                                        # лінтер
uv run ruff format .                                       # форматування
uv run mypy                                                # перевірка типів
```

### Змінні оточення (`.env.example`)

| Змінна | За замовчуванням | Призначення |
|---|---|---|
| `GOOGLE_API_KEY` | — | Ключ Gemini (потрібен лише для AI: TUI + AI-підказки команд) |
| `ASSISTANT_T800_MODEL` | `google-gla:gemini-3.1-flash-lite` | Перевизначення моделі |
| `ASSISTANT_T800_MAX_HISTORY_MESSAGES` | `10` | Ліміт історії чату |

### Дані

- Адресна книга: `.data/address_book.pkl` (створюється автоматично)
- Історія команд CLI: `.data/cli_commands_history`

---

## 2. Який функціонал є

Проєкт — це **персональний CLI/TUI помічник для керування контактами** з опційним AI-агентом (Google Gemini). Це навчальний проєкт GoIT із чистою шаруватою архітектурою.

### Архітектурні шари

Деталі — у [architecture.md](architecture.md).

```
domain → repositories → services → application → interfaces (CLI / TUI)
                                                ↑
                              localization, storage, suggestions, ai
```

| Шар | Призначення | Де дивитися |
|---|---|---|
| **domain** | Моделі: `Contact`, `Phone`, `Email`, `Address`, `Birthday`, теги | `src/assistant_t800/domain/` |
| **repositories** | `ContactsRepository` — in-memory CRUD + пошук | `src/assistant_t800/repositories/contacts.py` |
| **services** | `ContactsService` — бізнес-операції поверх репозиторія | `src/assistant_t800/services/contacts.py` |
| **application** | Диспетчер команд, хендлери, `AppResult` / `AppError` | `src/assistant_t800/application/` |
| **interfaces** | CLI (основний) + TUI (Textual) + лаунчер | `src/assistant_t800/interfaces/` |
| **localization** | Українські та англійські повідомлення + аліаси команд | `src/assistant_t800/localization/` |
| **storage** | Pickle-персистенс із відновленням після збоїв | `src/assistant_t800/storage/` |
| **suggestions** | Fuzzy-match + AI-fallback для виправлення опечаток | `src/assistant_t800/suggestions/` |
| **ai** | Pydantic-AI агент «Арні», інструменти, JSON-серіалізація контактів для LLM | `src/assistant_t800/ai/` |
| **info_validator** | Класифікація токенів (phone/email/birthday/address) з опційним AI-fallback | `src/assistant_t800/info_validator/` |

### Команди CLI

Повний довідник — у [commands-help.md](commands-help.md). Тут — згруповано за призначенням:

**Створення та перегляд**
- `add "Іван Петренко" +380991234567 ivan@example.com country=UA city=Київ line="вул. Хрещатик, 1" 25.05.1990` — додати контакт
  - Телефон у форматі E.164 (`+380…`) або як 10 цифр національного формату (`0991234567`)
  - Адресу можна задати структуровано через `key=value` токени (`country=` / `city=` / `line=` / `zip=` / `region=`) або як одну строку (legacy fallback)
- `contacts` — список усіх
- `get "Іван Петренко"` — показати одного

**Пошук (6 режимів)**
- `search <текст>` — за всіма полями
- `search-name` / `search-phone` / `search-email` / `search-note` / `search-tag`

**Дні народження**
- `birthdays [N]` — на N днів уперед; субота/неділя автоматично переносяться на понеділок
- Реалізація: `src/assistant_t800/domain/birthdays.py`

**Редагування**
- `set-address`, `set-birthday`, `add-phone`, `add-email`, `edit-note`
- `edit-tags <name> [tag1 tag2 ...]` — інтерактивне редагування тегів
- `suggest-tags <name>` — AI пропонує теги, користувач підтверджує/править інлайн

**Видалення (з підтвердженням)**
- `remove`, `remove-address`, `remove-birthday`, `remove-phone`, `remove-email`, `remove-note`

**Інше**
- `help` / `?`, `exit` / `quit` / `q`

**Аліаси:** кожна команда має англійський, український і **«кириличний QWERTY»** аліас. Приклад: `remove` ≡ `delete` ≡ `видали` ≡ `куьщму`.

**Теги:** повноцінно підтримуються. Зберігаються нормалізованими (lowercase, без дублікатів), доступні через `search-tag`, керуються через `edit-tags` (ручне інлайн-редагування) і `suggest-tags` (AI). Окремих `add-tag` / `remove-tag` команд немає — все робиться через `edit-tags`.

### AI-функціонал

**Підказки команд** (`src/assistant_t800/suggestions/`)
1. Точна відповідність (ім'я команди або аліас)
2. Fuzzy-match через `rapidfuzz` (толерантність до опечаток)
3. Якщо score < 80 — AI-fallback (Gemini вгадує намір)

**AI-чат у TUI** (`src/assistant_t800/ai/agent.py`)
- Модель: Gemini 3.1 Flash Lite
- Персона: «Арні» — кібернетичний асистент у стилі T-800
- Інструменти 1:1 до методів `ContactsService` (`src/assistant_t800/ai/tools.py`) — CRUD контактів, пошук, дні народження, нотатки, плюс **мутація тегів** (`set_tags_from_text`, `clear_tags`)
- Історія діалогу з лімітом (за замовчуванням 10 повідомлень)
- Двопанельний UI: 70% контакти + 30% чат
- LLM бачить структуровані дані: усі read-інструменти повертають JSON через `ai/utils.py::format_contacts_for_llm` з обираними полями (`ContactField` enum) і капом за `max_items` (default 25, конфігурується)

### Валідація полів (`src/assistant_t800/domain/fields.py`, `domain/phone_validation.py`, `domain/country.py`)

| Поле | Правила |
|---|---|
| name | непорожній рядок |
| phone | приймає E.164 (`+380501234567`), національний формат (`0501234567`), з роздільниками/дужками; зберігається у канонічному E.164. Опційний AI-fallback (`domain/phone_ai.py`) для нерозпізнаних форматів — класифікує країну/оператора |
| email | прагматичний regex (`@` + домен) |
| birthday | `DD.MM.YYYY` / `DD-MM-YYYY` / `DD/MM/YYYY`, не в майбутньому |
| address | структурований запис (`AddressInput`): обов'язкові `country`, `city`, `line`; опційні `zip_code`, `region`. Country резолвиться через `domain/country.py` (ISO-коди + укр./рос./англ. синоніми: `UA` / `ukraine` / `україна` тощо) |

### Універсальний валідатор токенів (`src/assistant_t800/info_validator/`)

Окремий шар-фасад `InfoValidator`, який класифікує довільні рядки в `phone` / `email` / `birthday` / `address` / `unknown` за допомогою регекспів і опційного AI-fallback. Перший невпізнаний токен автоматично «промоутиться» в адресу. Поки що використовується як інфраструктура для розширення; основний парсинг команд (`add`, `set-address`) використовує деталізовані парсери в `application/contacts_args.py`.
