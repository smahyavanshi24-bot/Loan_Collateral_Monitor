import pandas as pd


def calculate_cover_trend(df):

    """
    Historical Cover Trend Analysis

    Provides:
    - Daily borrower cover movement
    - Peak cover
    - Lowest cover
    - Trend direction
    - Warning status
    """

    if df.empty:

        return pd.DataFrame()


    trend = (

        df.groupby(
            [
                "date",
                "borrower"
            ]
        )

        .agg(

            total_collateral=(
                "collateral_value",
                "sum"
            ),

            loan_amount=(
                "loan_amount",
                "max"
            )

        )

        .reset_index()

    )


    trend["cover"] = (

        trend["total_collateral"]
        /
        trend["loan_amount"]

    ).round(2)



    # Sort by borrower and date

    trend = trend.sort_values(
        [
            "borrower",
            "date"
        ]
    )



    summary = []


    for borrower in trend["borrower"].unique():


        borrower_df = trend[
            trend["borrower"] == borrower
        ]


        highest_cover = (

            borrower_df["cover"]
            .max()

        )


        lowest_cover = (

            borrower_df["cover"]
            .min()

        )


        latest_cover = (

            borrower_df["cover"]
            .iloc[-1]

        )



        if latest_cover < lowest_cover + 0.10:

            status = "🟡 WATCH"

        else:

            status = "🟢 STABLE"



        summary.append(

            {

                "Borrower":
                borrower,


                "Latest Cover":
                latest_cover,


                "Highest Cover":
                highest_cover,


                "Lowest Cover":
                lowest_cover,


                "Trend Status":
                status

            }

        )


    return pd.DataFrame(summary)



def get_cover_history(df):

    """
    Returns borrower wise historical cover data
    for charting
    """

    if df.empty:

        return pd.DataFrame()


    history = (

        df.groupby(
            [
                "date",
                "borrower"
            ]
        )

        .agg(

            collateral_value=(
                "collateral_value",
                "sum"
            ),

            loan_amount=(
                "loan_amount",
                "max"
            )

        )

        .reset_index()

    )


    history["cover"] = (

        history["collateral_value"]
        /
        history["loan_amount"]

    ).round(2)


    return history