# Pennywise — AI Expense Organizer

Pennywise is a local-first expense tracker with optional Ollama-powered
category suggestions and budgeting observations. Expense records are saved
locally in SQLite.

## Start the app

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run main.py
```

Open [http://localhost:8501](http://localhost:8501). Expense tracking,
filtering, summaries, deletion, and CSV export work without an AI model.

## Optional AI setup

Install and start [Ollama](https://ollama.com/), then set `OLLAMA_MODEL` to a
model tag installed on your machine. The default is `gemma4:e2b`. Set
`OLLAMA_URL` to change the Ollama server address. AI features use that Ollama
service; they do not send email or financial data to a hosted AI provider.

Set `EXPENSE_DB_PATH` to change where the SQLite database is stored. See
[skill.md](./skill.md) for additional details.
