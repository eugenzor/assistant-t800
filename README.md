# Персональний Assistant T800

Термінальний AI-асистент для керування контактами.

---

## Встановлення та запуск

### Передумови

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) — менеджер пакетів та середовищ

Встановити `uv` (якщо ще не встановлено):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Клонуйте репозиторій

```bash
git clone <repo-url>
cd assistant-t800
```

### 2. Налаштуйте змінні середовища

Скопіюйте файл прикладу та додайте свій API-ключ:

```bash
cp .env.example .env
```

Відкрийте `.env` і замініть `xxx` на ваш ключ:

```env
GOOGLE_API_KEY=AIza...ваш_ключ_тут
```

Опціонально — можна вказати іншу модель (за замовчуванням `google-gla:gemini-3.1-flash-lite`):

```env
ASSISTANT_T800_MODEL=google-gla:gemini-3.1-flash-lite
```



#### Отримання безкоштовного API-ключа Gemini

1. Перейдіть на [aistudio.google.com](https://aistudio.google.com) та увійдіть через Google-акаунт.
2. Прийміть умови використання (при першому вході).
3. У лівому сайдбарі або на головній панелі натисніть **Get API key**.
4. Натисніть **Create API key** → **Create key in new project**.
5. Скопіюйте згенерований ключ (починається з `AIza...`).

> Безкоштовний рівень не потребує кредитної картки та дозволяє використовувати моделі Gemini Flash для прототипування.


### 3. Встановіть залежності

```bash
uv sync
```


### 4. Запустіть застосунок

**Варіант А — через `uv run` (рекомендовано):**

```bash
uv run assistant-t800 --enable-ai
```

або через `main.py` напряму:

```bash
uv run python main.py --enable-ai
```

**Варіант Б — через активацію віртуального середовища:**

```bash
source .venv/bin/activate
assistant-t800 --enable-ai
```

або:

```bash
source .venv/bin/activate
python main.py --enable-ai
```

---

## Розробка

Запуск лінтера:

```bash
uv run ruff check .
uv run ruff format .
```
