"""Paths and default settings."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
REPORTS_DIR = BASE_DIR / "reports"

EXPENSES_CSV = DATA_DIR / "expenses.csv"
BUDGETS_CSV = DATA_DIR / "budgets.csv"

DEFAULT_MONTHLY_INCOME = 35000.0   # used for the savings calculation (change with --income)
NEAR_LIMIT_PCT = 80                # budget status becomes "NEAR" at this % of the limit
CURRENCY = "₹"
