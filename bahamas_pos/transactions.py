"""
Transaction management: sales, expenses, and credit handling.
"""
from typing import Optional
import database


def create_transaction(items: list[dict], payment_method: str, customer_name: str = "", date: Optional[str] = None) -> dict:
    """Create a new transaction with items and payment details."""
    if not items:
        raise ValueError("Transaction must have at least one item")
    if payment_method not in ("Mpesa", "Cash", "Credit"):
        raise ValueError("Invalid payment method")
    
    # Validate stock items only (services don't touch stock)
    for item in items:
        if "service_id" in item:
            continue
        code = item["code"]
        qty = item["quantity"]
        store_item = database.db.get_item(code)
        if not store_item:
            raise ValueError(f"Item {code} not found")
        if store_item["type"] == "product" and store_item["quantity"] < qty:
            raise ValueError(f"Insufficient stock for {code}")
    
    return database.db.create_transaction(items, payment_method, customer_name, date)


def add_expense(description: str, amount: float, date: Optional[str] = None) -> dict:
    """Add an expense and deduct from system balance."""
    if amount <= 0:
        raise ValueError("Expense amount must be positive")
    
    return database.db.add_expense(description, amount, date)


def clear_credit(customer_name: str, payment_method_cleared: str, date_cleared: Optional[str] = None) -> bool:
    """Clear customer credit by marking transactions as paid with details."""
    if payment_method_cleared not in ("Mpesa", "Cash"):
        raise ValueError("Invalid clearance payment method")
    return database.db.clear_credit(customer_name, payment_method_cleared, date_cleared)


def get_transaction(txn_id: str) -> Optional[dict]:
    """Get transaction by ID."""
    transactions = database.db.list_transactions()
    for txn in transactions:
        if txn["id"] == txn_id:
            return txn
    return None


def list_transactions() -> list[dict]:
    """Get all transactions."""
    return database.db.list_transactions()


def list_credits() -> dict:
    """Get all outstanding credits."""
    return database.db.list_credits()


def get_system_balance() -> float:
    """Get current system balance."""
    return database.db.get_system_balance()
