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

Expense tracking works without Ollama. For AI features, install and run Ollama,
check the exact model tag with `ollama list`, and set `OLLAMA_MODEL` if needed.
The default model is `gemma4:e2b`. Set `OLLAMA_URL` if Ollama is not running at
`http://localhost:11434`.

## Data and privacy

Expense data stays in the local SQLite file `expenses.db` by default. Set
`EXPENSE_DB_PATH` to store it elsewhere. AI features send the expense
description or aggregated totals to the configured Ollama service; individual
transactions are not sent to the budgeting assistant. Do not enter bank
passwords, full card numbers, or other credentials.
