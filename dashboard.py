"""Streamlit dashboard (optional).  Run with:  streamlit run dashboard.py"""
import io

import pandas as pd
import streamlit as st

from src import analyzer, budget, plots
from src.config import BUDGETS_CSV, DEFAULT_MONTHLY_INCOME, EXPENSES_CSV
from src.loader import clean, load_raw

st.set_page_config(page_title="Personal Expense Tracker", page_icon="💸", layout="wide")
st.title("💸 Personal Expense Tracker")
st.caption("Upload your own CSV (date, category, amount, payment_method, description) or use the synthetic demo data.")

up = st.sidebar.file_uploader("Upload expenses CSV", type="csv")
income = st.sidebar.number_input("Monthly income (₹)", min_value=0.0, value=float(DEFAULT_MONTHLY_INCOME), step=1000.0)

try:
    raw = load_raw(io.BytesIO(up.getvalue()) if up else EXPENSES_CSV)
except (FileNotFoundError, ValueError) as e:
    st.error(f"{e}\n\nRun `python main.py --generate-data` first, or upload a valid CSV.")
    st.stop()

df, stats = clean(raw)
if df.empty:
    st.error("No valid rows after cleaning.")
    st.stop()
budgets = budget.load_budgets(BUDGETS_CSV) if BUDGETS_CSV.exists() else pd.Series(dtype=float)

months = list(analyzer.by_month(df).index)
month = st.sidebar.selectbox("Month", months[::-1])
accounts = st.sidebar.multiselect("Payment methods", sorted(df["payment_method"].unique()), default=sorted(df["payment_method"].unique()))
view = df[df["payment_method"].isin(accounts)]

s = analyzer.summarize(view, month, income)
d = analyzer.month_df(view, month)
start, end, *_ = analyzer.month_span(view, month)
bdf = budget.check(d, budgets)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total spend", f"₹{s['total_spend']:,.0f}")
c2.metric("Average per day", f"₹{s['avg_daily']:,.0f}")
c3.metric("Savings", f"₹{s['savings']:,.0f}", f"{s['savings_rate']:.0f}% of income")
c4.metric("Top category", s["top_category"] or "n/a")

st.subheader("💡 Insights")
for line in analyzer.make_insights(s, bdf):
    st.write("• " + line)

left, right = st.columns(2)
with left:
    st.pyplot(plots.category_bar(analyzer.by_category(d), f"Spending by category: {month}"))
    st.pyplot(plots.daily_trend(analyzer.daily_totals(d, start, end), f"Daily spending: {month}"))
with right:
    st.pyplot(plots.monthly_line(analyzer.by_month(view)))
    st.pyplot(plots.payment_pie(analyzer.by_payment(d), f"Payment methods: {month}"))

st.subheader("Budget check")
if budgets.empty:
    st.info("No budgets.csv found.")
else:
    st.dataframe(bdf.round(1), use_container_width=True, hide_index=True)
    st.pyplot(plots.budget_chart(bdf, f"Budget vs actual: {month}"))

with st.expander(f"Cleaning report: {stats['rows_in']} rows read, {stats['rows_out']} kept"):
    st.json(stats)
st.download_button("⬇ Download cleaned data (CSV)", df.drop(columns=["month"]).to_csv(index=False), "cleaned_expenses.csv", "text/csv")
