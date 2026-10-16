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

For local development, install and start [Ollama](https://ollama.com/), then
set `OLLAMA_MODEL` to a model tag installed on your machine. The default is
`gemma4:e2b`. Set `OLLAMA_URL` to change the Ollama server address.

The hosted app can use Ollama Cloud. Create an API key in
[Ollama settings](https://ollama.com/settings/keys), then add it as the
`OLLAMA_API_KEY` secret in the Render service's Environment settings. Do not
put the key in source code or share it in chat. When this key is configured,
the app defaults to `https://ollama.com` and model `gemma4:31b`; optionally
set `OLLAMA_URL` or `OLLAMA_MODEL` in Render to override those defaults.

AI requests are sent to the configured Ollama service: expense descriptions
for category suggestions, and the selected date range's aggregated totals,
category amounts, and question for budgeting observations. The app does not
send these requests to a separate AI provider.

Set `EXPENSE_DB_PATH` to change where the SQLite database is stored. See
[skill.md](./skill.md) for additional details.

## Public demo on Render

The repository includes a Render Blueprint. To create a public demo, sign in
to Render, choose **New** → **Blueprint**, and select this GitHub repository.
Render will build the Streamlit app and assign it a public `onrender.com`
address. The free service uses temporary local storage, so demo expenses can
be lost when the service restarts. All visitors share the same database; do
not enter personal financial information.
