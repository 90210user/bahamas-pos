"""
Dynamic BAHAMAS CYBER CAFE AND PHONE REPAIR POS System
Super simple and bulletproof version that definitely works!
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import json
from datetime import datetime
import os
try:
    # Use the full-featured windows for real functionality
    from windows import (
        SalesWindow,
        ExpenseWindow,
        ItemsWindow,
        TransactionsWindow,
        CreditsWindow,
        AddStockWindow,
        StockReportWindow,
        SalesReportWindow,
    )
except Exception:
    # Fallback if windows module is unavailable at runtime
    SalesWindow = ExpenseWindow = ItemsWindow = TransactionsWindow = CreditsWindow = AddStockWindow = StockReportWindow = SalesReportWindow = None

class DynamicPOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BAHAMAS CYBER CAFE AND PHONE REPAIR POS")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Current user
        self.current_user = None
        
        # Initialize database
        self.init_database()
        
        # Start with login
        self.show_login()
        
    def init_database(self):
        """Initialize SQLite database."""
        self.conn = sqlite3.connect("pos_database.db")
        cursor = self.conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE,
                name TEXT,
                type TEXT,
                price REAL,
                quantity INTEGER,
                category TEXT,
                service_category TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                transaction_id TEXT UNIQUE,
                items TEXT,
                total REAL,
                payment_method TEXT,
                customer_name TEXT,
                paid BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                description TEXT,
                amount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Migrate: ensure new columns exist (SQLite is forgiving)
        try:
            cursor.execute("ALTER TABLE items ADD COLUMN category TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE items ADD COLUMN service_category TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Insert default users if not exist
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                         ("admin", "admin123", "admin"))
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                         ("cashier", "cash123", "cashier"))
        
        self.conn.commit()
        
    def show_login(self):
        """Show login screen."""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        # Title with dynamic styling
        title_frame = tk.Frame(main_frame, bg='#2c3e50', relief=tk.RAISED, bd=2)
        title_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_label = tk.Label(title_frame, 
                              text="BAHAMAS CYBER CAFE\nAND PHONE REPAIR", 
                              font=("Arial", 20, "bold"), 
                              fg='white', bg='#2c3e50',
                              justify=tk.CENTER)
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(title_frame, 
                                 text="Point of Sale System", 
                                 font=("Arial", 14), 
                                 fg='#ecf0f1', bg='#2c3e50')
        subtitle_label.pack(pady=(0, 20))
        
        # Login form with dynamic styling
        form_frame = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=2)
        form_frame.pack(pady=20, padx=50, fill=tk.X)
        
        # Form title
        form_title = tk.Label(form_frame, text="LOGIN", 
                             font=("Arial", 16, "bold"), 
                             fg='#2c3e50', bg='white')
        form_title.pack(pady=20)
        
        # Username
        tk.Label(form_frame, text="Username:", 
                font=("Arial", 12, "bold"), 
                fg='#34495e', bg='white').pack(anchor=tk.W, padx=30, pady=(10, 5))
        
        self.username_entry = tk.Entry(form_frame, width=30, 
                                      font=("Arial", 12), 
                                      relief=tk.SUNKEN, bd=2)
        self.username_entry.pack(padx=30, pady=(0, 15))
        
        # Password
        tk.Label(form_frame, text="Password:", 
                font=("Arial", 12, "bold"), 
                fg='#34495e', bg='white').pack(anchor=tk.W, padx=30, pady=(10, 5))
        
        self.password_entry = tk.Entry(form_frame, width=30, 
                                      font=("Arial", 12), 
                                      show="*", relief=tk.SUNKEN, bd=2)
        self.password_entry.pack(padx=30, pady=(0, 20))
        
        # Login button with dynamic styling
        login_btn = tk.Button(form_frame, text="LOGIN", 
                             font=("Arial", 14, "bold"),
                             bg='#27ae60', fg='white',
                             relief=tk.RAISED, bd=3,
                             command=self.login,
                             width=15, height=2)
        login_btn.pack(pady=20)
        
        # Status label
        self.status_label = tk.Label(main_frame, text="Enter your credentials to login", 
                                    font=("Arial", 11), 
                                    fg='#7f8c8d', bg='#f0f0f0')
        self.status_label.pack(pady=20)
        
        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.login())
        
        # Focus on username
        self.username_entry.focus()
        
    def login(self):
        """Handle login with dynamic feedback."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # Dynamic status updates
        self.status_label.config(text="Logging in...", fg='#f39c12')
        self.root.update()
        
        if not username or not password:
            self.status_label.config(text="Please enter both username and password", fg='#e74c3c')
            return
            
        # Check credentials
        cursor = self.conn.cursor()
        cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", 
                      (username, password))
        user = cursor.fetchone()
        
        if user:
            self.current_user = {"username": user[0], "role": user[1]}
            self.status_label.config(text="Login successful!", fg='#27ae60')
            self.root.update()
            # Wait a moment then show main UI
            self.root.after(1500, self.show_main_dashboard)
        else:
            self.status_label.config(text="Invalid credentials!", fg='#e74c3c')
            
    def show_main_dashboard(self):
        """Show main dashboard with dynamic styling."""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Header with dynamic styling
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(header_frame, 
                              text="BAHAMAS CYBER CAFE AND PHONE REPAIR", 
                              font=("Arial", 18, "bold"), 
                              fg='white', bg='#2c3e50')
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # User info
        user_label = tk.Label(header_frame, 
                             text=f"Welcome, {self.current_user['username']} ({self.current_user['role']})", 
                             font=("Arial", 12), 
                             fg='#ecf0f1', bg='#2c3e50')
        user_label.pack(side=tk.RIGHT, padx=20, pady=20)
        
        # Navigation panel
        nav_frame = tk.Frame(self.root, bg='#34495e', height=60)
        nav_frame.pack(fill=tk.X)
        nav_frame.pack_propagate(False)
        
        # Navigation buttons with dynamic styling
        buttons = [
            ("🛒 New Sale", self.new_sale, '#27ae60'),
            ("💰 Add Expense", self.add_expense, '#f39c12'),
            ("📦 View Items", self.view_items, '#3498db'),
            ("📋 Transactions", self.view_transactions, '#9b59b6'),
            ("💳 Credits", self.view_credits, '#e67e22'),
        ]
        
        if self.current_user['role'] == 'admin':
            buttons.extend([
                ("➕ Add Stock", self.add_stock, '#e74c3c'),
                ("📊 Stock Report", self.stock_report, '#1abc9c'),
                ("📈 Sales Report", self.sales_report, '#8e44ad'),
            ])
        
        buttons.append(("🚪 Logout", self.logout, '#95a5a6'))
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(nav_frame, text=text, 
                           font=("Arial", 10, "bold"),
                           bg=color, fg='white',
                           relief=tk.RAISED, bd=2,
                           command=command,
                           width=12, height=2)
            btn.pack(side=tk.LEFT, padx=5, pady=10)
            
        # Main content area
        self.content_frame = tk.Frame(self.root, bg='#ecf0f1')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg='#bdc3c7', height=30)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        
        # Balance display
        balance = self.get_system_balance()
        balance_label = tk.Label(status_frame, 
                                text=f"System Balance: KES {balance:.2f}", 
                                font=("Arial", 10, "bold"), 
                                fg='#27ae60', bg='#bdc3c7')
        balance_label.pack(side=tk.RIGHT, padx=20, pady=5)
        
        # Welcome message
        welcome_frame = tk.Frame(self.content_frame, bg='white', relief=tk.RAISED, bd=2)
        welcome_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        welcome_label = tk.Label(welcome_frame, 
                                text=f"🎉 Welcome to BAHAMAS CYBER CAFE AND PHONE REPAIR POS System!\n\n"
                                     f"👤 Logged in as: {self.current_user['username']} ({self.current_user['role']})\n\n"
                                     f"🚀 Use the colorful buttons above to navigate the system.\n"
                                     f"💡 Each button has a specific function for managing your business.",
                                font=("Arial", 14), 
                                fg='#2c3e50', bg='white',
                                justify=tk.CENTER)
        welcome_label.pack(expand=True)

    # ---------- Utility helpers ----------
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def generate_item_code(self) -> str:
        cur = self.conn.cursor()
        cur.execute("SELECT code FROM items ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if not row or not row[0] or not row[0].startswith("ITEM"):
            return "ITEM001"
        try:
            num = int(row[0][4:]) + 1
        except Exception:
            num = 1
        return f"ITEM{num:03d}"

    def list_items(self):
        cur = self.conn.cursor()
        cur.execute("SELECT code, name, type, price, quantity, IFNULL(category,''), IFNULL(service_category,'') FROM items ORDER BY code")
        return cur.fetchall()
        
    def get_system_balance(self):
        """Get current system balance."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM transactions WHERE paid = 1")
        sales = cursor.fetchone()[0]
        return sales
        
    def new_sale(self):
        """Open the Sales window."""
        if SalesWindow:
            SalesWindow(self)
        else:
            self.show_dynamic_popup("🛒 New Sale", "Sales window not available.")
        
    def add_expense(self):
        """Open the Expense window."""
        if ExpenseWindow:
            ExpenseWindow(self)
        else:
            self.show_dynamic_popup("💰 Add Expense", "Expense window not available.")
        
    def view_items(self):
        """Render items table in the main content area."""
        self.clear_content()

        header = tk.Frame(self.content_frame, bg='white', relief=tk.RAISED, bd=2)
        header.pack(fill=tk.X, padx=10, pady=(10, 0))

        tk.Label(header, text="📦 Inventory Items", font=("Arial", 14, "bold"),
                 fg='#2c3e50', bg='white').pack(side=tk.LEFT, padx=10, pady=10)

        btn_frame = tk.Frame(header, bg='white')
        btn_frame.pack(side=tk.RIGHT, padx=10)

        tk.Button(btn_frame, text="Refresh", bg='#3498db', fg='white',
                  font=("Arial", 10, "bold"), width=10,
                  command=self.view_items).pack(side=tk.LEFT, padx=5)

        if self.current_user and self.current_user.get('role') == 'admin':
            tk.Button(btn_frame, text="Add Item", bg='#27ae60', fg='white',
                      font=("Arial", 10, "bold"), width=10,
                      command=self.add_stock).pack(side=tk.LEFT, padx=5)

        table_frame = tk.Frame(self.content_frame, bg='white', relief=tk.RAISED, bd=2)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        cols = ("Code", "Name", "Type", "Category", "ServiceCat", "Price", "Quantity")
        self.items_tree = ttk.Treeview(table_frame, columns=cols, show='headings', selectmode='browse')
        for col in cols:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=120 if col!="Name" else 180, anchor=tk.CENTER)
        vs = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=vs.set)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vs.pack(side=tk.RIGHT, fill=tk.Y)

        # Right edit panel
        edit_panel = tk.Frame(self.content_frame, bg='white', relief=tk.RAISED, bd=2)
        edit_panel.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(edit_panel, text="Selected Code:", font=("Arial", 10, "bold"), bg='white').grid(row=0, column=0, padx=8, pady=6, sticky='e')
        self.edit_code = tk.StringVar()
        tk.Entry(edit_panel, textvariable=self.edit_code, state='readonly', width=16).grid(row=0, column=1, padx=8, pady=6)

        tk.Label(edit_panel, text="Price (KES):", font=("Arial", 10, "bold"), bg='white').grid(row=0, column=2, padx=8, pady=6, sticky='e')
        self.edit_price = tk.StringVar()
        tk.Entry(edit_panel, textvariable=self.edit_price, width=16).grid(row=0, column=3, padx=8, pady=6)

        tk.Label(edit_panel, text="Quantity:", font=("Arial", 10, "bold"), bg='white').grid(row=0, column=4, padx=8, pady=6, sticky='e')
        self.edit_qty = tk.StringVar()
        tk.Entry(edit_panel, textvariable=self.edit_qty, width=16).grid(row=0, column=5, padx=8, pady=6)

        def on_select(event=None):
            sel = self.items_tree.selection()
            if not sel:
                return
            vals = self.items_tree.item(sel[0], 'values')
            code, name, t, cat, scat, price, qty = vals
            self.edit_code.set(code)
            try:
                self.edit_price.set(str(float(str(price).replace('KES','').strip())))
            except Exception:
                self.edit_price.set(str(price))
            self.edit_qty.set(str(qty))

        self.items_tree.bind('<<TreeviewSelect>>', on_select)

        def do_save():
            code = self.edit_code.get().strip()
            if not code:
                messagebox.showerror("Error", "Select an item first")
                return
            try:
                price = float(self.edit_price.get())
                qty = int(self.edit_qty.get())
            except Exception:
                messagebox.showerror("Error", "Invalid price or quantity")
                return
            cur = self.conn.cursor()
            cur.execute("UPDATE items SET price=?, quantity=? WHERE code=?", (price, qty, code))
            self.conn.commit()
            self.view_items()
            messagebox.showinfo("Saved", f"Updated {code}")

        def do_delete():
            code = self.edit_code.get().strip()
            if not code:
                messagebox.showerror("Error", "Select an item first")
                return
            if not messagebox.askyesno("Confirm", f"Delete item {code}?"):
                return
            cur = self.conn.cursor()
            cur.execute("DELETE FROM items WHERE code=?", (code,))
            self.conn.commit()
            self.view_items()
            messagebox.showinfo("Deleted", f"Removed {code}")

        tk.Button(edit_panel, text="Save", command=do_save, bg='#27ae60', fg='white',
                  font=("Arial", 10, "bold"), width=10).grid(row=0, column=6, padx=8)
        tk.Button(edit_panel, text="Delete", command=do_delete, bg='#e74c3c', fg='white',
                  font=("Arial", 10, "bold"), width=10).grid(row=0, column=7, padx=8)

        # Load data
        for code, name, t, price, qty, cat, scat in self.list_items():
            self.items_tree.insert('', tk.END, values=(code, name, t, cat, scat, f"KES {price:.2f}", qty))
        
    def view_transactions(self):
        """Open the Transactions window."""
        if TransactionsWindow:
            TransactionsWindow(self)
        else:
            self.show_dynamic_popup("📋 Transactions", "Transactions window not available.")
        
    def view_credits(self):
        """Open the Credits window."""
        if CreditsWindow:
            CreditsWindow(self)
        else:
            self.show_dynamic_popup("💳 Credits", "Credits window not available.")
        
    def add_stock(self):
        """Open Add Stock form (admin only) and save to DB."""
        if self.current_user.get('role') != 'admin':
            messagebox.showerror("Access Denied", "Only administrators can add stock.")
            return

        win = tk.Toplevel(self.root)
        win.title("➕ Add New Item")
        win.geometry("420x360")
        win.transient(self.root)
        win.grab_set()

        frm = tk.Frame(win, bg='white')
        frm.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(frm, text="Item Name", font=("Arial", 11, "bold"), bg='white', fg='#2c3e50').grid(row=0, column=0, sticky='w', pady=8)
        name_var = tk.StringVar()
        tk.Entry(frm, textvariable=name_var, font=("Arial", 11), width=28, bd=2, relief=tk.SUNKEN).grid(row=0, column=1, pady=8)

        tk.Label(frm, text="Type", font=("Arial", 11, "bold"), bg='white', fg='#2c3e50').grid(row=1, column=0, sticky='w', pady=8)
        type_var = tk.StringVar(value='product')
        type_box = ttk.Combobox(frm, textvariable=type_var, values=["product", "service", "internet_token"], state='readonly', width=25)
        type_box.grid(row=1, column=1, pady=8)

        tk.Label(frm, text="Price (KES)", font=("Arial", 11, "bold"), bg='white', fg='#2c3e50').grid(row=2, column=0, sticky='w', pady=8)
        price_var = tk.StringVar()
        tk.Entry(frm, textvariable=price_var, font=("Arial", 11), width=28, bd=2, relief=tk.SUNKEN).grid(row=2, column=1, pady=8)

        # Category for stock
        tk.Label(frm, text="Stock Category", font=("Arial", 11, "bold"), bg='white', fg='#2c3e50').grid(row=3, column=0, sticky='w', pady=8)
        category_var = tk.StringVar(value='cyber part')
        category_box = ttk.Combobox(frm, textvariable=category_var, values=["cyber part", "phone part", ""], state='readonly', width=25)
        category_box.grid(row=3, column=1, pady=8)

        # Service category
        tk.Label(frm, text="Service Type", font=("Arial", 11, "bold"), bg='white', fg='#2c3e50').grid(row=4, column=0, sticky='w', pady=8)
        service_cat_var = tk.StringVar(value='')
        service_cat_box = ttk.Combobox(frm, textvariable=service_cat_var, values=["cyber service", "phone repair service", "phone accessories", ""], state='readonly', width=25)
        service_cat_box.grid(row=4, column=1, pady=8)

        tk.Label(frm, text="Quantity", font=("Arial", 11, "bold"), bg='white', fg='#2c3e50').grid(row=5, column=0, sticky='w', pady=8)
        qty_var = tk.StringVar(value='0')
        qty_entry = tk.Entry(frm, textvariable=qty_var, font=("Arial", 11), width=28, bd=2, relief=tk.SUNKEN)
        qty_entry.grid(row=5, column=1, pady=8)

        def on_type_change(event=None):
            if type_var.get() != 'product':
                qty_var.set('0')
                qty_entry.configure(state='disabled')
                # services do not use stock category; encourage service category
                if type_var.get() == 'service':
                    service_cat_box.set('cyber service')
            else:
                qty_entry.configure(state='normal')

        type_box.bind('<<ComboboxSelected>>', on_type_change)
        on_type_change()

        def save_item():
            name = name_var.get().strip()
            t = type_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Item name is required")
                return
            try:
                price = float(price_var.get())
            except Exception:
                messagebox.showerror("Error", "Invalid price")
                return
            if t == 'product':
                try:
                    qty = int(qty_var.get())
                    if qty < 0:
                        raise ValueError
                except Exception:
                    messagebox.showerror("Error", "Invalid quantity")
                    return
            else:
                qty = 0

            code = self.generate_item_code()
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO items (code, name, type, price, quantity, category, service_category) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (code, name, t, price, qty, category_var.get() if t=='product' else '', service_cat_var.get() if t=='service' else '')
            )
            self.conn.commit()
            messagebox.showinfo("Success", f"Item added: {code} - {name}")
            win.destroy()
            # After adding, show items table
            self.view_items()

        btns = tk.Frame(frm, bg='white')
        btns.grid(row=4, column=0, columnspan=2, pady=20)
        tk.Button(btns, text="Save", command=save_item, bg='#27ae60', fg='white',
                  font=("Arial", 11, "bold"), width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Cancel", command=win.destroy, bg='#95a5a6', fg='white',
                  font=("Arial", 11, "bold"), width=10).pack(side=tk.LEFT, padx=5)
            
    def stock_report(self):
        """Open the Stock Report window (admin only)."""
        if self.current_user['role'] == 'admin':
            if StockReportWindow:
                StockReportWindow(self)
            else:
                self.show_dynamic_popup("📊 Stock Report", "Stock Report window not available.")
        else:
            messagebox.showerror("Access Denied", "Only administrators can view stock reports.")
            
    def sales_report(self):
        """Open the Sales Report window (admin only)."""
        if self.current_user['role'] == 'admin':
            if SalesReportWindow:
                SalesReportWindow(self)
            else:
                self.show_dynamic_popup("📈 Sales Report", "Sales Report window not available.")
        else:
            messagebox.showerror("Access Denied", "Only administrators can view sales reports.")
            
    def show_dynamic_popup(self, title, message):
        """Show dynamic popup with styling."""
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("500x400")
        popup.configure(bg='#ecf0f1')
        popup.transient(self.root)
        popup.grab_set()
        
        # Center the popup
        popup.geometry("+%d+%d" % (self.root.winfo_rootx() + 200, self.root.winfo_rooty() + 150))
        
        # Header
        header_frame = tk.Frame(popup, bg='#2c3e50', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text=title, 
                              font=("Arial", 16, "bold"), 
                              fg='white', bg='#2c3e50')
        title_label.pack(expand=True)
        
        # Content
        content_frame = tk.Frame(popup, bg='white', relief=tk.RAISED, bd=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        message_label = tk.Label(content_frame, text=message, 
                                font=("Arial", 12), 
                                fg='#2c3e50', bg='white',
                                justify=tk.LEFT)
        message_label.pack(expand=True, padx=20, pady=20)
        
        # Buttons
        button_frame = tk.Frame(popup, bg='#ecf0f1')
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(button_frame, text="OK", 
                 font=("Arial", 12, "bold"),
                 bg='#27ae60', fg='white',
                 command=popup.destroy,
                 width=10).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(button_frame, text="Cancel", 
                 font=("Arial", 12, "bold"),
                 bg='#95a5a6', fg='white',
                 command=popup.destroy,
                 width=10).pack(side=tk.RIGHT, padx=5)
        
    def logout(self):
        """Handle logout."""
        self.current_user = None
        self.show_login()
        
    def run(self):
        """Start the application."""
        self.root.mainloop()


if __name__ == "__main__":
    print("🚀 Starting BAHAMAS CYBER CAFE AND PHONE REPAIR POS System...")
    app = DynamicPOS()
    app.run()
