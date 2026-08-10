import sqlite3
import os
import pandas as pd


DATABASE_FILE = os.path.join(
    "database",
    "collateral.db"
)


# ============================================================
# INITIALIZE SHARE MOVEMENT TABLE
# ============================================================

def initialize_share_movements():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS share_movements (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            movement_date TEXT NOT NULL,

            borrower TEXT NOT NULL,

            security TEXT NOT NULL,

            movement_type TEXT NOT NULL,

            shares INTEGER NOT NULL,

            reference TEXT,

            remarks TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    connection.commit()
    connection.close()


# ============================================================
# RECORD SHARE MOVEMENT
# ============================================================

def record_share_movement(
    movement_date,
    borrower,
    security,
    movement_type,
    shares,
    reference="",
    remarks=""
):

    movement_type = movement_type.upper().strip()

    if movement_type not in [
        "ADD",
        "RELEASE"
    ]:
        raise ValueError(
            "Movement type must be ADD or RELEASE."
        )

    shares = int(shares)

    if shares <= 0:
        raise ValueError(
            "Shares must be greater than zero."
        )

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO share_movements
        (
            movement_date,
            borrower,
            security,
            movement_type,
            shares,
            reference,
            remarks
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(movement_date),
            borrower,
            security,
            movement_type,
            shares,
            reference,
            remarks
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# GET ALL SHARE MOVEMENTS
# ============================================================

def get_share_movements():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    df = pd.read_sql_query(
        """
        SELECT
            id,
            movement_date,
            borrower,
            security,
            movement_type,
            shares,
            reference,
            remarks,
            created_at
        FROM share_movements
        ORDER BY
            movement_date DESC,
            id DESC
        """,
        connection
    )

    connection.close()

    return df


# ============================================================
# CALCULATE NET SHARE MOVEMENT
# ============================================================

def get_net_share_movement(
    borrower,
    security
):

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    query = """
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN movement_type = 'ADD'
                        THEN shares

                        WHEN movement_type = 'RELEASE'
                        THEN -shares

                        ELSE 0
                    END
                ),
                0
            )
        FROM share_movements

        WHERE borrower = ?
        AND security = ?
    """

    result = connection.execute(
        query,
        (
            borrower,
            security
        )
    ).fetchone()

    connection.close()

    return int(result[0] or 0)


# ============================================================
# GET CURRENT SHARES
# ============================================================

def get_current_shares(
    historical_shares,
    borrower,
    security
):

    net_movement = get_net_share_movement(
        borrower,
        security
    )

    current_shares = (
        int(historical_shares)
        + net_movement
    )

    return max(
        0,
        current_shares
    )