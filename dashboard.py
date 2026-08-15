import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from zoneinfo import ZoneInfo

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
from modules.live_collateral import get_active_live_securities

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

from datetime import datetime
from zoneinfo import ZoneInfo

refresh_time = datetime.now(
    ZoneInfo("Asia/Kolkata")
)

st.caption(
    f"🔄 Dashboard refreshed: "
    f"{refresh_time.strftime('%d-%b-%Y %H:%M:%S')} IST"
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
# LIVE MARKET COLLATERAL POSITION
# ============================================================

st.subheader("🟢 Live Market Collateral Position")

st.caption(
    "Live market prices from the current loan/security master. "
    "Historical database records are not modified."
)

LIVE_SECURITIES = get_active_live_securities()


# ------------------------------------------------------------
# INDIA TRADING DATE
# ------------------------------------------------------------

# ------------------------------------------------------------
# INDIA TRADING DATE
# ------------------------------------------------------------

today_ist = pd.Timestamp(
    datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date()
)

# If today is Saturday/Sunday, use the
# latest weekday trading date.
live_trading_date = today_ist

while live_trading_date.weekday() >= 5:
    live_trading_date -= pd.Timedelta(days=1)

# ------------------------------------------------------------
# FETCH LIVE DATA ONCE PER SECURITY
# ------------------------------------------------------------

live_rows = []

for item in LIVE_SECURITIES:

    try:

        # ----------------------------------------------------
        # NSE SYMBOL
        # ----------------------------------------------------

        nse_symbol = str(
            item.get("nse_symbol") or ""
        ).strip()

        if not nse_symbol:

            raise Exception(
                "NSE Symbol is missing"
            )


        # ----------------------------------------------------
        # MARKET DATA
        # ----------------------------------------------------

        market_data = get_live_stock_data(
            nse_symbol
        )

        if not market_data:

            raise Exception(
                "Market data unavailable"
            )


        live_price = market_data.get(
            "price"
        )

        previous_close = market_data.get(
            "previous_close"
        )

        daily_change = market_data.get(
            "daily_change_%"
        )

        last_updated = market_data.get(
            "last_updated",
            "Unavailable"
        )

        week_52_low = market_data.get(
            "52_week_low"
        )

        distance_from_low = market_data.get(
            "distance_from_52_week_low_%"
        )


        if (
            live_price is None
            or live_price <= 0
        ):

            raise Exception(
                "Invalid live price"
            )


        # ----------------------------------------------------
        # CURRENT SHARES
        # ----------------------------------------------------

        shares = int(
            item["current_shares"]
        )


        # ----------------------------------------------------
        # LOAN AMOUNT
        # ----------------------------------------------------

        loan_amount = float(
            item["loan_amount"]
        )


        # ----------------------------------------------------
        # IMPORTANT:
        #
        # BORROWER LEVEL REQUIRED COVER
        #
        # Example:
        # ABC Ltd = 2.50x
        # ----------------------------------------------------

        borrower_required_cover = float(
            item["required_cover"]
        )

        # ----------------------------------------------------
        # SECURITY LEVEL REQUIRED COVER
        #
        # Example:
        # Kalyan = 1.00x
        # Mindspace = 1.00x
        # ----------------------------------------------------

        security_required_cover = float(
            item.get(
                "security_required_cover",
                1.0
            )
        )


        # ----------------------------------------------------
        # LIVE COLLATERAL
        # ----------------------------------------------------

        collateral_cr = (
            live_price
            * shares
            / 10_000_000
        )


        # ----------------------------------------------------
        # SECURITY-WISE COVER
        # ----------------------------------------------------

        security_cover = (
            collateral_cr
            / loan_amount
            if loan_amount > 0
            else None
        )


        # ----------------------------------------------------
        # SECURITY-WISE BUFFER
        #
        # Compare security cover against
        # security-specific requirement.
        # ----------------------------------------------------

        security_buffer = (
            security_cover
            - security_required_cover
            if security_cover is not None
            else None
        )


        # ----------------------------------------------------
        # SECURITY-WISE STATUS
        # ----------------------------------------------------

        if security_cover is None:

            risk_status = (
                "⚪ Price Unavailable"
            )

        elif (
            security_cover
            >= security_required_cover
        ):

            risk_status = (
                "🟢 Safe"
            )

        else:

            risk_status = (
                "🔴 Action Required"
            )


        # ----------------------------------------------------
        # MARKET ALERT
        # ----------------------------------------------------

        market_alert = "🟢 Normal"


        if (
            daily_change is not None
            and daily_change <= -5
        ):

            market_alert = (
                "🔴 5%+ Fall"
            )

        elif (
            daily_change is not None
            and daily_change <= -3
        ):

            market_alert = (
                "🟡 Sharp Fall"
            )

        elif (
            daily_change is not None
            and daily_change >= 5
        ):

            market_alert = (
                "🟢 5%+ Rise"
            )

        elif (
            daily_change is not None
            and daily_change >= 3
        ):

            market_alert = (
                "🟢 Strong Rise"
            )


        if (
            distance_from_low is not None
            and distance_from_low <= 5
        ):

            market_alert = (
                "🔴 Near 52-Week Low"
            )


        # ----------------------------------------------------
        # STORE LIVE ROW
        # ----------------------------------------------------

        live_rows.append(
    {
        "date": live_trading_date,
        "borrower": item["borrower"],
        "security": item["security"],
        "nse_symbol": nse_symbol,
        "isin": item.get("isin", ""),
        "price": live_price,
        "previous_close": previous_close,
        "daily_change_%": daily_change,
        "52_week_low": week_52_low,
        "distance_from_52_week_low_%": distance_from_low,
        "last_updated": last_updated,
        "shares": shares,
        "loan_amount": loan_amount,
        "collateral_value": collateral_cr,

        # Security-wise cover
        "cover": security_cover,

        # Borrower-wise stipulated cover
        "borrower_required_cover": borrower_required_cover,

        # Security-wise stipulated cover
        "required_cover": security_required_cover,

        # Security-wise buffer
        "buffer": security_buffer,

        "risk_status": risk_status,
        "market_alert": market_alert,
    }
)            

    except Exception as e:

        print(
            f"Live market error for "
            f"{item.get('security', 'Unknown')}: {e}"
        )


        # ----------------------------------------------------
        # KEEP SECURITY VISIBLE EVEN IF PRICE UNAVAILABLE
        # ----------------------------------------------------

        live_rows.append(
    {
        "date": live_trading_date,
        "borrower": item["borrower"],
        "security": item["security"],
        "nse_symbol": item.get("nse_symbol", ""),
        "isin": item.get("isin", ""),
        "price": None,
        "previous_close": None,
        "daily_change_%": None,
        "52_week_low": None,
        "distance_from_52_week_low_%": None,
        "last_updated": "Unavailable",
        "shares": int(item["current_shares"]),
        "loan_amount": float(item["loan_amount"]),
        "collateral_value": None,
        "cover": None,

        # IMPORTANT:
        # Borrower-level required cover
        "borrower_required_cover": float(
            item.get("required_cover", 2.5)
            
        ),

            
        # IMPORTANT:
        # Security-level required cover
        "required_cover": float(
            item.get("security_required_cover",1.0)
        ),

        "buffer": None,
        "risk_status": "⚪ Price Unavailable",
        "market_alert": "⚪ Price Unavailable",
    }

            
)

# ------------------------------------------------------------
# LIVE DATAFRAME
# ------------------------------------------------------------

live_df = pd.DataFrame(
    live_rows
)

# ============================================================
# LIVE DISPLAY TABLE
# ============================================================

display_live_df = live_df[
    [
        "borrower",
        "security",
        "nse_symbol",
        "price",
        "last_updated",
        "shares",
        "collateral_value",
        "cover",
        "required_cover",
        "buffer",
        "risk_status",
    ]
].copy()


display_live_df = display_live_df.rename(
    columns={
        "borrower":
            "Borrower",

        "security":
            "Security",

        "nse_symbol":
            "NSE Symbol",

        "price":
            "Live Price",

        "last_updated":
            "Market Data Time",

        "shares":
            "Shares",

        "collateral_value":
            "Live Collateral (Cr)",

        "cover":
            "Security Cover",

        "required_cover":
            "Required Security Cover",

        "buffer":
            "Security Buffer",

        "risk_status":
            "Status",
    }
)

# ------------------------------------------------------------
# FORMAT MARKET DATA TIME
# ------------------------------------------------------------

def format_market_data_time(value):

    if pd.isna(value):
        return "Unavailable"

    value = str(value)

    if value == "Unavailable":
        return value

    try:

        timestamp = pd.to_datetime(
            value,
            errors="coerce"
        )

        if pd.isna(timestamp):
            return value

        # Daily-close timestamp
        if timestamp.hour == 0 and timestamp.minute == 0 and timestamp.second == 0:
            return timestamp.strftime("%d-%b-%Y")

        # Intraday timestamp
        return timestamp.strftime("%d-%b-%Y %H:%M:%S")

    except Exception:

        return value


display_live_df["Market Data Time"] = (
    display_live_df["Market Data Time"]
    .apply(format_market_data_time)
)

# ------------------------------------------------------------
# FORMAT PRICE
# ------------------------------------------------------------

display_live_df["Live Price"] = (
    display_live_df["Live Price"]
    .apply(
        lambda x:
        f"₹{x:,.2f}"
        if pd.notna(x)
        else "Unavailable"
    )
)


# ------------------------------------------------------------
# FORMAT SHARES
# ------------------------------------------------------------

display_live_df["Shares"] = (
    display_live_df["Shares"]
    .apply(
        lambda x:
        f"{int(x):,}"
        if pd.notna(x)
        else "—"
    )
)


# ------------------------------------------------------------
# FORMAT COLLATERAL
# ------------------------------------------------------------

display_live_df["Live Collateral (Cr)"] = (
    display_live_df["Live Collateral (Cr)"]
    .apply(
        lambda x:
        f"₹{x:,.2f} Cr"
        if pd.notna(x)
        else "Unavailable"
    )
)


# ------------------------------------------------------------
# FORMAT SECURITY COVER
# ------------------------------------------------------------

display_live_df["Security Cover"] = (
    display_live_df["Security Cover"]
    .apply(
        lambda x:
        f"{x:.2f}x"
        if pd.notna(x)
        else "—"
    )
)


# ------------------------------------------------------------
# FORMAT REQUIRED SECURITY COVER
# ------------------------------------------------------------

display_live_df["Required Security Cover"] = (
    display_live_df["Required Security Cover"]
    .apply(
        lambda x:
        f"{x:.2f}x"
        if pd.notna(x)
        else "—"
    )
)


# ------------------------------------------------------------
# FORMAT BUFFER
# ------------------------------------------------------------

display_live_df["Security Buffer"] = (
    display_live_df["Security Buffer"]
    .apply(
        lambda x:
        f"{x:+.2f}x"
        if pd.notna(x)
        else "—"
    )
)


# ------------------------------------------------------------
# DISPLAY
# ------------------------------------------------------------

st.dataframe(
    display_live_df[
        [
            "Borrower",
            "Security",
            "NSE Symbol",
            "Live Price",
            "Market Data Time",
            "Shares",
            "Live Collateral (Cr)",
            "Security Cover",
            "Required Security Cover",
            "Security Buffer",
            "Status",
        ]
    ],
    width="stretch",
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
# 1. LIVE BORROWER RISK SUMMARY
# ============================================================

st.subheader("👥 Borrower Risk Summary")

# ------------------------------------------------------------
# BUILD LIVE BORROWER SUMMARY
# ------------------------------------------------------------
#
# IMPORTANT:
# This section uses ONLY the current live database-driven
# collateral data in live_df.
#
# It does NOT use the old historical collateral database.
# Therefore newly added borrowers such as ABC Ltd will appear
# here automatically.
# ------------------------------------------------------------

live_borrower_rows = []

if not live_df.empty:

    for borrower_name, borrower_data in live_df.groupby(
        "borrower",
        dropna=False
    ):

        # ----------------------------------------------------
        # Keep rows where live collateral was successfully
        # calculated.
        # ----------------------------------------------------

        valid_data = borrower_data[
            pd.to_numeric(
                borrower_data["collateral_value"],
                errors="coerce"
            ).notna()
        ].copy()


        if valid_data.empty:
            continue


        # ----------------------------------------------------
        # Loan amount
        #
        # Loan amount is repeated for every security.
        # Therefore DO NOT SUM it.
        # ----------------------------------------------------

        loan_amount_cr = pd.to_numeric(
            valid_data["loan_amount"],
            errors="coerce"
        ).dropna()


        if loan_amount_cr.empty:
            continue


        loan_amount_cr = float(
            loan_amount_cr.iloc[0]
        )


        # ----------------------------------------------------
        # Total live collateral
        # ----------------------------------------------------

        collateral_value_cr = pd.to_numeric(
            valid_data["collateral_value"],
            errors="coerce"
        ).sum()


        collateral_value_cr = float(
            collateral_value_cr
        )


        # ----------------------------------------------------
        # Total borrower cover
        # ----------------------------------------------------

        if loan_amount_cr > 0:

            total_cover = (
                collateral_value_cr
                / loan_amount_cr
            )

        else:

            total_cover = None


        # ----------------------------------------------------
        # Required borrower-level cover
        #
        # This comes from the loan master data and is repeated
        # on each security row.
        # ----------------------------------------------------

        required_cover_values = pd.to_numeric(
            valid_data["required_cover"],
            errors="coerce"
        ).dropna()


        if required_cover_values.empty:

            required_cover = None

        else:

            required_cover = float(
                valid_data["borrower_required_cover"].max()
            )


        # ----------------------------------------------------
        # Buffer
        # ----------------------------------------------------

        if (
            total_cover is not None
            and required_cover is not None
        ):

            buffer = (
                total_cover
                - required_cover
            )

        else:

            buffer = None


        # ----------------------------------------------------
        # Risk status
        # ----------------------------------------------------

        if (
            total_cover is not None
            and required_cover is not None
            and total_cover >= required_cover
        ):

            status = "🟢 COMPLIED"

        elif (
            total_cover is not None
            and required_cover is not None
        ):

            status = "🔴 ACTION REQUIRED"

        else:

            status = "⚪ DATA UNAVAILABLE"


        # ----------------------------------------------------
        # Store borrower summary
        # ----------------------------------------------------

        live_borrower_rows.append(
            {
                "market_data_time": (
                valid_data["last_updated"]
                .iloc[0]
                ),
                "borrower": str(
                    borrower_name
                ),

                "loan_amount": loan_amount_cr,

                "collateral_value":
                    collateral_value_cr,

                "total_cover":
                    total_cover,

                "required_cover":
                    required_cover,

                "buffer":
                    buffer,

                "status":
                    status,
            }
        )


# ============================================================
# CREATE SUMMARY DATAFRAME
# ============================================================

live_borrower_risk = pd.DataFrame(
    live_borrower_rows
)


# ============================================================
# DISPLAY LIVE BORROWER SUMMARY
# ============================================================

if live_borrower_risk.empty:

    st.info(
        "No live borrower collateral data is currently "
        "available."
    )

else:

    borrower_view = (
        live_borrower_risk.copy()
    )

    borrower_view["market_data_time"] = (
        borrower_view["market_data_time"]
        .apply(format_market_data_time)
    )

    # --------------------------------------------------------
    # FORMAT LOAN AMOUNT
    # --------------------------------------------------------

    borrower_view["loan_amount"] = (
        borrower_view["loan_amount"]
        .apply(
            lambda x:
            f"₹{x:,.2f} Cr"
            if pd.notna(x)
            else "—"
        )
    )


    # --------------------------------------------------------
    # FORMAT COLLATERAL
    # --------------------------------------------------------

    borrower_view["collateral_value"] = (
        borrower_view["collateral_value"]
        .apply(
            lambda x:
            f"₹{x:,.2f} Cr"
            if pd.notna(x)
            else "—"
        )
    )


    # --------------------------------------------------------
    # FORMAT COVER
    # --------------------------------------------------------

    borrower_view["total_cover"] = (
        borrower_view["total_cover"]
        .apply(
            lambda x:
            f"{x:.2f}x"
            if pd.notna(x)
            else "—"
        )
    )


    # --------------------------------------------------------
    # FORMAT REQUIRED COVER
    # --------------------------------------------------------

    borrower_view["required_cover"] = (
        borrower_view["required_cover"]
        .apply(
            lambda x:
            f"{x:.2f}x"
            if pd.notna(x)
            else "—"
        )
    )


    # --------------------------------------------------------
    # FORMAT BUFFER
    # --------------------------------------------------------

    borrower_view["buffer"] = (
        borrower_view["buffer"]
        .apply(
            lambda x:
            f"{x:+.2f}x"
            if pd.notna(x)
            else "—"
        )
    )


    # --------------------------------------------------------
    # FINAL COLUMN NAMES
    # --------------------------------------------------------

    borrower_view = borrower_view.rename(
        columns={
            "market_data_time":
            "Market Data Time",

            "borrower":
                "Borrower",

            "loan_amount":
                "Loan Amount",

            "collateral_value":
                "Live Collateral",

            "total_cover":
                "Live Cover",

            "required_cover":
                "Required Cover",

            "buffer":
                "Buffer",

            "status":
                "Status",
        }
    )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    st.dataframe(
        borrower_view[
            [
                "Market Data Time",
                "Borrower",
                "Loan Amount",
                "Live Collateral",
                "Live Cover",
                "Required Cover",
                "Buffer",
                "Status",
            ]
        ],
        width="stretch",
        hide_index=True,
    )

# ============================================================
# 3. LIVE IMMEDIATE ATTENTION
# ============================================================

st.subheader("🚨 Immediate Attention Required")


critical_live = live_df[
    live_df["cover"].notna()
    &
    (
        live_df["cover"]
        <
        live_df["required_cover"]
    )
].copy()


if not critical_live.empty:

    st.error(
        f"{len(critical_live)} live security record(s) "
        "below required cover."
    )


    critical_view = critical_live[
        [
            "date",
            "borrower",
            "security",
            "cover",
            "required_cover",
            "buffer",
            "risk_status",
        ]
    ].copy()


    critical_view["date"] = (
        critical_view["date"]
        .dt.strftime("%d-%b-%Y")
    )


    critical_view["cover"] = (
        critical_view["cover"]
        .apply(format_cover)
    )


    critical_view["required_cover"] = (
        critical_view["required_cover"]
        .apply(format_cover)
    )


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
        "No live collateral shortfall detected."
    )


# ============================================================
# 4. LIVE MARKET MOVEMENT MONITORING
# ============================================================

st.subheader("📉 Market Movement Monitoring")


market_view = live_df[
    [
        "date",
        "borrower",
        "security",
        "price",
        "previous_close",
        "daily_change_%",
        "market_alert",
    ]
].copy()


market_view = market_view.sort_values(
    ["borrower", "security"]
)


market_view = market_view.rename(
    columns={
        "date": "date",
        "borrower": "borrower",
        "security": "security",
        "price": "price",
        "previous_close": "previous_close",
        "daily_change_%": "daily_change_%",
        "market_alert": "market_alert",
    }
)


market_view["date"] = (
    market_view["date"]
    .dt.strftime("%d-%b-%Y")
)


market_view["price"] = (
    market_view["price"]
    .apply(
        lambda x:
        f"₹{x:,.2f}"
        if pd.notna(x)
        else "Unavailable"
    )
)


market_view["previous_close"] = (
    market_view["previous_close"]
    .apply(
        lambda x:
        f"₹{x:,.2f}"
        if pd.notna(x)
        else "—"
    )
)


market_view["daily_change_%"] = (
    market_view["daily_change_%"]
    .apply(
        lambda x:
        f"{x:+.2f}%"
        if pd.notna(x)
        else "—"
    )
)


st.dataframe(
    market_view,
    width="stretch",
    hide_index=True,
)

# ============================================================
# 5. LIVE COLLATERAL STRESS TESTING
# ============================================================

st.subheader("📉 Collateral Stress Testing")

st.caption(
    "Stress the underlying security price and evaluate both "
    "security-wise and borrower-wise collateral cover."
)

st.markdown(
    "<div style='margin-left: 20px; "
    "font-size: 19px; font-weight: 600; "
    "margin-top: 14px; margin-bottom: 10px;'>"
    "5.1 Stress Scenario"
    "</div>",
    unsafe_allow_html=True,
)

# ============================================================
# STRESS MODE
# ============================================================

stress_mode = st.selectbox(
    "Stress Mode",
    [
        "Single Scrip",
        "Combined Scrips",
        "Custom Scrips",
    ],
    key="stress_mode",
)


# ============================================================
# AVAILABLE BORROWERS
# ============================================================

if live_df.empty:

    st.info(
        "Live collateral data is unavailable."
    )

else:

    stress_borrowers = sorted(
        live_df["borrower"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


    if not stress_borrowers:

        st.info(
            "No active borrowers are available "
            "for stress testing."
        )

    else:

        selected_stress_borrower = st.selectbox(
            "Borrower",
            stress_borrowers,
            key="stress_borrower",
        )


        # ====================================================
        # FILTER SELECTED BORROWER
        # ====================================================

        borrower_stress_df = live_df[
            live_df["borrower"].astype(str)
            ==
            str(selected_stress_borrower)
        ].copy()


        borrower_stress_df = borrower_stress_df.drop_duplicates(
            subset=["security"],
            keep="first"
        )


        available_stress_securities = sorted(
            borrower_stress_df["security"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )


        # ====================================================
        # PRICE FALL OPTIONS
        # ====================================================

        price_fall_options = [
            0,
            5,
            10,
            15,
            20,
            25,
            30,
            40,
            50,
        ]


        # ====================================================
        # SINGLE SCRIP
        # ====================================================
              
        if stress_mode == "Single Scrip":

            selected_stress_security = st.selectbox(
                "Underlying Scrip",
                available_stress_securities,
                key="single_stress_security",
            )

            
            selected_price_fall = st.selectbox(
                "Underlying Price Fall",
                price_fall_options,
                format_func=lambda x: f"{x}%",
                key="single_stress_fall",
            )


            stress_result = run_stress_test(
                borrower_stress_df,
                mode="Single Scrip",
                selected_security=selected_stress_security,
                price_fall=selected_price_fall,
            )


        # ====================================================
        # COMBINED SCRIPS
        # ====================================================

        elif stress_mode == "Combined Scrips":

            selected_price_fall = st.selectbox(
                "Underlying Price Fall",
                price_fall_options,
                format_func=lambda x: f"{x}%",
                key="combined_stress_fall",
            )


            stress_result = run_stress_test(
                borrower_stress_df,
                mode="Combined Scrips",
                price_fall=selected_price_fall,
            )


        # ====================================================
        # CUSTOM SCRIPS
        # ====================================================

        else:

            st.markdown(
                "**Select securities and assign an individual "
                "underlying price fall.**"
            )


            custom_selected_securities = st.multiselect(
                "Select Underlying Scrips",
                available_stress_securities,
                key="custom_stress_securities",
            )


            custom_stresses = {}


            if custom_selected_securities:

                st.markdown(
                "<div style='margin-left: 60px; "
                "font-size: 19px; font-weight: 600;'>"
                "Custom Price Stress"
                "</div>",
                unsafe_allow_html=True,
            )


                for security in custom_selected_securities:

                    custom_stresses[security] = st.selectbox(
                        f"{security} — Price Fall",
                        price_fall_options,
                        format_func=lambda x: f"{x}%",
                        key=f"custom_stress_{security}",
                    )


                stress_result = run_stress_test(
                    borrower_stress_df,
                    mode="Custom Scrips",
                    custom_stresses=custom_stresses,
                )

            else:

                stress_result = {
                    "security_result":
                        pd.DataFrame(),

                    "borrower_result":
                        pd.DataFrame(),

                    "stress_map":
                        {},

                    "mode":
                        "Custom Scrips",
                }


        # ====================================================
        # RESULTS
        # ====================================================

        security_result = stress_result[
            "security_result"
        ]

        borrower_result = stress_result[
            "borrower_result"
        ]

        st.markdown(
            "<div style='margin-left: 20px; "
            "font-size: 19px; font-weight: 600;'>"
            "5.2 Stress Test Results"
            "</div>",
            unsafe_allow_html=True,
        )


        # ====================================================
        # SECURITY STRESS RESULT
        # ====================================================

        st.markdown(
            "<div style='margin-left: 60px; "
            "font-size: 19px; font-weight: 600;'>"
            "5.2.1 Security Stress Result"
            "</div>",
            unsafe_allow_html=True,
        )


        if security_result.empty:

            if stress_mode == "Custom Scrips":

                st.info(
                    "Select at least one security "
                    "to run a custom stress test."
                )

            else:

                st.info(
                    "Stress-test data is unavailable."
                )

        else:

            security_display = security_result[
                [
                    "Security",
                    "Stressed Price",
                    "Stressed Collateral",
                    "Stressed Cover",
                    "Required Cover",
                    "Buffer",
                    "Status",
                ]
            ].copy()


            # ------------------------------------------------
            # FORMAT PRICE
            # ------------------------------------------------

            security_display[
                "Stressed Price"
            ] = security_display[
                "Stressed Price"
            ].apply(
                lambda x:
                f"₹{x:,.2f}"
                if pd.notna(x)
                else "—"
            )


            # ------------------------------------------------
            # FORMAT COLLATERAL
            # ------------------------------------------------

            security_display[
                "Stressed Collateral"
            ] = security_display[
                "Stressed Collateral"
            ].apply(
                lambda x:
                f"₹{x:,.2f} Cr"
                if pd.notna(x)
                else "—"
            )


            # ------------------------------------------------
            # FORMAT COVER
            # ------------------------------------------------

            for column in [
                "Stressed Cover",
                "Required Cover",
                "Buffer",
            ]:

                security_display[column] = (
                    security_display[column]
                    .apply(
                        lambda x:
                        f"{x:.2f}x"
                        if pd.notna(x)
                        else "—"
                    )
                )


            st.dataframe(
                security_display,
                width="stretch",
                hide_index=True,
            )


            # =================================================
            # BORROWER IMPACT
            # =================================================

            st.markdown(
                "<div style='margin-left: 60px; "
                "font-size: 19px; font-weight: 600;'>"
                "5.2.2 Borrower Impact"
                "</div>",
                unsafe_allow_html=True,
            )


            if not borrower_result.empty:

                borrower_display = borrower_result[
                    [
                        "Borrower",
                        "Stressed Collateral",
                        "Stressed Cover",
                        "Required Cover",
                        "Buffer",
                        "Status",
                    ]
                ].copy()


                borrower_display[
                    "Stressed Collateral"
                ] = borrower_display[
                    "Stressed Collateral"
                ].apply(
                    lambda x:
                    f"₹{x:,.2f} Cr"
                    if pd.notna(x)
                    else "—"
                )


                for column in [
                    "Stressed Cover",
                    "Required Cover",
                    "Buffer",
                ]:

                    borrower_display[column] = (
                        borrower_display[column]
                        .apply(
                            lambda x:
                            f"{x:.2f}x"
                            if pd.notna(x)
                            else "—"
                        )
                    )


                st.dataframe(
                    borrower_display,
                    width="stretch",
                    hide_index=True,
                )


                # ---------------------------------------------
                # RESULT SUMMARY
                # ---------------------------------------------

                borrower_status = (
                    borrower_result[
                        "Status"
                    ].iloc[0]
                )


                st.info(
                    f"Borrower Stress Result: "
                    f"{borrower_status}"
                )



    # ----------------------------------------------------
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
# AVAILABLE BORROWERS
# ============================================================

borrowers = sorted(
    df["borrower"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
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
