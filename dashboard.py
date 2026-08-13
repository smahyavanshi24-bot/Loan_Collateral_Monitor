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
from modules.market_monitor import add_market_monitoring
from modules.market_data import get_live_stock_data
from streamlit_autorefresh import st_autorefresh

from modules.share_movements import (
    initialize_share_movements,
    record_share_movement,
    get_share_movements,
    get_original_shares,
    get_current_shares,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Loan Collateral Risk Dashboard",
    page_icon="📊",
    layout="wide",
)

load_theme()

# ============================================================
# LIVE MARKET AUTO REFRESH
# ============================================================

st_autorefresh(
    interval=60 * 1000,
    key="live_market_refresh"
)


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
# LIVE MARKET COLLATERAL MONITORING
# ============================================================

st.subheader("🔴 Live Market Collateral Position")

st.caption(
    "Live intraday prices. Historical database records are not modified."
)

LIVE_SECURITIES = [
    {
        "borrower": "Everbest",
        "security": "JSW Energy",
        "shares": 2_533_300,
        "loan_amount": 120.00,
        "required_cover": 1.00,
    },
    {
        "borrower": "Everbest",
        "security": "JSW Steel",
        "shares": 1_096_000,
        "loan_amount": 120.00,
        "required_cover": 1.00,
    },
    {
        "borrower": "Siddeshwari",
        "security": "JSW Energy",
        "shares": 9_200_000,
        "loan_amount": 250.00,
        "required_cover": 1.50,
    },
    {
        "borrower": "Siddeshwari",
        "security": "Jindal Steel & Power",
        "shares": 1_600_000,
        "loan_amount": 250.00,
        "required_cover": 0.50,
    },
]

live_rows = []

for item in LIVE_SECURITIES:

    try:

        market_data = get_live_stock_data(
            item["security"]
        )

        live_price = market_data["price"]

        live_collateral_cr = (
            live_price
            * item["shares"]
            / 10_000_000
        )

        live_cover = (
            live_collateral_cr
            / item["loan_amount"]
        )

        buffer = (
            live_cover
            - item["required_cover"]
        )

        status = (
            "🟢 COMPLIED"
            if live_cover >= item["required_cover"]
            else "🔴 SHORTFALL"
        )

        live_rows.append(
            {
                "Borrower": item["borrower"],
                "Security": item["security"],
                "Live Price": live_price,
                "Shares": item["shares"],
                "Live Collateral (Cr)": live_collateral_cr,
                "Live Cover": live_cover,
                "Required Cover": item["required_cover"],
                "Buffer": buffer,
                "Status": status,
            }
        )

    except Exception as e:

        live_rows.append(
            {
                "Borrower": item["borrower"],
                "Security": item["security"],
                "Live Price": None,
                "Shares": item["shares"],
                "Live Collateral (Cr)": None,
                "Live Cover": None,
                "Required Cover": item["required_cover"],
                "Buffer": None,
                "Status": f"⚪ Price unavailable",
            }
        )

live_df = pd.DataFrame(live_rows)

# ============================================================
# FORMAT LIVE VALUES FOR DISPLAY
# ============================================================

display_live_df = live_df.copy()

display_live_df["Live Price"] = (
    display_live_df["Live Price"]
    .apply(
        lambda x: f"₹{x:,.2f}"
        if pd.notna(x)
        else "Unavailable"
    )
)

display_live_df["Live Collateral (Cr)"] = (
    display_live_df["Live Collateral (Cr)"]
    .apply(
        lambda x: f"₹{x:,.2f} Cr"
        if pd.notna(x)
        else "Unavailable"
    )
)

display_live_df["Live Cover"] = (
    display_live_df["Live Cover"]
    .apply(
        lambda x: f"{x:.2f}x"
        if pd.notna(x)
        else "—"
    )
)

display_live_df["Required Cover"] = (
    display_live_df["Required Cover"]
    .apply(
        lambda x: f"{x:.2f}x"
        if pd.notna(x)
        else "—"
    )
)

display_live_df["Buffer"] = (
    display_live_df["Buffer"]
    .apply(
        lambda x: f"{x:+.2f}x"
        if pd.notna(x)
        else "—"
    )
)

st.dataframe(
    display_live_df,
    use_container_width=True,
    hide_index=True,
)

# ============================================================
# LOAD HISTORICAL COLLATERAL DATA
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
    errors="coerce",
)

df = df[
    df["date"].notna()
].copy()

df["date"] = df["date"].dt.normalize()


# ============================================================
# REMOVE WEEKENDS
# ============================================================

df = df[
    df["date"].dt.weekday < 5
].copy()


# ============================================================
# SORT HISTORICAL DATA
# ============================================================

df = df.sort_values(
    ["date", "borrower", "security"]
).reset_index(
    drop=True
)


# ============================================================
# LATEST TRADING DATE
# ============================================================

latest_trading_date = df["date"].max()


# ============================================================
# RISK CALCULATION
#
# Historical records are NOT modified here.
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
        errors="coerce",
    )

    risk_df = risk_df[
        risk_df["date"].notna()
    ].copy()

    risk_df["date"] = (
        risk_df["date"]
        .dt.normalize()
    )

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
        errors="coerce",
    )

    market_df = market_df[
        market_df["date"].notna()
    ].copy()

    market_df["date"] = (
        market_df["date"]
        .dt.normalize()
    )

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
    "status",
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

    borrower_view["loan_amount"] = (
        borrower_view["loan_amount"]
        .apply(format_crore)
    )


if "collateral_value" in borrower_view.columns:

    borrower_view["collateral_value"] = (
        borrower_view["collateral_value"]
        .apply(format_crore)
    )


if "total_cover" in borrower_view.columns:

    borrower_view["total_cover"] = (
        borrower_view["total_cover"]
        .apply(format_cover)
    )


if "required_cover" in borrower_view.columns:

    borrower_view["required_cover"] = (
        borrower_view["required_cover"]
        .apply(format_cover)
    )


if "buffer" in borrower_view.columns:

    borrower_view["buffer"] = (
        borrower_view["buffer"]
        .apply(format_cover)
    )


st.dataframe(
    borrower_view,
    width="stretch",
    hide_index=True,
)


# ============================================================
# 2. SECURITY RISK MONITORING
#
# LATEST TRADING DATE ONLY
# ============================================================

st.subheader("🚦 Security Risk Monitoring")


security_columns = [
    "date",
    "borrower",
    "security",
    "cover",
    "required_cover",
    "buffer",
    "risk_status",
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

    security_view["cover"] = (
        security_view["cover"]
        .apply(format_cover)
    )


if "required_cover" in security_view.columns:

    security_view["required_cover"] = (
        security_view["required_cover"]
        .apply(format_cover)
    )


if "buffer" in security_view.columns:

    security_view["buffer"] = (
        security_view["buffer"]
        .apply(format_cover)
    )


st.dataframe(
    security_view,
    width="stretch",
    hide_index=True,
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
        "below required cover."
    )


    critical_columns = [
        "date",
        "borrower",
        "security",
        "cover",
        "required_cover",
        "buffer",
        "risk_status",
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


    if "cover" in critical_view.columns:

        critical_view["cover"] = (
            critical_view["cover"]
            .apply(format_cover)
        )


    if "required_cover" in critical_view.columns:

        critical_view["required_cover"] = (
            critical_view["required_cover"]
            .apply(format_cover)
        )


    if "buffer" in critical_view.columns:

        critical_view["buffer"] = (
            critical_view["buffer"]
            .apply(format_cover)
        )


    st.dataframe(
        critical_view,
        width="stretch",
        hide_index=True,
    )


else:

    st.success(
        "No collateral shortfall detected for the "
        "latest trading date."
    )


# ============================================================
# 4. MARKET MOVEMENT MONITORING
#
# LATEST TRADING DATE ONLY
# ============================================================

st.subheader("📉 Market Movement Monitoring")


market_columns = [
    "date",
    "borrower",
    "security",
    "price",
    "daily_change_%",
    "market_alert",
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
    hide_index=True,
)


# ============================================================
# 5. COLLATERAL STRESS TESTING
# ============================================================

st.subheader("📉 Collateral Stress Testing")


try:

    stress_df = run_stress_test(
        df.copy()
    )


    if (
        stress_df is not None
        and not stress_df.empty
    ):

        stress_view = stress_df.copy()


        # ----------------------------------------------------
        # FINANCIAL AMOUNTS
        # ----------------------------------------------------

        financial_columns = [
            "Current Collateral",
            "Stressed Collateral",
            "Loan Amount",
        ]


        for column in financial_columns:

            if column in stress_view.columns:

                stress_view[column] = (
                    stress_view[column]
                    .apply(format_crore)
                )


        # ----------------------------------------------------
        # COVER
        # ----------------------------------------------------

        cover_columns = [
            "Cover",
            "Required Cover",
        ]


        for column in cover_columns:

            if column in stress_view.columns:

                stress_view[column] = (
                    stress_view[column]
                    .apply(format_cover)
                )


        st.dataframe(
            stress_view,
            width="stretch",
            hide_index=True,
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
# 6. SHARE MOVEMENT TRACKING
#
# THIS IS THE ONLY SHARE MOVEMENT TABLE
#
# Historical collateral records are NEVER edited.
#
# Original Shares
# Current No. of Shares
# Movement Date
# Movement Type
# Movement Shares
# Resulting Shares
# ============================================================

st.divider()

st.subheader("📊 Share Movement Tracking")


st.caption(
    "Tracks additions and releases of pledged shares separately "
    "from historical collateral records. Historical data is never "
    "overwritten."
)


# ============================================================
# LOAD SHARE MOVEMENTS
# ============================================================

try:

    movement_df = get_share_movements()

except Exception as e:

    movement_df = pd.DataFrame()

    st.error(
        "Share movement data could not be loaded: "
        + str(e)
    )


# ============================================================
# BUILD SHARE MOVEMENT TABLE
# ============================================================

if movement_df is None:
    movement_df = pd.DataFrame()

if not movement_df.empty:

    movement_view = movement_df.copy()

    # --------------------------------------------------------
    # NORMALIZE COLUMN NAMES
    # --------------------------------------------------------

    movement_view.columns = [
        str(column).strip()
        for column in movement_view.columns
    ]

    # --------------------------------------------------------
    # BUILD DISPLAY TABLE
    # --------------------------------------------------------

    display_rows = []

    for _, movement in movement_view.iterrows():

        borrower = movement["borrower"]
        security = movement["security"]

        # TRUE ORIGINAL SHARE BALANCE
        original_shares = get_original_shares(
            df,
            borrower,
            security
        )

        # OPENING BALANCE BEFORE THIS MOVEMENT
        opening_shares = movement.get(
            "opening_shares",
            None
        )

        # RESULTING BALANCE AFTER THIS MOVEMENT
        resulting_shares = movement.get(
            "resulting_shares",
            None
        )

        # ----------------------------------------------------
        # FALLBACK CALCULATION
        # ----------------------------------------------------

        if pd.isna(opening_shares):

            opening_shares = original_shares

            previous_movements = movement_view[
                (movement_view["borrower"] == borrower)
                &
                (movement_view["security"] == security)
                &
                (
                    pd.to_datetime(
                        movement_view["movement_date"]
                    )
                    <
                    pd.to_datetime(
                        movement["movement_date"]
                    )
                )
            ].sort_values(
                ["movement_date", "id"]
            )

            for _, previous in previous_movements.iterrows():

                previous_type = str(
                    previous["movement_type"]
                ).upper()

                previous_shares = pd.to_numeric(
                    previous["movement_shares"],
                    errors="coerce"
                )

                if pd.isna(previous_shares):
                    continue

                if previous_type == "ADDITION":
                    opening_shares += int(previous_shares)

                elif previous_type == "RELEASE":
                    opening_shares -= int(previous_shares)

        # ----------------------------------------------------
        # RESULTING SHARES
        # ----------------------------------------------------

        if pd.isna(resulting_shares):

            movement_shares = pd.to_numeric(
                movement["movement_shares"],
                errors="coerce"
            )

            if pd.isna(movement_shares):
                movement_shares = 0

            movement_type = str(
                movement["movement_type"]
            ).upper()

            if movement_type == "ADDITION":
                resulting_shares = (
                    int(opening_shares)
                    + int(movement_shares)
                )

            elif movement_type == "RELEASE":
                resulting_shares = (
                    int(opening_shares)
                    - int(movement_shares)
                )

            else:
                resulting_shares = int(opening_shares)

        # ----------------------------------------------------
        # SIGNED MOVEMENT FOR DISPLAY
        # ----------------------------------------------------

        movement_shares = pd.to_numeric(
            movement["movement_shares"],
            errors="coerce"
        )

        if pd.isna(movement_shares):
            movement_shares = 0

        movement_type = str(
            movement["movement_type"]
        ).upper()

        if movement_type == "RELEASE":
            signed_movement = -abs(
                int(movement_shares)
            )
        else:
            signed_movement = abs(
                int(movement_shares)
            )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        movement_date = pd.to_datetime(
            movement["movement_date"],
            errors="coerce"
        )

        display_rows.append(
            {
                "Borrower": borrower,
                "Security": security,
                "Original Shares": int(original_shares),
                "Current No. of Shares": int(opening_shares),
                "Movement Date": (
                    movement_date.strftime("%d-%b-%Y")
                    if pd.notna(movement_date)
                    else "—"
                ),
                "Movement": movement_type,
                "Movement Shares": signed_movement,
                "Resulting Shares": int(resulting_shares),
            }
        )

    movement_display = pd.DataFrame(display_rows)

    # --------------------------------------------------------
    # FORMAT NUMBERS
    # --------------------------------------------------------

    movement_display["Original Shares"] = (
        movement_display["Original Shares"]
        .map(lambda x: f"{x:,}")
    )

    movement_display["Current No. of Shares"] = (
        movement_display["Current No. of Shares"]
        .map(lambda x: f"{x:,}")
    )

    movement_display["Movement Shares"] = (
        movement_display["Movement Shares"]
        .map(
            lambda x:
            f"{x:+,}"
        )
    )

    movement_display["Resulting Shares"] = (
        movement_display["Resulting Shares"]
        .map(lambda x: f"{x:,}")
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    st.dataframe(
        movement_display,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No share movements have been recorded yet."
    )


# ============================================================
# ADD FUTURE SHARE MOVEMENT
# ============================================================

st.subheader("➕ Record Future Share Movement")


st.caption(
    "Use this section whenever shares are additionally pledged "
    "or released. The movement is stored separately and does "
    "not rewrite historical collateral records."
)


# ============================================================
# AVAILABLE BORROWERS
# ============================================================

borrowers = sorted(
    df["borrower"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


if borrowers:

    movement_borrower = st.selectbox(
        "Borrower",
        borrowers,
        key="movement_borrower",
    )


    # --------------------------------------------------------
    # SECURITIES
    # --------------------------------------------------------

    securities = sorted(
        df.loc[
            df["borrower"] == movement_borrower,
            "security",
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


    if securities:

        movement_security = st.selectbox(
            "Security",
            securities,
            key="movement_security",
        )


        # ----------------------------------------------------
        # CURRENT SHARE BALANCE
        # ----------------------------------------------------

        try:

            current_share_balance = get_current_shares(
                movement_borrower,
                movement_security,
            )

            current_share_balance = int(
                current_share_balance
            )

        except Exception:

            security_history = df[
                (df["borrower"] == movement_borrower)
                &
                (df["security"] == movement_security)
            ].copy()


            if security_history.empty:

                current_share_balance = 0

            else:

                security_history = (
                    security_history
                    .sort_values("date")
                )

                current_share_balance = int(
                    security_history.iloc[-1]["shares"]
                )


        st.metric(
            "Current No. of Shares",
            f"{current_share_balance:,}",
        )


        # ----------------------------------------------------
        # MOVEMENT DATE
        # ----------------------------------------------------

        movement_date = st.date_input(
            "Movement Date",
            value=latest_trading_date.date(),
            key="future_movement_date",
        )


        # ----------------------------------------------------
        # MOVEMENT TYPE
        # ----------------------------------------------------

        movement_type = st.selectbox(
            "Movement Type",
            [
                "Addition",
                "Release",
            ],
            key="future_movement_type",
        )


        # ----------------------------------------------------
        # NUMBER OF SHARES
        # ----------------------------------------------------

        movement_quantity = st.number_input(
            "Movement Shares",
            min_value=1,
            step=1000,
            value=100000,
            key="future_movement_quantity",
        )


        # ----------------------------------------------------
        # PREVIEW
        # ----------------------------------------------------

        if movement_type == "Addition":

            resulting_shares = (
                current_share_balance
                + int(movement_quantity)
            )

            movement_symbol = "+"

        else:

            resulting_shares = (
                current_share_balance
                - int(movement_quantity)
            )

            movement_symbol = "−"


        if resulting_shares < 0:

            st.error(
                "Release cannot exceed the current number "
                "of pledged shares."
            )

        else:

            preview_columns = st.columns(3)


            preview_columns[0].metric(
                "Opening Shares",
                f"{current_share_balance:,}",
            )


            preview_columns[1].metric(
                "Movement",
                f"{movement_symbol}{int(movement_quantity):,}",
            )


            preview_columns[2].metric(
                "Resulting Shares",
                f"{resulting_shares:,}",
            )


            # ------------------------------------------------
            # SAVE MOVEMENT
            # ------------------------------------------------

            if st.button(
                "💾 Save Share Movement",
                type="primary",
                key="save_share_movement",
            ):

                if resulting_shares < 0:

                    st.error(
                        "Cannot save a release greater than "
                        "the current share balance."
                    )

                else:

                    try:

                        record_share_movement(
                            movement_date=str(
                                movement_date
                            ),
                            borrower=movement_borrower,
                            security=movement_security,
                            movement_type=movement_type,
                            movement_shares=int(
                                movement_quantity
                            ),
                        )


                        st.success(
                            "Share movement recorded successfully."
                        )


                        st.info(
                            f"{movement_borrower} | "
                            f"{movement_security} | "
                            f"{movement_type} | "
                            f"{int(movement_quantity):,} shares | "
                            f"Resulting shares: "
                            f"{resulting_shares:,}"
                        )


                        st.rerun()


                    except Exception as e:

                        st.error(
                            "Share movement could not be saved: "
                            + str(e)
                        )


# ============================================================
# 7. COMPLETE HISTORICAL DATA
#
# IMPORTANT:
# This table is the ORIGINAL historical database.
# Share movements do NOT rewrite it.
# ============================================================

st.divider()

st.subheader("📚 Complete Historical Data")


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
    "status",
]


available_historical_columns = [
    column
    for column in historical_columns
    if column in historical_view.columns
]


historical_view = historical_view[
    available_historical_columns
].sort_values(
    [
        "date",
        "borrower",
        "security",
    ],
    ascending=[
        False,
        True,
        True,
    ],
)


if "date" in historical_view.columns:

    historical_view["date"] = (
        historical_view["date"]
        .dt.strftime("%d-%b-%Y")
    )


if "price" in historical_view.columns:

    historical_view["price"] = (
        pd.to_numeric(
            historical_view["price"],
            errors="coerce",
        )
        .map(
            lambda x:
            f"₹{x:,.2f}"
            if pd.notna(x)
            else "—"
        )
    )


if "shares" in historical_view.columns:

    historical_view["shares"] = (
        pd.to_numeric(
            historical_view["shares"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
        .map(lambda x: f"{x:,}")
    )


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
    hide_index=True,
)


# ============================================================
# 8. HISTORICAL BORROWER COVER MOVEMENT
# ============================================================

st.subheader("📈 Historical Borrower Cover Movement")


cover_history = df.copy()


cover_history["collateral_value"] = pd.to_numeric(
    cover_history["collateral_value"],
    errors="coerce",
)


cover_history["loan_amount"] = pd.to_numeric(
    cover_history["loan_amount"],
    errors="coerce",
)


cover_history = cover_history[
    cover_history["date"].notna()
    &
    cover_history["collateral_value"].notna()
    &
    cover_history["loan_amount"].notna()
].copy()


cover_history = cover_history[
    cover_history["date"].dt.weekday < 5
].copy()


borrower_daily = (
    cover_history
    .groupby(
        [
            "date",
            "borrower",
        ],
        as_index=False,
    )
    .agg(
        collateral_value=(
            "collateral_value",
            "sum",
        ),
        loan_amount=(
            "loan_amount",
            "first",
        ),
    )
)


borrower_daily["total_cover"] = (
    borrower_daily["collateral_value"]
    /
    borrower_daily["loan_amount"]
)


borrower_daily["total_cover"] = pd.to_numeric(
    borrower_daily["total_cover"],
    errors="coerce",
)


borrower_daily = borrower_daily[
    borrower_daily["total_cover"].notna()
].copy()


borrower_daily = borrower_daily.sort_values(
    [
        "date",
        "borrower",
    ]
).reset_index(
    drop=True
)


cover_table = borrower_daily[
    [
        "date",
        "borrower",
        "total_cover",
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
    hide_index=True,
)


# ============================================================
# DATE-WISE COVER CHART
# ============================================================

if not borrower_daily.empty:

    chart_data = borrower_daily[
        [
            "date",
            "borrower",
            "total_cover",
        ]
    ].copy()


    chart_data["date"] = pd.to_datetime(
        chart_data["date"]
    ).dt.date


    chart_data = chart_data.rename(
        columns={
            "date": "Trading Date",
            "borrower": "Borrower",
            "total_cover": "Borrower Cover",
        }
    )


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
                    labelAngle=-45,
                ),
            ),

            y=alt.Y(
                "Borrower Cover:Q",
                title="Borrower Cover (x)",
                scale=alt.Scale(
                    domain=[
                        0,
                        3,
                    ],
                    nice=False,
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
                        3.00,
                    ],
                    format=".2f",
                ),
            ),

            color=alt.Color(
                "Borrower:N",
                title="Borrower",
            ),

            tooltip=[

                alt.Tooltip(
                    "Trading Date:T",
                    title="Date",
                    format="%d-%b-%Y",
                ),

                alt.Tooltip(
                    "Borrower:N",
                    title="Borrower",
                ),

                alt.Tooltip(
                    "Borrower Cover:Q",
                    title="Cover",
                    format=".2f",
                ),
            ],
        )
        .properties(
            height=450,
        )
    )


    st.altair_chart(
        cover_chart,
        width="stretch",
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(
    "Loan Collateral Risk Monitoring System | "
    "Historical collateral records are retained by trading date. "
    "Share additions and releases are tracked separately."
)

