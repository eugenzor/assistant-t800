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
