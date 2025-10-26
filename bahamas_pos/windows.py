"""
Window classes for the POS system GUI.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import List, Dict
import tkinter.simpledialog as simpledialog
import calendar as pycalendar
try:
    from tkcalendar import DateEntry  # optional dependency
    from tkcalendar import Calendar as TkCalendar
except Exception:
    DateEntry = None
    TkCalendar = None


class DatePickerDialog(tk.Toplevel):
    def __init__(self, master, initial_date: datetime):
        super().__init__(master)
        self.title("Select Date")
        self.transient(master)
        self.grab_set()
        self.selected_date = initial_date
        self.result = None
        container = ttk.Frame(self, padding="8")
        container.pack(fill=tk.BOTH, expand=True)
        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 6))
        self.month_var = tk.IntVar(value=initial_date.month)
        self.year_var = tk.IntVar(value=initial_date.year)
        def shift_month(delta: int):
            m = self.month_var.get() - 1 + delta
            y = self.year_var.get() + m // 12
            m = m % 12 + 1
            self.month_var.set(m)
            self.year_var.set(y)
            render_calendar()
        ttk.Button(header, text="◀", width=3, command=lambda: shift_month(-1)).pack(side=tk.LEFT)
        self.title_lbl = ttk.Label(header, text="", font=("Arial", 11, "bold"))
        self.title_lbl.pack(side=tk.LEFT, padx=8)
        ttk.Button(header, text="▶", width=3, command=lambda: shift_month(1)).pack(side=tk.LEFT)
        ttk.Button(header, text="Today", command=lambda: self._pick(datetime.now())).pack(side=tk.RIGHT)
        body = ttk.Frame(container)
        body.pack(fill=tk.BOTH, expand=True)
        self.grid_frame = ttk.Frame(body)
        self.grid_frame.pack()
        footer = ttk.Frame(container)
        footer.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(footer, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)
        def render_calendar():
            for w in self.grid_frame.winfo_children():
                w.destroy()
            month = self.month_var.get()
            year = self.year_var.get()
            self.title_lbl.config(text=f"{pycalendar.month_name[month]} {year}")
            # Header weekdays
            for i, name in enumerate(["Mo","Tu","We","Th","Fr","Sa","Su"]):
                ttk.Label(self.grid_frame, text=name, width=4, anchor=tk.CENTER).grid(row=0, column=i, padx=2, pady=2)
            # Calendar rows
            cal = pycalendar.Calendar(firstweekday=0)
            row = 1
            for week in cal.monthdayscalendar(year, month):
                for col, day in enumerate(week):
                    if day == 0:
                        ttk.Label(self.grid_frame, text="", width=4).grid(row=row, column=col, padx=2, pady=2)
                    else:
                        d = datetime(year, month, day)
                        btn = ttk.Button(self.grid_frame, text=str(day), width=4, command=lambda dd=d: self._pick(dd))
                        btn.grid(row=row, column=col, padx=2, pady=2)
                row += 1
        def build_tkcalendar():
            for w in body.winfo_children():
                w.destroy()
            cal_widget = TkCalendar(body, selectmode='day', year=initial_date.year, month=initial_date.month, day=initial_date.day, date_pattern='yyyy-mm-dd')
            cal_widget.pack()
            actions = ttk.Frame(container)
            actions.pack(fill=tk.X, pady=(6, 0))
            ttk.Button(actions, text="Today", command=lambda: cal_widget.selection_set(datetime.now())).pack(side=tk.LEFT)
            ttk.Button(actions, text="OK", command=lambda: self._pick(datetime.strptime(cal_widget.get_date(), '%Y-%m-%d'))).pack(side=tk.RIGHT)
            ttk.Button(actions, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=6)
        if TkCalendar:
            build_tkcalendar()
        else:
            render_calendar()
    def _pick(self, d: datetime):
        self.result = d
        self.destroy()


class CalendarField(ttk.Frame):
    def __init__(self, master, label_text: str):
        super().__init__(master)
        ttk.Label(self, text=label_text).pack(side=tk.LEFT)
        self.var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        self.entry = ttk.Entry(self, textvariable=self.var, width=16)
        self.entry.pack(side=tk.LEFT, padx=(6, 6))
        ttk.Button(self, text="📅", width=3, command=self.open_picker).pack(side=tk.LEFT)
    def open_picker(self):
        try:
            current = datetime.strptime(self.var.get(), '%Y-%m-%d')
        except Exception:
            current = datetime.now()
        dlg = DatePickerDialog(self.winfo_toplevel(), current)
        self.wait_window(dlg)
        if dlg.result:
            self.var.set(dlg.result.strftime('%Y-%m-%d'))
    def get_date_str(self) -> str:
        return self.var.get().strip()

import auth
import database
import reports
import stock
import transactions


class SalesWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("New Sale - BAHAMAS POS")
        self.window.geometry("800x600")
        self.window.transient(parent.root)
        self.window.grab_set()
        
        self.cart_items = []
        self.setup_ui()
        self.load_items()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left frame - Item selection
        left_frame = ttk.LabelFrame(main_frame, text="Select Items", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Item selection
        ttk.Label(left_frame, text="Item:").pack(anchor=tk.W)
        self.item_var = tk.StringVar()
        self.item_combo = ttk.Combobox(left_frame, textvariable=self.item_var, state="readonly", width=30)
        self.item_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Quantity
        qty_frame = ttk.Frame(left_frame)
        qty_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(qty_frame, text="Quantity:").pack(side=tk.LEFT)
        self.qty_var = tk.StringVar(value="1")
        qty_entry = ttk.Entry(qty_frame, textvariable=self.qty_var, width=10)
        qty_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Add to cart button
        ttk.Button(left_frame, text="Add to Cart", command=self.add_to_cart).pack(pady=10)
        
        # Cart display
        cart_frame = ttk.LabelFrame(left_frame, text="Cart", padding="5")
        cart_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Cart treeview
        columns = ("Item", "Qty", "Price", "Total")
        self.cart_tree = ttk.Treeview(cart_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=100)
        
        # Scrollbar for cart
        cart_scrollbar = ttk.Scrollbar(cart_frame, orient=tk.VERTICAL, command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)
        
        self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cart_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Remove item button
        ttk.Button(left_frame, text="Remove Selected", command=self.remove_from_cart).pack(pady=5)
        
        # Right frame - Payment
        right_frame = ttk.LabelFrame(main_frame, text="Payment Details", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Transaction date
        self.sale_date_field = CalendarField(right_frame, "Date:")
        self.sale_date_field.pack(fill=tk.X, pady=(0, 10))
        
        # Payment method
        ttk.Label(right_frame, text="Payment Method:").pack(anchor=tk.W)
        self.payment_var = tk.StringVar(value="Cash")
        payment_combo = ttk.Combobox(right_frame, textvariable=self.payment_var, 
                                   values=["Cash", "Mpesa", "Credit"], state="readonly")
        payment_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Customer name (for credit)
        ttk.Label(right_frame, text="Customer Name:").pack(anchor=tk.W)
        self.customer_var = tk.StringVar()
        customer_entry = ttk.Entry(right_frame, textvariable=self.customer_var)
        customer_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Total display
        self.total_label = ttk.Label(right_frame, text="Total: KES 0.00", 
                                   font=("Arial", 14, "bold"))
        self.total_label.pack(pady=20)
        
        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Process Sale", command=self.process_sale).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Clear Cart", command=self.clear_cart).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(fill=tk.X, pady=2)
        
        # Bind payment method change
        payment_combo.bind("<<ComboboxSelected>>", self.on_payment_change)
        
    def load_items(self):
        """Load items into the combobox."""
        items = stock.list_items()
        item_list = []
        for item in items:
            if item["type"] == "product" and item["quantity"] > 0:
                item_list.append(f"{item['code']} - {item['name']} (KES {item['price']:.2f})")
            elif item["type"] in ["service", "internet_token"]:
                item_list.append(f"{item['code']} - {item['name']} (KES {item['price']:.2f})")
        
        self.item_combo['values'] = item_list
        if item_list:
            self.item_combo.current(0)
            
    def add_to_cart(self):
        """Add selected item to cart."""
        selected = self.item_var.get()
        if not selected:
            messagebox.showerror("Error", "Please select an item")
            return
            
        try:
            qty = int(self.qty_var.get())
            if qty <= 0:
                messagebox.showerror("Error", "Quantity must be positive")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity")
            return
            
        # Extract item code
        code = selected.split(" - ")[0]
        item = stock.get_item(code)
        if not item:
            messagebox.showerror("Error", "Item not found")
            return
            
        # Check stock for products
        if item["type"] == "product" and item["quantity"] < qty:
            messagebox.showerror("Error", f"Insufficient stock. Available: {item['quantity']}")
            return
            
        # Add to cart
        cart_item = {
            "code": code,
            "name": item["name"],
            "price": item["price"],
            "quantity": qty,
            "total": item["price"] * qty
        }
        
        # Check if item already in cart
        for i, existing in enumerate(self.cart_items):
            if existing["code"] == code:
                self.cart_items[i]["quantity"] += qty
                self.cart_items[i]["total"] = self.cart_items[i]["quantity"] * self.cart_items[i]["price"]
                break
        else:
            self.cart_items.append(cart_item)
            
        self.update_cart_display()
        
    def remove_from_cart(self):
        """Remove selected item from cart."""
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select an item to remove")
            return
            
        item = self.cart_tree.item(selection[0])
        index = self.cart_tree.index(selection[0])
        del self.cart_items[index]
        self.update_cart_display()
        
    def clear_cart(self):
        """Clear all items from cart."""
        self.cart_items = []
        self.update_cart_display()
        
    def update_cart_display(self):
        """Update the cart display."""
        # Clear existing items
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
            
        # Add cart items
        total = 0
        for item in self.cart_items:
            self.cart_tree.insert("", tk.END, values=(
                item["name"],
                item["quantity"],
                f"KES {item['price']:.2f}",
                f"KES {item['total']:.2f}"
            ))
            total += item["total"]
            
        self.total_label.config(text=f"Total: KES {total:.2f}")
        
    def on_payment_change(self, event=None):
        """Handle payment method change."""
        if self.payment_var.get() == "Credit":
            self.customer_var.set("")
        else:
            self.customer_var.set("")
            
    def process_sale(self):
        """Process the sale."""
        if not self.cart_items:
            messagebox.showerror("Error", "Cart is empty")
            return
            
        payment_method = self.payment_var.get()
        customer_name = self.customer_var.get().strip()
        
        if payment_method == "Credit" and not customer_name:
            messagebox.showerror("Error", "Customer name required for credit sales")
            return
            
        try:
            # Prepare transaction items
            txn_items = [{"code": item["code"], "quantity": item["quantity"]} for item in self.cart_items]
            
            # Create transaction
            date_value = self.sale_date_field.get_date_str() or None
            txn = transactions.create_transaction(txn_items, payment_method, customer_name, date_value)
            
            # Show success message
            messagebox.showinfo("Success", f"Sale processed successfully!\nTransaction ID: {txn['id']}\nTotal: KES {txn['total']:.2f}")
            
            # Show receipt
            self.show_receipt(txn)
            
            # Clear cart and close
            self.clear_cart()
            self.window.destroy()
            
            # Update parent status
            self.parent.update_status()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            
    def show_receipt(self, transaction):
        """Show receipt window."""
        ReceiptWindow(self.parent, transaction)


class ExpenseWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Add Expense - BAHAMAS POS")
        self.window.geometry("400x300")
        self.window.transient(parent.root)
        self.window.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Add Expense", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=10)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.desc_var = tk.StringVar()
        desc_entry = ttk.Entry(form_frame, textvariable=self.desc_var, width=30)
        desc_entry.grid(row=0, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Amount
        ttk.Label(form_frame, text="Amount (KES):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.amount_var = tk.StringVar()
        amount_entry = ttk.Entry(form_frame, textvariable=self.amount_var, width=30)
        amount_entry.grid(row=1, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Date
        ttk.Label(form_frame, text="Date:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.expense_date_field = CalendarField(form_frame, "")
        self.expense_date_field.grid(row=2, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Add Expense", command=self.add_expense).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT)
        
        # Focus on description
        desc_entry.focus()
        
    def add_expense(self):
        """Add the expense."""
        description = self.desc_var.get().strip()
        if not description:
            messagebox.showerror("Error", "Please enter a description")
            return
            
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")
            return
            
        try:
            date_value = (self.expense_date_field.get_date_str() or None)
            expense = transactions.add_expense(description, amount, date_value)
            messagebox.showinfo("Success", f"Expense added successfully!\nDescription: {expense['description']}\nAmount: KES {expense['amount']:.2f}")
            
            self.window.destroy()
            self.parent.update_status()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))


class ItemsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Items - BAHAMAS POS")
        self.window.geometry("800x500")
        self.window.transient(parent.root)
        
        self.setup_ui()
        self.load_items()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Items Inventory", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Items treeview
        columns = ("Code", "Name", "Type", "Price", "Quantity")
        self.items_tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        
        for col in columns:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=scrollbar.set)
        
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Refresh", command=self.load_items).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT)
        
    def load_items(self):
        """Load items into the treeview."""
        # Clear existing items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
            
        # Load items
        items = stock.list_items()
        for item in items:
            self.items_tree.insert("", tk.END, values=(
                item["code"],
                item["name"],
                item["type"],
                f"KES {item['price']:.2f}",
                item["quantity"]
            ))


class TransactionsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Transactions - BAHAMAS POS")
        self.window.geometry("900x500")
        self.window.transient(parent.root)
        
        self.setup_ui()
        self.load_transactions()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Recent Transactions", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Filters
        filters_frame = ttk.Frame(main_frame)
        filters_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(filters_frame, text="From (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.from_date = tk.StringVar()
        ttk.Entry(filters_frame, textvariable=self.from_date, width=12).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(filters_frame, text="To:").pack(side=tk.LEFT)
        self.to_date = tk.StringVar()
        ttk.Entry(filters_frame, textvariable=self.to_date, width=12).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(filters_frame, text="Type:").pack(side=tk.LEFT)
        self.type_filter = tk.StringVar(value="all")
        ttk.Combobox(filters_frame, textvariable=self.type_filter, values=["all", "sale", "expense"], state="readonly", width=10).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(filters_frame, text="Payment:").pack(side=tk.LEFT)
        self.payment_filter = tk.StringVar(value="all")
        ttk.Combobox(filters_frame, textvariable=self.payment_filter, values=["all", "Cash", "Mpesa", "Credit"], state="readonly", width=10).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Button(filters_frame, text="Apply", command=self.load_transactions).pack(side=tk.LEFT)

        # Transactions treeview
        columns = ("ID", "Type", "Date", "Amount", "Payment", "Customer", "Paid", "Date Cleared", "Cleared By")
        self.txn_tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        
        for col in columns:
            self.txn_tree.heading(col, text=col)
            self.txn_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.txn_tree.yview)
        self.txn_tree.configure(yscrollcommand=scrollbar.set)
        
        self.txn_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Refresh", command=self.load_transactions).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Export", command=self.export_transactions).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="View Receipt", command=self.view_receipt).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT)
        
    def load_transactions(self):
        """Load transactions into the treeview."""
        # Clear existing items
        for item in self.txn_tree.get_children():
            self.txn_tree.delete(item)
            
        # Load transactions
        txns = transactions.list_transactions()
        # Apply filters
        f_from = (self.from_date.get() or "").strip()
        f_to = (self.to_date.get() or "").strip()
        f_type = self.type_filter.get()
        f_pay = self.payment_filter.get()

        def in_range(d: str) -> bool:
            if not d:
                return True
            if f_from and d < f_from:
                return False
            if f_to and d > f_to:
                return False
            return True

        for txn in txns:
            if f_type != "all" and txn.get("type", "sale") != f_type:
                continue
            if f_pay != "all" and txn.get("payment_method", "-") != f_pay:
                continue
            if not in_range(txn.get("date", "")):
                continue

            paid_status = "Yes" if txn.get("paid", True) else "No"
            customer = txn.get("customer_name") or (txn.get("description") if txn.get("type") == "expense" else "-")
            self.txn_tree.insert("", tk.END, values=(
                txn.get("id"),
                txn.get("type", "sale"),
                txn.get("date", "N/A"),
                f"KES {txn.get('total', 0):.2f}",
                txn.get("payment_method", "-"),
                customer,
                paid_status,
                txn.get("date_cleared", "-"),
                txn.get("payment_method_cleared", "-")
            ))

    def export_transactions(self):
        """Export transactions table to a text file (placeholder for Excel/PDF)."""
        file_path = filedialog.asksaveasfilename(
            title="Save Transactions",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            rows = []
            for child in self.txn_tree.get_children():
                rows.append(self.txn_tree.item(child, "values"))
            with open(file_path, 'w', encoding='utf-8') as f:
                headers = ["ID", "Type", "Date", "Amount", "Payment", "Customer", "Paid", "Date Cleared", "Cleared By"]
                f.write("\t".join(headers) + "\n")
                for r in rows:
                    f.write("\t".join(map(str, r)) + "\n")
            messagebox.showinfo("Success", f"Transactions exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")
            
    def view_receipt(self):
        """View receipt for selected transaction."""
        selection = self.txn_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a transaction")
            return
            
        item = self.txn_tree.item(selection[0])
        txn_id = item["values"][0]
        
        txn = transactions.get_transaction(txn_id)
        if txn:
            ReceiptWindow(self.parent, txn)
        else:
            messagebox.showerror("Error", "Transaction not found")


class CreditsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Outstanding Credits - BAHAMAS POS")
        self.window.geometry("600x400")
        self.window.transient(parent.root)
        
        self.setup_ui()
        self.load_credits()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Outstanding Credits", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Credits treeview
        columns = ("Customer", "Amount", "Transactions")
        self.credits_tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        
        for col in columns:
            self.credits_tree.heading(col, text=col)
            self.credits_tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.credits_tree.yview)
        self.credits_tree.configure(yscrollcommand=scrollbar.set)
        
        self.credits_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Refresh", command=self.load_credits).pack(side=tk.LEFT, padx=(0, 10))
        
        if auth.is_admin(self.parent.current_user):
            ttk.Button(button_frame, text="Clear Credit", command=self.clear_credit).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT)
        
    def load_credits(self):
        """Load credits into the treeview."""
        # Clear existing items
        for item in self.credits_tree.get_children():
            self.credits_tree.delete(item)
            
        # Load credits
        credits = transactions.list_credits()
        for customer, info in credits.items():
            txn_count = len(info["transaction_ids"])
            self.credits_tree.insert("", tk.END, values=(
                customer,
                f"KES {info['amount']:.2f}",
                f"{txn_count} transaction(s)"
            ))
            
    def clear_credit(self):
        """Clear selected credit (admin only)."""
        if not auth.is_admin(self.parent.current_user):
            messagebox.showerror("Access Denied", "Only administrators can clear credits")
            return
            
        selection = self.credits_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a credit to clear")
            return
            
        item = self.credits_tree.item(selection[0])
        customer = item["values"][0]
        
        if messagebox.askyesno("Confirm", f"Clear credit for {customer}?"):
            # Ask for payment method and date
            method = simpledialog.askstring("Payment Method", "Enter clearance method (Cash/Mpesa):", parent=self.window)
            if not method or method not in ("Cash", "Mpesa"):
                messagebox.showerror("Error", "Invalid payment method")
                return
            date_value = simpledialog.askstring("Clearance Date", "Enter date (YYYY-MM-DD) or leave blank for today:", parent=self.window)
            if transactions.clear_credit(customer, method, (date_value.strip() if date_value else None)):
                messagebox.showinfo("Success", f"Credit cleared for {customer}")
                self.load_credits()
                self.parent.update_status()
            else:
                messagebox.showerror("Error", "Failed to clear credit")


class AddStockWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Add Stock - BAHAMAS POS")
        self.window.geometry("500x400")
        self.window.transient(parent.root)
        self.window.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Add New Item", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=10)
        
        # Item name
        ttk.Label(form_frame, text="Item Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=30)
        name_entry.grid(row=0, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Item type
        ttk.Label(form_frame, text="Item Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="product")
        type_combo = ttk.Combobox(form_frame, textvariable=self.type_var, 
                                values=["product", "service", "internet_token"], 
                                state="readonly", width=27)
        type_combo.grid(row=1, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Price
        ttk.Label(form_frame, text="Price (KES):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.price_var = tk.StringVar()
        price_entry = ttk.Entry(form_frame, textvariable=self.price_var, width=30)
        price_entry.grid(row=2, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Quantity
        ttk.Label(form_frame, text="Initial Quantity:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.qty_var = tk.StringVar(value="0")
        qty_entry = ttk.Entry(form_frame, textvariable=self.qty_var, width=30)
        qty_entry.grid(row=3, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Bind type change
        type_combo.bind("<<ComboboxSelected>>", self.on_type_change)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Add Item", command=self.add_item).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT)
        
        # Focus on name
        name_entry.focus()
        
    def on_type_change(self, event=None):
        """Handle item type change."""
        if self.type_var.get() != "product":
            self.qty_var.set("0")
            
    def add_item(self):
        """Add the new item."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter item name")
            return
            
        item_type = self.type_var.get()
        
        try:
            price = float(self.price_var.get())
            if price < 0:
                messagebox.showerror("Error", "Price cannot be negative")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid price")
            return
            
        try:
            qty = int(self.qty_var.get())
            if qty < 0:
                messagebox.showerror("Error", "Quantity cannot be negative")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity")
            return
            
        try:
            item = stock.add_item(name, item_type, price, qty)
            messagebox.showinfo("Success", f"Item added successfully!\nCode: {item['code']}\nName: {item['name']}")
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))


class StockReportWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Stock Report - BAHAMAS POS")
        self.window.geometry("800x500")
        self.window.transient(parent.root)
        
        self.setup_ui()
        self.load_report()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Stock Report", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Report treeview
        columns = ("Code", "Item Name", "Received", "Used", "Remaining")
        self.report_tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=scrollbar.set)
        
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Refresh", command=self.load_report).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Export", command=self.export_report).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT)
        
    def load_report(self):
        """Load stock report data."""
        # Clear existing items
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
            
        # Load report data
        rows = stock.stock_report_rows()
        for row in rows:
            self.report_tree.insert("", tk.END, values=(
                row["code"],
                row["name"],
                row["received"],
                row["used"],
                row["remaining"]
            ))
            
    def export_report(self):
        """Export report to file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Stock Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(reports.generate_stock_report())
                messagebox.showinfo("Success", f"Report exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export report: {e}")


class SalesReportWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Sales Report - BAHAMAS POS")
        self.window.geometry("600x400")
        self.window.transient(parent.root)
        
        self.setup_ui()
        self.load_report()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Sales Summary", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Report text
        self.report_text = tk.Text(main_frame, wrap=tk.WORD, font=("Courier", 10))
        self.report_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Refresh", command=self.load_report).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Export", command=self.export_report).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT)
        
    def load_report(self):
        """Load sales report."""
        self.report_text.delete(1.0, tk.END)
        report = reports.generate_sales_summary()
        self.report_text.insert(1.0, report)
        
    def export_report(self):
        """Export report to file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Sales Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(reports.generate_sales_summary())
                messagebox.showinfo("Success", f"Report exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export report: {e}")


class ReceiptWindow:
    def __init__(self, parent, transaction):
        self.parent = parent
        self.transaction = transaction
        self.window = tk.Toplevel(parent.root)
        self.window.title("Receipt - BAHAMAS POS")
        self.window.geometry("500x600")
        self.window.transient(parent.root)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Receipt text
        self.receipt_text = tk.Text(main_frame, wrap=tk.WORD, font=("Courier", 10))
        self.receipt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Print", command=self.print_receipt).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Save", command=self.save_receipt).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT)
        
        # Load receipt
        self.load_receipt()
        
    def load_receipt(self):
        """Load receipt text."""
        self.receipt_text.delete(1.0, tk.END)
        receipt = reports.generate_receipt(self.transaction)
        self.receipt_text.insert(1.0, receipt)
        
    def print_receipt(self):
        """Print receipt."""
        try:
            self.receipt_text.print()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print: {e}")
            
    def save_receipt(self):
        """Save receipt to file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Receipt",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(reports.generate_receipt(self.transaction))
                messagebox.showinfo("Success", f"Receipt saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save receipt: {e}")
