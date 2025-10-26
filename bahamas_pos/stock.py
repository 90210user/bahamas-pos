"""
Stock management: item entry, inventory tracking, and logs.
"""
from typing import Optional
import database


def add_item(name: str, item_type: str, price: float, quantity: int = 0, buying_price: float = 0.0, selling_price: Optional[float] = None) -> dict:
    """Create an item with an auto code and store it."""
    if not name:
        raise ValueError("Item name is required")
    if item_type not in ("product", "service"):
        raise ValueError("Invalid item type")
    if price < 0:
        raise ValueError("Price cannot be negative")
    if item_type != "product":
        quantity = 0

    return database.db.add_item(name, item_type, price, quantity, 'unit', buying_price, selling_price)


def get_item(code: str) -> Optional[dict]:
    """Get item by code."""
    return database.db.get_item(code)


def list_items() -> list[dict]:
    """Get all items."""
    return database.db.list_items()


def adjust_stock(code: str, delta_quantity: int) -> None:
    """Adjust stock quantity."""
    item = get_item(code)
    if not item:
        raise ValueError("Item code not found")
    if item["type"] != "product":
        return  # no stock tracking for non-products
    
    new_qty = item["quantity"] + int(delta_quantity)
    if new_qty < 0:
        raise ValueError("Insufficient stock")
    
    database.db.update_item_quantity(code, new_qty)
    database.db.log_stock_action(code, "added" if delta_quantity > 0 else "used", abs(int(delta_quantity)))


def update_item(code: str, name: str, quantity: int, buying_price: float, selling_price: float) -> None:
    """Update an existing stock item."""
    if quantity < 0:
        raise ValueError("Quantity cannot be negative")
    if buying_price < 0 or selling_price < 0:
        raise ValueError("Prices cannot be negative")
    database.db.update_item(code, name, quantity, buying_price, selling_price)


def delete_items(codes: list[str]) -> int:
    """Delete multiple items by code."""
    return database.db.delete_items(codes)


def log_stock(code: str, action: str, qty: int) -> None:
    """Log stock action."""
    database.db.log_stock_action(code, action, qty)


def stock_report_rows() -> list[dict]:
    """Get stock report data."""
    return database.db.get_stock_report_data()
