# Чек-лист готовності Assistant T800

## Позначення

* ✅ реалізовано;
* 🟡 частково реалізовано або підготовлено архітектурно;
* ❌ заплановано.

---

# 1. Основні вимоги проєкту (GoIT)

## 1.1. Контакти

| Статус | Вимога                     | Поточний стан                                                                        |
| ------ | -------------------------- | ------------------------------------------------------------------------------------ |
| ✅      | Додавання контактів        | `add <name> [phone] [email] [address] [birthday]`                                    |
| ✅      | Перегляд усіх контактів    | `contacts`                                                                           |
| ✅      | Перегляд одного контакту   | `get <name>`                                                                         |
| ✅      | Пошук контактів            | `search`, `search-name`, `search-phone`, `search-email`, `search-note`, `search-tag` |
| ✅      | Дні народження             | `birthdays [days]`                                                                   |
| ✅      | Редагування адреси         | `set-address <name> <address>`                                                       |
| ✅      | Редагування дня народження | `set-birthday <name> <birthday>`                                                     |
| ✅      | Додавання телефонів        | `add-phone <name> <phone>`                                                           |
| ✅      | Додавання e-mail           | `add-email <name> <email>`                                                           |
| ✅      | Видалення контакту         | `remove <name>`                                                                      |
| ✅      | Видалення адреси           | `remove-address <name>`                                                              |
| ✅      | Видалення дня народження   | `remove-birthday <name>`                                                             |
| ✅      | Видалення телефонів        | `remove-phone <name> [phone]`                                                        |
| ✅      | Видалення e-mail           | `remove-email <name> [email]`                                                        |

## 1.2. Нотатки

| Статус | Вимога              | Поточний стан                        |
| ------ | ------------------- | ------------------------------------ |
| ✅      | Додавання нотаток   | `edit-note <name> [note]`            |
| ✅      | Редагування нотаток | Інтерактивний редактор (`TextInput`) |
| ✅      | Видалення нотаток   | `remove-note <name>`                 |
| ✅      | Пошук по нотатках   | `search-note`                        |

## 1.3. Валідація

| Статус | Вимога             | Поточний стан           |
| ------ | ------------------ | ----------------------- |
| ✅      | Валідація phone    | Domain field `Phone`    |
| ✅      | Валідація email    | Domain field `Email`    |
| ✅      | Валідація birthday | Domain field `Birthday` |

## 1.4. Зберігання даних

| Статус | Вимога                       | Поточний стан  |
| ------ | ---------------------------- | -------------- |
| ✅      | Persistence                  | Pickle storage |
| ✅      | Збереження між перезапусками | Реалізовано    |
| ✅      | Історія команд               | Реалізовано    |

## 1.5. CLI

| Статус | Вимога                        | Поточний стан       |
| ------ | ----------------------------- | ------------------- |
| ✅      | CLI інтерфейс                 | Реалізовано         |
| ✅      | Help                          | Реалізовано         |
| ✅      | Підтвердження небезпечних дій | Реалізовано         |
| ✅      | Автодоповнення                | `prompt_toolkit`    |
| ✅      | Історія команд                | `prompt_toolkit`    |
| ✅      | Suggestions                   | Fuzzy + AI fallback |

---

# 2. Розширений функціонал

Цей функціонал не входив до базових вимог фінального проєкту.

| Статус | Функціонал              | Поточний стан                       |
| ------ | ----------------------- | ----------------------------------- |
| ✅      | Теги контактів          | `edit-tags <name>`                  |
| ✅      | Пошук за тегами         | `search-tag`                        |
| ✅      | Rich welcome screen     | Реалізовано                         |
| ✅      | Rich contact card       | Реалізовано                         |
| ✅      | Rich contacts table     | Реалізовано                         |
| ✅      | Rich birthdays table    | Реалізовано                         |
| ✅      | Inline note editor      | Під карткою контакту                |
| ✅      | Inline tags editor      | Під карткою контакту                |
| ✅      | Inline hint panels      | Реалізовано                         |
| ✅      | Localization            | Українська та англійська            |
| ✅      | BaseInput               | History + completion                |
| ✅      | EditableInput           | Single-line editor                  |
| ✅      | TextInput               | Multiline editor                    |
| ✅      | Fallback input          | Стандартний `input()`               |
| ✅      | Atomic save             | Реалізовано                         |
| ✅      | Backup storage          | Реалізовано                         |
| ✅      | Recovery workflow       | Реалізовано                         |
| ✅      | Startup recovery prompt | Реалізовано                         |
| ✅      | AI command suggestions  | Реалізовано                         |
| ✅      | Extended Phone Validation + AI fallback   | Підтримка міжнародних форматів, AI як допоміжний шар        |
| ✅      | Extended Address Validation + AI fallback | Нормалізація та структуризація адрес                        |
| ✅      | AI Tag Suggestions                        | Аналіз контакту, адреси, нотаток, тегів та схожих контактів |
| ✅      | TUI support             | Реалізовано як додатковий інтерфейс |

---

# 3. Архітектурна готовність

| Статус | Компонент               | Поточний стан                         |
|--------|-------------------------|---------------------------------------|
| ✅      | Domain-first validation | Реалізовано                           |
| ✅      | Thin handlers           | Реалізовано                           |
| ✅      | Service layer           | Реалізовано                           |
| ✅      | Repository layer        | Реалізовано                           |
| ✅      | Storage abstraction     | Реалізовано                           |
| ✅      | Prompting abstraction   | Реалізовано                           |
| ✅      | Edit resolvers          | Реалізовано                           |
| ✅      | Rich rendering modules  | Реалізовано                           |
| ✅      | Localization layer      | Реалізовано                           |
| ✅      | Suggestions subsystem   | Реалізовано                           |
| ✅      | Розвиток TUI            | Подальше розширення функціоналу та UX |
| ✅      | Test coverage           | Поточний чекпоінт: **740 passed**     |

---

# 4. Можливі зміни

| Статус | Feature                | Notes                                                |
|--------|------------------------|------------------------------------------------------|
| 🟡     | Tag grouping / sorting | Архітектурно підтримується                           |
| 🟡     | SQLite storage adapter | Repository layer вже підготовлений                   |
| 🟡     | Export / Import        | Може бути додано поверх service/storage layer        |
