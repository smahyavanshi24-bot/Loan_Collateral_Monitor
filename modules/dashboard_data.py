import sqlite3
import pandas as pd


DATABASE_PATH = "database/collateral.db"



def get_collateral_history():

    conn = sqlite3.connect(
        DATABASE_PATH
    )


    query = """
    SELECT

        date,
        borrower,
        loan_amount,
        security,
        shares,
        price,
        collateral_value,
        cover,
        required_cover,
        status

    FROM collateral_history

    ORDER BY date

    """


    df = pd.read_sql_query(
        query,
        conn
    )


    conn.close()


    return df




def get_borrower_summary():

    df = get_collateral_history()


    summary = (
        df.groupby(
            [
                "borrower",
                "loan_amount"
            ]
        )
        .agg(
            {
                "collateral_value":"sum"
            }
        )
        .reset_index()
    )


    summary["total_cover"] = (
        summary["collateral_value"]
        /
        summary["loan_amount"]
    )


    return summary




def get_risk_alerts():

    df = get_collateral_history()


    alerts = df[
        df["status"]
        .str.contains(
            "Shortfall"
        )
    ]


    return alerts