"""
Shared in-memory data store for the POS skeleton.
This module centralizes placeholder storage to make future persistence easier.
"""

# Business branding
BUSINESS_NAME: str = "BAHAMAS CYBER CAFE AND PHONE REPAIR"
LOGO_PATH: str | None = None  # optional path to logo/photo

# Simple balance placeholder (e.g., cash drawer). Updated by sales/expenses.
system_balance: float = 0.0

# Items: code -> {name, type, price, quantity}
items: dict[str, dict] = {}

# Transactions: list of dicts
transactions: list[dict] = []

# Expenses: list of dicts {description, amount}
expenses: list[dict] = []

# Stock logs: list of dicts {code, action, qty}
stock_logs: list[dict] = []

# Credits: customer -> {amount, transaction_ids}
credits: dict[str, dict] = {}

# Simple counters for codes/ids
_item_counter: int = 0
_txn_counter: int = 0


def next_item_code() -> str:
    """Generate the next item code like ITEM001."""
    global _item_counter
    _item_counter += 1
    return f"ITEM{_item_counter:03d}"


def next_transaction_id() -> str:
    """Generate the next transaction id like TXN0001."""
    global _txn_counter
    _txn_counter += 1
    return f"TXN{_txn_counter:04d}"
