# Assistant T800 — Command Help

## General Rules

- Use quotes for values containing spaces.

  Example:

  ```bash
  add "John Smith" 0991112233 "New York"
  ```

- Use semicolon `;` to pass multiple phones, emails, or tags.

  Example:

  ```bash
  add-phone John 0991112233;0992223344
  ```

- All remove commands require confirmation.

- Type `help` to show this help.

- Type `exit`, `quit`, or `q` to close the assistant.


---

# Contact Commands


## Add Contact

### `add <name> [phone] [email] [address] [birthday]`

Create a new contact.

Optional values may be passed in any order:

| Type      | Description |
|-----------|-------------|
| phone     | 10-digit phone number |
| email     | Valid email address |
| address   | Free text, use quotes if it contains spaces |
| birthday  | `DD.MM.YYYY`, `DD-MM-YYYY`, or `DD/MM/YYYY` |

Examples:

```bash
add John
add John 0991112233
add John john@example.com
add John 0991112233 john@example.com "New York" 25.05.1990
add "John Smith" john@example.com 25/05/1990 "New York"
```


---

## Show All Contacts

### `contacts`

Show all saved contacts.

Example:

```bash
contacts
```


---

## Get Contact

### `get <name>`

Show detailed information about one contact.

Examples:

```bash
get John
get "John Smith"
```


---

# Search Commands


## Global Search

### `search <query>`

Search contacts by:

- name
- phone
- email
- address
- birthday
- note text
- tags

Search is case-insensitive and supports partial matches.

Examples:

```bash
search john
search gmail.com
search 099
search urgent
search "New York"
```


---

## Search by Name

### `search-name <query>`

Search contacts by name.

Examples:

```bash
search-name john
search-name smith
```


---

## Search by Phone

### `search-phone <query>`

Search contacts by phone number.

Partial matches are supported.

Examples:

```bash
search-phone 099
search-phone 2233
```


---

## Search by Email

### `search-email <query>`

Search contacts by email address.

Examples:

```bash
search-email gmail
search-email john@
```


---

## Search by Note

### `search-note <query>`

Search contacts by note text.

Examples:

```bash
search-note project
search-note "meeting tomorrow"
```


---

## Search by Tag

### `search-tag <query>`

Search contacts by tags.

Examples:

```bash
search-tag work
search-tag urgent
```


---

## Upcoming Birthdays

### `birthdays <days>`

Show contacts whose birthdays occur within the next number of days.

Weekend birthday greetings are moved to Monday.

Examples:

```bash
birthdays 7
birthdays 14
```


---

# Contact Update Commands


## Set Address

### `set-address <name> <address>`

Set or replace a contact address.

Examples:

```bash
set-address John "New York"
set-address "John Smith" "Kyiv, Ukraine"
```


---

## Set Birthday

### `set-birthday <name> <birthday>`

Set or replace a contact birthday.

Supported formats:

- `DD.MM.YYYY`
- `DD-MM-YYYY`
- `DD/MM/YYYY`

Examples:

```bash
set-birthday John 25.05.1990
set-birthday "John Smith" 25/05/1990
```


---

## Add Phone

### `add-phone <name> <phone>`

Add one or more phone numbers to an existing contact.

Multiple values must be separated with `;`.

Examples:

```bash
add-phone John 0991112233
add-phone John 0991112233;0992223344
add-phone "John Smith" 0991112233
```


---

## Add Email

### `add-email <name> <email>`

Add one or more email addresses to an existing contact.

Multiple values must be separated with `;`.

Examples:

```bash
add-email John john@example.com
add-email John john@example.com;work@example.com
add-email "John Smith" john@example.com
```


---

# Contact Remove Commands


## Remove Contact

### `remove <name>`

Delete the whole contact.

This command always asks for confirmation.

Examples:

```bash
remove John
remove "John Smith"
```


---

## Remove Address

### `remove-address <name>`

Remove the contact address.

This command always asks for confirmation.

Examples:

```bash
remove-address John
remove-address "John Smith"
```


---

## Remove Birthday

### `remove-birthday <name>`

Remove the contact birthday.

This command always asks for confirmation.

Examples:

```bash
remove-birthday John
remove-birthday "John Smith"
```


---

## Remove Phone

### `remove-phone <name> <phone>`

Remove one or more phone numbers from a contact.

Multiple values must be separated with `;`.

This command always asks for confirmation.

Examples:

```bash
remove-phone John 0991112233
remove-phone John 0991112233;0992223344
remove-phone "John Smith" 0991112233
```


---

## Remove Email

### `remove-email <name> <email>`

Remove one or more email addresses from a contact.

Multiple values must be separated with `;`.

This command always asks for confirmation.

Examples:

```bash
remove-email John john@example.com
remove-email John john@example.com;work@example.com
remove-email "John Smith" john@example.com
```


---

# Contact Note Commands


## Edit Note

### `edit-note <name>`

Open the current contact note in an interactive editor.

Behavior:
1. Load the current note text
2. Open a multiline editor
3. Save the updated text back to the contact

If the note is empty, an empty editor will be opened.

Examples:

```bash
edit-note John
edit-note "John Smith"
```


---

## Remove Note

### `remove-note <name>`

Remove the note attached to a contact.

This command always asks for confirmation.

Internally the system stores a special empty value instead of deleting the field.

Examples:

```bash
remove-note John
remove-note "John Smith"
```


---

# Contact Tag Commands


## Add Tag

### `add-tag <name> <tag>`

Add one or more tags to a contact.

Multiple tags must be separated with `;`.

Examples:

```bash
add-tag John work
add-tag John work;urgent
add-tag "John Smith" personal;family
```


---

## Remove Tag

### `remove-tag <name> <tag>`

Remove one or more tags from a contact.

Multiple tags must be separated with `;`.

This command always asks for confirmation.

Examples:

```bash
remove-tag John work
remove-tag John work;urgent
remove-tag "John Smith" personal
```


---

# System Commands


## Help

### `help`

Show this help.


---

## Exit

### `exit`
### `quit`
### `q`

Close the assistant.