"""
Demo script to test the POS system functionality.
This script demonstrates the core features without user interaction.
"""
import auth
import data_store as store
import reports
import stock
import transactions


def demo():
    """Run a demonstration of the POS system."""
    print("=" * 60)
    print("BAHAMAS CYBER CAFE AND PHONE REPAIR - DEMO")
    print("=" * 60)
    
    # Test authentication
    print("\n1. Testing Authentication...")
    user = auth.login("admin", "admin123")
    print(f"Admin login: {'SUCCESS' if user else 'FAILED'}")
    
    # Test item creation
    print("\n2. Adding Items...")
    try:
        # Add some sample items
        item1 = stock.add_item("Envelopes", "product", 5.0, 100)
        print(f"Added: {item1['code']} - {item1['name']}")
        
        item2 = stock.add_item("Phone Screen Repair", "service", 1500.0)
        print(f"Added: {item2['code']} - {item2['name']}")
        
        item3 = stock.add_item("Internet Token 1GB", "internet_token", 50.0)
        print(f"Added: {item3['code']} - {item3['name']}")
    except Exception as e:
        print(f"Error adding items: {e}")
    
    # Test sales transaction
    print("\n3. Processing Sale...")
    try:
        sale_items = [
            {"code": "ITEM001", "quantity": 2},  # 2 envelopes
            {"code": "ITEM003", "quantity": 1}   # 1 internet token
        ]
        txn = transactions.create_transaction(sale_items, "Cash")
        print(f"Sale completed: {txn['id']} - Total: KES {txn['total']:.2f}")
        
        # Generate receipt
        receipt = reports.generate_receipt(txn)
        print("\nReceipt:")
        print(receipt)
    except Exception as e:
        print(f"Error processing sale: {e}")
    
    # Test credit sale
    print("\n4. Processing Credit Sale...")
    try:
        credit_items = [{"code": "ITEM002", "quantity": 1}]  # Phone repair
        credit_txn = transactions.create_transaction(credit_items, "Credit", "John Doe")
        print(f"Credit sale: {credit_txn['id']} - Customer: John Doe")
    except Exception as e:
        print(f"Error processing credit sale: {e}")
    
    # Test expense
    print("\n5. Adding Expense...")
    try:
        expense = transactions.add_expense("Lunch", 60.0)
        print(f"Expense added: {expense['description']} - KES {expense['amount']:.2f}")
    except Exception as e:
        print(f"Error adding expense: {e}")
    
    # Test reports
    print("\n6. Generating Reports...")
    print("\nStock Report:")
    print(reports.generate_stock_report())
    
    print("\nSales Summary:")
    print(reports.generate_sales_summary())
    
    # Test admin functions
    print("\n7. Testing Admin Functions...")
    if auth.is_admin(user):
        print("Admin access confirmed")
        auth.set_logo_path(user, "/path/to/logo.png")
        print("Logo path set")
        
        # Clear credit
        if transactions.clear_credit("John Doe"):
            print("Credit cleared for John Doe")
    else:
        print("Admin access denied")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
