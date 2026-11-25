"""Load and clean expense data. Returns the clean DataFrame plus a stats dict about what changed."""
import numpy as np
import pandas as pd
from .categorizer import classify

REQUIRED = ["date", "category", "amount", "payment_method", "description"]
CATEGORY_ALIASES = {
    "food": "Food & Dining", "food & dining": "Food & Dining", "dining": "Food & Dining",
    "grocery": "Groceries", "groceries": "Groceries", "transport": "Transport", "travel": "Transport",
    "bills": "Bills & Utilities", "utilities": "Bills & Utilities", "bills & utilities": "Bills & Utilities",
    "shopping": "Shopping", "entertainment": "Entertainment", "health": "Health", "medical": "Health",
    "education": "Education", "rent": "Rent",
}
PAYMENT_ALIASES = {
    "upi": "UPI", "gpay": "UPI", "phonepe": "UPI", "paytm": "UPI", "card": "Card", "credit card": "Card",
    "debit card": "Card", "cash": "Cash", "net banking": "Net Banking", "netbanking": "Net Banking",
}


def load_raw(path) -> pd.DataFrame:
    """Read everything as text first, so we control the conversions."""
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}. Expected: {REQUIRED}")
    return df[REQUIRED].copy()


def clean(raw: pd.DataFrame):
    stats = {"rows_in": len(raw)}
    df = raw.copy()
    for col in REQUIRED:
        df[col] = df[col].astype(str).str.strip()

    # 1) dates -> datetime (bad ones become NaT and are dropped)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    # 2) amounts -> numbers ("₹1,250" / "Rs. 99" -> 1250 / 99)
    df["amount"] = pd.to_numeric(df["amount"].str.replace(r"(?i)rs\.?|₹|,|\s", "", regex=True), errors="coerce")

    bad_date = df["date"].isna()
    bad_amount = df["amount"].isna()
    stats["bad_date"], stats["bad_amount"] = int(bad_date.sum()), int((bad_amount & ~bad_date).sum())
    df = df[~(bad_date | bad_amount)]

    non_positive = ~(df["amount"] > 0)                 # refunds / zero rows are not expenses
    stats["non_positive"] = int(non_positive.sum())
    df = df[~non_positive].copy()

    # 3) categories: aliases, then rules from description for blanks/unknowns
    lower = df["category"].str.lower()
    mapped = lower.map(CATEGORY_ALIASES)
    guessed = df["description"].map(classify)
    blank = lower == ""
    stats["categorised_by_rule"] = int(blank.sum())
    df["category"] = np.where(blank, guessed, mapped.fillna(df["category"].str.title()))

    # 4) payment methods
    pay = df["payment_method"].str.lower().map(PAYMENT_ALIASES)
    df["payment_method"] = np.where(df["payment_method"] == "", "Unknown", pay.fillna(df["payment_method"].str.title()))

    # 5) duplicates
    before = len(df)
    df = df.drop_duplicates(subset=REQUIRED)
    stats["duplicates"] = before - len(df)

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df = df.sort_values("date").reset_index(drop=True)
    stats["rows_out"] = len(df)
    return df, stats


def load_clean(path):
    return clean(load_raw(path))
