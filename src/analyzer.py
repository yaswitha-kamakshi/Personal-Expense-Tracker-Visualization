"""All the numbers: category, monthly, payment, daily, KPIs and insights."""
import numpy as np
import pandas as pd


def by_category(df) -> pd.Series:
    return df.groupby("category")["amount"].sum().sort_values(ascending=False)


def by_month(df) -> pd.Series:
    return df.groupby("month")["amount"].sum().sort_index()


def by_payment(df) -> pd.Series:
    return df.groupby("payment_method")["amount"].sum().sort_values(ascending=False)


def daily_totals(df, start, end) -> pd.Series:
    """Spend per calendar day, with 0 for days without spending."""
    s = df.groupby(df["date"].dt.normalize())["amount"].sum()
    return s.reindex(pd.date_range(start, end), fill_value=0.0)


def month_df(df, month):
    return df[df["month"] == month]


def month_span(df_all, month):
    """(start, end, days_elapsed, days_in_month, in_progress) for a month, limited to the last data date."""
    p = pd.Period(month)
    start, month_end = p.start_time.normalize(), p.end_time.normalize()
    last = df_all["date"].max().normalize()
    end = min(month_end, last)
    return start, end, (end - start).days + 1, p.days_in_month, end < month_end


def summarize(df_all, month, income) -> dict:
    d = month_df(df_all, month)
    start, end, days, dim, in_progress = month_span(df_all, month)
    total = float(d["amount"].sum())
    cats = by_category(d)
    pays = by_payment(d)
    daily = daily_totals(d, start, end)
    peak = daily_totals(d[d["category"] != "Rent"], start, end)
    months = list(by_month(df_all).index)
    prev = months[months.index(month) - 1] if month in months and months.index(month) > 0 else None
    prev_total = float(month_df(df_all, prev)["amount"].sum()) if prev else None
    mean, std = (float(np.mean(d["amount"])), float(np.std(d["amount"]))) if len(d) else (0.0, 0.0)
    large = d[d["amount"] > mean + 2 * std].sort_values("amount", ascending=False).head(3)
    return {
        "month": month, "days_elapsed": days, "days_in_month": dim, "in_progress": in_progress,
        "total_spend": total, "transactions": len(d), "avg_transaction": mean,
        "avg_daily": total / days if days else 0.0,
        "projected_month": total / days * dim if days else 0.0,
        "income": float(income), "savings": float(income) - total,
        "savings_rate": (float(income) - total) / float(income) * 100 if income else 0.0,
        "top_category": cats.index[0] if len(cats) else None,
        "top_category_amount": float(cats.iloc[0]) if len(cats) else 0.0,
        "top_category_share": float(cats.iloc[0] / total * 100) if len(cats) and total else 0.0,
        "top_payment": pays.index[0] if len(pays) else None,
        "top_payment_share": float(pays.iloc[0] / total * 100) if len(pays) and total else 0.0,
        "peak_day": peak.idxmax() if len(peak) else None,          # rent (1st of month) is excluded
        "peak_day_amount": float(peak.max()) if len(peak) else 0.0,
        "prev_month": prev, "prev_total": prev_total,
        "mom_change_pct": ((total - prev_total) / prev_total * 100) if prev_total else None,
        "large_transactions": large[["date", "category", "amount", "description"]].to_dict("records"),
    }


def make_insights(s: dict, budget_df: pd.DataFrame, cur="₹") -> list:
    out = []
    if s["top_category"]:
        out.append(f"Highest spending category: {s['top_category']} ({cur}{s['top_category_amount']:,.0f}, {s['top_category_share']:.0f}% of spending).")
    if s["mom_change_pct"] is not None:
        word = "up" if s["mom_change_pct"] > 0 else "down"
        note = f" vs {s['prev_month']} (month still in progress, so this is not a full comparison)" if s["in_progress"] else f" vs {s['prev_month']}"
        out.append(f"Spending is {word} {abs(s['mom_change_pct']):.0f}%{note}.")
    if s["in_progress"]:
        out.append(f"At this pace you will spend about {cur}{s['projected_month']:,.0f} by month end.")
    over = budget_df[budget_df["status"] == "OVER"]
    if len(over):
        names = ", ".join(f"{r.category} (+{cur}{-r.remaining:,.0f})" for r in over.itertuples())
        out.append(f"Over budget in: {names}.")
    near = budget_df[budget_df["status"] == "NEAR"]
    if len(near):
        out.append("Close to the limit: " + ", ".join(near["category"]) + ".")
    if s["top_payment"]:
        out.append(f"Most used payment method: {s['top_payment']} ({s['top_payment_share']:.0f}% of spending).")
    if s["peak_day"] is not None:
        out.append(f"Highest-spend day: {s['peak_day']:%d %b} ({cur}{s['peak_day_amount']:,.0f}).")
    sr = s["savings_rate"]
    out.append(f"Savings rate: {sr:.0f}% " + ("(healthy: 20% or more)." if sr >= 20 else "(below the common 20% target)." if sr >= 0 else "(spending is higher than income!)."))
    return out
