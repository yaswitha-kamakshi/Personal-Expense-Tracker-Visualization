"""Charts (matplotlib, styled with seaborn when available). Every function returns a Figure."""
import matplotlib
matplotlib.use("Agg")   # draw to files; no window needed
import matplotlib.pyplot as plt
import pandas as pd
from .config import CURRENCY, OUTPUTS_DIR

try:
    import seaborn as sns
    sns.set_theme(style="whitegrid")
    PALETTE = sns.color_palette("deep")
except ImportError:      # works without seaborn too
    plt.style.use("ggplot")
    PALETTE = plt.rcParams["axes.prop_cycle"].by_key()["color"]


def category_bar(by_cat: pd.Series, title="Spending by category"):
    fig, ax = plt.subplots(figsize=(9, 5))
    s = by_cat.sort_values()
    bars = ax.barh(s.index, s.values, color=PALETTE[0])
    for b, v in zip(bars, s.values):
        ax.text(v, b.get_y() + b.get_height() / 2, f" {CURRENCY}{v:,.0f}", va="center", fontsize=9)
    ax.set_xlabel(f"Amount ({CURRENCY})")
    ax.set_title(title)
    ax.set_xlim(0, s.max() * 1.15)
    fig.tight_layout()
    return fig


def monthly_line(by_month: pd.Series, title="Monthly spending trend"):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(by_month.index, by_month.values, marker="o", linewidth=2.5, color=PALETTE[3])
    for x, v in zip(by_month.index, by_month.values):
        ax.annotate(f"{CURRENCY}{v:,.0f}", (x, v), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=9)
    ax.set_ylabel(f"Total spend ({CURRENCY})")
    ax.set_title(title)
    ax.set_ylim(0, by_month.max() * 1.2)
    fig.tight_layout()
    return fig


def payment_pie(by_pay: pd.Series, title="Spending by payment method"):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(by_pay.values, labels=by_pay.index, autopct="%1.0f%%", startangle=90, colors=PALETTE[: len(by_pay)],
           wedgeprops={"edgecolor": "white"})
    ax.set_title(title)
    fig.tight_layout()
    return fig


def daily_trend(daily: pd.Series, title="Daily spending trend"):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(daily.index, daily.values, color=PALETTE[0], alpha=0.5, label="Daily spend", width=0.8)
    ax.plot(daily.index, daily.rolling(7, min_periods=1).mean(), color=PALETTE[3], linewidth=2.5, label="7-day average")
    ax.set_ylabel(f"Amount ({CURRENCY})")
    ax.set_title(title)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def budget_chart(budget_df: pd.DataFrame, title="Budget vs actual"):
    t = budget_df.dropna(subset=["limit"]).sort_values("pct_used")
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#d62728" if s == "OVER" else "#ff7f0e" if s == "NEAR" else "#2ca02c" for s in t["status"]]
    ax.barh(t["category"], t["limit"], color="lightgray", label="Budget")
    ax.barh(t["category"], t["spent"], color=colors, height=0.5, label="Spent")
    ax.set_xlabel(f"Amount ({CURRENCY})")
    ax.set_title(title + "  (red = over, orange = near limit)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig


def save_all(by_cat, by_month, by_pay, daily, budget_df, month, outdir=OUTPUTS_DIR) -> dict:
    outdir.mkdir(exist_ok=True)
    figs = {
        "category_bar": category_bar(by_cat, f"Spending by category: {month}"),
        "monthly_line": monthly_line(by_month),
        "payment_pie": payment_pie(by_pay, f"Spending by payment method: {month}"),
        "daily_trend": daily_trend(daily, f"Daily spending: {month}"),
        "budget_chart": budget_chart(budget_df, f"Budget vs actual: {month}"),
    }
    paths = {}
    for name, fig in figs.items():
        paths[name] = outdir / f"{name}_{month}.png"
        fig.savefig(paths[name], dpi=110)
        plt.close(fig)
    return paths
