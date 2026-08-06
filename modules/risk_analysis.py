import pandas as pd



def calculate_risk(df):

    result = df.copy()


    result["buffer"] = (
        result["cover"]
        -
        result["required_cover"]
    )


    result["risk_status"] = result.apply(

        lambda x:

        "🔴 Action Required"

        if x["buffer"] < 0

        else

        "🟡 Watch"

        if x["buffer"] < 0.25

        else

        "🟢 Safe",

        axis=1

    )


    result["shortfall_cover"] = result.apply(

        lambda x:

        abs(x["buffer"])

        if x["buffer"] < 0

        else 0,

        axis=1

    )


    return result