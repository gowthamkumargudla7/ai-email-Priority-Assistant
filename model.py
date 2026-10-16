"""Ollama integration for expense categorization and budgeting help."""

import json
import os

import requests

CATEGORIES = [
    "Auto / Transport",
    "Bills",
    "Education",
    "Entertainment",
    "Food",
    "Health",
    "Housing",
    "Shopping",
    "Travel",
    "Other",
]

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")


def ollama_status() -> tuple[bool, str]:
    """Return whether the configured Ollama service is responding."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        response.raise_for_status()
        return True, "Ollama is connected."
    except requests.RequestException:
        return (
            False,
            "Ollama is not reachable. Start Ollama to use AI features; "
            "manual expense tracking still works.",
        )


def _chat(prompt: str, model_name: str = "", timeout: int = 90) -> str:
    model = (model_name or DEFAULT_MODEL).strip()
    if not model:
        raise ValueError("Enter an Ollama model name.")

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a careful personal expense assistant. "
                            "Use only the supplied information. Be concise "
                            "and practical. Never request bank passwords, "
                            "card numbers, or other sensitive credentials."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.2},
            },
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError as error:
        raise RuntimeError(
            "Cannot connect to Ollama. Start Ollama and check "
            "that it is running at the configured OLLAMA_URL."
        ) from error
    except requests.exceptions.Timeout as error:
        raise RuntimeError(
            "The Ollama request timed out. Try again or check whether "
            "the model is responding."
        ) from error
    except requests.exceptions.HTTPError as error:
        raise RuntimeError(
            f"Ollama returned an HTTP error. Check that model '{model}' "
            "is installed and available."
        ) from error
    except requests.exceptions.RequestException as error:
        raise RuntimeError("Could not complete the Ollama request.") from error

    try:
        data = response.json()
        content = data.get("message", {}).get("content", "")
    except (ValueError, AttributeError) as error:
        raise RuntimeError("Ollama returned an invalid response.") from error

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Ollama returned an empty response.")
    return content.strip()


def categorize_expense(description: str, model_name: str = "") -> str:
    """Suggest one category for a description using the configured model."""
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Enter an expense description to categorize.")

    prompt = (
        f"Categorize this expense description: {description.strip()!r}\n"
        f"Choose exactly one category from: {', '.join(CATEGORIES)}.\n"
        "Return only the category name, with no explanation."
    )
    result = _chat(prompt, model_name=model_name, timeout=45)
    normalized = result.strip().strip(" .,:;\"'`").casefold()
    for category in CATEGORIES:
        if normalized == category.casefold():
            return category
    raise RuntimeError("Ollama returned an unknown category. Please try again.")


def ask_expense_assistant(
    question: str,
    summary: dict,
    model_name: str = "",
) -> str:
    """Answer a budgeting question using aggregate expense data only."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Enter a question about your spending.")

    try:
        safe_summary = {
            "date_range": str(summary.get("date_range", "all recorded dates")),
            "total": round(float(summary.get("total", 0)), 2),
            "count": int(summary.get("count", 0)),
            "average": round(float(summary.get("average", 0)), 2),
            "by_category": [
                {
                    "category": str(row[0]),
                    "amount": round(float(row[1]), 2),
                }
                for row in summary.get("by_category", [])
            ],
        }
    except (TypeError, ValueError, IndexError) as error:
        raise ValueError("The expense summary is invalid.") from error

    prompt = (
        "The following is the user's expense summary in Indian rupees (INR):\n"
        f"{json.dumps(safe_summary, ensure_ascii=False)}\n\n"
        f"User question: {question.strip()}\n\n"
        "Give practical budgeting observations. Say when there is not enough "
        "detail. Do not claim to see individual transactions when only "
        "aggregated totals are provided. This is general budgeting help, "
        "not professional financial advice."
    )
    return _chat(prompt, model_name=model_name)
