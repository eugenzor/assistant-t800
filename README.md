# Assistant T800

Assistant T800 is a Python 3.13+ personal assistant for managing contacts from the terminal.

The main interface is a classic CLI. The project also includes an optional Textual-based TUI with AI chat support.

---

## Current Features

### Contact management

- Add contacts with:
  - name
  - phone numbers
  - email addresses
  - address
  - birthday
- Show all contacts.
- Show one contact by name.
- Search contacts by all fields or by a specific field.
- Show upcoming birthdays with weekend congratulations moved to Monday.
- Update address and birthday.
- Add one or more phone numbers or email addresses.
- Remove contacts and contact fields with confirmation.
- Remove one, many, or all phone numbers / email addresses.

### Search

Implemented commands:

- `search <query>`
- `search-name <query>`
- `search-phone <query>`
- `search-email <query>`
- `search-note <query>`
- `search-tag <query>`

Search is case-insensitive and supports partial matches.

### Persistence

Address book data is stored in:

```text
.data/address_book.pkl
```

CLI command history is stored in:

```text
.data/cli_commands_history
```

### CLI UX

- Command history.
- Command completion.
- Fallback to standard `input()` if `prompt_toolkit` is unavailable.
- Aliases in English and Ukrainian.
- Long alias resolution, for example `знайди телефон Аліса` can resolve to `search-phone Аліса`.

### AI suggestions

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

- `edit-note <name>` — interactive contact note editing.
- `remove-note <name>` — clear the note attached to a contact.
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
py -3.13 -m venv .venv
.venv\Scripts\activate.bat
```

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
python3.13 -m venv .venv
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
birthdays
birthdays 14
add-phone "John Smith" 0992223344;0993334455
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

---

## Tech Stack

- Python 3.13+
- CLI with `prompt_toolkit`
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
- command history and completion;
- contact management;
- search;
- birthdays;
- pickle persistence;
- AI suggestions;
- optional TUI.

The next planned area is contact-attached notes and tags editing commands.
