# -*- coding: utf-8 -*-

import pandas as pd


# ============================================================
# CONSOLIDATED RISK ALERT ENGINE
# ============================================================

def generate_risk_alerts(
    risk_df,
    market_df=None,
    margin_df=None
):

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if risk_df is None or risk_df.empty:

        return pd.DataFrame()

    result = risk_df.copy()

    # ========================================================
    # NORMALIZE DATE
    # ========================================================

    if "date" in result.columns:

        result["date"] = pd.to_datetime(
            result["date"],
            errors="coerce"
        ).dt.normalize()

    # ========================================================
    # NUMERIC COLUMNS
    # ========================================================

    numeric_columns = [
        "cover",
        "required_cover",
        "buffer",
        "price",
        "collateral_value",
        "loan_amount"
    ]

    for column in numeric_columns:

        if column in result.columns:

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce"
            )

    # ========================================================
    # DEFAULT ALERT COLUMNS
    # ========================================================

    result["alert_level"] = "🟢 Normal"

    result["alert_reason"] = ""

    result["action_required"] = "No"

    # ========================================================
    # PROCESS EACH SECURITY
    # ========================================================

    for index, row in result.iterrows():

        alerts = []

        # ----------------------------------------------------
        # COVER CHECK
        # ----------------------------------------------------

        cover = row.get(
            "cover"
        )

        required_cover = row.get(
            "required_cover"
        )

        if (
            pd.notna(cover)
            and pd.notna(required_cover)
            and cover < required_cover
        ):

            alerts.append(
                "Collateral Cover Below Required Level"
            )

        # ----------------------------------------------------
        # MARKET DATA
        # ----------------------------------------------------

        market_row = None

        if (
            market_df is not None
            and not market_df.empty
        ):

            try:

                market_matches = market_df[
                    (
                        market_df["borrower"]
                        == row["borrower"]
                    )
                    &
                    (
                        market_df["security"]
                        == row["security"]
                    )
                    &
                    (
                        pd.to_datetime(
                            market_df["date"],
                            errors="coerce"
                        ).dt.normalize()
                        == row["date"]
                    )
                ]

                if not market_matches.empty:

                    market_row = (
                        market_matches.iloc[-1]
                    )

            except Exception:

                market_row = None

        # ====================================================
        # DAILY FALL CHECK
        # ====================================================

        if market_row is not None:

            daily_change = market_row.get(
                "daily_change_%"
            )

            if (
                pd.notna(daily_change)
                and daily_change <= -5
            ):

                alerts.append(
                    "Market Price Fall 5% or More"
                )

            elif (
                pd.notna(daily_change)
                and daily_change <= -3
            ):

                alerts.append(
                    "Sharp Market Price Fall"
                )

        # ====================================================
        # 52 WEEK LOW CHECK
        # ====================================================

        if market_row is not None:

            distance_low = market_row.get(
                "distance_from_52_week_low_%"
            )

            if (
                pd.notna(distance_low)
                and distance_low <= 5
            ):

                alerts.append(
                    "Price Near 52-Week Low"
                )

        # ====================================================
        # LOWER CIRCUIT CHECK
        # ====================================================

        if market_row is not None:

            market_alert = str(
                market_row.get(
                    "market_alert",
                    ""
                )
            )

            if (
                "Circuit" in market_alert
                and
                "Not Available" not in market_alert
            ):

                alerts.append(
                    "Lower Circuit Risk"
                )

        # ====================================================
        # DETERMINE ALERT LEVEL
        # ====================================================

        if (
            "Collateral Cover Below Required Level"
            in alerts
            or
            "Market Price Fall 5% or More"
            in alerts
            or
            "Lower Circuit Risk"
            in alerts
        ):

            result.at[
                index,
                "alert_level"
            ] = "🔴 Critical"

            result.at[
                index,
                "action_required"
            ] = "Yes"

        elif alerts:

            result.at[
                index,
                "alert_level"
            ] = "🟠 Warning"

            result.at[
                index,
                "action_required"
            ] = "Monitor"

        else:

            result.at[
                index,
                "alert_level"
            ] = "🟢 Normal"

            result.at[
                index,
                "action_required"
            ] = "No"

        # ====================================================
        # ALERT REASON
        # ====================================================

        if alerts:

            result.at[
                index,
                "alert_reason"
            ] = "; ".join(
                alerts
            )

        else:

            result.at[
                index,
                "alert_reason"
            ] = "No risk trigger"

    # ========================================================
    # FINAL SORT
    # ========================================================

    if "date" in result.columns:

        result = result.sort_values(
            [
                "date",
                "borrower",
                "security"
            ],
            ascending=[
                False,
                True,
                True
            ]
        )

    # ========================================================
    # RETURN
    # ========================================================

    return result.reset_index(
        drop=True
    )