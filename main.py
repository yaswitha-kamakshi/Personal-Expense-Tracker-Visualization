"""Personal Expense Tracker with Data Visualization - entry point.

  python main.py --generate-data        # create synthetic expenses.csv + budgets.csv
  python main.py                        # analyse the latest month in data/expenses.csv
  python main.py --month 2026-10        # analyse a specific month
  python main.py --file data/my_expenses.csv --income 40000
  python main.py --no-charts            # skip PNG charts
"""
import argparse
import sys

from src import analyzer, budget, plots, reporter
from src.config import BUDGETS_CSV, CURRENCY, DEFAULT_MONTHLY_INCOME, EXPENSES_CSV
from src.loader import load_clean

C = CURRENCY


def parse_args():
    p = argparse.ArgumentParser(description="Personal Expense Tracker with Data Visualization")
    p.add_argument("--file", default=str(EXPENSES_CSV), help="expenses CSV (date,category,amount,payment_method,description)")
    p.add_argument("--budgets", default=str(BUDGETS_CSV), help="budgets CSV (category,monthly_limit)")
    p.add_argument("--month", default="", help="month to analyse, e.g. 2026-10 (default: latest)")
    p.add_argument("--income", type=float, default=DEFAULT_MONTHLY_INCOME, help="monthly income for savings calculation")
    p.add_argument("--no-charts", action="store_true")
    p.add_argument("--generate-data", action="store_true", help="create synthetic data files and exit")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main():
    a = parse_args()
    if a.generate_data:
        from src.generate_data import write_files
        write_files(a.seed)
        return

    try:
        df, stats = load_clean(a.file)
        budgets = budget.load_budgets(a.budgets)
    except FileNotFoundError as e:
        sys.exit(f"File not found: {e.filename}\nTip: run  python main.py --generate-data  first.")
    except ValueError as e:
        sys.exit(f"Problem with the data: {e}")
    if df.empty:
        sys.exit("No valid expense rows after cleaning.")

    months = list(analyzer.by_month(df).index)
    month = a.month or months[-1]
    if month not in months:
        sys.exit(f"Month {month} not found. Available: {', '.join(months)}")

    print("\n" + "=" * 62)
    print(" DATA CLEANING")
    print("=" * 62)
    print(f" Rows read {stats['rows_in']}  ->  kept {stats['rows_out']}")
    print(f" Dropped: {stats['bad_date']} bad date, {stats['bad_amount']} bad amount, {stats['non_positive']} refund/zero, {stats['duplicates']} duplicate")
    print(f" Category guessed from description for {stats['categorised_by_rule']} rows")

    s = analyzer.summarize(df, month, a.income)
    d = analyzer.month_df(df, month)
    by_cat, by_pay = analyzer.by_category(d), analyzer.by_payment(d)
    by_month = analyzer.by_month(df)
    start, end, *_ = analyzer.month_span(df, month)
    daily = analyzer.daily_totals(d, start, end)
    bdf = budget.check(d, budgets)
    insights = analyzer.make_insights(s, bdf, C)

    status = f"month in progress: {s['days_elapsed']} of {s['days_in_month']} days" if s["in_progress"] else "full month"
    print("\n" + "=" * 62)
    print(f" EXPENSE SUMMARY: {month}  ({status})")
    print("=" * 62)
    print(f" Total spend      : {C}{s['total_spend']:,.0f}  ({s['transactions']} transactions)")
    print(f" Average per day  : {C}{s['avg_daily']:,.0f}")
    print(f" Income / Savings : {C}{s['income']:,.0f} / {C}{s['savings']:,.0f}  ({s['savings_rate']:.0f}% saved)")
    print("\n SPENDING BY CATEGORY")
    for name, amt in by_cat.items():
        print(f"   {name:<20}{C}{amt:>9,.0f}  {amt / s['total_spend'] * 100:>3.0f}%  " + "█" * int(amt / by_cat.max() * 20))
    print("\n BUDGET CHECK")
    icon = {"OVER": "🔴", "NEAR": "🟠", "OK": "🟢", "NO BUDGET": "⚪"}
    for r in bdf.itertuples():
        lim = "   n/a" if r.limit != r.limit else f"{C}{r.limit:,.0f}"
        pct = "  -" if r.pct_used != r.pct_used else f"{r.pct_used:.0f}%"
        print(f"   {icon[r.status]} {r.category:<20}{C}{r.spent:>8,.0f} / {lim:<7} {pct:>5}  {r.status}")
    print("\n INSIGHTS")
    for line in insights:
        print(f"   • {line}")

    csvs = reporter.save_csvs(df, by_cat, by_month, by_pay, bdf, month)
    report = reporter.save_text(reporter.build_text(s, stats, by_cat, bdf, insights), month)
    charts = {} if a.no_charts else plots.save_all(by_cat, by_month, by_pay, daily, bdf, month)

    print("\n" + "=" * 62)
    print(f" Report : {report}")
    print(f" CSVs   : outputs/ ({len(csvs)} files)")
    print(f" Charts : {'skipped' if a.no_charts else f'outputs/ ({len(charts)} PNG files)'}")
    print("=" * 62)


if __name__ == "__main__":
    main()
