import sqlite3
import os
import sqlite3
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATABASE_FILE = os.path.join(
    BASE_DIR,
    "database",
    "collateral.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return sqlite3.connect(DATABASE_FILE)


# ============================================================
# INITIALIZE / MIGRATE SHARE MOVEMENT TABLE
# ============================================================

def initialize_share_movements():

    connection = get_connection()
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

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            movement_shares INTEGER,

            opening_shares INTEGER,

            resulting_shares INTEGER
        )
        """
    )

    # --------------------------------------------------------
    # Migrate existing table if columns are missing
    # --------------------------------------------------------

    existing_columns = {
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(share_movements)"
        ).fetchall()
    }

    required_columns = {
        "movement_shares": "INTEGER",
        "opening_shares": "INTEGER",
        "resulting_shares": "INTEGER"
    }

    for column, datatype in required_columns.items():

        if column not in existing_columns:

            cursor.execute(
                f"""
                ALTER TABLE share_movements
                ADD COLUMN {column} {datatype}
                """
            )

    connection.commit()
    connection.close()


# ============================================================
# GET ALL SHARE MOVEMENTS
# ============================================================

def get_share_movements():

    initialize_share_movements()

    connection = get_connection()

    query = """
        SELECT
            id,
            movement_date,
            borrower,
            security,
            movement_type,
            movement_shares,
            opening_shares,
            resulting_shares,
            reference,
            remarks,
            created_at
        FROM share_movements
        ORDER BY
            movement_date,
            borrower,
            security,
            id
    """

    df = pd.read_sql_query(
        query,
        connection
    )

    connection.close()

    if not df.empty:

        df["movement_date"] = pd.to_datetime(
            df["movement_date"],
            errors="coerce"
        )

    return df


# ============================================================
# GET TRUE ORIGINAL SHARES
# ============================================================

def get_original_shares(
    collateral_df,
    borrower,
    security
):
    """
    Return the TRUE original opening share balance.

    Priority:

    1. Earliest movement opening_shares.
    2. If no movement exists, use the earliest
       collateral-history share balance.

    IMPORTANT:
    Current shares from collateral history must NOT
    be treated as original shares when movement history
    already exists.
    """

    # --------------------------------------------------------
    # Check movement history first
    # --------------------------------------------------------

    movements = get_share_movements()

    if not movements.empty:

        movements = movements[
            (movements["borrower"] == borrower)
            &
            (movements["security"] == security)
        ].copy()

        movements = movements[
            movements["movement_date"].notna()
        ].copy()

        if not movements.empty:

            movements = movements.sort_values(
                ["movement_date", "id"]
            )

            first_movement = movements.iloc[0]

            opening_shares = first_movement[
                "opening_shares"
            ]

            if pd.notna(opening_shares):

                return int(opening_shares)

    # --------------------------------------------------------
    # No movement history
    # --------------------------------------------------------

    rows = collateral_df[
        (collateral_df["borrower"] == borrower)
        &
        (collateral_df["security"] == security)
    ].copy()

    if rows.empty:
        return 0

    rows["date"] = pd.to_datetime(
        rows["date"],
        errors="coerce"
    )

    rows = rows[
        rows["date"].notna()
    ].copy()

    if rows.empty:
        return 0

    rows = rows.sort_values("date")

    return int(
        rows.iloc[0]["shares"]
    )


# ============================================================
# CALCULATE SHARE POSITION AS OF A DATE
# ============================================================

def get_shares_as_of_date(
    collateral_df,
    borrower,
    security,
    calculation_date
):
    """
    Calculate the applicable share balance on a
    particular trading date.

    Formula:

        Original Shares
        + all additions up to date
        - all releases up to date

    Historical collateral records are NOT modified.
    """

    calculation_date = pd.to_datetime(
        calculation_date
    ).normalize()

    # --------------------------------------------------------
    # TRUE ORIGINAL BALANCE
    # --------------------------------------------------------

    original_shares = get_original_shares(
        collateral_df,
        borrower,
        security
    )

    if original_shares == 0:
        return 0

    # --------------------------------------------------------
    # MOVEMENTS
    # --------------------------------------------------------

    movements = get_share_movements()

    if movements.empty:
        return original_shares

    movements = movements[
        (movements["borrower"] == borrower)
        &
        (movements["security"] == security)
        &
        (movements["movement_date"].notna())
    ].copy()

    if movements.empty:
        return original_shares

    # --------------------------------------------------------
    # Only movements occurring on or before date
    # --------------------------------------------------------

    movements = movements[
        movements["movement_date"].dt.normalize()
        <= calculation_date
    ].copy()

    if movements.empty:
        return original_shares

    movements = movements.sort_values(
        ["movement_date", "id"]
    )

    # --------------------------------------------------------
    # Start from ORIGINAL shares
    # --------------------------------------------------------

    current_shares = original_shares

    # --------------------------------------------------------
    # Apply each movement exactly once
    # --------------------------------------------------------

    for _, movement in movements.iterrows():

        movement_type = str(
            movement["movement_type"]
        ).upper()

        movement_shares = movement[
            "movement_shares"
        ]

        if pd.isna(movement_shares):

            movement_shares = movement["shares"]

        movement_shares = int(
            movement_shares
        )

        if movement_type == "ADDITION":

            current_shares += movement_shares

        elif movement_type == "RELEASE":

            current_shares -= movement_shares

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if current_shares < 0:

        raise ValueError(
            f"Share balance became negative for "
            f"{borrower} / {security}"
        )

    return int(current_shares)


# ============================================================
# APPLY REVISED SHARE POSITIONS
# ============================================================

def apply_revised_share_positions(
    collateral_df
):
    """
    Create a calculation copy of collateral history
    using the applicable share balance for each date.

    IMPORTANT:

    The original historical database is NOT changed.

    Only the returned DataFrame is modified.
    """

    initialize_share_movements()

    df = collateral_df.copy()

    if df.empty:
        return df

    # --------------------------------------------------------
    # Normalize dates
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["date"] = df["date"].dt.normalize()

    # --------------------------------------------------------
    # Calculate applicable shares for every row
    # --------------------------------------------------------

    revised_shares = []

    for _, row in df.iterrows():

        revised = get_shares_as_of_date(
            collateral_df,
            row["borrower"],
            row["security"],
            row["date"]
        )

        revised_shares.append(
            revised
        )

    df["shares"] = revised_shares

    # --------------------------------------------------------
    # Recalculate collateral value
    # --------------------------------------------------------

    if "price" in df.columns:

        df["price"] = pd.to_numeric(
            df["price"],
            errors="coerce"
        )

        df["collateral_value"] = (
            df["price"]
            *
            df["shares"]
        )

    return df


# ============================================================
# RECORD NEW SHARE MOVEMENT
# ============================================================

def record_share_movement(
    collateral_df,
    borrower,
    security,
    movement_date,
    movement_type,
    movement_shares,
    reference=None,
    remarks=None
):
    """
    Record a future or current share movement.

    ADDITION:
        opening + movement

    RELEASE:
        opening - movement

    The movement becomes effective from the
    movement date itself.
    """

    initialize_share_movements()

    movement_date = pd.to_datetime(
        movement_date
    ).normalize()

    movement_type = str(
        movement_type
    ).upper()

    movement_shares = int(
        movement_shares
    )

    # --------------------------------------------------------
    # Validate movement type
    # --------------------------------------------------------

    if movement_type not in {
        "ADDITION",
        "RELEASE"
    }:

        raise ValueError(
            "movement_type must be ADDITION or RELEASE"
        )

    # --------------------------------------------------------
    # Validate number of shares
    # --------------------------------------------------------

    if movement_shares <= 0:

        raise ValueError(
            "movement_shares must be greater than zero"
        )

    # --------------------------------------------------------
    # Opening balance = balance immediately before
    # the movement date.
    # --------------------------------------------------------

    opening_shares = get_shares_as_of_date(
        collateral_df,
        borrower,
        security,
        movement_date - pd.Timedelta(days=1)
    )

    # --------------------------------------------------------
    # Calculate resulting balance
    # --------------------------------------------------------

    if movement_type == "ADDITION":

        resulting_shares = (
            opening_shares
            +
            movement_shares
        )

    else:

        resulting_shares = (
            opening_shares
            -
            movement_shares
        )

        if resulting_shares < 0:

            raise ValueError(
                "Release cannot exceed available shares."
            )

    # --------------------------------------------------------
    # Insert movement
    # --------------------------------------------------------

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO share_movements (

            movement_date,
            borrower,
            security,
            movement_type,
            shares,
            reference,
            remarks,
            movement_shares,
            opening_shares,
            resulting_shares

        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            movement_date.strftime("%Y-%m-%d"),
            borrower,
            security,
            movement_type,
            movement_shares,
            reference,
            remarks,
            movement_shares,
            opening_shares,
            resulting_shares
        )
    )

    connection.commit()

    movement_id = cursor.lastrowid

    connection.close()

    return {
        "id": movement_id,
        "movement_date": movement_date,
        "borrower": borrower,
        "security": security,
        "movement_type": movement_type,
        "movement_shares": movement_shares,
        "opening_shares": opening_shares,
        "resulting_shares": resulting_shares
    }


# ============================================================
# CURRENT SHARE POSITION
# ============================================================

def get_current_shares(
    collateral_df,
    borrower,
    security
):
    """
    Return the latest applicable share position.
    """

    if collateral_df.empty:
        return 0

    dates = pd.to_datetime(
        collateral_df["date"],
        errors="coerce"
    )

    dates = dates.dropna()

    if dates.empty:
        return 0

    latest_date = dates.max()

    return get_shares_as_of_date(
        collateral_df,
        borrower,
        security,
        latest_date
    )


# ============================================================
# BUILD DISPLAY TABLE
# ============================================================

def build_share_movement_table(
    collateral_df
):
    """
    Build the exact share movement table required
    for the dashboard.

    Columns:

    Borrower
    Security
    Original Shares
    Current No. of Shares
    Movement Date
    Movement
    Movement Shares
    Resulting Shares
    """

    initialize_share_movements()

    movements = get_share_movements()

    # --------------------------------------------------------
    # Base securities from collateral data
    # --------------------------------------------------------

    securities = (
        collateral_df[
            [
                "borrower",
                "security",
                "shares"
            ]
        ]
        .drop_duplicates(
            subset=[
                "borrower",
                "security"
            ]
        )
        .copy()
    )

    if securities.empty:
        return pd.DataFrame(
            columns=[
                "Borrower",
                "Security",
                "Original Shares",
                "Current No. of Shares",
                "Movement Date",
                "Movement",
                "Movement Shares",
                "Resulting Shares"
            ]
        )

    output = []

    for _, security_row in securities.iterrows():

        borrower = security_row["borrower"]
        security = security_row["security"]

        original = get_original_shares(
            collateral_df,
            borrower,
            security
        )

        # ----------------------------------------------------
        # Movement records
        # ----------------------------------------------------

        security_movements = movements[
            (movements["borrower"] == borrower)
            &
            (movements["security"] == security)
        ].copy()

        security_movements = security_movements.sort_values(
            ["movement_date", "id"]
        )

        # ----------------------------------------------------
        # No movement
        # ----------------------------------------------------

        if security_movements.empty:

            output.append(
                {
                    "Borrower": borrower,
                    "Security": security,
                    "Original Shares": original,
                    "Current No. of Shares": original,
                    "Movement Date": pd.NaT,
                    "Movement": "No movement",
                    "Movement Shares": None,
                    "Resulting Shares": original
                }
            )

            continue

        # ----------------------------------------------------
        # Movement rows
        # ----------------------------------------------------

        opening_balance = original

        for _, movement in security_movements.iterrows():

            movement_type = str(
                movement["movement_type"]
            ).upper()

            movement_shares = movement[
                "movement_shares"
            ]

            if pd.isna(movement_shares):

                movement_shares = movement["shares"]

            movement_shares = int(
                movement_shares
            )

            if movement_type == "ADDITION":

                signed_movement = movement_shares
                resulting = (
                    opening_balance
                    +
                    movement_shares
                )
                display_movement = "Addition"

            else:

                signed_movement = -movement_shares
                resulting = (
                    opening_balance
                    -
                    movement_shares
                )
                display_movement = "Release"

            output.append(
                {
                    "Borrower": borrower,
                    "Security": security,
                    "Original Shares": original,
                    "Current No. of Shares": opening_balance,
                    "Movement Date": movement["movement_date"],
                    "Movement": display_movement,
                    "Movement Shares": signed_movement,
                    "Resulting Shares": resulting
                }
            )

            opening_balance = resulting

    result = pd.DataFrame(output)

    if not result.empty:

        result = result.sort_values(
            [
                "Borrower",
                "Security",
                "Movement Date"
            ],
            na_position="last"
        ).reset_index(drop=True)

    return result