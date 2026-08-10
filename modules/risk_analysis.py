# -*- coding: utf-8 -*-

import pandas as pd


# ============================================================
# RISK ANALYSIS
# ============================================================

def calculate_risk(df):

    # ========================================================
    # NO DATA
    # ========================================================

    if df is None or df.empty:

        return pd.DataFrame()

    # ========================================================
    # COPY DATA
    # ========================================================

    result = df.copy()

    # ========================================================
    # DATE
    # ========================================================

    if "date" in result.columns:

        result["date"] = pd.to_datetime(
            result["date"],
            errors="coerce"
        )

        # Remove time component

        result["date"] = (
            result["date"]
            .dt.normalize()
        )

    # ========================================================
    # COVER
    # ========================================================

    if "cover" not in result.columns:

        result["cover"] = pd.NA

    result["cover"] = pd.to_numeric(
        result["cover"],
        errors="coerce"
    )

    # ========================================================
    # REQUIRED COVER
    #
    # IMPORTANT:
    # NEVER hardcode historical values.
    #
    # The required_cover stored with each record is
    # authoritative.
    # ========================================================

    if "required_cover" not in result.columns:

        result["required_cover"] = 1.00

    result["required_cover"] = pd.to_numeric(
        result["required_cover"],
        errors="coerce"
    )

    # Only use 1.00 if the value itself is missing.

    result["required_cover"] = (
        result["required_cover"]
        .fillna(1.00)
    )

    # ========================================================
    # BUFFER
    # ========================================================

    result["buffer"] = (
        result["cover"]
        -
        result["required_cover"]
    )

    result["buffer"] = (
        result["buffer"]
        .round(2)
    )

    # ========================================================
    # RISK STATUS
    # ========================================================

    def determine_risk(row):

        cover = row["cover"]

        required_cover = (
            row["required_cover"]
        )

        # ----------------------------------------------------
        # Invalid / unavailable cover
        # ----------------------------------------------------

        if (
            pd.isna(cover)
            or
            cover <= 0
        ):

            return "🔴 Action Required"

        # ----------------------------------------------------
        # Below required cover
        # ----------------------------------------------------

        if cover < required_cover:

            return "🔴 Action Required"

        # ----------------------------------------------------
        # Meets required cover
        # ----------------------------------------------------

        return "🟢 Safe"

    result["risk_status"] = (
        result.apply(
            determine_risk,
            axis=1
        )
    )

    # ========================================================
    # SORT
    # ========================================================

    if all(
        column in result.columns
        for column in [
            "date",
            "borrower",
            "security"
        ]
    ):

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
    # RESET INDEX
    # ========================================================

    result = result.reset_index(
        drop=True
    )

    # ========================================================
    # RETURN
    # ========================================================

    return result