import pandas as pd


def run_stress_test(df, scenarios=None):
    """
    Collateral Stress Testing Engine

    Uses ONLY the latest available trading date.

    Calculates the impact of stock-price falls on:
    - Total collateral value
    - Borrower-level cover ratio
    - Risk status

    Assumption:
    A uniform percentage fall in all pledged securities
    reduces collateral value by the same percentage.
    """

    if df.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # DEFAULT STRESS SCENARIOS
    # --------------------------------------------------------

    if scenarios is None:
        scenarios = [
            0,
            -5,
            -10,
            -15,
            -20,
            -30
        ]

    # --------------------------------------------------------
    # COPY DATA
    # --------------------------------------------------------

    df = df.copy()

    # --------------------------------------------------------
    # NUMERIC CONVERSION
    # --------------------------------------------------------

    df["loan_amount"] = pd.to_numeric(
        df["loan_amount"],
        errors="coerce"
    )

    df["collateral_value"] = pd.to_numeric(
        df["collateral_value"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # REMOVE INVALID RECORDS
    # --------------------------------------------------------

    df = df[
        df["loan_amount"].notna()
        &
        df["collateral_value"].notna()
    ].copy()

    if df.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # NORMALIZE DATE
    # --------------------------------------------------------

    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        df = df[
            df["date"].notna()
        ].copy()

    if df.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # REMOVE WEEKENDS
    # --------------------------------------------------------

    df = df[
        df["date"].dt.weekday < 5
    ].copy()

    if df.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # LATEST TRADING DATE ONLY
    # --------------------------------------------------------

    latest_trading_date = df["date"].max()

    latest_df = df[
        df["date"] == latest_trading_date
    ].copy()

    if latest_df.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # BORROWER-WISE CURRENT POSITION
    # --------------------------------------------------------

    borrower_summary = (
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

            current_collateral=(
                "collateral_value",
                "sum"
            )
        )
    )

    # --------------------------------------------------------
    # REQUIRED BORROWER COVER
    #
    # Your current system uses 2.00x as the total
    # borrower-level required cover.
    # --------------------------------------------------------

    required_cover = 2.00

    # --------------------------------------------------------
    # STRESS CALCULATION
    # --------------------------------------------------------

    results = []

    for _, row in borrower_summary.iterrows():

        borrower = row["borrower"]

        loan_amount = row["loan_amount"]

        current_collateral = row[
            "current_collateral"
        ]

        if loan_amount <= 0:
            continue

        for fall in scenarios:

            # Example:
            # -10% -> 0.90
            # -30% -> 0.70

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

            # ------------------------------------------------
            # RISK STATUS
            # ------------------------------------------------

            if stressed_cover >= 2.10:

                status = "🟢 SAFE"

            elif stressed_cover >= 2.00:

                status = "🟡 WATCH"

            else:

                status = "🔴 ACTION REQUIRED"

            # ------------------------------------------------
            # RESULT
            # ------------------------------------------------

            results.append(
                {
                    "Trading Date":
                        latest_trading_date.strftime(
                            "%d-%b-%Y"
                        ),

                    "Borrower":
                        borrower,

                    "Price Fall %":
                        f"{abs(fall)}%",

                    "Current Collateral":
                        round(
                            current_collateral,
                            2
                        ),

                    "Stressed Collateral":
                        round(
                            stressed_collateral,
                            2
                        ),

                    "Loan Amount":
                        round(
                            loan_amount,
                            2
                        ),

                    "Cover":
                        round(
                            stressed_cover,
                            2
                        ),

                    "Required Cover":
                        required_cover,

                    "Status":
                        status
                }
            )

    return pd.DataFrame(results)