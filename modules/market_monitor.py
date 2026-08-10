# -*- coding: utf-8 -*-

import pandas as pd

from modules.market_data import (
    get_market_monitoring_data
)


# ============================================================
# MARKET MOVEMENT MONITORING
# ============================================================

def add_market_monitoring(df):

    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()

    # ========================================================
    # REQUIRED COLUMNS
    # ========================================================

    required_columns = [
        "date",
        "borrower",
        "security",
        "price"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in result.columns
    ]

    if missing_columns:

        raise Exception(
            "Missing columns in market monitoring: "
            + ", ".join(missing_columns)
        )

    # ========================================================
    # DATE
    # ========================================================

    result["date"] = pd.to_datetime(
        result["date"],
        errors="coerce"
    )

    result["date"] = (
        result["date"]
        .dt.normalize()
    )

    result = result[
        result["date"].notna()
    ].copy()

    # ========================================================
    # PRICE
    # ========================================================

    result["price"] = pd.to_numeric(
        result["price"],
        errors="coerce"
    )

    # ========================================================
    # REMOVE INVALID PRICE RECORDS
    #
    # A market record with price 0 should never be shown.
    # ========================================================

    result = result[
        result["price"].notna()
        &
        (result["price"] > 0)
    ].copy()

    if result.empty:
        return result

    # ========================================================
    # INITIAL COLUMNS
    # ========================================================

    result["previous_close"] = pd.NA

    result["daily_change_%"] = pd.NA

    result["52_week_low"] = pd.NA

    result["distance_from_52_week_low_%"] = pd.NA

    result["market_alert"] = "🟢 Normal"

    # ========================================================
    # PROCESS EACH SECURITY
    # ========================================================

    for security_name in result["security"].dropna().unique():

        # ----------------------------------------------------
        # FETCH CURRENT NSE MARKET DATA
        # ----------------------------------------------------

        try:

            market_data = (
                get_market_monitoring_data(
                    security_name
                )
            )

        except Exception as e:

            print(
                f"Market monitoring error for "
                f"{security_name}: {e}"
            )

            continue

        if not market_data:

            continue

        # ----------------------------------------------------
        # Extract values
        # ----------------------------------------------------

        current_price = market_data.get(
            "price"
        )

        previous_close = market_data.get(
            "previous_close"
        )

        daily_change = market_data.get(
            "daily_change_%"
        )

        week_low = market_data.get(
            "52_week_low"
        )

        distance_from_low = market_data.get(
            "distance_from_52_week_low_%"
        )

        # ----------------------------------------------------
        # VALIDATE CURRENT PRICE
        # ----------------------------------------------------

        if (
            current_price is None
            or current_price <= 0
        ):

            continue

        # ====================================================
        # UPDATE ALL RECORDS OF THIS SECURITY
        # ====================================================

        security_mask = (
            result["security"]
            == security_name
        )

        result.loc[
            security_mask,
            "previous_close"
        ] = previous_close

        result.loc[
            security_mask,
            "daily_change_%"
        ] = daily_change

        result.loc[
            security_mask,
            "52_week_low"
        ] = week_low

        result.loc[
            security_mask,
            "distance_from_52_week_low_%"
        ] = distance_from_low

        # ====================================================
        # MARKET ALERT
        # ====================================================

        alert = "🟢 Normal"

        if (
            daily_change is not None
            and daily_change <= -5
        ):

            alert = "🔴 5%+ Fall"

        elif (
            daily_change is not None
            and daily_change <= -3
        ):

            alert = "🟠 Sharp Fall"

        elif (
            daily_change is not None
            and daily_change >= 5
        ):

            alert = "🟢 5%+ Rise"

        elif (
            daily_change is not None
            and daily_change >= 3
        ):

            alert = "🟢 Strong Rise"

        # ----------------------------------------------------
        # 52-WEEK LOW ALERT
        # ----------------------------------------------------

        if (
            distance_from_low is not None
            and distance_from_low <= 5
        ):

            alert = "🔴 Near 52-Week Low"

        # ----------------------------------------------------
        # UPDATE ALERT
        # ----------------------------------------------------

        result.loc[
            security_mask,
            "market_alert"
        ] = alert

    # ========================================================
    # NUMERIC CONVERSION
    # ========================================================

    numeric_columns = [
        "price",
        "previous_close",
        "daily_change_%",
        "52_week_low",
        "distance_from_52_week_low_%"
    ]

    for column in numeric_columns:

        if column in result.columns:

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce"
            )

    # ========================================================
    # ROUND VALUES
    # ========================================================

    result["price"] = (
        result["price"]
        .round(2)
    )

    result["previous_close"] = (
        result["previous_close"]
        .round(2)
    )

    result["daily_change_%"] = (
        result["daily_change_%"]
        .round(2)
    )

    result["52_week_low"] = (
        result["52_week_low"]
        .round(2)
    )

    result["distance_from_52_week_low_%"] = (
        result[
            "distance_from_52_week_low_%"
        ]
        .round(2)
    )

    # ========================================================
    # FINAL SORT
    # ========================================================

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
    ).reset_index(
        drop=True
    )

    # ========================================================
    # RETURN
    # ========================================================

    return result