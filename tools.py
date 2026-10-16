"""SQLite storage, reporting, and CSV export for expense records."""

import csv
import io
import math
import os
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Any

from model import CATEGORIES

DB_PATH = Path(
    os.getenv("EXPENSE_DB_PATH", str(Path(__file__).resolve().parent / "expenses.db"))
)


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def _validate_dates(start_date: date | str | None, end_date: date | str | None):
    start = _normalize_date(start_date) if start_date is not None else None
    end = _normalize_date(end_date) if end_date is not None else None
    if start and end and start > end:
        raise ValueError("The start date must be on or before the end date.")
    return start, end


def _normalize_date(value: date | str) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if not isinstance(value, str):
        raise ValueError("Expense dates must use YYYY-MM-DD format.")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError("Expense dates must use YYYY-MM-DD format.") from error


def init_db() -> None:
    """Create the expense table if it does not already exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                expense_date TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def add_expense(
    description: str,
    amount: float,
    expense_date: date | str | None = None,
    category: str = "Other",
) -> int:
    """Validate and store an expense, returning its new database ID."""
    if not isinstance(description, str):
        raise ValueError("Expense description must be text.")
    description = description.strip()
    if not description:
        raise ValueError("Expense description cannot be empty.")
    if len(description) > 240:
        raise ValueError("Expense description cannot exceed 240 characters.")

    try:
        amount = float(amount)
    except (TypeError, ValueError) as error:
        raise ValueError("Expense amount must be a valid number.") from error
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("Expense amount must be greater than zero.")

    if expense_date is None:
        normalized_date = date.today().isoformat()
    else:
        normalized_date = _normalize_date(expense_date)
    if not isinstance(category, str) or category.strip() not in CATEGORIES:
        raise ValueError("Choose a valid expense category.")

    with closing(_connect()) as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO expenses (description, amount, expense_date, category)
            VALUES (?, ?, ?, ?)
            """,
            (description, amount, normalized_date, category.strip()),
        )
        return int(cursor.lastrowid)


def get_expenses(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
) -> list[dict[str, Any]]:
    """Return matching expenses, newest first."""
    start, end = _validate_dates(start_date, end_date)
    query = (
        "SELECT id, description, amount, expense_date, category FROM expenses"
    )
    conditions = []
    parameters: list[str] = []
    if start:
        conditions.append("expense_date >= ?")
        parameters.append(start)
    if end:
        conditions.append("expense_date <= ?")
        parameters.append(end)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY expense_date DESC, id DESC"

    with closing(_connect()) as connection, connection:
        rows = connection.execute(query, parameters).fetchall()
    return [dict(row) for row in rows]


def get_summary(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
) -> dict[str, Any]:
    """Aggregate totals and category amounts for a date range."""
    start, end = _validate_dates(start_date, end_date)
    rows = get_expenses(start, end)
    total = sum(float(row["amount"]) for row in rows)
    category_totals: dict[str, float] = {}
    for row in rows:
        category = row["category"]
        category_totals[category] = (
            category_totals.get(category, 0.0) + float(row["amount"])
        )

    if start or end:
        date_range = f"{start or 'beginning'} to {end or 'today'}"
    else:
        date_range = "all recorded dates"
    return {
        "date_range": date_range,
        "total": total,
        "count": len(rows),
        "average": total / len(rows) if rows else 0.0,
        "by_category": sorted(
            category_totals.items(), key=lambda item: item[1], reverse=True
        ),
    }


def delete_expense(expense_id: int) -> bool:
    """Delete one expense, returning whether a record was removed."""
    try:
        normalized_id = int(expense_id)
    except (TypeError, ValueError) as error:
        raise ValueError("Expense ID must be a valid integer.") from error
    if normalized_id <= 0:
        raise ValueError("Expense ID must be a positive integer.")
    with closing(_connect()) as connection, connection:
        cursor = connection.execute(
            "DELETE FROM expenses WHERE id = ?", (normalized_id,)
        )
        return cursor.rowcount > 0


def export_expenses_csv(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
) -> str:
    """Export the selected date range as CSV text."""
    rows = get_expenses(start_date, end_date)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["id", "date", "description", "category", "amount_inr"])
    for row in rows:
        writer.writerow(
            [
                row["id"],
                row["expense_date"],
                row["description"],
                row["category"],
                f"{float(row['amount']):.2f}",
            ]
        )
    return output.getvalue()
