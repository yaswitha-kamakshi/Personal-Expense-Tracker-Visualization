"""Save the cleaned data, summary CSVs and a readable text report."""
from datetime import datetime
from .config import CURRENCY, OUTPUTS_DIR, REPORTS_DIR


def save_csvs(df, by_cat, by_month, by_pay, budget_df, month):
    OUTPUTS_DIR.mkdir(exist_ok=True)
    paths = {
        "cleaned": OUTPUTS_DIR / "cleaned_expenses.csv",
        "category": OUTPUTS_DIR / f"category_summary_{month}.csv",
        "monthly": OUTPUTS_DIR / "monthly_summary.csv",
        "payment": OUTPUTS_DIR / f"payment_summary_{month}.csv",
        "budget": OUTPUTS_DIR / f"budget_check_{month}.csv",
    }
    df.drop(columns=["month"]).to_csv(paths["cleaned"], index=False)
    by_cat.rename("total").to_csv(paths["category"])
    by_month.rename("total").to_csv(paths["monthly"])
    by_pay.rename("total").to_csv(paths["payment"])
    budget_df.round(1).to_csv(paths["budget"], index=False)
    return paths


def build_text(s, stats, by_cat, budget_df, insights) -> str:
    c = CURRENCY
    L = ["PERSONAL EXPENSE REPORT", f"Month: {s['month']}   Generated: {datetime.now():%Y-%m-%d %H:%M}", "=" * 60,
         "", "DATA CLEANING",
         f"  rows read {stats['rows_in']} -> kept {stats['rows_out']} | bad dates {stats['bad_date']}, bad amounts {stats['bad_amount']}, "
         f"refunds/zero {stats['non_positive']}, duplicates {stats['duplicates']}, categorised by rule {stats['categorised_by_rule']}",
         "", "KEY NUMBERS",
         f"  Total spend         : {c}{s['total_spend']:,.0f}  ({s['transactions']} transactions)",
         f"  Average per day     : {c}{s['avg_daily']:,.0f}  ({s['days_elapsed']} of {s['days_in_month']} days)",
         f"  Average transaction : {c}{s['avg_transaction']:,.0f}",
         f"  Income / Savings    : {c}{s['income']:,.0f} / {c}{s['savings']:,.0f}  ({s['savings_rate']:.0f}%)", "",
         "SPENDING BY CATEGORY"]
    L += [f"  {name:<20}{c}{amt:>9,.0f}" for name, amt in by_cat.items()]
    L += ["", "BUDGET CHECK"]
    for r in budget_df.itertuples():
        lim = "-" if r.limit != r.limit else f"{c}{r.limit:,.0f}"
        pct = "-" if r.pct_used != r.pct_used else f"{r.pct_used:.0f}%"
        L.append(f"  {r.category:<20}spent {c}{r.spent:>8,.0f} / {lim:<8} {pct:>5}  {r.status}")
    L += ["", "INSIGHTS"] + [f"  - {i}" for i in insights]
    if s["large_transactions"]:
        L += ["", "UNUSUALLY LARGE TRANSACTIONS"] + [f"  - {t['date']:%d %b} {t['category']}: {c}{t['amount']:,.0f} ({t['description']})" for t in s["large_transactions"]]
    return "\n".join(L)


def save_text(text: str, month: str):
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"expense_report_{month}.txt"
    path.write_text(text, encoding="utf-8")
    return path
