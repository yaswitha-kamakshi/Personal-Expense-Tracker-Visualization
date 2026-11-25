"""Compare spending with monthly category budgets."""
import pandas as pd
from .config import NEAR_LIMIT_PCT


def load_budgets(path) -> pd.Series:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    return df.set_index("category")["monthly_limit"].astype(float)


def check(month_df: pd.DataFrame, budgets: pd.Series) -> pd.DataFrame:
    spent = month_df.groupby("category")["amount"].sum()
    table = pd.DataFrame({"limit": budgets, "spent": spent}).fillna({"spent": 0.0})
    table["remaining"] = table["limit"] - table["spent"]
    table["pct_used"] = table["spent"] / table["limit"] * 100

    def status(row):
        if pd.isna(row["limit"]):
            return "NO BUDGET"
        if row["pct_used"] > 100:
            return "OVER"
        return "NEAR" if row["pct_used"] >= NEAR_LIMIT_PCT else "OK"

    table["status"] = table.apply(status, axis=1)
    table = table.reset_index().rename(columns={"index": "category"})
    return table.sort_values("pct_used", ascending=False, na_position="last").reset_index(drop=True)
