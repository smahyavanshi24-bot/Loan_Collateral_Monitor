import sqlite3
import os

DATABASE_PATH = "database/collateral.db"


# -------------------------------------------------
# Initialize Database
# -------------------------------------------------

def initialize_database():

    os.makedirs(
        "database",
        exist_ok=True
    )

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    # -----------------------------
    # Collateral History
    # -----------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS collateral_history

    (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        date TEXT,

        borrower TEXT,

        security TEXT,

        price REAL,

        shares INTEGER,

        loan_amount REAL,

        collateral_value REAL,

        cover REAL,

        required_cover REAL,

        status TEXT,

        shortfall_cover REAL,

        additional_collateral_required REAL

    )

    """)

    # -----------------------------
    # Alert History
    # -----------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS alert_history

    (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        date TEXT,

        borrower TEXT,

        security TEXT,

        alert_type TEXT,

        sent_time TEXT

    )

    """)

    conn.commit()
    conn.close()


# -------------------------------------------------
# Save Collateral Record
# -------------------------------------------------

def save_record(record):

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO collateral_history

    (

        date,

        borrower,

        security,

        price,

        shares,

        loan_amount,

        collateral_value,

        cover,

        required_cover,

        status,

        shortfall_cover,

        additional_collateral_required

    )

    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)

    """,

    (

        record["date"],

        record["borrower"],

        record["security"],

        record["price"],

        record["shares"],

        record["loan_amount"],

        record["collateral_value"],

        record["cover"],

        record["required_cover"],

        record["status"],

        record["shortfall_cover"],

        record["additional_collateral_required"]

    ))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Check if Alert Already Sent
# -------------------------------------------------

def alert_already_sent(date, borrower, security):

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute("""

    SELECT COUNT(*)

    FROM alert_history

    WHERE

    date=?

    AND borrower=?
    AND security=?

    """,

    (

        date,

        borrower,

        security

    ))

    count = cursor.fetchone()[0]

    conn.close()

    return count > 0


# -------------------------------------------------
# Save Alert History
# -------------------------------------------------

def save_alert(date, borrower, security):

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO alert_history

    (

        date,

        borrower,

        security,

        alert_type,

        sent_time

    )

    VALUES

    (?,?,?,?,time('now'))

    """,

    (

        date,

        borrower,

        security,

        "WhatsApp"

    ))

    conn.commit()

    conn.close()


# -------------------------------------------------
# Fetch History
# -------------------------------------------------

def get_history():

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM collateral_history

    ORDER BY id DESC

    """)

    rows = cursor.fetchall()

    conn.close()

    return rows