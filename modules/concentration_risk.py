import pandas as pd


def calculate_concentration(df):

    """
    Collateral Concentration Risk Analysis

    Calculates:
    - Security wise collateral value
    - Percentage contribution
    - Concentration risk level
    """


    if df.empty:

        return pd.DataFrame()



    concentration = (

        df.groupby("security")

        .agg(

            collateral_value=(
                "collateral_value",
                "sum"
            )

        )

        .reset_index()

    )



    total_collateral = (

        concentration["collateral_value"]
        .sum()

    )



    concentration["contribution_%"] = (

        concentration["collateral_value"]
        /
        total_collateral
        *
        100

    ).round(2)



    def risk_level(x):

        if x >= 50:

            return "🔴 HIGH"

        elif x >= 30:

            return "🟡 MODERATE"

        else:

            return "🟢 LOW"



    concentration["risk_status"] = (

        concentration["contribution_%"]
        .apply(risk_level)

    )



    concentration = concentration.sort_values(

        by="contribution_%",

        ascending=False

    )



    return concentration