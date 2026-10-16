import csv
import io
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import tools


class ExpenseStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "test-expenses.db"
        self.db_path_patch = patch.object(tools, "DB_PATH", self.database)
        self.db_path_patch.start()
        tools.init_db()

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def test_add_filter_summarize_and_export(self):
        tools.add_expense(" Groceries ", 1250, date(2026, 10, 1), "Food")
        tools.add_expense("Bus pass", 300, date(2026, 10, 3), "Auto / Transport")

        rows = tools.get_expenses("2026-10-02", "2026-10-31")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["description"], "Bus pass")

        summary = tools.get_summary()
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["total"], 1550)
        self.assertEqual(summary["average"], 775)
        self.assertEqual(summary["by_category"][0], ("Food", 1250))

        exported = list(csv.reader(io.StringIO(tools.export_expenses_csv())))
        self.assertEqual(exported[0], ["id", "date", "description", "category", "amount_inr"])
        self.assertEqual(len(exported), 3)

    def test_delete_returns_false_for_missing_expense(self):
        expense_id = tools.add_expense("Lunch", 100, category="Food")
        self.assertTrue(tools.delete_expense(expense_id))
        self.assertFalse(tools.delete_expense(expense_id))

    def test_rejects_invalid_expenses_and_date_ranges(self):
        for amount in (0, -1, float("inf"), float("nan")):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    tools.add_expense("Invalid", amount)
        with self.assertRaises(ValueError):
            tools.add_expense("Lunch", 100, "not-a-date", "Food")
        with self.assertRaises(ValueError):
            tools.add_expense("Lunch", 100, category="Unknown")
        with self.assertRaises(ValueError):
            tools.get_expenses("2026-10-02", "2026-10-01")


if __name__ == "__main__":
    unittest.main()
