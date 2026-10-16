"""Streamlit interface for the AI Expense Organizer."""

from datetime import date

import pandas as pd
import streamlit as st

from model import CATEGORIES, ask_expense_assistant, categorize_expense, ollama_status
from tools import (
    add_expense,
    delete_expense,
    export_expenses_csv,
    get_expenses,
    get_summary,
    init_db,
)

st.set_page_config(
    page_title="Pennywise — Expense Organizer",
    page_icon="₹",
    layout="wide",
)

init_db()


def suggest_category() -> None:
    description = st.session_state.get("description", "").strip()
    if not description:
        st.session_state["category_error"] = "Enter an expense description first."
        return

    try:
        st.session_state["entry_category"] = categorize_expense(
            description,
            st.session_state.get("model_name", ""),
        )
        st.session_state["category_error"] = ""
    except (RuntimeError, ValueError) as error:
        st.session_state["category_error"] = str(error)


def add_expense_from_form() -> None:
    try:
        add_expense(
            st.session_state.get("description", ""),
            st.session_state["entry_amount"],
            st.session_state["entry_date"],
            st.session_state["entry_category"],
        )
    except ValueError as error:
        st.session_state["add_expense_error"] = str(error)
        st.session_state["add_expense_success"] = False
    else:
        st.session_state["description"] = ""
        st.session_state["entry_category"] = "Other"
        st.session_state["add_expense_error"] = ""
        st.session_state["add_expense_success"] = True


st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1440px;}
    [data-testid="stMetric"] {
        background: rgba(48, 117, 92, 0.08);
        border: 1px solid rgba(48, 117, 92, 0.16);
        padding: 1rem 1.15rem;
        border-radius: 14px;
    }
    [data-testid="stMetricLabel"] {font-size: 0.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("Pennywise")
    st.caption("A calmer view of your money.")
    st.divider()
    st.subheader("Add an expense")
    st.text_input(
        "What was it for?",
        key="description",
        placeholder="e.g. Weekly groceries",
        max_chars=240,
    )
    st.number_input(
        "Amount (₹)",
        min_value=0.01,
        value=250.00,
        step=50.00,
        format="%.2f",
        key="entry_amount",
    )
    st.date_input(
        "Date",
        value=date.today(),
        key="entry_date",
    )

    st.button("Suggest category with AI", on_click=suggest_category)
    if st.session_state.get("category_error"):
        st.error(st.session_state["category_error"])

    st.selectbox(
        "Category",
        CATEGORIES,
        key="entry_category",
        index=CATEGORIES.index("Other"),
    )
    st.button(
        "Add expense",
        type="primary",
        use_container_width=True,
        on_click=add_expense_from_form,
    )
    if st.session_state.get("add_expense_success"):
        st.success("Expense added.")
    if st.session_state.get("add_expense_error"):
        st.error(st.session_state["add_expense_error"])

    st.divider()
    st.subheader("Filters")
    start_date = st.date_input("From", value=None, key="filter_start")
    end_date = st.date_input("To", value=None, key="filter_end")
    if start_date and end_date and start_date > end_date:
        st.error("The start date must be on or before the end date.")
        start_date = None
        end_date = None

    st.divider()
    st.subheader("AI settings")
    st.text_input(
        "Ollama model",
        value="",
        key="model_name",
        placeholder="Uses OLLAMA_MODEL or gemma4:e2b",
        help="Use the exact model tag shown by `ollama list`.",
    )
    available, status_message = ollama_status()
    if available:
        st.success(status_message)
    else:
        st.info(status_message)

st.title("Your spending, at a glance")
st.caption("Track everyday spending and find useful patterns without the noise.")

if start_date and end_date and start_date > end_date:
    st.warning("Choose a valid date range in the sidebar.")
    st.stop()

summary = get_summary(start_date, end_date)
expenses = get_expenses(start_date, end_date)

metric_columns = st.columns(4)
metric_columns[0].metric("Total spent", f"₹{summary['total']:,.2f}")
metric_columns[1].metric("Transactions", f"{summary['count']:,}")
metric_columns[2].metric("Average expense", f"₹{summary['average']:,.2f}")
top_category = summary["by_category"][0][0] if summary["by_category"] else "—"
metric_columns[3].metric("Top category", top_category)

left_column, right_column = st.columns([1.45, 1], gap="large")
with left_column:
    st.subheader("Spending by category")
    if summary["by_category"]:
        category_data = pd.DataFrame(
            summary["by_category"], columns=["Category", "Amount (₹)"]
        ).set_index("Category")
        st.bar_chart(category_data, use_container_width=True, color="#2F755C")
    else:
        st.info("Add an expense to see your category breakdown.")

with right_column:
    st.subheader("Budget check-in")
    st.write(
        "Ask a question about this date range. The assistant receives only "
        "aggregated totals and category amounts."
    )
    question = st.text_input(
        "Your question",
        placeholder="Where am I spending the most?",
        key="assistant_question",
    )
    if st.button("Ask the assistant", disabled=not question.strip()):
        try:
            with st.spinner("Looking at your spending summary..."):
                advice = ask_expense_assistant(
                    question.strip(),
                    summary,
                    st.session_state.get("model_name", ""),
                )
            st.session_state["assistant_answer"] = advice
        except (RuntimeError, ValueError) as error:
            st.error(str(error))
    if st.session_state.get("assistant_answer"):
        st.info(st.session_state["assistant_answer"])
    st.caption("General budgeting observations only, not financial advice.")

st.divider()
st.subheader("Transactions")
export_column, delete_column = st.columns([1, 1])
with export_column:
    st.download_button(
        "Download CSV",
        data=export_expenses_csv(start_date, end_date),
        file_name="expenses.csv",
        mime="text/csv",
        disabled=not expenses,
    )

if expenses:
    transaction_frame = pd.DataFrame(expenses)
    transaction_frame = transaction_frame.rename(
        columns={
            "expense_date": "Date",
            "description": "Description",
            "category": "Category",
            "amount": "Amount (₹)",
        }
    )[["Date", "Description", "Category", "Amount (₹)", "id"]]
    transaction_frame["Amount (₹)"] = transaction_frame["Amount (₹)"].map(
        lambda value: f"₹{value:,.2f}"
    )
    st.dataframe(
        transaction_frame,
        hide_index=True,
        use_container_width=True,
        column_config={"id": st.column_config.NumberColumn("ID", width="small")},
    )

    with delete_column:
        selected_expense = st.selectbox(
            "Remove a transaction",
            expenses,
            format_func=lambda row: (
                f"#{row['id']} · {row['expense_date']} · "
                f"{row['description']} · ₹{row['amount']:,.2f}"
            ),
            key="expense_to_delete",
        )
        if st.button("Delete selected expense", type="secondary"):
            if delete_expense(selected_expense["id"]):
                st.success("Expense deleted.")
                st.rerun()
            st.error("That expense no longer exists. Refresh and try again.")
else:
    st.info("No expenses match this date range yet.")

st.caption(
    "Your records are stored in a local SQLite database. "
    "AI features use your configured Ollama service."
)
