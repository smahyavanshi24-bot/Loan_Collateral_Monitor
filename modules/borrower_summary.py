import pandas as pd


def borrower_summary(df):

    if df.empty:
        return pd.DataFrame()


    data = df.copy()


    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    data["loan_amount"] = pd.to_numeric(
        data["loan_amount"],
        errors="coerce"
    )

    data["collateral_value"] = pd.to_numeric(
        data["collateral_value"],
        errors="coerce"
    )

    data["required_cover"] = pd.to_numeric(
        data["required_cover"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # Latest date only for current borrower position
    # --------------------------------------------------------

    latest_date = data["date"].max()


    latest = data[
        data["date"] == latest_date
    ].copy()


    # --------------------------------------------------------
    # Borrower-level summary
    #
    # IMPORTANT:
    # We calculate the required collateral by security using
    # the required cover applicable to EACH security.
    # --------------------------------------------------------

    latest["required_collateral"] = (
        latest["loan_amount"]
        *
        latest["required_cover"]
    )


    summary = (
        latest
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
            ),

            required_collateral=(
                "required_collateral",
                "sum"
            )
        )
    )


    # --------------------------------------------------------
    # Actual total cover
    # --------------------------------------------------------

    summary["total_cover"] = (
        summary["collateral_value"]
        /
        summary["loan_amount"]
    )


    # --------------------------------------------------------
    # Effective required cover
    #
    # This is based on the actual required collateral from
    # the individual securities, not a hardcoded 2.00x.
    # --------------------------------------------------------

    summary["required_cover"] = (
        summary["required_collateral"]
        /
        summary["loan_amount"]
    )


    # --------------------------------------------------------
    # Buffer
    # --------------------------------------------------------

    summary["buffer"] = (
        summary["total_cover"]
        -
        summary["required_cover"]
    )


    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    summary["status"] = summary.apply(
        lambda row:
        "🔴 Action Required"
        if row["total_cover"] <
           row["required_cover"]
        else "🟢 OK Complied",
        axis=1
    )


    # --------------------------------------------------------
    # Remove helper column
    # --------------------------------------------------------

    summary = summary.drop(
        columns=[
            "required_collateral"
        ]
    )


    return summary