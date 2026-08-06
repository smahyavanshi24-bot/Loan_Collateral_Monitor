import sqlite3
import pandas as pd
import os


DATABASE_PATH = "database/collateral.db"


def get_collateral_history():

    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        return pd.DataFrame()


    try:

        conn = sqlite3.connect(
            DATABASE_PATH
        )


        query = """
        SELECT *
        FROM collateral
        ORDER BY id DESC
        """


        df = pd.read_sql_query(
            query,
            conn
        )


        conn.close()


        return df


    except Exception as e:

        print(
            "Database Error:",
            e
        )

        return pd.DataFrame()



def get_latest_records():

    df = get_collateral_history()


    if df.empty:

        return df


    return df.head(10)



def get_summary():

    df = get_collateral_history()


    if df.empty:

        return {

            "total_records": 0,

            "total_collateral": 0,

            "average_cover": 0

        }


    return {

        "total_records":
            len(df),


        "total_collateral":
            df["collateral_value"].sum(),


        "average_cover":
            round(
                df["cover"].mean(),
                2
            )

    }