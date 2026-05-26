# Localization Guide

## Призначення

Усі тексти, які бачить користувач, мають бути винесені в localization layer.

Не можна писати user-facing тексти прямо в handlers, services, repositories або presenter.

---

## Структура

```text
src/assistant_t800/localization/
├── messages.py
├── multilang.py
└── locales/
    ├── en.ini
    └── uk.ini
```

---

## `messages.py`

Тут описуються enum-и:

- `Message`
- `ErrorCode`
- `MultiLangEnum`

Приклад:

```python
class Message(MultiLangEnum):
    CONTACT_ADDED = auto()
```

---

## Locale-файли

У `uk.ini`:

```ini
[Message]
CONTACT_ADDED = Контакт «{name}» додано.
```

У `en.ini`:

```ini
[Message]
CONTACT_ADDED = Contact "{name}" has been added.
```

---

## Використання

```python
return AppResult.ok(Message.CONTACT_ADDED, name=name)
```

Presenter або `render_message()` відрендерить текст через поточну локаль.

---

## Confirmation messages

Для confirmation використовується:

```python
Message.CONFIRM_REMOVE_CONTACT
```

та методи:

```python
confirm_render(...)
confirm_check(answer)
```

Локалізація не повинна сама викликати `input()`.

---

## Правило

Якщо текст бачить користувач — він має бути в `.ini`.
