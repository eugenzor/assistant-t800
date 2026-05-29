# Assistant T800

Assistant T800 is a Python 3.13+ personal assistant for managing contacts from the terminal.

The primary interface is a CLI with command history, completion, aliases, localized messages, Rich output, and optional AI-based command suggestions. The project also contains an optional Textual-based TUI / AI-chat layer, but the current main product is the CLI.

---

## Current Features

### Contact Management

- Add contacts with:
  - name;
  - one or more phone numbers;
  - one or more e-mail addresses;
  - address;
  - birthday.
- Show all contacts.
- Show one contact as a detailed card.
- Search contacts by all fields or by a specific field.
- Show upcoming birthdays with weekend congratulations moved to Monday.
- Update address and birthday.
- Add one or more phone numbers or e-mail addresses.
- Remove contacts and contact fields with confirmation.
- Remove one, many, or all phone numbers / e-mail addresses.

### Notes

- Edit contact notes with:

```bash
edit-note <name>
```

- The inline note editor is shown under the contact card.
- Existing note text is prefilled.
- Key bindings:
  - `Enter` — new line;
  - `Ctrl+S` — save;
  - `Esc` / `Ctrl+C` — cancel.
- Direct note update is also supported:

```bash
edit-note <name> "note text"
```

- Notes can be removed with:

```bash
remove-note <name>
```

### Tags

Tags are managed through one user-friendly command:

```bash
edit-tags <name>
```

The command opens an inline editable field under the contact card.

- Existing tags are prefilled.
- Tags can be separated by `;` or `,`.
- Empty saved tag text means "remove all tags" and requires confirmation.
- `Esc` cancels editing and does not change tags.

### AI Tag Suggestions

Let the AI pick tags for a contact:

```bash
suggest-tags <name>
```

How it works:

- The AI looks at the contact's name, country, city, note, birthday month and current tags, then suggests up to 5 short tags.
- It writes tags in the same language as the contact's data (Ukrainian or English).
- The suggested tags are joined with the existing ones and shown in the same editable line as `edit-tags`.
- You can edit, add or remove tags, then `Enter` to save or `Esc` to cancel. Nothing is saved until you confirm.

Why it's useful:

- You don't have to think up tags yourself — the AI reads contact info and does it.
- You stay in control: you always see and edit the tags before they are saved.
- Manual tagging still works the same; this is just a faster way to add tags.

Needs a `GOOGLE_API_KEY` (see below). The command only works interactively; if `prompt_toolkit` is missing, use `edit-tags` instead.

### Search

Implemented commands:

- `search <query>`
- `search-name <query>`
- `search-phone <query>`
- `search-email <query>`
- `search-note <query>`
- `search-tag <query>`

Search is case-insensitive and supports partial matches.

No-match results are not treated as successful OK results. They return the corresponding warning/info status, for example `NAME_NOT_FOUND`, `QUERY_NOT_FOUND`, `PHONE_NOT_FOUND`, and similar.

### CLI UX

- Command history.
- Command completion.
- Canonical command completion words, not raw aliases.
- Fallback to standard `input()` if `prompt_toolkit` is unavailable.
- Aliases in English and Ukrainian.
- Long alias resolution, for example:

```text
знайди телефон Аліса
```

can resolve to:

```text
search-phone Аліса
```

### Rich Output

The CLI uses Rich for cleaner output when available:

- welcome screen;
- contact cards;
- status panels;
- contacts table;
- birthdays table;
- inline hint bars for note/tag editing.

### Persistence

Address book data is stored in:

```text
.data/address_book.pkl
```

CLI command history is stored in:

```text
.data/cli_commands_history
```

Storage uses safe pickle persistence:

- atomic save through a temporary file;
- `fsync()` before replacing the real database file;
- `.bak` backup file;
- recovery from empty or corrupted main storage;
- startup prompt to restore from backup if the main storage file is empty and the backup is valid.

### AI Suggestions

If a command is unknown, the assistant can suggest a corrected command using:

- fuzzy matching via `rapidfuzz`;
- AI fallback via `pydantic-ai` and Gemini.

Example:

```bash
видали Аліса
```

can be resolved to:

```bash
remove Аліса
```

### Optional TUI

The Textual TUI is available as an additional AI-powered interface. It shares the same pickle storage file with the CLI.

---

## Planned Features

These features are already prepared by the architecture but are not fully exposed through CLI commands yet:

- `add-tag <name> <tag>` — add one or more tags.
- `remove-tag <name> <tag>` — remove one or more tags.
- Optional sorting or grouping by tags.

---

## Requirements

- Python 3.13+
- Git
- `uv` as the recommended environment and dependency manager
- Google Gemini API key for AI suggestions and TUI AI mode

---

## Installation with uv

`uv` is the recommended way to run the project.

### 1. Install uv

Windows PowerShell:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Linux / macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the terminal after installation if the `uv` command is not available immediately.

### 2. Clone the repository

```bash
git clone <repo-url>
cd assistant-t800
```

### 3. Create the environment and install dependencies

```bash
uv sync
```

### 4. Configure environment variables

Copy the example file:

Windows CMD:

```cmd
copy .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux / macOS:

```bash
cp .env.example .env
```

Set your Gemini API key:

```env
GOOGLE_API_KEY=AIza...your_key_here
```

Optional model override:

```env
GOOGLE_API_MODEL=google:gemini-3.1-flash-lite
```

### 5. Run the CLI

```bash
uv run assistant-t800
```

or:

```bash
uv run python main.py
```

### 6. Run the TUI

```bash
uv run assistant-t800 tui
```

or:

```bash
uv run assistant-t800 --enable-ai
```

---

## Standard pip installation

Use this option if you do not want to use `uv`.

### 1. Create and activate a virtual environment

Windows CMD:

```cmd
py -m venv .venv
.venv\Scripts\activate.bat
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

For the full project, including AI support:

```bash
pip install -r requirements-ai.txt
```

For development tools:

```bash
pip install -r requirements-dev.txt
```

### 3. Install the package in editable mode

```bash
pip install -e .
```

### 4. Run

```bash
assistant-t800
```

or:

```bash
python main.py
```

---

## Running with PYTHONPATH

If the package is not installed in editable mode, use `PYTHONPATH=src`.

Windows CMD:

```cmd
set PYTHONPATH=src
python main.py
```

Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
python main.py
```

Linux / macOS:

```bash
PYTHONPATH=src python main.py
```

---

## Command Examples

```bash
add "John Smith" 0991112233 john@example.com "New York" 25.05.1990
contacts
get "John Smith"
search-phone 099
search-note demo
search-tag work
birthdays
birthdays 14
add-phone "John Smith" 0992223344;0993334455
add-email "John Smith" john@example.com;work@example.com
edit-note "John Smith"
edit-tags "John Smith"
remove-note "John Smith"
remove-email "John Smith"
remove "John Smith"
```

Use quotes for values containing spaces.

---

## Getting a Gemini API Key

1. Open Google AI Studio.
2. Sign in with your Google account.
3. Create an API key.
4. Add it to `.env` as `GOOGLE_API_KEY`.

If both `GOOGLE_API_KEY` and `GEMINI_API_KEY` are set, the Google provider may print a warning and use `GOOGLE_API_KEY`. Prefer keeping only `GOOGLE_API_KEY` in this project.

---

## Development

Install development dependencies:

```bash
uv sync --group dev
```

Run checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Format code:

```bash
uv run ruff format .
```

With pip:

```bash
pip install -r requirements-dev.txt
ruff check .
ruff format --check .
pytest
```

### Running unit tests

Run tests:

```bash
uv run pytest
```

Run with verbose output:

```bash
uv run pytest -v
```

Current checkpoint test result:

```text
609 passed, 1 skipped
```

---

## Tech Stack

- Python 3.13+
- CLI with `prompt_toolkit`
- Rich terminal rendering
- Textual TUI
- `pydantic-ai`
- Google Gemini via `google-genai`
- `python-dotenv`
- pickle storage
- Ruff
- pytest

---

## Project Status

The current baseline includes:

- working CLI;
- command aliases;
- command history and clean completion;
- contact management;
- note management;
- inline tag management;
- search;
- birthdays;
- Rich UI rendering;
- structured application statuses;
- safe pickle persistence with backup and recovery;
- AI command suggestions;
- optional TUI;
- updated test suite.

The next planned area is AI-assisted data enrichment: 
- AI phone validation fallback, 
- AI address parsing/validation, 
- AI tag suggestions.
