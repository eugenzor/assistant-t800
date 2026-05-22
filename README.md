# Assistant T800

AI-powered terminal assistant for contact management.

Assistant T800 is a Python 3.13+ terminal application that combines a Textual-based TUI with AI-assisted contact handling. The current version focuses on managing contacts through a natural-language AI interface.

---

## Features

- AI-powered contact management
- Modern terminal UI built with Textual
- Contact storage with:
  - names
  - phone numbers
  - email addresses
  - birthdays
  - physical addresses
- Contact validation
- Interactive AI chat interface
- Gemini AI integration via `pydantic-ai`
- Python 3.13+ support

---

## Requirements

- Python 3.13+
- Git
- Google Gemini API key

`uv` is optional. The project can be installed and run with standard Python tools: `venv` and `pip`.

---

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd assistant-t800
```

---

## 2. Create and activate a virtual environment

### Windows CMD

```cmd
py -3.13 -m venv .venv
.venv\Scripts\activate.bat
```

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the environment again.

### Linux / macOS

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install dependencies

### Standard installation

```bash
pip install -r requirements-ai.txt
```

If you also need development tools:

```bash
pip install -r requirements-dev.txt
```

---

## 4. Configure environment variables

Copy the example configuration file:

### Windows CMD

```cmd
copy .env.example .env
```

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Linux / macOS

```bash
cp .env.example .env
```

Open `.env` and replace `xxx` with your real Gemini API key:

```env
GOOGLE_API_KEY=AIza...your_key_here
```

Optionally, you may specify another AI model:

```env
ASSISTANT_T800_MODEL=google-gla:gemini-3.1-flash-lite
```

---

## Getting a Free Gemini API Key

1. Open https://aistudio.google.com
2. Sign in with your Google account.
3. Accept the terms of service if prompted.
4. Click **Get API key**.
5. Select **Create API key** → **Create key in new project**.
6. Copy the generated key. It usually starts with `AIza...`.

> The free tier does not require a credit card and is sufficient for development and prototyping with Gemini Flash models.

---

## Running the Application

The project uses a `src` layout. If the package is not installed in editable mode, Python must know where the source directory is located.

### Recommended option: install the package in editable mode

Run once after installing dependencies:

```bash
pip install -e .
```

Then start the application:

```bash
assistant-t800 --enable-ai
```

or:

```bash
python main.py --enable-ai
```

---

## Alternative: run with `PYTHONPATH`

Use this option if you do not want to install the package in editable mode.

### Windows CMD

```cmd
set PYTHONPATH=src
python main.py --enable-ai
```

### Windows PowerShell

```powershell
$env:PYTHONPATH = "src"
python main.py --enable-ai
```

### Linux / macOS

```bash
PYTHONPATH=src python main.py --enable-ai
```

---

## Optional: Running with uv

`uv` is not required, but it can simplify dependency and environment management.

Install `uv` only if you want to use it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then run:

```bash
uv sync
uv run assistant-t800 --enable-ai
```

or:

```bash
uv run python main.py --enable-ai
```

---

## Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run Ruff checks:

```bash
ruff check .
```

Format the codebase:

```bash
ruff format .
```

Run tests:

```bash
pytest
```

With `uv`, the same commands can be executed as:

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

---

## Tech Stack

- Python 3.13
- Textual
- pydantic-ai
- Google Gemini
- pydantic-settings
- python-dotenv
- Ruff
- pytest

---

## Project Status

The project is currently focused on the AI-powered TUI workflow.

Classic CLI mode and additional assistant features are planned for future development.