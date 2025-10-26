# BAHAMAS CYBER CAFE AND PHONE REPAIR POS (Web UI)

A modern, local POS system with a web interface (Flask + Bootstrap) and SQLite storage. This guide walks you through installation and running on any computer.

## System Requirements
- Python 3.10+ (3.11 recommended)
- pip (Python package manager)
- Internet access for first-time dependency installation (templates load Bootstrap from CDN)

## 1) Download / Copy Project
- Option A (Git):
```
git clone <repo-url>
cd bahamas_pos
```
- Option B (Manual): copy the `bahamas_pos` folder to the target computer and open a terminal in that folder.

## 2) Create and Activate Virtual Environment (Recommended)
- Windows (PowerShell):
```
python -m venv venv
venv\Scripts\activate
```
- macOS / Linux (bash/zsh):
```
python3 -m venv venv
source venv/bin/activate
```

## 3) Install Dependencies
Install all required Python packages:
```
pip install -r requirements.txt
```
If you hit issues, upgrade pip first:
```
python -m pip install --upgrade pip
```

## 4) Database Setup
- The system uses a local SQLite database file: `pos_database.db` in the project root.
- First run will automatically create the database and tables if missing.
- Schema updates are handled with safe `ALTER TABLE` checks at startup (no manual steps needed).

## 5) Run the App
Start the local web server:
```
python app.py
```
Then open your browser at:
```
http://127.0.0.1:5000/
```

### LAN Access (Same Network)
- The app is configured to bind on all interfaces: it runs on `0.0.0.0:5000`.
- Find your local IP on Windows (PowerShell):
```
ipconfig | findstr IPv4
```
- Other PCs on the same LAN can access:
```
http://<your-local-ip>:5000
```
Example: `http://192.168.1.23:5000`

### Default Login Credentials
- Admin: `admin` / `admin123`
- Cashier: `cashier` / `cash123`

If you need to reset:
- Delete `pos_database.db` to start fresh (this erases data), or
- Manually edit users in the database using any SQLite editor.

## 6) Using the POS
- Dashboard: Overview widgets and navigation.
- Add Stock: Create inventory items (admin).
- Record Sale: Choose between Stock Item or Service, set quantity, select payment method (Cash / Mpesa / Credit), pick date, and submit. Service sales do not reduce stock.
- Record Expense: Add expenses with date.
- Credits: Shows outstanding credits; admin can clear a credit by selecting clearance date and payment method. Original credit date is preserved and linked.
- Transactions: Combined view of sales (stock + services) and expenses with filters (date range, type, payment). Cleared credits show clearance date/method; pending credits show as outstanding.
- Reports: Sales and stock reports with summary. (Excel/PDF export supported if you install optional libraries.)
- Services: Manage service catalog (e.g., Photocopy, Printing) with per-unit prices (admin).

## 7) Dark/Light Mode
- Toggle theme in the sidebar. The last selected theme is persisted and loaded on next start.

## 8) Reports & Exports (Optional)
To enable exports, install:
```
pip install openpyxl reportlab pandas
```
- Excel (.xlsx) exports use `openpyxl`.
- PDF exports use `reportlab`.
- Some advanced summaries may use `pandas`.
- Exported files are saved to the path you choose or to an `exports/` folder (when implemented).

## 9) Transferring Data to Another Computer
- All data is kept in `pos_database.db`.
- To migrate: copy the entire project folder including `pos_database.db` to the other machine and follow steps 2–5 above.
- For a clean slate: delete `pos_database.db` before running.

### Sharing the Database Between Two PCs (LAN)
- Place the database file in a shared folder accessible by both PCs (e.g., mapped drive `Z:\shared_folder\pos_database.db`).
- Set an environment variable before starting the app to point to the shared DB:
  - Windows (PowerShell):
  ```
  $env:POS_DB_PATH = "Z:/shared_folder/pos_database.db"
  python app.py
  ```
- The app will use `POS_DB_PATH` if set; otherwise it falls back to the local `pos_database.db`.
- Tip: Ensure only one instance writes at a time for best reliability; SQLite WAL mode is enabled to improve concurrency.

## 10) Notes
- Tech Stack: Flask (backend), Jinja templates, Bootstrap (CDN), SQLite.
- Code Structure:
  - `app.py`: Flask routes and pages.
  - `database.py`: Persistence (SQLite), schema creation/migrations.
  - `transactions.py`: Business logic (sales/expenses/credits).
  - `templates/`: HTML templates.
  - `requirements.txt`: Python dependencies.
  - `README.md`: This guide.
- Legacy Desktop UI: The repo includes a Tkinter desktop version (`main.py`, `windows.py`), but the web app (`app.py`) is the recommended interface.

## Troubleshooting
- Nothing shows in browser:
  - Ensure the terminal says the server is running on `http://127.0.0.1:5000`.
  - Try a different port by editing `app.run(port=5001)` in `app.py`.
- Database is locked:
  - Close other running instances or SQLite editors that have `pos_database.db` open, then retry.
- Module not found (e.g., Flask):
  - Ensure venv is activated and `pip install -r requirements.txt` completed successfully.
