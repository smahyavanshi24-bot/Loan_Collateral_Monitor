import pandas as pd


def run_stress_test(df, scenarios=None):

    """
    Collateral Stress Testing Engine

    Calculates impact of stock price fall on:
    - Collateral Value
    - Cover Ratio
    - Risk Status
    """


    if df.empty:
        return pd.DataFrame()


    if scenarios is None:

        scenarios = [
            0,
            -5,
            -10,
            -15,
            -20,
            -30
        ]


    results = []


    for borrower in df["borrower"].unique():


        borrower_df = df[
            df["borrower"] == borrower
        ]


        loan_amount = (
            borrower_df["loan_amount"]
            .max()
        )


        current_collateral = (
            borrower_df["collateral_value"]
            .sum()
        )


        for fall in scenarios:


            stress_factor = (
                1 + (fall / 100)
            )


            stressed_collateral = (
                current_collateral *
                stress_factor
            )


            stressed_cover = (
                stressed_collateral /
                loan_amount
            )


            if stressed_cover >= 2:

                status = "🟢 SAFE"


            elif stressed_cover >= 1.5:

                status = "🟡 WATCH"


            else:

                status = "🔴 ACTION REQUIRED"



            results.append(

                {

                    "Borrower":
                    borrower,


                    "Price Fall %":
                    f"{abs(fall)}%",


                    "Collateral Value":
                    round(
                        stressed_collateral,
                        2
                    ),


                    "Cover":
                    round(
                        stressed_cover,
                        2
                    ),


                    "Status":
                    status

                }

            )


    return pd.DataFrame(results)