
import os
import sqlite3
from pathlib import Path

from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

# Version 1: Add Sale only
VERSION = "v1"

# Database path works in Windows and Docker.
DEFAULT_DB = Path(__file__).resolve().parent / "sales.db"
DB_PATH = Path(os.getenv("DB_PATH", str(DEFAULT_DB))).resolve()

# Create the database directory if it does not exist.
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db():
    connection = sqlite3.connect(str(DB_PATH), timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        """)


initialize_db()


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Sales System - V1</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f1f4f9;
            margin: 0;
            padding: 25px;
            color: #243047;
        }

        main {
            max-width: 650px;
            margin: 40px auto;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 3px 15px rgba(0, 0, 0, 0.08);
        }

        h1, h2 {
            color: #243b64;
        }

        .version {
            color: #64748b;
        }

        input, button {
            box-sizing: border-box;
            width: 100%;
            padding: 12px;
            margin: 10px 0;
        }

        input {
            border: 1px solid #cbd5e1;
            border-radius: 5px;
        }

        button {
            background: #243b64;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }

        button:hover {
            background: #172a4a;
        }

        .success {
            padding: 15px;
            background: #e6f6e9;
            color: #176534;
            border-radius: 6px;
        }

        .error {
            padding: 15px;
            background: #fee2e2;
            color: #991b1b;
            border-radius: 6px;
        }
    </style>
</head>

<body>
<main>
    <h1>Sales System</h1>

    <p>Registration Number: 24MIS0356</p>
    <p class="version">Version 1 — Add Sale</p>

    <h2>Record a New Sale</h2>

    {% if message %}
        <p class="{{ message_type }}">{{ message }}</p>
    {% endif %}

    <form method="post" action="{{ url_for('add_sale') }}">
        <input
            type="text"
            name="product"
            placeholder="Product Name"
            maxlength="100"
            required
        >

        <input
            type="number"
            name="quantity"
            placeholder="Quantity"
            min="1"
            step="1"
            required
        >

        <input
            type="number"
            name="price"
            placeholder="Price per Unit (₹)"
            min="0.01"
            step="0.01"
            required
        >

        <button type="submit">Record Sale</button>
    </form>

    <p>
        This version allows the user to enter sale details
        and save the record in the database.
    </p>
</main>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(
        HTML_PAGE,
        message=request.args.get("message", ""),
        message_type=request.args.get("type", "success")
    )


@app.post("/add")
def add_sale():
    product = request.form.get("product", "").strip()

    try:
        quantity = int(request.form.get("quantity", ""))
        price = float(request.form.get("price", ""))

        if (
            not product
            or len(product) > 100
            or quantity <= 0
            or quantity > 1_000_000
            or price <= 0
            or price > 1_000_000_000
        ):
            raise ValueError

    except (ValueError, TypeError, OverflowError):
        return (
            "Invalid input. Enter a product, positive whole-number "
            "quantity and valid unit price.",
            400
        )

    try:
        with get_db() as db:
            db.execute(
                """
                INSERT INTO sales (product, quantity, price)
                VALUES (?, ?, ?)
                """,
                (product, quantity, price)
            )

    except sqlite3.Error:
        app.logger.exception("Failed to record sale")
        return "Unable to save the sale. Please try again.", 500

    return redirect(url_for(
        "index",
        message="Sale recorded successfully!",
        type="success"
    ))


@app.get("/health")
def health():
    try:
        with get_db() as db:
            db.execute("SELECT 1").fetchone()

        return {"status": "healthy", "version": VERSION}, 200

    except sqlite3.Error:
        return {"status": "unhealthy"}, 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
