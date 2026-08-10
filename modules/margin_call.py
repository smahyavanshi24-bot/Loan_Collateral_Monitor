import pandas as pd


def calculate_margin_call(df):

    if df.empty:
        return pd.DataFrame()


    data = df.copy()


    # ========================================================
    # NUMERIC CONVERSION
    # ========================================================

    data["loan_amount"] = pd.to_numeric(
        data["loan_amount"],
        errors="coerce"
    )

    data["collateral_value"] = pd.to_numeric(
        data["collateral_value"],
        errors="coerce"
    )

    data["cover"] = pd.to_numeric(
        data["cover"],
        errors="coerce"
    )

    data["required_cover"] = pd.to_numeric(
        data["required_cover"],
        errors="coerce"
    )


    # ========================================================
    # LATEST DATE ONLY
    # ========================================================

    latest_date = data["date"].max()

    data = data[
        data["date"] == latest_date
    ].copy()


    # ========================================================
    # REQUIRED COLLATERAL
    #
    # Each security uses its OWN required cover.
    # ========================================================

    data["required_collateral"] = (
        data["loan_amount"]
        *
        data["required_cover"]
    )


    # ========================================================
    # COLLATERAL SHORTFALL
    # ========================================================

    data["collateral_shortfall"] = (
        data["required_collateral"]
        -
        data["collateral_value"]
    )


    # Negative shortfall means there is no margin call.

    data["collateral_shortfall"] = (
        data["collateral_shortfall"]
        .clip(lower=0)
    )


    # ========================================================
    # MARGIN CALL STATUS
    # ========================================================

    data["margin_call_status"] = data.apply(
        lambda row:
        "🔴 MARGIN CALL REQUIRED"
        if row["cover"] <
           row["required_cover"]
        else "🟢 NO ACTION",
        axis=1
    )


    # ========================================================
    # DISPLAY
    # ========================================================

    result = data[
        [
            "borrower",
            "security",
            "cover",
            "required_cover",
            "loan_amount",
            "collateral_value",
            "collateral_shortfall",
            "margin_call_status"
        ]
    ].copy()


    # ========================================================
    # FORMATTING
    # ========================================================

    result["cover"] = (
        result["cover"]
        .round(2)
        .astype(str)
        + "x"
    )


    result["required_cover"] = (
        result["required_cover"]
        .round(2)
        .astype(str)
        + "x"
    )


    result["loan_amount"] = (
        result["loan_amount"]
        .map(
            lambda x:
            f"₹{x:,.0f}"
        )
    )


    result["collateral_value"] = (
        result["collateral_value"]
        .map(
            lambda x:
            f"₹{x:,.0f}"
        )
    )


    result["collateral_shortfall"] = (
        result["collateral_shortfall"]
        .map(
            lambda x:
            f"₹{x:,.0f}"
        )
    )


    return result