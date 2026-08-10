import sqlite3
import os
import pandas as pd


# ============================================================
# ABSOLUTE DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "collateral.db"
)


# ============================================================
# GET ALL COLLATERAL HISTORY
# ============================================================

def get_collateral_history():

    print(
        "DATABASE USED:",
        DATABASE_PATH
    )

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    query = """
        SELECT
            id,
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
            date ASC,
            id ASC
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df


# ============================================================
# GET CURRENT BORROWER SUMMARY
# ============================================================

def get_borrower_summary():

    df = get_collateral_history()

    if df.empty:

        return pd.DataFrame()


    df["loan_amount"] = pd.to_numeric(
        df["loan_amount"],
        errors="coerce"
    )

    df["collateral_value"] = pd.to_numeric(
        df["collateral_value"],
        errors="coerce"
    )


    latest_date = df["date"].max()


    latest_df = df[
        df["date"] == latest_date
    ].copy()


    summary = (
        latest_df
        .groupby(
            "borrower",
            as_index=False
        )
        .agg(
            loan_amount=(
                "loan_amount",
                "first"
            ),

            collateral_value=(
                "collateral_value",
                "sum"
            )
        )
    )


    summary["total_cover"] = (
        summary["collateral_value"]
        /
        summary["loan_amount"]
    )


    summary["required_cover"] = 2.00


    summary["buffer"] = (
        summary["total_cover"]
        -
        summary["required_cover"]
    )


    summary["status"] = summary.apply(
        lambda row:
        "🟢 OK Complied"
        if row["total_cover"]
        >= row["required_cover"]
        else "🔴 Shortfall",
        axis=1
    )


    return summary


# ============================================================
# HISTORICAL BORROWER COVER
# ============================================================

def get_historical_borrower_cover():

    df = get_collateral_history()

    if df.empty:

        return pd.DataFrame()


    df["loan_amount"] = pd.to_numeric(
        df["loan_amount"],
        errors="coerce"
    )

    df["collateral_value"] = pd.to_numeric(
        df["collateral_value"],
        errors="coerce"
    )


    historical = (
        df.groupby(
            [
                "date",
                "borrower"
            ],
            as_index=False
        )
        .agg(
            loan_amount=(
                "loan_amount",
                "first"
            ),

            collateral_value=(
                "collateral_value",
                "sum"
            )
        )
    )


    historical["total_cover"] = (
        historical["collateral_value"]
        /
        historical["loan_amount"]
    )


    return historical.sort_values(
        [
            "date",
            "borrower"
        ]
    )