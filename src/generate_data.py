"""Create SYNTHETIC expense data (3 months, ends today) with realistic mess to clean.

No real bank data is used. Fixed seed -> same data every time.
"""
import numpy as np
import pandas as pd
from .config import BUDGETS_CSV, DATA_DIR, EXPENSES_CSV

CATEGORIES = {   # name: (weight, min amount, max amount, descriptions)
    "Food & Dining":     (0.30, 100, 450,  ["Swiggy order", "Zomato dinner", "Cafe coffee", "Restaurant lunch", "Biryani"]),
    "Groceries":         (0.12, 200, 950,  ["Big Bazaar", "D-Mart groceries", "Reliance Fresh", "Vegetables"]),
    "Transport":         (0.22, 40, 300,   ["Uber ride", "Ola cab", "Metro card recharge", "Petrol", "Rapido bike"]),
    "Shopping":          (0.10, 400, 1500, ["Amazon order", "Flipkart purchase", "Myntra clothes", "Ajio order"]),
    "Entertainment":     (0.08, 150, 500,  ["BookMyShow movie", "Cinema tickets", "Spotify", "Gaming"]),
    "Health":            (0.07, 100, 900,  ["Apollo pharmacy", "Doctor consultation", "Gym day pass"]),
    "Education":         (0.03, 150, 700,  ["Udemy course", "Books", "Exam fee"]),
    "Bills & Utilities": (0.05, 150, 600,  ["Electricity bill", "Water bill", "DTH recharge"]),
}
PAYMENTS = ["UPI", "Card", "Cash", "Net Banking"]
PAY_P = [0.55, 0.20, 0.17, 0.08]

BUDGETS = {"Food & Dining": 4000, "Groceries": 5000, "Transport": 2500, "Shopping": 3000,
           "Entertainment": 1500, "Bills & Utilities": 3000, "Health": 1500, "Education": 1500, "Rent": 8000}


def generate(seed: int = 42, today=None) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    today = pd.Timestamp(today if today is not None else pd.Timestamp.today()).normalize()
    start = (today - pd.DateOffset(months=2)).replace(day=1)
    names = list(CATEGORIES)
    weights = np.array([CATEGORIES[n][0] for n in names])
    weights = weights / weights.sum()
    rows = []
    fixed = {1: ("Rent", 8000, "Monthly rent", "Net Banking"), 5: ("Bills & Utilities", 799, "WiFi broadband", "UPI"),
             10: ("Entertainment", 649, "Netflix subscription", "Card"), 12: ("Bills & Utilities", 299, "Mobile recharge", "UPI")}

    for day in pd.date_range(start, today):
        if day.day in fixed:
            c, a, d, p = fixed[day.day]
            rows.append((day, c, float(a), p, d))
        for _ in range(rng.choice([0, 1, 2, 3], p=[0.2, 0.4, 0.28, 0.12])):
            cat = str(rng.choice(names, p=weights))
            _, lo, hi, descs = CATEGORIES[cat]
            amount = round(rng.uniform(lo, hi) / 10) * 10
            if day.weekday() >= 5 and cat in ("Food & Dining", "Entertainment", "Shopping"):
                amount *= 1.3                                    # weekends cost more
            if cat == "Shopping" and day.month == today.month:
                amount *= 1.7                                    # current month: overspend on shopping
            rows.append((day, cat, float(round(amount)), str(rng.choice(PAYMENTS, p=PAY_P)), str(rng.choice(descs))))

    df = pd.DataFrame(rows, columns=["date", "category", "amount", "payment_method", "description"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["amount"] = df["amount"].map(lambda v: f"{v:.0f}")
    return _add_mess(df, rng)


def _add_mess(df: pd.DataFrame, rng) -> pd.DataFrame:
    """Inject typical real-world problems so the cleaning step has something to do."""
    df = df.copy()
    n = len(df)
    idx = rng.choice(n, size=14, replace=False)
    df.loc[idx[:4], "category"] = ""                                         # missing category
    df.loc[idx[4:7], "category"] = df.loc[idx[4:7], "category"].str.upper()  # FOOD & DINING
    df.loc[idx[7:10], "category"] = df.loc[idx[7:10], "category"].str.lower() + " "  # trailing space
    df.loc[idx[10:12], "payment_method"] = df.loc[idx[10:12], "payment_method"].str.lower()
    df.loc[idx[12], "date"] = "not a date"                                   # bad date
    df.loc[idx[13], "amount"] = "abc"                                        # bad amount
    fmt = rng.choice(n, size=3, replace=False)
    df.loc[fmt, "amount"] = df.loc[fmt, "amount"].map(lambda v: f"₹{int(v):,}")   # "₹1,250"
    df = pd.concat([df, df.iloc[[5, 40]]], ignore_index=True)               # two duplicate rows
    refund = pd.DataFrame([{"date": df["date"].iloc[10], "category": "Shopping", "amount": "-500",
                            "payment_method": "UPI", "description": "Refund"}])
    return pd.concat([df, refund], ignore_index=True)


def write_files(seed: int = 42) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    df = generate(seed)
    df.to_csv(EXPENSES_CSV, index=False)
    pd.DataFrame({"category": list(BUDGETS), "monthly_limit": list(BUDGETS.values())}).to_csv(BUDGETS_CSV, index=False)
    print(f"Created {len(df)} synthetic expense rows -> {EXPENSES_CSV}")
    print(f"Created {len(BUDGETS)} budgets -> {BUDGETS_CSV}")
