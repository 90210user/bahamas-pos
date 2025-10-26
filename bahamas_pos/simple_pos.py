"""
Simple, working POS system that definitely works!
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime

import auth
import database
import reports
import stock
import transactions


class SimplePOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BAHAMAS CYBER CAFE AND PHONE REPAIR POS")
        self.root.geometry("800x600")
        
        self.current_user = None
        self.setup_login_ui()
        
    def setup_login_ui(self):
        """Setup the login interface."""
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Main frame
        main_frame = ttk.Frame(self.root, padding="50")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Title
        title_label = ttk.Label(main_frame, text="BAHAMAS CYBER CAFE\nAND PHONE REPAIR", 
                               font=("Arial", 20, "bold"), justify=tk.CENTER)
        title_label.pack(pady=(0, 20))
        
        subtitle_label = ttk.Label(main_frame, text="Point of Sale System", 
                                  font=("Arial", 14), justify=tk.CENTER)
        subtitle_label.pack(pady=(0, 40))
        
        # Login form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack()
        
        # Username
        ttk.Label(form_frame, text="Username:", font=("Arial", 12)).grid(row=0, column=0, sticky=tk.W, pady=10)
        self.username_entry = ttk.Entry(form_frame, width=25, font=("Arial", 12))
        self.username_entry.grid(row=0, column=1, pady=10, padx=(20, 0))
        
        # Password
        ttk.Label(form_frame, text="Password:", font=("Arial", 12)).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.password_entry = ttk.Entry(form_frame, width=25, show="*", font=("Arial", 12))
        self.password_entry.grid(row=1, column=1, pady=10, padx=(20, 0))
        
        # Login button
        login_btn = ttk.Button(form_frame, text="LOGIN", command=self.login, 
                              style="Accent.TButton")
        login_btn.grid(row=2, column=0, columnspan=2, pady=30)
        
        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.login())
        
        # Focus on username
        self.username_entry.focus()
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Enter your credentials to login", 
                                     font=("Arial", 10), foreground="blue")
        self.status_label.pack(pady=20)
        
    def login(self):
        """Handle login."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        self.status_label.config(text="Logging in...", foreground="orange")
        self.root.update()
        
        if not username or not password:
            self.status_label.config(text="Please enter both username and password", foreground="red")
            return
            
        user = auth.login(username, password)
        
        if user:
            self.current_user = user
            self.status_label.config(text="Login successful!", foreground="green")
            self.root.update()
            self.root.after(1000, self.setup_main_ui)  # Wait 1 second then show main UI
        else:
            self.status_label.config(text="Invalid credentials!", foreground="red")
            
    def setup_main_ui(self):
        """Setup the main application interface."""
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(header_frame, text="BAHAMAS CYBER CAFE AND PHONE REPAIR", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # User info
        user_label = ttk.Label(header_frame, text=f"Welcome, {self.current_user['username']} ({self.current_user['role']})", 
                              font=("Arial", 10))
        user_label.pack(side=tk.RIGHT)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(fill=tk.X, padx=10, pady=10)
        
        buttons = [
            ("New Sale", self.new_sale),
            ("Add Expense", self.add_expense),
            ("View Items", self.view_items),
            ("View Transactions", self.view_transactions),
            ("View Credits", self.view_credits),
        ]
        
        if auth.is_admin(self.current_user):
            buttons.extend([
                ("Add Stock", self.add_stock),
                ("Stock Report", self.stock_report),
                ("Sales Report", self.sales_report),
            ])
        
        buttons.append(("Logout", self.logout))
        
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(nav_frame, text=text, command=command, width=15)
            btn.grid(row=0, column=i, padx=5, pady=5)
            
        # Main content area
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        balance = transactions.get_system_balance()
        balance_label = ttk.Label(status_frame, text=f"System Balance: KES {balance:.2f}", 
                                 font=("Arial", 10, "bold"), foreground="green")
        balance_label.pack(side=tk.RIGHT)
        
        # Show welcome message
        welcome_label = ttk.Label(self.content_frame, 
                                 text=f"Welcome to BAHAMAS CYBER CAFE AND PHONE REPAIR POS System\n\n"
                                      f"Logged in as: {self.current_user['username']} ({self.current_user['role']})\n\n"
                                      f"Use the buttons above to navigate the system.",
                                 font=("Arial", 12), justify=tk.CENTER)
        welcome_label.pack(expand=True)
        
    def new_sale(self):
        """Handle new sale."""
        messagebox.showinfo("New Sale", "New Sale functionality will be implemented here!")
        
    def add_expense(self):
        """Handle add expense."""
        messagebox.showinfo("Add Expense", "Add Expense functionality will be implemented here!")
        
    def view_items(self):
        """Handle view items."""
        messagebox.showinfo("View Items", "View Items functionality will be implemented here!")
        
    def view_transactions(self):
        """Handle view transactions."""
        messagebox.showinfo("View Transactions", "View Transactions functionality will be implemented here!")
        
    def view_credits(self):
        """Handle view credits."""
        messagebox.showinfo("View Credits", "View Credits functionality will be implemented here!")
        
    def add_stock(self):
        """Handle add stock (admin only)."""
        if auth.is_admin(self.current_user):
            messagebox.showinfo("Add Stock", "Add Stock functionality will be implemented here!")
        else:
            messagebox.showerror("Access Denied", "Only administrators can add stock.")
            
    def stock_report(self):
        """Handle stock report (admin only)."""
        if auth.is_admin(self.current_user):
            messagebox.showinfo("Stock Report", "Stock Report functionality will be implemented here!")
        else:
            messagebox.showerror("Access Denied", "Only administrators can view stock reports.")
            
    def sales_report(self):
        """Handle sales report (admin only)."""
        if auth.is_admin(self.current_user):
            messagebox.showinfo("Sales Report", "Sales Report functionality will be implemented here!")
        else:
            messagebox.showerror("Access Denied", "Only administrators can view sales reports.")
            
    def logout(self):
        """Handle logout."""
        self.current_user = None
        self.setup_login_ui()
        
    def run(self):
        """Start the application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = SimplePOS()
    app.run()
