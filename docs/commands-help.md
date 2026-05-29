# Assistant T800 — Command Help

This document describes commands implemented in the current CLI checkpoint.

---

## General Rules

Use quotes for values containing spaces:

```bash
add "John Smith" 0991112233 "New York"
```

Use configured multi-value separators for multiple values. Current separators include `;` and `,` where supported.

```bash
add-phone John 0991112233;0992223344
add-email John john@example.com;work@example.com
edit-tags John work;friends,usa
```

Remove commands ask for confirmation.

Type `help` or `?` to show help.

Type `exit`, `quit`, or `q` to close the assistant.

---

## Contact Commands

### `add <name> [phone] [email] [address] [birthday]`

Create a new contact.

Examples:

```bash
add John
add John 0991112233
add John john@example.com
add John 0991112233 john@example.com "New York" 25.05.1990
add "John Smith" john@example.com 25/05/1990 "New York"
```

---

### `contacts`

Show all contacts.

Aliases include:

```text
all
контакти
```

---

### `get <name>`

Show detailed contact card.

```bash
get John
get "John Smith"
```

---

### `search <query>`

Search contacts by all searchable fields.

```bash
search John
search 099
search New
search work
```

Search includes:

* name
* phone
* email
* address
* birthday
* notes
* tags

---

### `search-name <query>`

Search by contact name.

```bash
search-name John
```

---

### `search-phone <query>`

Search by phone.

```bash
search-phone 099
```

---

### `search-email <query>`

Search by e-mail.

```bash
search-email gmail
```

---

### `search-note <query>`

Search by note text.

```bash
search-note demo
```

---

### `search-tag <query>`

Search by tag.

```bash
search-tag work
```

---

### `birthdays [days]`

Show contacts whose birthdays should be congratulated within the selected period.

Default period: 7 days.

```bash
birthdays
birthdays 14
```

If the birthday falls on Saturday or Sunday, the congratulation date is moved to Monday.

---

## Update Commands

### `set-address <name> <address>`

Set or replace contact address.

```bash
set-address John "New York, Wall Street"
```

---

### `set-birthday <name> <birthday>`

Set or replace contact birthday.

Supported input formats:

```text
DD.MM.YYYY
DD-MM-YYYY
DD/MM/YYYY
```

Example:

```bash
set-birthday John 25.05.1990
```

---

### `add-phone <name> <phone>`

Add one or more phone numbers.

```bash
add-phone John 0991112233
add-phone John 0991112233;0992223344
```

---

### `add-email <name> <email>`

Add one or more e-mail addresses.

```bash
add-email John john@example.com
add-email John john@example.com;work@example.com
```

---

## Notes

### `edit-note <name>`

Open an inline multiline note editor directly below the contact card.

The current note text is automatically loaded into the editor.

Example:

```bash
edit-note "John Smith"
```

Key bindings:

```text
Enter    → new line
Ctrl+S   → save
Esc      → cancel
Ctrl+C   → cancel
```

Behavior:

* existing note text is prefilled;
* editing happens under the contact card;
* save updates the contact note;
* successful save returns to the contact card and displays a success status;
* `Esc` or `Ctrl+C` cancels editing and returns to the contact card without changes.

---

### `edit-note <name> [note]`

Directly replace note text without opening the editor.

```bash
edit-note "John Smith" "Call after the demo"
```

---

### `remove-note <name>`

Remove contact note.

```bash
remove-note "John Smith"
```

This command asks for confirmation.

---

## Tags

### `edit-tags <name>`

Open an inline single-line tag editor directly below the contact card.

The current tags are automatically loaded into the editor.

```bash
edit-tags "John Smith"
```

Behavior:

* existing tags are prefilled;
* `;` and `,` are accepted as separators;
* all tags are replaced by the entered value;
* `Esc` cancels editing and returns to the contact card without changes.

If the saved value is empty:

* the assistant asks for confirmation;
* after confirmation all tags are removed;
* the contact card is displayed with a status message.

---

### `edit-tags <name> [tags]`

Directly replace all tags without opening the editor.

```bash
edit-tags "John Smith" "work; friends, usa"
```

Examples:

```bash
edit-tags John work
edit-tags John work;urgent
edit-tags John work;friends,usa
```

Rules:

* existing tags are completely replaced;
* duplicate tags are ignored by domain validation;
* empty value removes all tags after confirmation.

---

## Remove Commands

### `remove <name>`

Remove the whole contact with confirmation.

```bash
remove John
```

---

### `remove-address <name>`

Remove address.

```bash
remove-address John
```

---

### `remove-birthday <name>`

Remove birthday.

```bash
remove-birthday John
```

---

### `remove-phone <name> [phone]`

Remove one phone or all phones.

```bash
remove-phone John 0991112233
remove-phone John
```

If no phone is specified:

* no phones → error;
* one phone → confirmation to remove it;
* multiple phones → confirmation to remove all.

---

### `remove-email <name> [email]`

Remove one e-mail or all e-mails.

```bash
remove-email John john@example.com
remove-email John
```

If no e-mail is specified:

* no e-mails → error;
* one e-mail → confirmation to remove it;
* multiple e-mails → confirmation to remove all.

---

## Suggestions

If a command is unknown, CLI may suggest a corrected command using fuzzy and AI providers.

Example:

```text
видали Аліса
```

may be suggested as:

```text
remove Аліса
```

Other examples:

```text
contats
serch John
видали телефон Аліса
```

may be resolved to:

```text
contacts
search John
remove-phone Аліса
```

---

## System Commands

### `help`

Show command help.

```bash
help
```

---

### `?`

Alias for help.

```bash
?
```

---

### `exit`, `quit`, `q`

Close the assistant.

```bash
exit
quit
q
```
