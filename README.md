FIXME
● Reviewed the AI module. Here's my validation of the print tool idea.

  Current state

  - Tools return ToolReturn(metadata=DisplayPayload(...)). apply_display extracts the last payload from the run and routes it to Presenter.refresh_contacts / refresh_birthdays / print.
  - Presenter.print(text) and DisplayPayload(kind="text", text=...) already exist (deps.py:24, results.py:14, display.py:37-39, presenter.py:28-30, 83-86) — but no tool currently emits a text payload, so this branch is dead code today.
  - The display always renders fixed, hard-coded layouts in _render_contacts / _render_birthdays. The fields parameter on read tools only trims what's sent to the LLM (formatting.py), not what the panel shows.

  Verdict: the idea is valid, with caveats

  Pros
  - Half the plumbing is already in place — adding a print tool is ~10 lines + a system-prompt rule.
  - Solves the actual gap: arbitrary per-request views ("just names and phones", "group by tag", "as a phonebook").
  - Plays to LLM strengths (formatting text).

  Risks to weigh
  1. Hallucination / integrity loss. Today the display path serializes domain objects directly — the panel cannot lie. With print, the LLM retypes data and can drop digits in a phone, misspell a name, omit a row, etc. The structured path's strongest guarantee disappears.
  2. Visual inconsistency. _render_contacts uses Textual markup ([bold], [dim]). LLM-generated text won't match unless the prompt teaches it — and even then, output will drift between runs.
  3. Tokens & latency. To "print" 50 contacts the model must re-emit every value as output tokens. Structured payloads cost zero output tokens for the display.
  4. Two overlapping paths. Without crisp rules the model will pick print vs list_contacts arbitrarily. The system prompt currently says "Панель оновлюється автоматично після виконання інструментів — не потрібно окремо викликати інструменти лише для оновлення панелі" (agent.py:84-85) — that rule
  directly fights print. It would need rewriting.

  Recommendation

  Add it, but as a fallback, not the default. Two-layer approach works best:

  - First, extend DisplayPayload(kind="contacts") with an optional display_fields: frozenset[str] | None and teach _render_contacts to honor it. The existing read tools gain a display_fields arg the LLM passes for "show only names and phones" — structured, no hallucination, cheap.
  - Then add print(text) for genuinely free-form requests ("show as a CSV", "group by tag with counts") that the structured path can't express. System prompt: prefer structured tools; use print only when the user asks for a custom layout.

  Want me to sketch the implementation for either or both?


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
- Edit and remove contact notes.
- Add and remove contact tags.
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

These features are optional follow-up improvements:

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
edit-note "John Smith" "Call after demo"
add-tag "John Smith" work;urgent
remove-tag "John Smith" urgent
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

Run the full test suite:

```bash
uv run pytest
```

Run with verbose output:

```bash
uv run pytest -v
```

Run only the AI tools tests:

```bash
uv run pytest tests/test_ai_tools.py
```

Run a specific test by name:

```bash
uv run pytest -k "test_add_contact"
```

Run with coverage report:

```bash
uv run pytest --cov=src/assistant_t800 --cov-report=term-missing
```

With pip (activate the virtual environment first):

```bash
pytest
pytest -v
pytest tests/test_ai_tools.py
pytest --cov=src/assistant_t800 --cov-report=term-missing
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

The next planned area is optional tag sorting or grouping.
