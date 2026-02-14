"""
Mock transaction data generator for AI Sage Financial Coach MVP demo.

Produces realistic UK banking transaction data. In production this is
replaced by the real Customer 360 / transaction API.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

Category = Literal[
    "groceries",
    "eating_out",
    "transport",
    "utilities",
    "subscriptions",
    "shopping",
    "entertainment",
    "health",
    "salary",
    "savings_transfer",
    "cash_withdrawal",
    "other",
]


@dataclass
class Transaction:
    transaction_id: str
    date: date
    amount: Decimal          # negative = debit, positive = credit
    merchant: str
    category: Category
    channel: str             # "card", "direct_debit", "bacs", "atm"
    balance_after: Decimal


@dataclass
class CustomerProfile:
    customer_id: str
    name: str
    monthly_salary: Decimal
    salary_day: int          # day-of-month salary lands
    transactions: list[Transaction] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Merchant registry
# ---------------------------------------------------------------------------

MERCHANTS: dict[Category, list[str]] = {
    "groceries":        ["Tesco", "Sainsbury's", "Aldi", "Asda", "Waitrose", "M&S Food"],
    "eating_out":       ["Pret a Manger", "Greggs", "McDonald's", "Nando's", "Deliveroo", "Uber Eats", "Costa Coffee"],
    "transport":        ["TfL", "National Rail", "Shell", "BP Fuel", "Uber", "Trainline"],
    "utilities":        ["British Gas", "EDF Energy", "Thames Water", "BT Broadband", "Sky TV"],
    "subscriptions":    ["Netflix", "Spotify", "Amazon Prime", "Apple iCloud", "Disney+", "Gym Membership"],
    "shopping":         ["Amazon", "ASOS", "Next", "John Lewis", "Marks & Spencer", "eBay"],
    "entertainment":    ["Odeon Cinema", "Vue Cinema", "Ticketmaster", "Steam", "PlayStation Store"],
    "health":           ["Boots", "Day Lewis Pharmacy", "Bupa", "Nuffield Health"],
    "cash_withdrawal":  ["ATM Withdrawal"],
    "other":            ["Misc Charge", "Bank Fee"],
}

# Typical monthly spend ranges (£) — used to produce realistic amounts
SPEND_RANGES: dict[Category, tuple[float, float]] = {
    "groceries":        (60.0,  200.0),
    "eating_out":       (8.0,   45.0),
    "transport":        (5.0,   150.0),
    "utilities":        (30.0,  120.0),
    "subscriptions":    (4.99,  14.99),
    "shopping":         (15.0,  180.0),
    "entertainment":    (10.0,  60.0),
    "health":           (5.0,   40.0),
    "cash_withdrawal":  (20.0,  100.0),
    "other":            (5.0,   25.0),
}

SPEND_FREQUENCIES: dict[Category, int] = {
    "groceries":        6,    # ~1-2x per week
    "eating_out":       5,
    "transport":        6,
    "utilities":        3,    # monthly direct debits
    "subscriptions":    4,
    "shopping":         3,
    "entertainment":    2,
    "health":           1,
    "cash_withdrawal":  1,
    "other":            1,
}


def _random_date_in_month(year: int, month: int) -> date:
    if month == 12:
        last_day = 31
    else:
        last_day = (date(year, month + 1, 1) - timedelta(days=1)).day
    return date(year, month, random.randint(1, last_day))


def generate_customer(
    customer_id: str = "CUST_001",
    name: str = "Alex Johnson",
    monthly_salary: float = 3200.0,
    months: int = 6,
    seed: int = 42,
) -> CustomerProfile:
    """
    Generate a deterministic mock customer with 6 months of transactions.
    Deterministic via seed so demos are reproducible.
    """
    random.seed(seed)

    profile = CustomerProfile(
        customer_id=customer_id,
        name=name,
        monthly_salary=Decimal(str(monthly_salary)),
        salary_day=25,
    )

    today = date.today()
    # Start from `months` ago
    start_month = today.month - months
    start_year = today.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1

    balance = Decimal("2500.00")
    txn_counter = 0

    for m_offset in range(months):
        month = (start_month + m_offset - 1) % 12 + 1
        year = start_year + (start_month + m_offset - 1) // 12

        # Salary credit
        salary_date = date(year, month, min(25, 28))
        balance += profile.monthly_salary
        profile.transactions.append(Transaction(
            transaction_id=f"TXN_{txn_counter:05d}",
            date=salary_date,
            amount=profile.monthly_salary,
            merchant="LLOYDS PAYROLL - Employer Ltd",
            category="salary",
            channel="bacs",
            balance_after=balance,
        ))
        txn_counter += 1

        # Spending transactions
        for category, freq in SPEND_FREQUENCIES.items():
            if category == "salary":
                continue
            lo, hi = SPEND_RANGES[category]
            for _ in range(freq):
                amount = Decimal(str(round(random.uniform(lo, hi), 2)))
                txn_date = _random_date_in_month(year, month)
                balance -= amount
                merchant = random.choice(MERCHANTS.get(category, ["Unknown"]))
                profile.transactions.append(Transaction(
                    transaction_id=f"TXN_{txn_counter:05d}",
                    date=txn_date,
                    amount=-amount,
                    merchant=merchant,
                    category=category,
                    channel="card",
                    balance_after=balance,
                ))
                txn_counter += 1

    # Sort chronologically
    profile.transactions.sort(key=lambda t: t.date)
    return profile


# ---------------------------------------------------------------------------
# Convenience: pre-built demo profiles
# ---------------------------------------------------------------------------

def get_demo_customer() -> CustomerProfile:
    """Returns a single reproducible demo customer for presentations."""
    return generate_customer(
        customer_id="CUST_DEMO_001",
        name="Alex Johnson",
        monthly_salary=3200.0,
        months=6,
        seed=42,
    )


def get_demo_customer_with_life_events() -> CustomerProfile:
    """
    Demo customer with realistic life event signals injected into recent
    transactions, designed to trigger the life event detector.

    Signals injected (last 2 months):
      - NEW BABY:      2x nursery payments + baby equipment purchases
      - INCOME CHANGE: salary increased from £3,200 → £3,800 (promotion)
      - PROPERTY:      solicitor + surveyor fees (buying a home)

    Use this profile when demoing Epic 2.1 life event detection.
    """
    # Build base profile with standard transactions
    profile = generate_customer(
        customer_id="CUST_DEMO_002",
        name="Alex Johnson",
        monthly_salary=3200.0,
        months=6,
        seed=42,
    )

    today = date.today()
    balance = profile.transactions[-1].balance_after
    txn_counter = 9000   # offset to avoid ID clashes

    def _add(txn_date: date, amount: Decimal, merchant: str,
             category: Category, channel: str = "card") -> None:
        nonlocal balance, txn_counter
        balance -= amount
        profile.transactions.append(Transaction(
            transaction_id=f"TXN_{txn_counter:05d}",
            date=txn_date,
            amount=-amount,
            merchant=merchant,
            category=category,
            channel=channel,
            balance_after=balance,
        ))
        txn_counter += 1

    def _add_credit(txn_date: date, amount: Decimal, merchant: str) -> None:
        nonlocal balance, txn_counter
        balance += amount
        profile.transactions.append(Transaction(
            transaction_id=f"TXN_{txn_counter:05d}",
            date=txn_date,
            amount=amount,
            merchant=merchant,
            category="salary",
            channel="bacs",
            balance_after=balance,
        ))
        txn_counter += 1

    # ---- Signal 1: NEW BABY (last 6 weeks) ----
    # Two nursery direct debits in the last 5 weeks
    _add(today - timedelta(days=35), Decimal("850.00"),
         "Busy Bees Nursery", "other", "direct_debit")
    _add(today - timedelta(days=5),  Decimal("850.00"),
         "Busy Bees Nursery", "other", "direct_debit")
    # Baby equipment purchases
    _add(today - timedelta(days=42), Decimal("649.00"),
         "Mamas and Papas", "shopping")
    _add(today - timedelta(days=40), Decimal("124.99"),
         "Boots", "health")

    # ---- Signal 2: INCOME CHANGE (last 2 months — promotion) ----
    # Remove the last two £3,200 salary transactions and replace with £3,800
    new_salary = Decimal("3800.00")
    old_salary = Decimal("3200.00")
    # Remove the 2 most recent base salary transactions
    salary_txns = sorted(
        [t for t in profile.transactions if t.category == "salary"],
        key=lambda t: t.date,
        reverse=True,
    )
    for t in salary_txns[:2]:
        profile.transactions.remove(t)
    # Add replacement higher-salary transactions on the same pay dates
    _add_credit(today - timedelta(days=55), new_salary,
                "LLOYDS PAYROLL - Employer Ltd")
    _add_credit(today - timedelta(days=25), new_salary,
                "LLOYDS PAYROLL - Employer Ltd")

    # ---- Signal 3: PROPERTY PURCHASE (last 8 weeks) ----
    _add(today - timedelta(days=50), Decimal("1200.00"),
         "Morrison & Co Solicitors", "other", "bank_transfer")
    _add(today - timedelta(days=48), Decimal("450.00"),
         "RICS Surveyor Services", "other", "bank_transfer")
    _add(today - timedelta(days=45), Decimal("299.00"),
         "Land Registry Fee", "other", "bank_transfer")

    # Sort chronologically
    profile.transactions.sort(key=lambda t: t.date)
    return profile
