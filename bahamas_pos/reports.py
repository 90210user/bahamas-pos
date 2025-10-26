"""
Report generation: receipts and stock reports.
"""
import database
import stock
import transactions
import auth


def generate_receipt(transaction: dict) -> str:
    """Generate a text receipt for a transaction."""
    lines = []
    lines.append("=" * 50)
    lines.append("BAHAMAS CYBER CAFE AND PHONE REPAIR".center(50))
    lines.append("=" * 50)
    
    logo_path = auth.get_logo_path()
    if logo_path:
        lines.append(f"Logo: {logo_path}")
        lines.append("-" * 50)
    
    lines.append(f"Transaction ID: {transaction['id']}")
    lines.append(f"Date: {transaction.get('date', 'N/A')}")
    lines.append("-" * 50)
    
    # Items
    lines.append("ITEMS:")
    for item in transaction["items"]:
        code = item["code"]
        qty = item["quantity"]
        store_item = database.db.get_item(code)
        if store_item:
            name = store_item["name"]
            price = store_item["price"]
            subtotal = price * qty
            lines.append(f"{name} x{qty} @ KES {price:.2f} = KES {subtotal:.2f}")
    
    lines.append("-" * 50)
    lines.append(f"TOTAL: KES {transaction['total']:.2f}")
    lines.append(f"Payment Method: {transaction['payment_method']}")
    
    if transaction["customer_name"]:
        lines.append(f"Customer: {transaction['customer_name']}")
    
    if transaction["credit_status"]:
        lines.append("*** CREDIT SALE - NOT PAID ***")
    
    lines.append("=" * 50)
    lines.append("Thank you for your business!")
    lines.append("=" * 50)
    
    return "\n".join(lines)


def generate_stock_report() -> str:
    """Generate a stock report showing received/used/remaining."""
    lines = []
    lines.append("=" * 60)
    lines.append("STOCK REPORT".center(60))
    lines.append("BAHAMAS CYBER CAFE AND PHONE REPAIR".center(60))
    lines.append("=" * 60)
    
    rows = stock.stock_report_rows()
    if not rows:
        lines.append("No product items in stock.")
        return "\n".join(lines)
    
    # Header
    lines.append(f"{'Code':<10} {'Item Name':<25} {'Received':<10} {'Used':<10} {'Remaining':<10}")
    lines.append("-" * 60)
    
    # Data rows
    for row in rows:
        lines.append(f"{row['code']:<10} {row['name']:<25} {row['received']:<10} {row['used']:<10} {row['remaining']:<10}")
    
    lines.append("-" * 60)
    lines.append(f"Total Items: {len(rows)}")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def generate_sales_summary() -> str:
    """Generate a simple sales summary."""
    lines = []
    lines.append("=" * 50)
    lines.append("SALES SUMMARY".center(50))
    lines.append("BAHAMAS CYBER CAFE AND PHONE REPAIR".center(50))
    lines.append("=" * 50)
    
    summary = database.db.get_sales_summary()
    
    lines.append(f"Total Sales (Paid): KES {summary['total_sales']:.2f}")
    lines.append(f"Outstanding Credits: KES {summary['total_credits']:.2f}")
    lines.append(f"Total Expenses: KES {summary['total_expenses']:.2f}")
    lines.append(f"System Balance: KES {summary['system_balance']:.2f}")
    lines.append(f"Total Transactions: {summary['total_transactions']}")
    lines.append("=" * 50)
    
    return "\n".join(lines)
