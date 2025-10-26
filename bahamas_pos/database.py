"""
Database operations for the POS system using SQLite.
Handles all data persistence for users, items, transactions, and reports.
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import os

# Allow overriding DB path via environment variable for LAN/shared usage
DATABASE_FILE = os.environ.get("POS_DB_PATH", "pos_database.db")

class Database:
    def __init__(self):
        self.init_database()
    
    def _connect(self) -> sqlite3.Connection:
        """Create a SQLite connection with a sensible timeout."""
        conn = sqlite3.connect(DATABASE_FILE, timeout=15)
        return conn
    
    def init_database(self):
        """Initialize the database with required tables."""
        conn = self._connect()
        cursor = conn.cursor()
        # Improve concurrency
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=15000")
        except Exception:
            pass
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'cashier',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                price REAL NOT NULL,
                buying_price REAL DEFAULT 0,
                selling_price REAL,
                quantity INTEGER DEFAULT 0,
                unit_type TEXT DEFAULT 'unit',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                items TEXT NOT NULL,
                total REAL NOT NULL,
                payment_method TEXT NOT NULL,
                customer_name TEXT DEFAULT '',
                paid BOOLEAN DEFAULT 1,
                credit_status BOOLEAN DEFAULT 0,
                date TEXT,
                date_cleared TEXT,
                payment_method_cleared TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Stock logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Credits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL,
                transaction_ids TEXT NOT NULL,
                date_created TEXT,
                date_cleared TEXT,
                payment_method_cleared TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # System settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Services table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Backward-compatible migrations (ALTER TABLE safe attempts)
        def try_alter(sql: str):
            try:
                cursor.execute(sql)
            except Exception:
                pass

        try_alter("ALTER TABLE items ADD COLUMN unit_type TEXT DEFAULT 'unit'")
        # New price fields (safe if already exist)
        try_alter("ALTER TABLE items ADD COLUMN buying_price REAL DEFAULT 0")
        try_alter("ALTER TABLE items ADD COLUMN selling_price REAL")
        try_alter("ALTER TABLE transactions ADD COLUMN date TEXT")
        try_alter("ALTER TABLE transactions ADD COLUMN date_cleared TEXT")
        try_alter("ALTER TABLE transactions ADD COLUMN payment_method_cleared TEXT")
        try_alter("ALTER TABLE expenses ADD COLUMN date TEXT")
        try_alter("ALTER TABLE credits ADD COLUMN date_created TEXT")
        try_alter("ALTER TABLE credits ADD COLUMN date_cleared TEXT")
        try_alter("ALTER TABLE credits ADD COLUMN payment_method_cleared TEXT")
        # Services table exists by creation above; no alters needed

        conn.commit()
        conn.close()
        
        # Insert default admin user if not exists
        self.create_default_users()
    
    def create_default_users(self):
        """Create default admin and cashier users."""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", "admin123", "admin")
            )
        
        # Check if cashier user exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'cashier'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("cashier", "cash123", "cashier")
            )
        
        conn.commit()
        conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data if valid."""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT username, role FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {"username": result[0], "role": result[1]}
        return None
    
    def add_item(self, name: str, item_type: str, price: float, quantity: int = 0, unit_type: str = 'unit', buying_price: float = 0.0, selling_price: Optional[float] = None) -> Dict:
        """Add a new item to the database."""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Generate item code
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        code = f"ITEM{count + 1:03d}"
        
        eff_selling = selling_price if selling_price is not None else price
        cursor.execute(
            "INSERT INTO items (code, name, type, price, buying_price, selling_price, quantity, unit_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (code, name, item_type, price, buying_price, eff_selling, quantity, unit_type)
        )
        
        if quantity > 0:
            self.log_stock_action(code, "added", quantity)
        
        conn.commit()
        conn.close()
        
        return {"code": code, "name": name, "type": item_type, "price": price, "buying_price": buying_price, "selling_price": eff_selling, "quantity": quantity, "unit_type": unit_type}

    # Services CRUD
    def add_service(self, service_name: str, price: float) -> Dict:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO services (service_name, price) VALUES (?, ?)", (service_name, price))
        conn.commit()
        service_id = cursor.lastrowid
        conn.close()
        return {"id": service_id, "service_name": service_name, "price": price}

    def list_services(self) -> List[Dict]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, service_name, price FROM services ORDER BY service_name")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "service_name": r[1], "price": r[2]} for r in rows]

    def update_service(self, service_id: int, service_name: str, price: float) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE services SET service_name = ?, price = ? WHERE id = ?", (service_name, price, service_id))
        conn.commit()
        conn.close()

    def delete_service(self, service_id: int) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
        conn.commit()
        conn.close()
    
    def get_item(self, code: str) -> Optional[Dict]:
        """Get item by code."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT code, name, type, price, buying_price, selling_price, quantity, unit_type FROM items WHERE code = ?",
            (code,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "code": result[0],
                "name": result[1],
                "type": result[2],
                "price": result[3],
                "buying_price": result[4] if len(result) > 4 else 0.0,
                "selling_price": result[5] if len(result) > 5 and result[5] is not None else result[3],
                "quantity": result[6] if len(result) > 6 else 0,
                "unit_type": result[7] if len(result) > 7 else 'unit'
            }
        return None
    
    def list_items(self) -> List[Dict]:
        """Get all items."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT code, name, type, price, buying_price, selling_price, quantity, unit_type FROM items ORDER BY code")
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "code": row[0],
                "name": row[1],
                "type": row[2],
                "price": row[3],
                "buying_price": row[4] if len(row) > 4 else 0.0,
                "selling_price": row[5] if len(row) > 5 and row[5] is not None else row[3],
                "quantity": row[6] if len(row) > 6 else 0,
                "unit_type": row[7] if len(row) > 7 else 'unit'
            }
            for row in results
        ]
    
    def update_item_quantity(self, code: str, new_quantity: int):
        """Update item quantity."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE items SET quantity = ? WHERE code = ?",
            (new_quantity, code)
        )
        
        conn.commit()
        conn.close()

    def update_item(self, code: str, name: str, quantity: int, buying_price: float, selling_price: float) -> None:
        """Update core fields of an item."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE items SET name = ?, quantity = ?, buying_price = ?, selling_price = ?, price = ? WHERE code = ?",
            (name, quantity, buying_price, selling_price, selling_price, code)
        )
        conn.commit()
        conn.close()

    def delete_items(self, codes: List[str]) -> int:
        """Delete items by codes, return number deleted."""
        if not codes:
            return 0
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        q = f"DELETE FROM items WHERE code IN ({','.join(['?']*len(codes))})"
        cursor.execute(q, codes)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    
    def log_stock_action(self, code: str, action: str, quantity: int):
        """Log stock action."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO stock_logs (item_code, action, quantity) VALUES (?, ?, ?)",
            (code, action, quantity)
        )
        
        conn.commit()
        conn.close()
    
    def create_transaction(self, items: List[Dict], payment_method: str, customer_name: str = "", date: Optional[str] = None) -> Dict:
        """Create a new transaction."""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Generate transaction ID
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        transaction_id = f"TXN{count + 1:04d}"
        
        # Calculate total using this connection (avoid nested opens)
        total = 0.0
        code_to_item: Dict[str, Dict] = {}
        for item in items:
            # Support service sale structure: {service_id, quantity}
            if "service_id" in item:
                cursor.execute("SELECT price FROM services WHERE id = ?", (int(item["service_id"]),))
                row = cursor.fetchone()
                if not row:
                    raise ValueError("Service not found")
                price = float(row[0])
                qty = int(item.get("quantity", 1))
                total += price * qty
            else:
                cursor.execute("SELECT type, COALESCE(selling_price, price), quantity FROM items WHERE code = ?", (item["code"],))
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Item {item['code']} not found")
                item_type, price, qty_available = row
                code_to_item[item["code"]] = {"type": item_type, "price": price, "quantity": qty_available}
                if item_type == "product" and qty_available < int(item["quantity"]):
                    raise ValueError(f"Insufficient stock for {item['code']}")
                total += float(price) * int(item["quantity"])
        
        # Default date (YYYY-MM-DD)
        date_value = date or datetime.now().strftime('%Y-%m-%d')

        # Store transaction
        cursor.execute(
            "INSERT INTO transactions (transaction_id, items, total, payment_method, customer_name, paid, credit_status, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                transaction_id,
                json.dumps(items),
                total,
                payment_method,
                customer_name,
                payment_method != "Credit",
                payment_method == "Credit",
                date_value
            )
        )
        
        # Update stock for product items only (services do not affect stock)
        for item in items:
            if "service_id" in item:
                continue
            cached = code_to_item.get(item.get("code")) or {}
            if cached.get("type") == "product":
                new_quantity = int(cached["quantity"]) - int(item["quantity"])
                cursor.execute("UPDATE items SET quantity = ? WHERE code = ?", (new_quantity, item["code"]))
                cursor.execute("INSERT INTO stock_logs (item_code, action, quantity) VALUES (?, ?, ?)", (item["code"], "used", int(item["quantity"])) )
        
        # If credit, upsert into credits table
        if payment_method == "Credit":
            cursor.execute("SELECT amount, transaction_ids, date_created FROM credits WHERE customer_name = ?", (customer_name,))
            existing = cursor.fetchone()
            if existing:
                prev_amount, txn_ids_json, prev_date_created = existing
                txn_ids = json.loads(txn_ids_json)
                txn_ids.append(transaction_id)
                cursor.execute(
                    "UPDATE credits SET amount = ?, transaction_ids = ?, date_created = COALESCE(date_created, ?) WHERE customer_name = ?",
                    (prev_amount + total, json.dumps(txn_ids), date_value, customer_name)
                )
            else:
                cursor.execute(
                    "INSERT INTO credits (customer_name, amount, transaction_ids, date_created) VALUES (?, ?, ?, ?)",
                    (customer_name, total, json.dumps([transaction_id]), date_value)
                )

        conn.commit()
        conn.close()
        
        return {
            "id": transaction_id,
            "items": items,
            "total": total,
            "payment_method": payment_method,
            "customer_name": customer_name,
            "paid": payment_method != "Credit",
            "credit_status": payment_method == "Credit",
            "date": date_value
        }
    
    def add_expense(self, description: str, amount: float, date: Optional[str] = None) -> Dict:
        """Add an expense."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        date_value = date or datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute(
            "INSERT INTO expenses (description, amount, date) VALUES (?, ?, ?)",
            (description, amount, date_value)
        )
        
        conn.commit()
        conn.close()
        
        return {"description": description, "amount": amount, "date": date_value}
    
    def list_transactions(self) -> List[Dict]:
        """Get all transactions (sales and expenses unified)."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Sales transactions
        cursor.execute("SELECT transaction_id, items, total, payment_method, customer_name, paid, credit_status, date, date_cleared, payment_method_cleared, created_at FROM transactions")
        sales_rows = cursor.fetchall()

        # Expenses
        cursor.execute("SELECT id, description, amount, date, created_at FROM expenses")
        expense_rows = cursor.fetchall()

        conn.close()

        records: List[Dict] = []

        for row in sales_rows:
            records.append({
                "id": row[0],
                "items": json.loads(row[1]),
                "total": row[2],
                "payment_method": row[3],
                "customer_name": row[4],
                "paid": bool(row[5]),
                "credit_status": bool(row[6]),
                "date": row[7] or row[10],
                "date_cleared": row[8],
                "payment_method_cleared": row[9],
                "type": "sale"
            })

        for row in expense_rows:
            records.append({
                "id": f"EXP{row[0]:04d}",
                "items": [],
                "total": row[2],
                "payment_method": "-",
                "customer_name": "",
                "paid": True,
                "credit_status": False,
                "date": row[3] or row[4],
                "date_cleared": None,
                "payment_method_cleared": None,
                "type": "expense",
                "description": row[1]
            })

        # Sort by date (fallback to created_at implicit ordering if dates equal)
        def safe_date(rec: Dict) -> str:
            return rec.get("date") or ""

        records.sort(key=safe_date, reverse=True)
        return records
    
    def list_credits(self) -> Dict:
        """Get all credits with status and dates."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT customer_name, amount, transaction_ids, date_created, date_cleared, payment_method_cleared FROM credits")
        results = cursor.fetchall()
        conn.close()
        
        credits = {}
        for row in results:
            customer = row[0]
            amount = row[1]
            txn_ids = json.loads(row[2]) if row[2] else []
            date_created = row[3]
            date_cleared = row[4]
            method_cleared = row[5]
            status = "Cleared" if (date_cleared or 0) else "Pending"
            credits[customer] = {
                "amount": amount,
                "transaction_ids": txn_ids,
                "date_created": date_created,
                "date_cleared": date_cleared,
                "payment_method_cleared": method_cleared,
                "status": status,
                # Aliases to match explicit spec names
                "credit_date": date_created,
                "clearance_date": date_cleared,
                "payment_method": method_cleared,
            }
        return credits
    
    def clear_credit(self, customer_name: str, payment_method_cleared: str, date_cleared: Optional[str] = None) -> bool:
        """Clear customer credit and mark related transactions paid with clearance details."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT amount, transaction_ids FROM credits WHERE customer_name = ?", (customer_name,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False
        
        amount, transaction_ids = result
        transaction_ids = json.loads(transaction_ids)
        
        # Mark transactions as paid and record clearance details
        date_value = date_cleared or datetime.now().strftime('%Y-%m-%d')
        for txn_id in transaction_ids:
            cursor.execute(
                "UPDATE transactions SET paid = 1, credit_status = 0, payment_method_cleared = ?, date_cleared = ? WHERE transaction_id = ?",
                (payment_method_cleared, date_value, txn_id)
            )
        
        # Update credit record with clearance info and set amount to zero
        cursor.execute(
            "UPDATE credits SET amount = 0, date_cleared = ?, payment_method_cleared = ? WHERE customer_name = ?",
            (date_value, payment_method_cleared, customer_name)
        )
        
        conn.commit()
        conn.close()
        return True
    
    def get_system_balance(self) -> float:
        """Calculate system balance."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Sum of paid transactions
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM transactions WHERE paid = 1")
        total_sales = cursor.fetchone()[0]
        
        # Sum of expenses
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
        total_expenses = cursor.fetchone()[0]
        
        conn.close()
        return total_sales - total_expenses
    
    def get_stock_report_data(self) -> List[Dict]:
        """Get stock report data."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT i.code, i.name, 
                   COALESCE(SUM(CASE WHEN sl.action = 'added' THEN sl.quantity ELSE 0 END), 0) as received,
                   COALESCE(SUM(CASE WHEN sl.action = 'used' THEN sl.quantity ELSE 0 END), 0) as used,
                   i.quantity as remaining
            FROM items i
            LEFT JOIN stock_logs sl ON i.code = sl.item_code
            WHERE i.type = 'product'
            GROUP BY i.code, i.name, i.quantity
            ORDER BY i.code
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "code": row[0],
                "name": row[1],
                "received": row[2],
                "used": row[3],
                "remaining": row[4]
            }
            for row in results
        ]
    
    def get_sales_summary(self) -> Dict:
        """Get sales summary data."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Total sales (paid)
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM transactions WHERE paid = 1")
        total_sales = cursor.fetchone()[0]
        
        # Outstanding credits
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM credits")
        total_credits = cursor.fetchone()[0]
        
        # Total expenses
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
        total_expenses = cursor.fetchone()[0]
        
        # Total transactions
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_transactions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_sales": total_sales,
            "total_credits": total_credits,
            "total_expenses": total_expenses,
            "system_balance": total_sales - total_expenses,
            "total_transactions": total_transactions
        }
    
    def set_setting(self, key: str, value: str):
        """Set a system setting."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        
        conn.commit()
        conn.close()
    
    def get_setting(self, key: str, default: str = "") -> str:
        """Get a system setting."""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else default

    def delete_transactions(self, txn_ids: List[str]) -> int:
        """Delete transactions by transaction_id values."""
        if not txn_ids:
            return 0
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        q = f"DELETE FROM transactions WHERE transaction_id IN ({','.join(['?']*len(txn_ids))})"
        cursor.execute(q, txn_ids)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def delete_credits(self, customers: List[str]) -> int:
        """Delete credits by customer names."""
        if not customers:
            return 0
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        q = f"DELETE FROM credits WHERE customer_name IN ({','.join(['?']*len(customers))})"
        cursor.execute(q, customers)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def delete_expenses(self, expense_ids: List[int]) -> int:
        """Delete expenses by numeric ids."""
        if not expense_ids:
            return 0
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        q = f"DELETE FROM expenses WHERE id IN ({','.join(['?']*len(expense_ids))})"
        cursor.execute(q, expense_ids)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

# Global database instance
db = Database()
