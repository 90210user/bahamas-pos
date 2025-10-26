"""
Main Tkinter GUI application for BAHAMAS CYBER CAFE AND PHONE REPAIR POS System.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
from typing import Optional

# Try to import PIL, but make it optional
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL/Pillow not available. Logo functionality will be disabled.")

import auth
import database
import reports
import stock
import transactions
from windows import (SalesWindow, ExpenseWindow, ItemsWindow, TransactionsWindow, 
                    CreditsWindow, AddStockWindow, StockReportWindow, SalesReportWindow, ReceiptWindow)


class LoginWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Login - BAHAMAS POS")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center the window
        self.window.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui()
        self.result = None
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="BAHAMAS CYBER CAFE\nAND PHONE REPAIR", 
                               font=("Arial", 16, "bold"), justify=tk.CENTER)
        title_label.pack(pady=(0, 20))
        
        subtitle_label = ttk.Label(main_frame, text="Point of Sale System", 
                                  font=("Arial", 12), justify=tk.CENTER)
        subtitle_label.pack(pady=(0, 30))
        
        # Login form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=10)
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(form_frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Password
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(form_frame, width=25, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Login", command=self.login).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT)
        
        # Bind Enter key to login
        self.window.bind('<Return>', lambda e: self.login())
        
        # Focus on username entry
        self.username_entry.focus()
        
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        print(f"Login attempt: username='{username}', password='{password[:3]}...'")
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        user = auth.login(username, password)
        print(f"Login result: {user}")
        
        if user:
            self.result = user
            print("Login successful, closing window")
            self.window.destroy()
        else:
            print("Login failed")
            messagebox.showerror("Error", "Invalid credentials!")
            
    def cancel(self):
        self.result = None
        self.window.destroy()


class MainApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BAHAMAS CYBER CAFE AND PHONE REPAIR POS")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Current user
        self.current_user = None
        
        # Logo
        self.logo_image = None
        self.logo_label = None
        
        self.setup_ui()
        self.show_login()
        
    def setup_ui(self):
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header frame
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Logo and title
        logo_title_frame = ttk.Frame(self.header_frame)
        logo_title_frame.pack(side=tk.LEFT)
        
        # Logo placeholder
        self.logo_label = ttk.Label(logo_title_frame, text="LOGO", 
                                   font=("Arial", 12), background="lightgray", 
                                   width=10, anchor=tk.CENTER)
        self.logo_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Title
        title_label = ttk.Label(logo_title_frame, text="BAHAMAS CYBER CAFE AND PHONE REPAIR", 
                               font=("Arial", 18, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # User info
        self.user_frame = ttk.Frame(self.header_frame)
        self.user_frame.pack(side=tk.RIGHT)
        
        self.user_label = ttk.Label(self.user_frame, text="", font=("Arial", 10))
        self.user_label.pack()
        
        # Navigation buttons
        self.nav_frame = ttk.Frame(self.main_frame)
        self.nav_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Main content area
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", 
                                     font=("Arial", 9), foreground="blue")
        self.status_label.pack(side=tk.LEFT)
        
        self.balance_label = ttk.Label(self.status_frame, text="", 
                                      font=("Arial", 9, "bold"), foreground="green")
        self.balance_label.pack(side=tk.RIGHT)
        
    def show_login(self):
        """Show login window and wait for authentication."""
        login_window = LoginWindow(self.root)
        self.root.wait_window(login_window.window)
        
        if login_window.result:
            self.current_user = login_window.result
            self.setup_authenticated_ui()
            self.load_logo()
            self.update_status()
        else:
            self.root.quit()
            
    def setup_authenticated_ui(self):
        """Setup UI after successful login."""
        # Clear existing navigation
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
            
        # Update user info
        self.user_label.config(text=f"Welcome, {self.current_user['username']} ({self.current_user['role']})")
        
        # Navigation buttons
        buttons = [
            ("New Sale", self.show_sales_window),
            ("Add Expense", self.show_expense_window),
            ("View Items", self.show_items_window),
            ("View Transactions", self.show_transactions_window),
            ("View Credits", self.show_credits_window),
        ]
        
        if auth.is_admin(self.current_user):
            buttons.extend([
                ("Add Stock", self.show_add_stock_window),
                ("Stock Report", self.show_stock_report_window),
                ("Sales Report", self.show_sales_report_window),
                ("Set Logo", self.set_logo),
            ])
        
        buttons.append(("Logout", self.logout))
        
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(self.nav_frame, text=text, command=command)
            btn.grid(row=0, column=i, padx=5, pady=5)
            
        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Show welcome message
        welcome_label = ttk.Label(self.content_frame, 
                                 text=f"Welcome to BAHAMAS CYBER CAFE AND PHONE REPAIR POS System\n\n"
                                      f"Logged in as: {self.current_user['username']} ({self.current_user['role']})\n\n"
                                      f"Use the buttons above to navigate the system.",
                                 font=("Arial", 12), justify=tk.CENTER)
        welcome_label.pack(expand=True)
        
    def load_logo(self):
        """Load and display logo if available."""
        if not PIL_AVAILABLE:
            return
            
        logo_path = auth.get_logo_path()
        if logo_path and os.path.exists(logo_path):
            try:
                # Load and resize image
                image = Image.open(logo_path)
                image = image.resize((80, 60), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(image)
                self.logo_label.config(image=self.logo_image, text="")
            except Exception as e:
                print(f"Error loading logo: {e}")
                
    def update_status(self):
        """Update status bar with current balance."""
        balance = transactions.get_system_balance()
        self.balance_label.config(text=f"System Balance: KES {balance:.2f}")
        
    def set_logo(self):
        """Set logo path (admin only)."""
        if not auth.is_admin(self.current_user):
            messagebox.showerror("Access Denied", "Only administrators can set the logo.")
            return
            
        file_path = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if file_path:
            if auth.set_logo_path(self.current_user, file_path):
                messagebox.showinfo("Success", "Logo path set successfully!")
                self.load_logo()
            else:
                messagebox.showerror("Error", "Failed to set logo path.")
                
    def logout(self):
        """Logout and return to login screen."""
        self.current_user = None
        self.logo_image = None
        self.logo_label.config(image="", text="LOGO")
        self.user_label.config(text="")
        self.balance_label.config(text="")
        self.show_login()
        
    def show_sales_window(self):
        """Show sales transaction window."""
        SalesWindow(self)
        
    def show_expense_window(self):
        """Show expense window."""
        ExpenseWindow(self)
        
    def show_items_window(self):
        """Show items window."""
        ItemsWindow(self)
        
    def show_transactions_window(self):
        """Show transactions window."""
        TransactionsWindow(self)
        
    def show_credits_window(self):
        """Show credits window."""
        CreditsWindow(self)
        
    def show_add_stock_window(self):
        """Show add stock window (admin only)."""
        if auth.is_admin(self.current_user):
            AddStockWindow(self)
        else:
            messagebox.showerror("Access Denied", "Only administrators can add stock.")
            
    def show_stock_report_window(self):
        """Show stock report window (admin only)."""
        if auth.is_admin(self.current_user):
            StockReportWindow(self)
        else:
            messagebox.showerror("Access Denied", "Only administrators can view stock reports.")
            
    def show_sales_report_window(self):
        """Show sales report window (admin only)."""
        if auth.is_admin(self.current_user):
            SalesReportWindow(self)
        else:
            messagebox.showerror("Access Denied", "Only administrators can view sales reports.")
            
    def run(self):
        """Start the application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = MainApplication()
    app.run()
