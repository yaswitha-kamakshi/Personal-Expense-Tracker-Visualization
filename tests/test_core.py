import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import analyzer, budget
from src.categorizer import classify
from src.generate_data import generate
from src.loader import clean


def tiny():
    raw = pd.DataFrame({
        "date": ["2026-10-01", "2026-10-02", "2026-10-02", "bad", "2026-10-03", "2026-10-04"],
        "category": ["FOOD ", "", "shopping", "food", "Rent", "food"],
        "amount": ["₹1,200", "300", "-50", "100", "abc", "500"],
        "payment_method": ["upi", "CASH", "Card", "UPI", "UPI", ""],
        "description": ["lunch", "Swiggy order", "refund", "x", "rent", "dinner"]})
    return clean(raw)


class CleaningTests(unittest.TestCase):
    def test_stats_and_rows(self):
        df, st = tiny()
        self.assertEqual((st["bad_date"], st["bad_amount"], st["non_positive"]), (1, 1, 1))
        self.assertEqual(len(df), 3)

    def test_amount_symbol_and_commas(self):
        df, _ = tiny()
        self.assertIn(1200.0, df["amount"].tolist())

    def test_category_alias_and_rule(self):
        df, _ = tiny()
        self.assertEqual(sorted(df["category"].unique()), ["Food & Dining"])  # FOOD , blank+Swiggy, food

    def test_payment_normalised(self):
        df, _ = tiny()
        self.assertEqual(set(df["payment_method"]), {"UPI", "Cash", "Unknown"})

    def test_duplicates_removed(self):
        raw = pd.DataFrame({"date": ["2026-10-01"] * 2, "category": ["Food"] * 2, "amount": ["100"] * 2,
                            "payment_method": ["UPI"] * 2, "description": ["tea"] * 2})
        df, st = clean(raw)
        self.assertEqual((len(df), st["duplicates"]), (1, 1))


class CategorizerTests(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(classify("Swiggy order"), "Food & Dining")
        self.assertEqual(classify("Amazon Prime renewal"), "Entertainment")  # before generic Amazon
        self.assertEqual(classify("amazon order"), "Shopping")
        self.assertEqual(classify("cola bottle"), "Uncategorized")            # 'ola' must not match inside 'cola'
        self.assertEqual(classify(""), "Uncategorized")


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        raw = pd.DataFrame({
            "date": ["2026-09-10", "2026-10-01", "2026-10-02", "2026-10-03"],
            "category": ["Food", "Food", "Shopping", "Food"], "amount": ["1000", "200", "600", "200"],
            "payment_method": ["UPI", "UPI", "Card", "Cash"], "description": ["a", "b", "c", "d"]})
        self.df, _ = clean(raw)

    def test_summary_numbers(self):
        s = analyzer.summarize(self.df, "2026-10", income=10000)
        self.assertEqual(s["total_spend"], 1000)
        self.assertEqual(s["top_category"], "Shopping")          # 600 vs Food 400 in October
        self.assertEqual(s["savings"], 9000)
        self.assertAlmostEqual(s["savings_rate"], 90.0)
        self.assertTrue(s["in_progress"])            # data ends 3 Oct, month has 31 days
        self.assertEqual(s["days_elapsed"], 3)
        self.assertAlmostEqual(s["avg_daily"], 1000 / 3)

    def test_month_over_month(self):
        s = analyzer.summarize(self.df, "2026-10", 10000)
        self.assertEqual(s["prev_month"], "2026-09")
        self.assertAlmostEqual(s["mom_change_pct"], 0.0)

    def test_budget_status(self):
        d = analyzer.month_df(self.df, "2026-10")
        b = pd.Series({"Food & Dining": 300.0, "Shopping": 1000.0, "Health": 500.0})
        t = budget.check(d, b).set_index("category")
        self.assertEqual(t.loc["Food & Dining", "status"], "OVER")    # 400 of 300
        self.assertEqual(t.loc["Shopping", "status"], "OK")           # 60%
        self.assertEqual(t.loc["Health", "spent"], 0)

    def test_unbudgeted_category_flagged(self):
        d = analyzer.month_df(self.df, "2026-10")
        t = budget.check(d, pd.Series({"Health": 500.0})).set_index("category")
        self.assertEqual(t.loc["Food & Dining", "status"], "NO BUDGET")

    def test_daily_totals_fill_zero_days(self):
        d = analyzer.month_df(self.df, "2026-10")
        daily = analyzer.daily_totals(d, "2026-10-01", "2026-10-05")
        self.assertEqual(len(daily), 5)
        self.assertEqual(daily.iloc[-1], 0)


class GeneratorTests(unittest.TestCase):
    def test_deterministic_and_cleanable(self):
        a, b = generate(7, "2026-11-25"), generate(7, "2026-11-25")
        self.assertTrue(a.equals(b))
        df, st = clean(a)
        self.assertGreater(len(df), 100)
        self.assertGreaterEqual(st["duplicates"], 1)
        self.assertEqual(df["month"].nunique(), 3)


if __name__ == "__main__":
    unittest.main()
