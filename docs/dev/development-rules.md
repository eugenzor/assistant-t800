# Development Rules

## Загальні правила

- Код пишемо для навчального командного проєкту, але в охайному production-like стилі.
- Не ускладнюємо архітектуру без потреби.
- Не переписуємо стабільні модулі без прямого запиту.
- Не додаємо Java-style дроблення файлів там, де достатньо простого Python-модуля.

---

## Стиль коду

- Python 3.13+
- Повні type hints
- Docstrings англійською
- Коментарі англійською і тільки там, де вони справді пояснюють неочевидне
- User-facing тексти тільки через localization
- Ruff має проходити перед commit

---

## Заборонено

### Hardcoded user-facing text

Погано:

```python
return "Contact added"
```

Добре:

```python
return AppResult.ok(Message.CONTACT_ADDED, name=name)
```

### Бізнес-логіка в CLI

Погано:

```python
print("Contact removed")
contact.remove_phone(phone)
```

Добре:

```text
CLI → dispatcher → handler → service → repository
```

### Дублювання валідації

Не потрібно повторно перевіряти email або phone у CLI, якщо це вже робить domain field.

---

## Stable modules

Без прямого запиту не переписувати:

- `suggestions`
- `storage`
- `InputFactory`
- `localization`
- `CommandDispatcher`

Допускаються тільки точкові правки.

---

## Перед Pull Request

```bash
ruff check . --fix
ruff format .
ruff check .
```

Перевірити вручну:

- запуск CLI;
- `help`;
- `contacts`;
- `add`;
- `get`;
- `search`;
- destructive confirmation;
- suggestions для помилкової команди.
