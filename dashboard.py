import streamlit as st
import pandas as pd
import altair as alt

from modules.dashboard_theme import load_theme
from modules.dashboard_data import get_collateral_history
from modules.risk_analysis import calculate_risk
from modules.market_monitor import add_market_monitoring
from modules.borrower_summary import borrower_summary
from modules.stress_test import run_stress_test
from modules.formatting import format_crore, format_cover
from modules.share_movements import (
    initialize_share_movements,
    record_share_movement,
    get_share_movements,
    get_current_shares,
)

from modules.share_movements import (
    initialize_share_movements,
    record_share_movement,
    get_share_movements,
    get_current_shares,
)

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Loan Collateral Risk Dashboard",
    page_icon="📊",
    layout="wide"
)

load_theme()

# ============================================================
# INITIALIZE SHARE MOVEMENT SYSTEM
# ============================================================

initialize_share_movements()


# ============================================================
# HEADER
# ============================================================

st.title("📊 Loan Collateral Risk Monitoring System")

st.caption(
    "Credit Risk Dashboard | Collateral & Security Cover Monitoring"
)


# ============================================================
# LOAD COLLATERAL HISTORY
# ============================================================

df = get_collateral_history()

# ============================================================
# NO DATA CHECK
# ============================================================

if df.empty:
    st.warning("No collateral data available.")
    st.info(
        "Please run the collateral monitoring process first."
    )
    st.stop()


# ============================================================
# CLEAN DATA
# ============================================================

df = df.copy()


# ============================================================
# NORMALIZE DATE
# ============================================================

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df = df[df["date"].notna()].copy()

# Remove time completely
df["date"] = df["date"].dt.normalize()


# ============================================================
# REMOVE SATURDAY AND SUNDAY
# ============================================================

df = df[
    df["date"].dt.weekday < 5
].copy()


# ============================================================
# SORT DATA
# ============================================================

df = df.sort_values(
    ["date", "borrower", "security"]
).reset_index(drop=True)


# ============================================================
# LATEST TRADING DATE
# ============================================================

latest_trading_date = df["date"].max()


# ============================================================
# RISK CALCULATION
# ============================================================

risk_df = calculate_risk(
    df.copy()
)


# ============================================================
# NORMALIZE RISK DATE
# ============================================================

if "date" in risk_df.columns:

    risk_df["date"] = pd.to_datetime(
        risk_df["date"],
        errors="coerce"
    )

    risk_df = risk_df[
        risk_df["date"].notna()
    ].copy()

    risk_df["date"] = risk_df["date"].dt.normalize()

    risk_df = risk_df[
        risk_df["date"].dt.weekday < 5
    ].copy()


# ============================================================
# MARKET MONITORING
# ============================================================

market_df = add_market_monitoring(
    risk_df.copy()
)


# ============================================================
# NORMALIZE MARKET DATE
# ============================================================

if "date" in market_df.columns:

    market_df["date"] = pd.to_datetime(
        market_df["date"],
        errors="coerce"
    )

    market_df = market_df[
        market_df["date"].notna()
    ].copy()

    market_df["date"] = market_df["date"].dt.normalize()

    market_df = market_df[
        market_df["date"].dt.weekday < 5
    ].copy()


# ============================================================
# 1. BORROWER RISK SUMMARY
# ============================================================

st.subheader("👥 Borrower Risk Summary")


borrower_risk = borrower_summary(
    df.copy()
)


borrower_columns = [
    "borrower",
    "loan_amount",
    "collateral_value",
    "total_cover",
    "required_cover",
    "buffer",
    "status"
]


available_borrower_columns = [
    column
    for column in borrower_columns
    if column in borrower_risk.columns
]


borrower_view = borrower_risk[
    available_borrower_columns
].copy()

if "loan_amount" in borrower_view.columns:
    borrower_view["loan_amount"] = borrower_view[
        "loan_amount"
    ].apply(format_crore)

if "collateral_value" in borrower_view.columns:
    borrower_view["collateral_value"] = borrower_view[
        "collateral_value"
    ].apply(format_crore)

if "total_cover" in borrower_view.columns:
    borrower_view["total_cover"] = borrower_view[
        "total_cover"
    ].apply(format_cover)

if "required_cover" in borrower_view.columns:
    borrower_view["required_cover"] = borrower_view[
        "required_cover"
    ].apply(format_cover)

if "buffer" in borrower_view.columns:
    borrower_view["buffer"] = borrower_view[
        "buffer"
    ].apply(format_cover)

st.dataframe(
    borrower_view,
    width="stretch",
    hide_index=True
)


# ============================================================
# 2. SECURITY RISK MONITORING
# ONLY LATEST TRADING DATE
# ============================================================

st.subheader("🚦 Security Risk Monitoring")


security_columns = [
    "date",
    "borrower",
    "security",
    "cover",
    "required_cover",
    "buffer",
    "risk_status"
]


available_security_columns = [
    column
    for column in security_columns
    if column in risk_df.columns
]


security_view = risk_df[
    risk_df["date"] == latest_trading_date
].copy()


security_view = security_view[
    available_security_columns
]


security_view = security_view.sort_values(
    ["borrower", "security"]
)


if "date" in security_view.columns:

    security_view["date"] = (
        security_view["date"]
        .dt.strftime("%d-%b-%Y")
    )

if "cover" in security_view.columns:
    security_view["cover"] = security_view[
        "cover"
    ].apply(format_cover)

if "required_cover" in security_view.columns:
    security_view["required_cover"] = security_view[
        "required_cover"
    ].apply(format_cover)

if "buffer" in security_view.columns:
    security_view["buffer"] = security_view[
        "buffer"
    ].apply(format_cover)

st.dataframe(
    security_view,
    width="stretch",
    hide_index=True
)


st.caption(
    "Latest available trading date: "
    + latest_trading_date.strftime("%d-%b-%Y")
)


# ============================================================
# 3. IMMEDIATE ATTENTION REQUIRED
# ============================================================

st.subheader("🚨 Immediate Attention Required")


critical = risk_df[
    risk_df["risk_status"].astype(str)
    == "🔴 Action Required"
].copy()


critical_latest = critical[
    critical["date"] == latest_trading_date
].copy()


if not critical_latest.empty:

    st.error(
        f"{len(critical_latest)} security record(s) "
        "below required cover"
    )


    critical_columns = [
        "date",
        "borrower",
        "security",
        "cover",
        "required_cover",
        "buffer",
        "risk_status"
    ]


    available_critical_columns = [
        column
        for column in critical_columns
        if column in critical_latest.columns
    ]


    critical_view = critical_latest[
        available_critical_columns
    ].copy()


    if "date" in critical_view.columns:

        critical_view["date"] = (
            critical_view["date"]
            .dt.strftime("%d-%b-%Y")
        )


    st.dataframe(
        critical_view,
        width="stretch",
        hide_index=True
    )

else:

    st.success(
        "No collateral shortfall detected for the latest "
        "trading date."
    )


# ============================================================
# 4. MARKET MOVEMENT MONITORING
# ONLY LATEST TRADING DATE
# ============================================================

st.subheader("📉 Market Movement Monitoring")


market_columns = [
    "date",
    "borrower",
    "security",
    "price",
    "daily_change_%",
    "market_alert"
]


available_market_columns = [
    column
    for column in market_columns
    if column in market_df.columns
]


market_view = market_df[
    market_df["date"] == latest_trading_date
].copy()


market_view = market_view[
    available_market_columns
]


market_view = market_view.sort_values(
    ["borrower", "security"]
)


if "date" in market_view.columns:

    market_view["date"] = (
        market_view["date"]
        .dt.strftime("%d-%b-%Y")
    )


st.dataframe(
    market_view,
    width="stretch",
    hide_index=True
)
   
# ============================================================
# 5. COLLATERAL STRESS TESTING
# ============================================================

st.subheader("📉 Collateral Stress Testing")

try:

    stress_df = run_stress_test(
        df.copy()
    )

    if stress_df is not None and not stress_df.empty:

        stress_view = stress_df.copy()

        # ----------------------------------------------------
        # Convert financial amounts to ₹ Crore
        # ----------------------------------------------------

        if "Current Collateral" in stress_view.columns:
            stress_view["Current Collateral"] = (
                stress_view["Current Collateral"]
                .apply(format_crore)
            )

        if "Stressed Collateral" in stress_view.columns:
            stress_view["Stressed Collateral"] = (
                stress_view["Stressed Collateral"]
                .apply(format_crore)
            )

        if "Loan Amount" in stress_view.columns:
            stress_view["Loan Amount"] = (
                stress_view["Loan Amount"]
                .apply(format_crore)
            )

        # ----------------------------------------------------
        # Format cover ratios
        # ----------------------------------------------------

        if "Cover" in stress_view.columns:
            stress_view["Cover"] = (
                stress_view["Cover"]
                .apply(format_cover)
            )

        if "Required Cover" in stress_view.columns:
            stress_view["Required Cover"] = (
                stress_view["Required Cover"]
                .apply(format_cover)
            )

        st.dataframe(
            stress_view,
            width="stretch",
            hide_index=True
        )

    else:

        st.info(
            "No stress-test data available."
        )

except Exception as e:

    st.warning(
        "Stress testing could not be calculated: "
        + str(e)
    )


# ============================================================
# 8. COMPLETE HISTORICAL DATA
# ============================================================

st.subheader("📚 View Complete Historical Data")

historical_view = df.copy()

historical_columns = [
    "date",
    "borrower",
    "security",
    "price",
    "shares",
    "loan_amount",
    "collateral_value",
    "cover",
    "required_cover",
    "status"
]

available_historical_columns = [
    column
    for column in historical_columns
    if column in historical_view.columns
]

historical_view = historical_view[
    available_historical_columns
].sort_values(
    ["date", "borrower", "security"],
    ascending=[False, True, True]
)

# ------------------------------------------------------------
# Format date
# ------------------------------------------------------------

if "date" in historical_view.columns:

    historical_view["date"] = (
        historical_view["date"]
        .dt.strftime("%d-%b-%Y")
    )

# ------------------------------------------------------------
# Convert financial amounts to ₹ Crore
# ------------------------------------------------------------

if "loan_amount" in historical_view.columns:

    historical_view["loan_amount"] = (
        historical_view["loan_amount"]
        .apply(format_crore)
    )

if "collateral_value" in historical_view.columns:

    historical_view["collateral_value"] = (
        historical_view["collateral_value"]
        .apply(format_crore)
    )

# ------------------------------------------------------------
# Format cover ratios
# ------------------------------------------------------------

if "cover" in historical_view.columns:

    historical_view["cover"] = (
        historical_view["cover"]
        .apply(format_cover)
    )

if "required_cover" in historical_view.columns:

    historical_view["required_cover"] = (
        historical_view["required_cover"]
        .apply(format_cover)
    )

st.dataframe(
    historical_view,
    width="stretch",
    hide_index=True
)

# ============================================================
# 8. HISTORICAL BORROWER COVER MOVEMENT
# DATE-WISE ONLY
# ============================================================

st.subheader("📈 Historical Borrower Cover Movement")


cover_history = df.copy()


# ============================================================
# NUMERIC CONVERSION
# ============================================================

cover_history["collateral_value"] = pd.to_numeric(
    cover_history["collateral_value"],
    errors="coerce"
)


cover_history["loan_amount"] = pd.to_numeric(
    cover_history["loan_amount"],
    errors="coerce"
)


# ============================================================
# REMOVE INVALID RECORDS
# ============================================================

cover_history = cover_history[
    cover_history["date"].notna()
    &
    cover_history["collateral_value"].notna()
    &
    cover_history["loan_amount"].notna()
].copy()


# ============================================================
# REMOVE WEEKENDS
# ============================================================

cover_history = cover_history[
    cover_history["date"].dt.weekday < 5
].copy()


# ============================================================
# BORROWER DAILY COLLATERAL
# ============================================================

borrower_daily = (
    cover_history
    .groupby(
        ["date", "borrower"],
        as_index=False
    )
    .agg(
        collateral_value=(
            "collateral_value",
            "sum"
        ),
        loan_amount=(
            "loan_amount",
            "first"
        )
    )
)


# ============================================================
# BORROWER TOTAL COVER
# ============================================================

borrower_daily["total_cover"] = (
    borrower_daily["collateral_value"]
    /
    borrower_daily["loan_amount"]
)


# ============================================================
# CLEAN COVER
# ============================================================

borrower_daily["total_cover"] = pd.to_numeric(
    borrower_daily["total_cover"],
    errors="coerce"
)


borrower_daily = borrower_daily[
    borrower_daily["total_cover"].notna()
].copy()


# ============================================================
# SORT BY DATE
# ============================================================

borrower_daily = borrower_daily.sort_values(
    ["date", "borrower"]
).reset_index(drop=True)


# ============================================================
# HISTORICAL COVER TABLE
# ============================================================

cover_table = borrower_daily[
    [
        "date",
        "borrower",
        "total_cover"
    ]
].copy()


cover_table["date"] = (
    cover_table["date"]
    .dt.strftime("%d-%b-%Y")
)


cover_table["total_cover"] = (
    cover_table["total_cover"]
    .round(2)
)


st.dataframe(
    cover_table,
    width="stretch",
    hide_index=True
)


# ============================================================
# DATE-WISE COVER CHART
# ============================================================
#
# X-AXIS:
# Trading Date ONLY
#
# Y-AXIS:
# 0.00
# 0.25
# 0.50
# 0.75
# 1.00
# ...
# 3.00
#
# ============================================================

if not borrower_daily.empty:

    chart_data = borrower_daily[
        [
            "date",
            "borrower",
            "total_cover"
        ]
    ].copy()


    # Make absolutely sure date contains
    # no time information.

    chart_data["date"] = pd.to_datetime(
        chart_data["date"]
    ).dt.date


    chart_data = chart_data.rename(
        columns={
            "date": "Trading Date",
            "borrower": "Borrower",
            "total_cover": "Borrower Cover"
        }
    )


    # ========================================================
    # ALTair DATE-WISE CHART
    # ========================================================

    cover_chart = (
        alt.Chart(chart_data)
        .mark_line(
            point=True
        )
        .encode(

            x=alt.X(
                "Trading Date:T",
                title="Trading Date",
                axis=alt.Axis(
                    format="%d-%b-%Y",
                    labelAngle=-45
                )
            ),

            y=alt.Y(
                "Borrower Cover:Q",
                title="Borrower Cover (x)",

                scale=alt.Scale(
                    domain=[
                        0,
                        3
                    ],
                    nice=False
                ),

                axis=alt.Axis(
                    values=[
                        0,
                        0.25,
                        0.50,
                        0.75,
                        1.00,
                        1.25,
                        1.50,
                        1.75,
                        2.00,
                        2.25,
                        2.50,
                        2.75,
                        3.00
                    ],
                    format=".2f"
                )
            ),

            color=alt.Color(
                "Borrower:N",
                title="Borrower"
            ),

            tooltip=[
                alt.Tooltip(
                    "Trading Date:T",
                    title="Date",
                    format="%d-%b-%Y"
                ),

                alt.Tooltip(
                    "Borrower:N",
                    title="Borrower"
                ),

                alt.Tooltip(
                    "Borrower Cover:Q",
                    title="Cover",
                    format=".2f"
                )
            ]
        )
        .properties(
            height=450
        )
    )


    st.altair_chart(
        cover_chart,
        width="stretch"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(
    "Loan Collateral Risk Monitoring System | "
    "Historical records are retained by trading date."
)
