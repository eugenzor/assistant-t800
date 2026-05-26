# Commands Development Guide

## Призначення

Цей документ пояснює, як додавати, змінювати та підтримувати команди Assistant T800.

Команди реєструються в:

```text
src/assistant_t800/interfaces/cli/commands.py
```

А виконуються через handlers у:

```text
src/assistant_t800/application/handlers.py
```

---

## Основне правило

CLI не виконує бізнес-логіку напряму.

Правильний шлях:

```text
Command registry
→ CommandDispatcher
→ application handler
→ service
→ repository
→ domain
```

---

## Типи команд

### Команда без аргументів

```python
Command(
    name="contacts",
    handler=list_contacts,
    description=Message.CONTACTS_DESCRIPTION,
)
```

### Команда з обов'язковим аргументом

```python
Command(
    name="get",
    handler=get_contact,
    description=Message.GET_DESCRIPTION,
    args=("name",),
)
```

### Команда з optional argument

```python
Command(
    name="birthdays",
    handler=list_upcoming_birthdays,
    description=Message.BIRTHDAYS_DESCRIPTION,
    usage="birthdays [days]",
    optional_args=("days",),
)
```

### Команда з raw parsing

```python
Command(
    name="add",
    handler=add_contact,
    description=Message.ADD_DESCRIPTION,
    usage="add <name> [phone] [email] [address] [birthday]",
    parse_args=False,
)
```

---

## Aliases

Aliases додаються в `Command`.

```python
aliases=("знайди телефон", "search phone")
```

Dispatcher підтримує longest-prefix resolution, тому складні alias-и мають пріоритет над короткими.

Приклад:

```text
знайди телефон Аліса
```

має виконати `search-phone`, а не `search`.

---

## Destructive-команди

Для destructive-команд використовується confirmation flow.

Handler повертає:

```python
AppResult.confirm(Message.CONFIRM_REMOVE_CONTACT, name=name)
```

Після підтвердження runner викликає ту саму команду з `confirmed=True`.

---

## Команди-заглушки

Для запланованого функціоналу використовуйте:

```python
def edit_note(context: AppContext) -> AppResult:
    """Edit contact note."""
    return AppResult.fail(ErrorCode.NOT_IMPLEMENTED)
```

Команда має бути зареєстрована в `commands.py`, щоб інші розробники бачили її в системі.
