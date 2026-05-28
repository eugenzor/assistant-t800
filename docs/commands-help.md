# Assistant T800 — Command Help

This document describes both the commands implemented in the current CLI build and the commands already planned by the project architecture.

Status markers:

- **Implemented** — available in the current CLI.
- **Planned** — reserved by the architecture, but not implemented in the current CLI yet.

---

## General Rules

- Use quotes for values containing spaces.

  ```bash
  add "John Smith" 0991112233 "New York"
  ```

- Use semicolon `;` to pass multiple phones or emails.

  ```bash
  add-phone John 0991112233;0992223344
  add-email John john@example.com;work@example.com
  ```

- Remove commands always ask for confirmation.

- CLI command history is stored in:

  ```text
  .data/cli_commands_history
  ```

- Address book data is stored in:

  ```text
  .data/address_book.pkl
  ```

- Type `help` to show command help.

- Type `exit`, `quit`, or `q` to close the assistant.

---

## Implemented Contact Commands

### `add <name> [phone] [email] [address] [birthday]`

**Status:** Implemented

Create a new contact.

Optional values may be passed in any order:

| Value | Description |
| --- | --- |
| `phone` | Phone number validated by the domain model |
| `email` | Valid email address |
| `address` | Free text; use quotes if it contains spaces |
| `birthday` | `DD.MM.YYYY`, `DD-MM-YYYY`, or `DD/MM/YYYY` |

Examples:

```bash
add John
add John 0991112233
add John john@example.com
add John 0991112233 john@example.com "New York" 25.05.1990
add "John Smith" john@example.com 25/05/1990 "New York"
```

Aliases include:

```text
додати
```

---

### `contacts`

**Status:** Implemented

Show all saved contacts.

```bash
contacts
```

Aliases include:

```text
all
контакти
```

---

### `get <name>`

**Status:** Implemented

Show detailed information about one contact.

```bash
get John
get "John Smith"
```

Aliases include:

```text
надай
```

---

### `birthdays [days]`

**Status:** Implemented

Show contacts whose birthdays should be congratulated within the selected number of days.

If `days` is omitted, the default value is `7`.

Weekend birthday greetings are moved to the following Monday.

```bash
birthdays
birthdays 7
birthdays 14
```

Aliases include:

```text
дні народження
іменинники
```

---

## Implemented Search Commands

All search commands are case-insensitive and support partial matches.

### `search <query>`

**Status:** Implemented

Search contacts by all searchable fields:

- name
- phone
- email
- address
- birthday
- note text
- tags

```bash
search john
search gmail.com
search 099
search urgent
search "New York"
```

Aliases include:

```text
шукай
знайди
```

---

### `search-name <query>`

**Status:** Implemented

Search contacts by name.

```bash
search-name john
search-name smith
```

Aliases include:

```text
search name
шукай ім'я
знайди ім'я
```

---

### `search-phone <query>`

**Status:** Implemented

Search contacts by phone number.

```bash
search-phone 099
search-phone 2233
```

Aliases include:

```text
search phone
шукай телефон
знайди телефон
```

---

### `search-email <query>`

**Status:** Implemented

Search contacts by email address.

```bash
search-email gmail
search-email john@
```

Aliases include:

```text
search email
шукай ємейл
знайди ємейл
```

---

### `search-note <query>`

**Status:** Implemented

Search contacts by attached note text.

The note field exists in the contact model and can be edited with `edit-note`.

```bash
search-note project
search-note "meeting tomorrow"
```

Aliases include:

```text
search note
шукай нотатку
знайди нотатку
```

---

### `search-tag <query>`

**Status:** Implemented

Search contacts by tags.

Tag storage exists in the contact model and can be managed with `add-tag` and `remove-tag`.

```bash
search-tag work
search-tag urgent
```

Aliases include:

```text
search tag
шукай тег
знайди тег
```

---

## Implemented Contact Update Commands

### `set-address <name> <address>`

**Status:** Implemented

Set or replace a contact address.

```bash
set-address John "New York"
set-address "John Smith" "Kyiv, Ukraine"
```

Aliases include:

```text
set address
додай адресу
```

---

### `set-birthday <name> <birthday>`

**Status:** Implemented

Set or replace a contact birthday.

Supported date formats:

- `DD.MM.YYYY`
- `DD-MM-YYYY`
- `DD/MM/YYYY`

```bash
set-birthday John 25.05.1990
set-birthday "John Smith" 25/05/1990
```

Aliases include:

```text
set birthday
додай день народження
```

---

### `add-phone <name> <phone>`

**Status:** Implemented

Add one or more phone numbers to an existing contact.

Multiple values must be separated with `;`.

```bash
add-phone John 0991112233
add-phone John 0991112233;0992223344
add-phone "John Smith" 0991112233
```

Aliases include:

```text
add phone
додай телефон
```

---

### `add-email <name> <email>`

**Status:** Implemented

Add one or more email addresses to an existing contact.

Multiple values must be separated with `;`.

```bash
add-email John john@example.com
add-email John john@example.com;work@example.com
add-email "John Smith" john@example.com
```

Aliases include:

```text
add email
додай ємейл
```

---

## Implemented Contact Remove Commands

### `remove <name>`

**Status:** Implemented

Delete the whole contact.

This command always asks for confirmation.

```bash
remove John
remove "John Smith"
```

Aliases include:

```text
delete
видали
```

---

### `remove-address <name>`

**Status:** Implemented

Remove the contact address.

This command always asks for confirmation.

```bash
remove-address John
remove-address "John Smith"
```

Aliases include:

```text
remove address
delete address
видали адресу
```

---

### `remove-birthday <name>`

**Status:** Implemented

Remove the contact birthday.

This command always asks for confirmation.

```bash
remove-birthday John
remove-birthday "John Smith"
```

Aliases include:

```text
remove birthday
delete birthday
видали день народження
```

---

### `remove-phone <name> [phone]`

**Status:** Implemented

Remove one, many, or all phone numbers from a contact.

If `phone` is provided, the selected value or values are removed.

If `phone` is omitted:

- if the contact has one phone, it is removed;
- if the contact has several phones, the assistant asks whether all phones should be removed.

Multiple values must be separated with `;`.

```bash
remove-phone John
remove-phone John 0991112233
remove-phone John 0991112233;0992223344
remove-phone "John Smith" 0991112233
```

Aliases include:

```text
remove phone
delete phone
видали телефон
```

---

### `remove-email <name> [email]`

**Status:** Implemented

Remove one, many, or all email addresses from a contact.

If `email` is provided, the selected value or values are removed.

If `email` is omitted:

- if the contact has one email, it is removed;
- if the contact has several emails, the assistant asks whether all emails should be removed.

Multiple values must be separated with `;`.

```bash
remove-email John
remove-email John john@example.com
remove-email John john@example.com;work@example.com
remove-email "John Smith" john@example.com
```

Aliases include:

```text
remove email
delete email
видали ємейл
```

---

## Implemented Contact Note Commands

These commands manage the note attached to a contact.

### `edit-note <name> <note>`

**Status:** Implemented

Set or replace the current contact note.

Use quotes when the note contains spaces.

```bash
edit-note John "Call after demo"
edit-note "John Smith" "Meeting tomorrow at 10"
```

---

### `remove-note <name>`

**Status:** Implemented

Remove the note attached to a contact.

This command asks for confirmation and stores the internal empty note value.

```bash
remove-note John
remove-note "John Smith"
```

---

## Implemented Contact Tag Commands

These commands manage tags attached to contacts.

### `add-tag <name> <tag>`

**Status:** Implemented

Add one or more tags to a contact.

Multiple tags should be separated with `;`.

```bash
add-tag John work
add-tag John work;urgent
add-tag "John Smith" personal;family
```

---

### `remove-tag <name> <tag>`

**Status:** Implemented

Remove one or more tags from a contact.

Multiple tags should be separated with `;`.

This command asks for confirmation.

```bash
remove-tag John work
remove-tag John work;urgent
remove-tag "John Smith" personal
```

---

## AI Command Suggestions

**Status:** Implemented

If the user enters an unknown command, the assistant can suggest or run a corrected command using fuzzy matching and AI fallback.

Examples:

```bash
contats
видали Аліса
знайди телефон Аліса
```

The assistant can resolve natural-language-like input to canonical commands such as:

```bash
contacts
remove Аліса
search-phone Аліса
```

---

## Interface Modes

### CLI mode

**Status:** Implemented

Default mode:

```bash
assistant-t800
```

or:

```bash
assistant-t800 cli
```

---

### TUI mode

**Status:** Implemented as an optional AI interface

```bash
assistant-t800 tui
assistant-t800 --tui
assistant-t800 --enable-ai
```

---

## System Commands

### `help`

**Status:** Implemented

Show available commands.

```bash
help
```

---

### `exit`, `quit`, `q`

**Status:** Implemented

Close the assistant.

```bash
exit
quit
q
```
