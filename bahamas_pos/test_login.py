"""
Simple test script to debug login issues
"""
import tkinter as tk
from tkinter import ttk, messagebox
import auth

def test_login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    
    print(f"Attempting login with: {username}")
    
    if not username or not password:
        messagebox.showerror("Error", "Please enter both username and password")
        return
        
    user = auth.login(username, password)
    print(f"Login result: {user}")
    
    if user:
        messagebox.showinfo("Success", f"Login successful! Welcome {user['username']}")
        root.quit()
    else:
        messagebox.showerror("Error", "Invalid credentials!")

# Create main window
root = tk.Tk()
root.title("Login Test")
root.geometry("300x200")

# Create form
main_frame = ttk.Frame(root, padding="20")
main_frame.pack(fill=tk.BOTH, expand=True)

# Username
ttk.Label(main_frame, text="Username:").pack(anchor=tk.W)
username_entry = ttk.Entry(main_frame, width=25)
username_entry.pack(fill=tk.X, pady=(0, 10))

# Password
ttk.Label(main_frame, text="Password:").pack(anchor=tk.W)
password_entry = ttk.Entry(main_frame, width=25, show="*")
password_entry.pack(fill=tk.X, pady=(0, 10))

# Login button
ttk.Button(main_frame, text="Login", command=test_login).pack(pady=10)

# Focus on username
username_entry.focus()

# Bind Enter key
root.bind('<Return>', lambda e: test_login())

print("Test login window created. Try logging in with admin/admin123")

root.mainloop()
