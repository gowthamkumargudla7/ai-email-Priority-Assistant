# Pennywise — AI Expense Organizer

A local-first expense tracker built with Python, Streamlit, SQLite, and Ollama.

## Features

- Add expenses with a description, amount, date, and category.
- Optionally ask Ollama to suggest an expense category.
- Filter transactions by date and view totals, averages, and category charts.
- Ask for general budgeting observations based on aggregated totals.
- Export filtered transactions to CSV and delete records.
- Store records in a local SQLite database (`expenses.db`).

## Run locally

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment:
   - PowerShell: `python -m venv .venv` then `.\\.venv\\Scripts\\Activate.ps1`
   - Command Prompt: `python -m venv .venv` then `.venv\\Scripts\\activate.bat`
3. Install dependencies: `python -m pip install -r requirements.txt`
4. Start the app: `python -m streamlit run main.py`
5. Open `http://localhost:8501`.

Expense tracking works without Ollama. For local AI features, install and run
Ollama, check the exact model tag with `ollama list`, and set `OLLAMA_MODEL`
if needed. The default local model is `gemma4:e2b`. Set `OLLAMA_URL` if Ollama
is not running at `http://localhost:11434/api/chat`. This setting also accepts
the server base URL `http://localhost:11434`.

For a hosted deployment, configure the `OLLAMA_API_KEY` secret in the hosting
provider's environment settings using a key from
[Ollama settings](https://ollama.com/settings/keys). When the key is set, the
app defaults to `https://ollama.com/api/chat` and `gemma4:31b`; `OLLAMA_URL`
and `OLLAMA_MODEL` can override these values. A `localhost` URL on a hosted
deployment refers to the app container, not your personal computer. Keep API
keys out of source control.

## Data and privacy

Expense data stays in the local SQLite file `expenses.db` by default. Set
`EXPENSE_DB_PATH` to store it elsewhere. AI features send the expense description or aggregated totals to the
configured Ollama service; individual transactions are not sent to the
budgeting assistant. Do not enter bank passwords, full card numbers, or other
credentials.
