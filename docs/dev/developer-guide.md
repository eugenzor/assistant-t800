# Developer Guide

## Призначення документа

Цей документ пояснює, як працює поточна система **Assistant T800** і як безпечно додавати новий функціонал.

Проєкт уже має власний міні-фреймворк:

- єдина система команд;
- окремі шари відповідальності;
- локалізовані повідомлення;
- CLI-інтерфейс;
- підказки команд;
- збереження даних у pickle.

Головне правило для нових розробників:

> Не пишемо логіку прямо в CLI.  
> Команда має проходити через `application → services → repositories → domain`.

---

## Загальний потік виконання

```text
User input
→ CliRunner
→ CommandDispatcher
→ application handler
→ service
→ repository
→ domain model
→ AppResult
→ presenter
→ terminal output
```

---

## Основні шари системи

### `domain`

Містить доменні моделі та поля: `Contact`, `Name`, `Phone`, `Email`, `Birthday`, `Address`.

Саме тут має бути остаточна валідація значень. CLI або handler не повинні дублювати цю валідацію.

### `repositories`

Працює з колекцією контактів: додає, шукає, видаляє, повертає списки. Repository не друкує текст, не знає про CLI та не знає про локалізацію.

### `services`

Містить бізнес-операції. Service координує repository, виконує бізнес-правила, але не використовує `input()`, `print()` і не формує user-facing тексти.

### `application`

Шар команд. Тут знаходяться handlers, dispatcher, `AppResult`, `AppMessage` та application-level помилки.

### `interfaces`

Шар взаємодії з користувачем. Основний інтерфейс — CLI.

### `localization`

Єдиний шар для текстів користувача. У коді не повинно бути hardcoded user-facing текстів.

### `suggestions`

Модуль підказок команд. Уже реалізований і зазвичай не потребує змін.

### `storage`

Модуль збереження даних. Поточна реалізація використовує pickle і файл `.data/address_book.pkl`.

---

## Як додати нову команду

1. Додати повідомлення в `Message` або `ErrorCode`, якщо потрібно.
2. Додати переклади в `locales/en.ini` та `locales/uk.ini`.
3. Додати handler у `application/handlers.py`.
4. Зареєструвати команду в `interfaces/cli/commands.py`.
5. За потреби додати метод у service.
6. За потреби додати метод у repository.
7. За потреби додати або розширити domain model.
8. Оновити `commands-help.md`.
9. Запустити Ruff.

---

## Команди з аргументами

Команди з простими позиційними аргументами описуються через `args`.

```python
Command(
    name="get",
    handler=get_contact,
    description=Message.GET_DESCRIPTION,
    args=("name",),
)
```

Після dispatch у handler буде доступно:

```python
context.args["name"]
```

---

## Команди з optional arguments

Приклад:

```text
birthdays [days]
```

```python
Command(
    name="birthdays",
    handler=list_upcoming_birthdays,
    description=Message.BIRTHDAYS_DESCRIPTION,
    usage="birthdays [days]",
    optional_args=("days",),
)
```

---

## Команди з raw arguments

Складні команди використовують `parse_args=False`.

```python
Command(
    name="add",
    handler=add_contact,
    description=Message.ADD_DESCRIPTION,
    usage="add <name> [phone] [email] [address] [birthday]",
    parse_args=False,
)
```

Handler читає `context.raw_args` і сам викликає parser.

---

## Destructive-команди

Команди видалення повинні вимагати підтвердження.

```python
if not context.confirmed:
    result = AppResult.confirm(Message.CONFIRM_REMOVE_CONTACT, name=name)
else:
    result = ...
```

Runner після підтвердження повторно викликає dispatcher з `confirmed=True`.

---

## Not yet implemented команди

Якщо команда вже запланована архітектурно, але ще не реалізована:

```python
return AppResult.fail(ErrorCode.NOT_IMPLEMENTED)
```

Так команда буде видима для інших розробників і не створюватиме `UNKNOWN_COMMAND`.

---

## Перед commit

```bash
ruff check . --fix
ruff format .
ruff check .
```

або через `uv`:

```bash
uv run ruff check . --fix
uv run ruff format .
uv run ruff check .
```
