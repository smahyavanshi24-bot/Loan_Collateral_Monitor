# -*- coding: utf-8 -*-

import sqlite3
import os


# ============================================================
# DATABASE FILE
# ============================================================

DATABASE_FILE = "database/collateral.db"


# ============================================================
# GET DATABASE CONNECTION
# ============================================================

def get_connection():

    os.makedirs(
        "database",
        exist_ok=True
    )

    return sqlite3.connect(
        DATABASE_FILE
    )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # COLLATERAL HISTORY
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS collateral_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            date TEXT NOT NULL,

            borrower TEXT NOT NULL,

            security TEXT NOT NULL,

            price REAL,

            shares REAL,

            loan_amount REAL,

            collateral_value REAL,

            cover REAL,

            required_cover REAL,

            status TEXT,

            shortfall_cover REAL,

            additional_collateral_required REAL

        )
        """
    )

    # --------------------------------------------------------
    # ALERT HISTORY
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alert_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            date TEXT NOT NULL,

            borrower TEXT NOT NULL,

            security TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    connection.commit()

    connection.close()


# ============================================================
# SAVE COLLATERAL RECORD
# ============================================================

def save_record(record):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO collateral_history (

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

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

            record[
                "additional_collateral_required"
            ]

        )
    )

    connection.commit()

    connection.close()



# ============================================================
# GET RECORDS BY DATE
# ============================================================

def get_records_by_date(date):

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
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

        FROM collateral_history

        WHERE date = ?

        ORDER BY borrower, security
        """,

        (date,)
    )

    rows = cursor.fetchall()

    connection.close()

    return [dict(row) for row in rows]
# ============================================================
# UPDATE EXISTING COLLATERAL RECORD
# ============================================================

def update_record(record):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE collateral_history

        SET
            price = ?,
            shares = ?,
            loan_amount = ?,
            collateral_value = ?,
            cover = ?,
            required_cover = ?,
            status = ?,
            shortfall_cover = ?,
            additional_collateral_required = ?

        WHERE
            date = ?
            AND borrower = ?
            AND security = ?
        """,

        (

            record["price"],

            record["shares"],

            record["loan_amount"],

            record["collateral_value"],

            record["cover"],

            record["required_cover"],

            record["status"],

            record["shortfall_cover"],

            record[
                "additional_collateral_required"
            ],

            record["date"],

            record["borrower"],

            record["security"],

        )
    )

    connection.commit()

    connection.close()

# ============================================================
# GET HISTORICAL RECORDS
# ============================================================

def get_all_records():

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

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

        FROM collateral_history

        ORDER BY
            date DESC,
            borrower,
            security

        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# CHECK WHETHER ALERT WAS ALREADY SENT
# ============================================================

def alert_already_sent(
    date,
    borrower,
    security
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM alert_history

        WHERE date = ?

        AND borrower = ?

        AND security = ?

        """,

        (
            date,
            borrower,
            security
        )
    )

    result = cursor.fetchone()

    connection.close()

    return (
        result is not None
        and result[0] > 0
    )


# ============================================================
# SAVE ALERT
# ============================================================

def save_alert(
    date,
    borrower,
    security
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO alert_history (

            date,
            borrower,
            security

        )

        VALUES (?, ?, ?)

        """,

        (
            date,
            borrower,
            security
        )
    )

    connection.commit()

    connection.close()