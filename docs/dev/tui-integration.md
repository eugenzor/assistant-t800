# TUI Integration Notes

## Статус

TUI є додатковим інтерфейсом, який не є основною ціллю фінального CLI-релізу.

Основний продукт — CLI.

---

## Що TUI може використовувати з системи

TUI не повинен дублювати бізнес-логіку.

Він може використовувати:

- `CommandDispatcher`
- `AppResult`
- application handlers
- services
- repositories
- storage
- localization messages

---

## Рекомендований підхід

TUI може надсилати команди в той самий dispatcher, що й CLI:

```python
result = dispatcher.dispatch("add Аліса 0506666666")
```

Після цього TUI сам вирішує, як показати результат користувачу.

---

## Що не варто робити

Не потрібно напряму змінювати repository або domain з TUI.

Погано:

```python
contact.phones.append(phone)
```

Добре:

```python
dispatcher.dispatch("add-phone Аліса 0506666666")
```

---

## Confirmation

Якщо команда повертає confirmation result, TUI може показати dialog і потім повторно викликати dispatcher з `confirmed=True`.

---

## Висновок

TUI має бути окремою оболонкою над тією самою application-системою, а не паралельною реалізацією логіки.
