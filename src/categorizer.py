"""Keyword rules that guess a category from a description (used when category is missing)."""
import re

# Order matters: the first matching category wins ("amazon prime" must be checked before "amazon").
RULES = {
    "Groceries": r"\b(big bazaar|reliance fresh|d-?mart|grocery|supermart|vegetables?)\b",
    "Food & Dining": r"\b(swiggy|zomato|restaurant|cafe|coffee|pizza|biryani|lunch|dinner)\b",
    "Transport": r"\b(uber|ola|rapido|metro|fuel|petrol|diesel|bus|auto)\b",
    "Bills & Utilities": r"\b(electric(ity)?|water bill|wifi|broadband|recharge|dth|gas)\b",
    "Entertainment": r"\b(netflix|amazon prime|prime video|spotify|cinema|bookmyshow|movie)\b",
    "Shopping": r"\b(amazon|flipkart|myntra|ajio)\b",
    "Health": r"\b(pharmacy|apollo|doctor|medicine|gym|clinic)\b",
    "Education": r"\b(udemy|coursera|course|books?|tuition|exam fee)\b",
    "Rent": r"\b(rent)\b",
}


def classify(description: str) -> str:
    text = (description or "").lower()
    for category, pattern in RULES.items():
        if re.search(pattern, text):
            return category
    return "Uncategorized"
