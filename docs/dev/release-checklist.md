# Release Checklist

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

---

## Ручна перевірка CLI

Перевірити:

```bash
python main.py
```

Команди:

```text
help
contacts
add Аліса 0506666666 alice@gmail.com "USA" 28.05.2016
get Аліса
search Аліса
search-phone 050
birthdays
remove-phone Аліса
remove Аліса
exit
```

---

## Перевірка suggestions

Перевірити natural-language input:

```text
видали Аліса
знайди телефон Аліса
додай контакт Аліса
```

---

## Перевірка persistence

1. Додати контакт.
2. Вийти з програми.
3. Запустити програму знову.
4. Перевірити, що контакт залишився.

Файл даних:

```text
.data/address_book.pkl
```

---

## Перевірка документації

Оновити:

- `README.md`
- `commands-help.md`
- `architecture.md`, якщо змінювалась архітектура
- `checklist.md`, якщо змінився статус вимог
