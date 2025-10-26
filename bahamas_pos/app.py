from __future__ import annotations
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from datetime import datetime
import os

# Reuse existing backend modules
import database
import transactions
import stock
import reports
import auth


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("POS_SECRET_KEY", "dev-secret-key")
    # Optional: accept SQLAlchemy-style URI to point to shared SQLite file
    # Example: sqlite:///Z:/bahamas_pos/database.db
    uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
    if uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = uri
        # Bridge to our sqlite3 layer which uses POS_DB_PATH
        if uri.startswith("sqlite:///"):
            os.environ["POS_DB_PATH"] = uri.replace("sqlite:///", "", 1)

    @app.context_processor
    def inject_globals():
        return {
            "current_user": session.get("user"),
            "theme": session.get("theme", database.db.get_setting("theme", "light")),
            "app_title": "BAHAMAS CYBER CAFE AND PHONE REPAIR POS",
            "now": lambda: datetime.now().strftime('%Y-%m-%d'),
        }

    @app.route("/")
    def index():
        if session.get("user"):
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            user = database.db.authenticate_user(username, password)
            if user:
                session["user"] = user
                flash("Welcome!", "success")
                return redirect(url_for("dashboard"))
            flash("Invalid credentials", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.pop("user", None)
        return redirect(url_for("login"))

    @app.route("/theme", methods=["POST"])
    def toggle_theme():
        new_theme = request.form.get("theme", "light")
        session["theme"] = new_theme
        # Persist preference
        database.db.set_setting("theme", new_theme)
        return redirect(request.referrer or url_for("dashboard"))

    def require_login():
        if not session.get("user"):
            return redirect(url_for("login"))
        return None

    @app.route("/dashboard")
    def dashboard():
        guard = require_login()
        if guard:
            return guard
        summary = database.db.get_sales_summary()
        # Optional search
        q = request.args.get("q", "").strip()
        search_results = None
        if q:
            # Naive search across items, transactions, credits
            items = stock.list_items()
            txns = transactions.list_transactions()
            creds = transactions.list_credits()
            results = []
            for it in items:
                if q.lower() in (it.get("code","")+" "+it.get("name","")) .lower():
                    results.append(f"Item {it['code']} - {it['name']} (KES {it.get('selling_price') or it.get('price')})")
            for t in txns:
                blob = f"{t.get('id')} {t.get('type')} {t.get('customer_name') or t.get('description','')} {t.get('payment_method')}"
                if q.lower() in blob.lower():
                    results.append(f"Txn {t['id']} - {t['type']} KES {t['total']:.2f} {t['payment_method']}")
            for cust in creds.keys():
                if q.lower() in cust.lower():
                    results.append(f"Credit - {cust}")
            search_results = results[:20]
        return render_template("dashboard.html", summary=summary, search_results=search_results)

    @app.route("/transactions", methods=["GET", "POST"])
    def view_transactions():
        guard = require_login()
        if guard:
            return guard
        if request.method == "POST":
            action = request.form.get("action")
            if action == "delete_selected":
                ids = request.form.getlist("selected_txn")
                # Split into sales (TXN...) and expenses (EXP...)
                sale_ids = [i for i in ids if not str(i).startswith("EXP")]
                exp_ids = [int(str(i)[3:]) for i in ids if str(i).startswith("EXP")]
                deleted_sales = database.db.delete_transactions(sale_ids) if sale_ids else 0
                deleted_exp = database.db.delete_expenses(exp_ids) if exp_ids else 0
                flash(f"Deleted {deleted_sales} sale(s), {deleted_exp} expense(s)", "success")
                return redirect(url_for("view_transactions"))
        f_type = request.args.get("type", "all")
        f_pay = request.args.get("payment", "all")
        f_from = request.args.get("from", "")
        f_to = request.args.get("to", "")
        rows = transactions.list_transactions()

        def in_range(d: str) -> bool:
            if not d:
                return True
            return (not f_from or d >= f_from) and (not f_to or d <= f_to)

        filtered = []
        for r in rows:
            if f_type != "all" and r.get("type", "sale") != f_type:
                continue
            if f_pay != "all" and r.get("payment_method", "-") != f_pay:
                continue
            if not in_range(r.get("date", "")):
                continue
            filtered.append(r)
        return render_template("transactions.html", rows=filtered, f_type=f_type, f_pay=f_pay, f_from=f_from, f_to=f_to)

    @app.route("/sales", methods=["GET", "POST"])
    def record_sale():
        guard = require_login()
        if guard:
            return guard
        items = stock.list_items()
        svc = database.db.list_services()
        if request.method == "POST":
            sale_type = request.form.get("sale_type", "stock")
            payment = request.form.get("payment_method", "Cash")
            customer = request.form.get("customer_name", "").strip()
            date_val = request.form.get("date", "") or None
            try:
                if sale_type == "service":
                    service_raw = request.form.get("service_id")
                    if not service_raw:
                        raise ValueError("Service is required")
                    service_id = int(service_raw)
                    qty = int(request.form.get("quantity", "1") or 1)
                    txn = transactions.create_transaction([{"service_id": service_id, "quantity": qty}], payment, customer, date_val)
                else:
                    code = request.form.get("item_code")
                    qty = int(request.form.get("quantity", "0") or 0)
                    txn = transactions.create_transaction([{"code": code, "quantity": qty}], payment, customer, date_val)
                flash(f"Sale recorded: {txn['id']}", "success")
                if payment == "Credit":
                    return redirect(url_for("manage_credits"))
                return redirect(url_for("view_transactions"))
            except Exception as e:
                flash(str(e), "error")
        return render_template("sales.html", items=items, services=svc)

    @app.route("/services", methods=["GET", "POST"]) 
    def manage_services():
        guard = require_login()
        if guard:
            return guard
        user = session.get("user")
        if not auth.is_admin(user):
            flash("Only administrators can manage services", "error")
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            action = request.form.get("action", "add")
            if action == "add":
                name = request.form.get("service_name", "").strip()
                price = float(request.form.get("price", "0") or 0)
                database.db.add_service(name, price)
            elif action == "delete_selected":
                ids = request.form.getlist("selected_service")
                for sid in ids:
                    try:
                        database.db.delete_service(int(sid))
                    except Exception:
                        continue
            elif action == "update":
                sid = int(request.form.get("id"))
                name = request.form.get("service_name", "").strip()
                price = float(request.form.get("price", "0") or 0)
                database.db.update_service(sid, name, price)
            elif action == "delete":
                sid = int(request.form.get("id"))
                database.db.delete_service(sid)
            return redirect(url_for("manage_services"))
        services = database.db.list_services()
        return render_template("services.html", services=services)

    @app.route("/expenses", methods=["GET", "POST"])
    def record_expense():
        guard = require_login()
        if guard:
            return guard
        if request.method == "POST":
            desc = request.form.get("description", "").strip()
            amount = float(request.form.get("amount", "0") or 0)
            date_val = request.form.get("date", "") or None
            try:
                transactions.add_expense(desc, amount, date_val)
                flash("Expense recorded", "success")
                return redirect(url_for("view_transactions"))
            except Exception as e:
                flash(str(e), "error")
        return render_template("expenses.html")

    @app.route("/credits", methods=["GET", "POST"]) 
    def manage_credits():
        guard = require_login()
        if guard:
            return guard
        user = session.get("user")
        credits = transactions.list_credits()
        if request.method == "POST":
            action = request.form.get("action", "clear")
            if action in ("delete_selected", "delete_one"):
                if not auth.is_admin(user):
                    flash("Only administrators can delete credits", "error")
                    return redirect(url_for("manage_credits"))
                customers = request.form.getlist("selected_credit") if action == "delete_selected" else [request.form.get("customer")]
                try:
                    customers = [c for c in customers if c]
                    deleted = database.db.delete_credits(customers)
                    flash(f"Deleted {deleted} credit record(s)", "success")
                except Exception as e:
                    flash(f"Delete failed: {e}", "error")
                return redirect(url_for("manage_credits"))
            customer = request.form.get("customer")
            method = request.form.get("method")
            date_val = request.form.get("date", "") or None
            if not auth.is_admin(user):
                flash("Only administrators can clear credits", "error")
            else:
                try:
                    transactions.clear_credit(customer, method, date_val)
                    flash("Credit cleared", "success")
                    return redirect(url_for("manage_credits"))
                except Exception as e:
                    flash(str(e), "error")
        # For transaction history view: include credit rows with dates
        rows = []
        for customer, info in credits.items():
            rows.append({
                "customer": customer,
                "amount": info.get("amount", 0.0),
                "date_created": info.get("date_created"),
                "date_cleared": info.get("date_cleared"),
                "payment_method_cleared": info.get("payment_method_cleared"),
                "status": info.get("status", "Pending"),
                "transactions": len(info.get("transaction_ids", [])),
            })
        return render_template("credits.html", credits=credits, credit_rows=rows)

    @app.route("/stock", methods=["GET", "POST"]) 
    def add_stock():
        guard = require_login()
        if guard:
            return guard
        user = session.get("user")
        if request.method == "POST":
            if not auth.is_admin(user):
                flash("Only administrators can add stock", "error")
            else:
                action = request.form.get("action", "add")
                try:
                    if action == "add":
                        name = request.form.get("name", "").strip()
                        type_ = request.form.get("type", "product")
                        price = float(request.form.get("price", "0") or 0)
                        qty = int(request.form.get("quantity", "0") or 0)
                        buying = float(request.form.get("buying_price", "0") or 0)
                        selling = request.form.get("selling_price")
                        selling_val = float(selling) if selling not in (None, "",) else None
                        stock.add_item(name, type_, price, qty, buying, selling_val)
                        flash("Item added", "success")
                    elif action == "update":
                        code = request.form.get("code", "").strip()
                        name = request.form.get("name", "").strip()
                        qty = int(request.form.get("quantity", "0") or 0)
                        buying = float(request.form.get("buying_price", "0") or 0)
                        selling = float(request.form.get("selling_price", "0") or 0)
                        stock.update_item(code, name, qty, buying, selling)
                        flash("Item updated", "success")
                    elif action == "delete_selected":
                        codes = request.form.getlist("selected")
                        deleted = stock.delete_items(codes)
                        flash(f"Deleted {deleted} item(s)", "success")
                    return redirect(url_for("add_stock"))
                except Exception as e:
                    flash(str(e), "error")
        items = stock.list_items()
        return render_template("stock.html", items=items)

    @app.route("/reports")
    def reports_page():
        guard = require_login()
        if guard:
            return guard
        summary = database.db.get_sales_summary()
        # Date range filters for transactions (affect exports later) - stock report remains overall
        from_d = request.args.get("from", "")
        to_d = request.args.get("to", "")
        stock_rows = database.db.get_stock_report_data()
        return render_template("reports.html", summary=summary, stock_rows=stock_rows)

    @app.route("/reports/export/excel")
    def export_reports_excel():
        guard = require_login()
        if guard:
            return guard
        from_d = request.args.get("from", "")
        to_d = request.args.get("to", "")
        rows = transactions.list_transactions()
        def in_range(d: str) -> bool:
            if not d:
                return True
            return (not from_d or d >= from_d) and (not to_d or d <= to_d)
        filtered = [r for r in rows if in_range(r.get("date", ""))]
        if not filtered:
            flash("No records found for selected range", "error")
            return redirect(url_for("reports_page", **{"from": from_d, "to": to_d}))
        # Build Excel
        try:
            from io import BytesIO
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Transactions"
            headers = ["ID", "Type", "Date", "Amount", "Payment", "Customer/Description", "Paid", "Cleared Date", "Cleared By"]
            ws.append(headers)
            for r in filtered:
                ws.append([
                    r.get("id"), r.get("type"), r.get("date"), r.get("total"), r.get("payment_method"),
                    r.get("customer_name") or r.get("description") or "-",
                    "Yes" if r.get("paid") else "No",
                    r.get("date_cleared") or "-",
                    r.get("payment_method_cleared") or "-",
                ])
            buf = BytesIO()
            wb.save(buf)
            buf.seek(0)
            filename = f"report_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            return send_file(buf, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            flash(f"Export failed: {e}", "error")
            return redirect(url_for("reports_page", **{"from": from_d, "to": to_d}))

    @app.route("/reports/export/pdf")
    def export_reports_pdf():
        guard = require_login()
        if guard:
            return guard
        from_d = request.args.get("from", "")
        to_d = request.args.get("to", "")
        rows = transactions.list_transactions()
        def in_range(d: str) -> bool:
            if not d:
                return True
            return (not from_d or d >= from_d) and (not to_d or d <= to_d)
        filtered = [r for r in rows if in_range(r.get("date", ""))]
        if not filtered:
            flash("No records found for selected range", "error")
            return redirect(url_for("reports_page", **{"from": from_d, "to": to_d}))
        try:
            from io import BytesIO
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            buf = BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            width, height = A4
            y = height - 50
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Transactions Report")
            y -= 20
            c.setFont("Helvetica", 10)
            c.drawString(40, y, f"Range: {from_d or '-'} to {to_d or '-'}  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            y -= 20
            headers = ["ID", "Type", "Date", "Amount", "Payment", "Customer", "Paid", "Clr Date", "Clr By"]
            c.setFont("Helvetica-Bold", 9)
            x_positions = [40, 90, 135, 190, 245, 310, 410, 450, 510]
            for i, h in enumerate(headers):
                c.drawString(x_positions[i], y, h)
            y -= 12
            c.setFont("Helvetica", 9)
            for r in filtered:
                if y < 60:
                    c.showPage()
                    y = height - 50
                vals = [
                    str(r.get("id")), r.get("type") or "-", r.get("date") or "-",
                    f"{r.get('total'):.2f}", r.get("payment_method") or "-",
                    (r.get("customer_name") or r.get("description") or "-")[:22],
                    "Yes" if r.get("paid") else "No",
                    r.get("date_cleared") or "-",
                    r.get("payment_method_cleared") or "-",
                ]
                for i, val in enumerate(vals):
                    c.drawString(x_positions[i], y, val)
                y -= 12
            c.showPage()
            c.save()
            buf.seek(0)
            filename = f"report_{datetime.now().strftime('%Y-%m-%d')}.pdf"
            return send_file(buf, as_attachment=True, download_name=filename, mimetype="application/pdf")
        except Exception as e:
            flash(f"Export failed: {e}", "error")
            return redirect(url_for("reports_page", **{"from": from_d, "to": to_d}))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)


