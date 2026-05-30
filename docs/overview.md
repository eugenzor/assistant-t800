# Огляд проєкту Assistant T800

Assistant T800 — це персональний CLI/TUI помічник для керування контактами з опційним AI-режимом на базі Google Gemini. Цей документ дає відповідь на три питання: **як запустити**, **який функціонал є**, і **що загалом можна робити** в проєкті.

> Суміжні документи в теці: [architecture.md](architecture.md) — внутрішня будова, [commands-help.md](commands-help.md) — повний довідник команд, [notes.md](notes.md) — презентаційні слайди (включно з AI-тегами), [checklist.md](checklist.md) — статус вимог GoIT.

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

### Змінні оточення

| Змінна | Обовʼязкова | За замовчуванням | Призначення |
|---|---|---|---|
| `GOOGLE_API_KEY` | так (лише для AI) | — | Ключ Gemini для AI-режиму: TUI та AI-підказки команд |
| `ASSISTANT_T800_MODEL` | ні | `google-gla:gemini-3.1-flash-lite` | Перевизначення моделі pydantic-ai |
| `MAX_HISTORY_MESSAGES` | ні | `10` | Ліміт історії чату (AI-агент, `ai/agent.py`) |
| `MAX_CONTACTS_IN_TOOL_RETURN` | ні | `25` | Ліміт контактів у відповіді AI-інструмента (`ai/utils.py`) |

Усі змінні читає `Settings` (pydantic-settings) із оточення та файлу `.env`
(`src/assistant_t800/config.py`). Імена ключів виводяться з імен полів і не
чутливі до регістру (`max_history_messages` ↔ `MAX_HISTORY_MESSAGES`).

Важливо:

- Необовʼязкові змінні можна не вказувати — тоді беруться значення за
  замовчуванням просто з `config.py` (їх **немає** у `.env.example`).
- Усі ці змінні впливають **лише на AI/TUI-режим**. Класичний CLI їх не
  використовує.
- У `.env.example` `GOOGLE_API_KEY` і `ASSISTANT_T800_MODEL` задані явно, а
  `MAX_HISTORY_MESSAGES` і `MAX_CONTACTS_IN_TOOL_RETURN` показані
  закоментованими як приклад опціональних перевизначень.

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
| **rich (presentation)** | Rich-компоненти (таблиця контактів, картка, привітання, статус), що використовуються і CLI, і TUI | `src/assistant_t800/interfaces/rich/` |
| **info_validator** | Класифікація токенів (phone/email/birthday/address) з опційним AI-fallback | `src/assistant_t800/info_validator/` |

### Команди CLI

Повний довідник — у [commands-help.md](commands-help.md). Тут — згруповано за призначенням:

**Створення та перегляд**
- `add "Іван Петренко" +380991234567 ivan@example.com country=UA city=Київ line="вул. Хрещатик, 1" 25.05.1990` — додати контакт
  - Телефон у форматі E.164 (`+380…`) або як 10 цифр національного формату (`0991234567`)
  - Адресу можна задати структуровано через `key=value` токени (`country=` / `city=` / `line=` / `zip=` / `region=`) або як одну строку (legacy fallback)
- `contacts` — список усіх (виводиться Rich-таблицею)
- `get "Іван Петренко"` — показати картку одного контакту (Rich-панель)

**Пошук (6 режимів)**
- `search <текст>` — за всіма полями
- `search-name` / `search-phone` / `search-email` / `search-note` / `search-tag`

**Дні народження**
- `birthdays [N]` — на N днів уперед; субота/неділя автоматично переносяться на понеділок
- Реалізація: `src/assistant_t800/domain/birthdays.py`

**Редагування**
- `set-address`, `set-birthday`, `add-phone`, `add-email`, `edit-note`
- `edit-tags <name> [tag1 tag2 ...]` — інтерактивне редагування тегів (інлайн-поле з prompt_toolkit)
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
- Контакти й дні народження в Textual-панелі рендеряться тими ж Rich-компонентами, що і в CLI (`interfaces/rich/contacts.py`, `contact_card.py`)

**AI-пропозиції тегів — `suggest-tags`** (`src/assistant_t800/ai/agent.py`, `services/contacts.py`)
- Окремий one-shot LLM-агент із власним system prompt-ом (детальніше — у [notes.md](notes.md))
- Готує приватний снапшот контакту: ім'я, нотатка, існуючі теги, місяць народження, телефон у замаскованому форматі (`+XXX*****`)
- LLM повертає до 5 нових тегів JSON-ом (1-2 слова, lowercase, без пунктуації)
- Сервіс чистить результат: дедуплікує, прибирає вже існуючі теги, обрізає до 5
- Користувач бачить контакт + інлайн-поле з об'єднанням `існуючі + запропоновані` → редагує → `Enter` зберігає, `Esc` скасовує
- Fallback: без `prompt_toolkit` або при помилці AI — повертається `SUGGEST_TAGS_FAILED`, користувач може застосувати `edit-tags` вручну

**Інтерактивні резолвери введення** (`src/assistant_t800/interfaces/cli/edit_resolvers.py`)
Перехоплюють введення до того, як його побачить диспетчер команд:
- `NoteEditResolver` — багаторядковий редактор нотаток
- `TagEditResolver` — інлайн-редактор тегів для `edit-tags`
- `SuggestTagsResolver` — виклик AI + інлайн-редактор для `suggest-tags`

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

---

## 3. Міні-презентація — що загалом можна робити

> **Assistant T800** — термінальний помічник-«адресна книга» з AI-режимом «Арні» у стилі T-800.

### Що це
Python 3.13 CLI + Textual TUI для зберігання та пошуку контактів. Опційно підключається Google Gemini як AI-помічник і парсер опечаток.

### Два режими роботи
- **CLI** (`assistant-t800`) — класичний REPL з автодоповненням та історією. Працює без інтернету і без AI-ключа.
- **TUI** (`assistant-t800 tui`) — Textual-застосунок із розділеним екраном: список контактів зліва, AI-чат справа. Потрібен `GOOGLE_API_KEY`.

### Що вміє робити з контактами
- Додавати / переглядати / видаляти
- Зберігати телефони (E.164 + класифікація країни/оператора), email, **структуровану адресу** (country/city/line/zip/region), день народження, нотатку, теги
- 6 видів пошуку (загальний + за name / phone / email / note / tag)
- Показ найближчих днів народження з перенесенням вихідних на понеділок
- Інлайн-редагування нотаток і тегів через `prompt_toolkit`
- Rich-таблиця для списку та Rich-картка для одного контакту (responsive — звужується на вузьких терміналах)
- Усі деструктивні операції — з підтвердженням

### AI-фішки
- **Опечатки розуміються автоматично:** спочатку fuzzy-match, потім Gemini як fallback
- **Кирилиця QWERTY:** ввів `куьщму` замість `remove` — зрозуміє
- **AI пропонує теги:** `suggest-tags <name>` — Gemini аналізує контакт (нотатку, ім'я, місяць народження тощо) і пропонує до 5 тегів; телефон передається замаскованим
- **Чат у TUI бачить дані:** усі read-інструменти повертають JSON, тому «Арні» дійсно «бачить» контакти, а не вгадує
- **AI керує тегами:** чат-агент тепер вміє і **встановлювати**, і **очищати** теги (`set_tags_from_text`, `clear_tags`) — мутації CRUD-полів і тегів через звичайний чат
- **AI-розпізнавання телефонів:** якщо телефон у невідомому форматі, є опційний AI-класифікатор країни/оператора (`domain/phone_ai.py`)
- **Підтримка української та англійської мов** для команд і повідомлень

### Під капотом
- Шарувата архітектура: domain → repo → service → application → interface
- Pickle-сховище в `.data/address_book.pkl` (CLI і TUI ділять один файл)
- `pydantic-settings` для конфігурації, `prompt_toolkit` для UX, `rapidfuzz` для fuzzy-пошуку
- CI: ruff + pytest через GitHub Actions

### Демо за 60 секунд

```bash
uv sync
uv run assistant-t800
> add "Іван Петренко" +380991112233 ivan@example.com country=UA city=Київ line="вул. Хрещатик, 1" 25.05.1990
> contacts                          # Rich-таблиця
> get "Іван Петренко"               # Rich-картка з тегами
> birthdays 30
> search-phone 099
> edit-note "Іван Петренко" "Передзвонити після демо"
> edit-tags "Іван Петренко"         # інлайн-поле для тегів
> suggest-tags "Іван Петренко"      # AI підкаже теги (потрібен GOOGLE_API_KEY)
> exit
```

---

## Як переконатися, що все працює

1. **Встановлення пройшло:** `uv sync` відпрацював без помилок, з'явилася тека `.venv/`
2. **CLI стартує:** `uv run assistant-t800` показує привітання та запрошення вводу
3. **Базовий CRUD:** `add "Test" +380991112233 country=UA city=Київ line="вул. Шевченка, 1"` → `contacts` → бачиш контакт у Rich-таблиці → `remove "Test"` → підтвердження → зник
4. **Телефон зберігається в E.164:** `get "Test"` показує `+380991112233` навіть якщо вводив `0991112233`
5. **Persistence:** перезапустити CLI, контакти на місці (файл `.data/address_book.pkl`)
6. **TUI (якщо є `GOOGLE_API_KEY`):** `uv run assistant-t800 tui` відкриває двопанельний екран, AI-чат відповідає
7. **AI-підказки команд:** введи `cintacts` — fuzzy запропонує `contacts`
8. **Теги вручну:** `edit-tags "<name>"` відкриває інлайн-поле, можна редагувати
9. **AI-теги (якщо є `GOOGLE_API_KEY`):** `suggest-tags "<name>"` повертає інлайн-поле з пропозиціями від Gemini
10. **Тести:** `uv run pytest` — усі проходять
11. **Лінтер:** `uv run ruff check .` без помилок
