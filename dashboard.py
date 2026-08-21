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


# ------------------------------------------------------------
# LIVE MARKET DATA / COLLATERAL ATTENTION
# ------------------------------------------------------------

# Securities for which a genuine live price is not available.
# Do NOT treat an old closing price as a live price.
missing_live = live_df[
    live_df["price"].isna()
].copy()


# ------------------------------------------------------------
# MISSING LIVE MARKET DATA
# ------------------------------------------------------------

if not missing_live.empty:

    missing_securities = (
        missing_live["security"]
        .dropna()
        .astype(str)
        .tolist()
    )

    if len(missing_securities) == 1:
        missing_text = missing_securities[0]
    else:
        missing_text = ", ".join(missing_securities)

    st.warning(
        "⚠️ Live market data incomplete. "
        f"Live price is currently unavailable for: {missing_text}. "
        "Borrower-level collateral cover cannot be fully assessed "
        "until live market data is available for all securities."
    )


# ------------------------------------------------------------
# LIVE COLLATERAL SHORTFALL
# ------------------------------------------------------------

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


elif missing_live.empty:

    st.success(
        "No live collateral shortfall detected."
    )

# ============================================================
# 4. SECURITY MARKET CHARTS
# ============================================================

st.subheader("📈 Security Market Charts")

st.caption(
    "Interactive market-price analysis for securities currently included "
    "in the loan/security master."
)

# ------------------------------------------------------------
# BUILD SECURITY LIST DYNAMICALLY
# ------------------------------------------------------------

chart_securities = (
    live_df[
        [
            "security",
            "nse_symbol"
        ]
    ]
    .dropna(
        subset=[
            "security",
            "nse_symbol"
        ]
    )
    .copy()
)

chart_securities["security"] = (
    chart_securities["security"]
    .astype(str)
    .str.strip()
)

chart_securities["nse_symbol"] = (
    chart_securities["nse_symbol"]
    .astype(str)
    .str.strip()
)

chart_securities = (
    chart_securities[
        (chart_securities["security"] != "")
        &
        (chart_securities["nse_symbol"] != "")
    ]
    .drop_duplicates(
        subset=["security"]
    )
    .sort_values("security")
    .reset_index(drop=True)
)

if chart_securities.empty:

    st.info(
        "No securities are currently available "
        "for market chart monitoring."
    )

else:

    selected_security = st.selectbox(
        "Security",
        chart_securities["security"].tolist(),
        key="market_chart_security"
    )

    selected_row = chart_securities[
        chart_securities["security"] == selected_security
    ].iloc[0]

    selected_symbol = str(
        selected_row["nse_symbol"]
    ).strip()

    yahoo_symbol = selected_symbol + ".NS"

    # --------------------------------------------------------
    # PROFESSIONAL CHART CONTROLS
    # --------------------------------------------------------

    control_left, control_right = st.columns([1.15, 1])

    with control_left:

        selected_period = st.radio(
            "Period",
            ["1D", "1W", "1M", "1Y", "5Y"],
            horizontal=True,
            key="market_chart_period"
        )

    with control_right:

        selected_chart_type = st.radio(
            "Chart Type",
            ["Line", "Candlestick", "Area"],
            horizontal=True,
            key="market_chart_type"
        )

            # --------------------------------------------------------
    # CURRENT / LATEST MARKET DATA
    # --------------------------------------------------------
    #
    # IMPORTANT:
    #
    # Live market data is required for collateral calculations.
    # This section is ONLY for the selected-security information
    # panel.
    #
    # If live intraday data is unavailable:
    #     - fetch latest verified NSE EOD close
    #     - clearly label it as "Latest NSE Close"
    #     - NEVER call it "Current Price"
    #     - NEVER use it as today's collateral price
    #
    # --------------------------------------------------------

    from modules.market_data import (
        get_live_stock_data,
        get_daily_market_data,
    )

    selected_market_data = None
    fallback_market_data = None

    market_is_live = False
    market_data_source = "Unavailable"

    # --------------------------------------------------------
    # 1. TRY LIVE MARKET DATA
    # --------------------------------------------------------

    try:

        selected_market_data = get_live_stock_data(
            selected_symbol
        )

        if (
            selected_market_data
            and selected_market_data.get("price") is not None
        ):

            market_is_live = True
            market_data_source = (
                selected_market_data.get(
                    "source",
                    "Live market data"
                )
            )

    except Exception:

        selected_market_data = None
        market_is_live = False

    # --------------------------------------------------------
    # 2. FALL BACK TO VERIFIED NSE EOD DATA
    # --------------------------------------------------------
    #
    # This is DISPLAY ONLY.
    #
    # It must never become the live collateral price.
    # --------------------------------------------------------

    if not market_is_live:

        try:

            fallback_market_data = get_daily_market_data(
                selected_symbol,
                stock_display_name=selected_security,
            )

            if (
                fallback_market_data
                and fallback_market_data.get("price") is not None
            ):

                market_data_source = (
                    fallback_market_data.get(
                        "source",
                        "NSE Bhavcopy EOD"
                    )
                )

        except Exception:

            fallback_market_data = None

    # --------------------------------------------------------
    # 3. INITIALISE DISPLAY VALUES
    # --------------------------------------------------------

    current_price = None
    previous_close = None
    daily_change = None
    week_52_low = None
    week_52_high = None
    market_cap = None
    market_data_time = None

    # --------------------------------------------------------
    # 4. LIVE DATA AVAILABLE
    # --------------------------------------------------------

    if market_is_live:

        current_price = (
            selected_market_data.get("price")
        )

        previous_close = (
            selected_market_data.get(
                "previous_close"
            )
        )

        daily_change = (
            selected_market_data.get(
                "daily_change_%"
            )
        )

        week_52_low = (
            selected_market_data.get(
                "52_week_low"
            )
        )

        week_52_high = (
            selected_market_data.get(
                "52_week_high"
            )
        )

        market_cap = (
            selected_market_data.get(
                "market_cap"
            )
        )

        market_data_time = (
            selected_market_data.get(
                "last_updated"
            )
        )

    # --------------------------------------------------------
    # 5. LIVE DATA UNAVAILABLE
    # --------------------------------------------------------
    #
    # Use EOD ONLY for market-information display.
    #
    # Do NOT populate current_price from the fallback.
    #
    # This is intentional.
    # --------------------------------------------------------

    else:

        if fallback_market_data:

            fallback_price = (
                fallback_market_data.get(
                    "price"
                )
            )

            fallback_date = (
                fallback_market_data.get(
                    "last_updated"
                )
            )

            # Keep the fallback price separate.
            #
            # We do NOT assign it to current_price.
            #

            latest_verified_close = (
                fallback_price
            )

            latest_verified_close_date = (
                fallback_date
            )

        else:

            latest_verified_close = None
            latest_verified_close_date = None

    # --------------------------------------------------------
    # 6. FETCH / PREPARE HISTORICAL CHART DATA
    # --------------------------------------------------------

    try:

        from modules.market_data import (
            get_market_chart_data
        )

        chart_data = get_market_chart_data(
            yahoo_symbol,
            period=selected_period,
            stock_display_name=selected_security
        )

        if (
            chart_data is None
            or chart_data.empty
        ):

            raise ValueError(
                f"No market history received "
                f"for {selected_security}"
            )

        import plotly.graph_objects as go

        from plotly.subplots import make_subplots

        chart_data = chart_data.copy()

        chart_data["datetime"] = pd.to_datetime(
            chart_data["datetime"],
            errors="coerce"
        )

        chart_data = chart_data[
            chart_data["datetime"].notna()
        ].copy()

        for column in [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]:

            if column in chart_data.columns:

                chart_data[column] = (
                    pd.to_numeric(
                        chart_data[column],
                        errors="coerce"
                    )
                )

        chart_data = (
            chart_data
            .dropna(
                subset=["close"]
            )
            .reset_index(
                drop=True
            )
        )

        if chart_data.empty:

            raise ValueError(
                f"No valid market history received "
                f"for {selected_security}"
            )

        # ----------------------------------------------------
        # 52-WEEK HIGH / LOW
        # ----------------------------------------------------

        if (
            week_52_low is None
            or pd.isna(week_52_low)
        ):

            low_values = (
                pd.to_numeric(
                    chart_data["low"],
                    errors="coerce"
                )
                .dropna()
            )

            if not low_values.empty:

                week_52_low = float(
                    low_values.min()
                )

        if (
            week_52_high is None
            or pd.isna(week_52_high)
        ):

            high_values = (
                pd.to_numeric(
                    chart_data["high"],
                    errors="coerce"
                )
                .dropna()
            )

            if not high_values.empty:

                week_52_high = float(
                    high_values.max()
                )

        # ----------------------------------------------------
        # FORMAT HELPERS
        # ----------------------------------------------------

        def _money(value):

            if (
                value is None
                or pd.isna(value)
            ):

                return "—"

            return (
                f"₹{float(value):,.2f}"
            )

        def _percent(value):

            if (
                value is None
                or pd.isna(value)
            ):

                return "—"

            return (
                f"{float(value):+.2f}%"
            )

        def _compact_number(value):

            if (
                value is None
                or pd.isna(value)
            ):

                return "—"

            value = float(value)

            if abs(value) >= 1_000_000_000:

                return (
                    f"{value / 1_000_000_000:.2f}B"
                )

            if abs(value) >= 1_000_000:

                return (
                    f"{value / 1_000_000:.2f}M"
                )

            if abs(value) >= 1_000:

                return (
                    f"{value / 1_000:.1f}K"
                )

            return f"{value:,.0f}"

        # ----------------------------------------------------
        # DISPLAY VALUES
        # ----------------------------------------------------

        if market_is_live:

            current_text = _money(
                current_price
            )

            previous_text = _money(
                previous_close
            )

            change_text = _percent(
                daily_change
            )

            absolute_change = None

            if (
                current_price is not None
                and previous_close is not None
                and pd.notna(current_price)
                and pd.notna(previous_close)
            ):

                absolute_change = (
                    float(current_price)
                    - float(previous_close)
                )

            absolute_change_text = (
                f"{absolute_change:+.2f}"
                if absolute_change is not None
                else "—"
            )

            price_card_label = (
                "Current Price"
            )

            price_card_sub = (
                str(market_data_time)
                if market_data_time
                else "Live market data"
            )

        else:

            current_text = "—"

            previous_text = "—"

            change_text = "—"

            absolute_change_text = "—"

            price_card_label = (
                "Latest NSE Close"
            )

            price_card_sub = (
                (
                    f"{latest_verified_close_date}"
                    if latest_verified_close_date
                    else "Latest verified close unavailable"
                )
                + "<br>"
                + "<span style='color:#b45309;'>"
                + "Live intraday unavailable"
                + "</span>"
            )

        # ----------------------------------------------------
        # CHANGE COLOUR
        # ----------------------------------------------------

        if (
            market_is_live
            and daily_change is not None
            and pd.notna(daily_change)
        ):

            change_class = (
                "market-card-change-positive"
                if float(daily_change) >= 0
                else "market-card-change-negative"
            )

            change_icon = (
                "▲"
                if float(daily_change) >= 0
                else "▼"
            )

        else:

            change_class = ""
            change_icon = ""

        # ----------------------------------------------------
        # 52-WEEK RANGE
        # ----------------------------------------------------

        if (
            week_52_low is not None
            and pd.notna(week_52_low)
            and week_52_high is not None
            and pd.notna(week_52_high)
        ):

            range_text = (
                f"{_money(week_52_low)}"
                f" &nbsp;—&nbsp; "
                f"{_money(week_52_high)}"
            )

        else:

            range_text = (
                "52-week range unavailable"
            )

        # ----------------------------------------------------
        # PROFESSIONAL MARKET CARD / CHART CSS
        # ----------------------------------------------------

        st.html(
            """
            <style>

            .market-card-row {
                display: grid;
                grid-template-columns:
                    repeat(4, minmax(0, 1fr));
                gap: 14px;
                margin: 18px 0 18px 0;
            }

            .market-card {
                border: 1px solid #e5e7eb;
                border-radius: 14px;
                padding: 18px 20px;
                min-height: 128px;
                background: linear-gradient(
                    145deg,
                    #ffffff 0%,
                    #f8fafc 100%
                );
                box-shadow:
                    0 4px 16px rgba(15, 23, 42, 0.06);
            }

            .market-card.blue {
                background: linear-gradient(
                    145deg,
                    #ffffff 0%,
                    #eff6ff 100%
                );
            }

            .market-card.green {
                background: linear-gradient(
                    145deg,
                    #ffffff 0%,
                    #f0fdf4 100%
                );
            }

            .market-card.orange {
                background: linear-gradient(
                    145deg,
                    #ffffff 0%,
                    #fffbeb 100%
                );
            }

            .market-card.purple {
                background: linear-gradient(
                    145deg,
                    #ffffff 0%,
                    #faf5ff 100%
                );
            }

            .market-card-label {
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                color: #64748b;
                margin-bottom: 7px;
            }

            .market-card-value {
                font-size: 27px;
                line-height: 1.15;
                font-weight: 750;
                color: #0f172a;
                margin-bottom: 7px;
            }

            .market-card-sub {
                font-size: 13px;
                color: #64748b;
                line-height: 1.5;
            }

            .market-card-change-positive {
                color: #16a34a;
                font-weight: 700;
            }

            .market-card-change-negative {
                color: #dc2626;
                font-weight: 700;
            }

            .market-card-icon {
                float: right;
                width: 34px;
                height: 34px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 17px;
                background: #eff6ff;
            }

            .market-chart-shell {
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                background: #ffffff;
                box-shadow:
                    0 5px 18px rgba(15, 23, 42, 0.06);
                padding: 8px 10px 2px 10px;
                margin-top: 6px;
            }

            .market-chart-title {
                padding: 12px 14px 4px 14px;
                font-size: 19px;
                font-weight: 750;
                color: #0f172a;
            }

            .market-chart-subtitle {
                padding: 0 14px 6px 14px;
                font-size: 12px;
                color: #64748b;
            }

            .market-stat-row {
                display: grid;
                grid-template-columns:
                    repeat(6, minmax(0, 1fr));
                gap: 9px;
                margin: 10px 0 8px 0;
            }

            .market-stat {
                border: 1px solid #eef2f7;
                border-radius: 10px;
                background: #f8fafc;
                padding: 10px 12px;
            }

            .market-stat-label {
                font-size: 11px;
                color: #64748b;
                margin-bottom: 4px;
            }

            .market-stat-value {
                font-size: 14px;
                font-weight: 700;
                color: #0f172a;
            }

            .market-footer {
                text-align: center;
                color: #64748b;
                font-size: 11px;
                padding: 8px 0 10px 0;
                border-top: 1px solid #eef2f7;
                margin-top: 7px;
            }

            @media (max-width: 900px) {

                .market-card-row {
                    grid-template-columns:
                        repeat(2, minmax(0, 1fr));
                }

                .market-stat-row {
                    grid-template-columns:
                        repeat(3, minmax(0, 1fr));
                }

            }

            @media (max-width: 600px) {

                .market-card-row,
                .market-stat-row {
                    grid-template-columns: 1fr;
                }

            }

            </style>
            """
        )

        # ----------------------------------------------------
        # MARKET CARDS
        # ----------------------------------------------------

        st.html(
            f"""
            <div class="market-card-row">

                <div class="market-card blue">

                    <div class="market-card-icon">
                        ₹
                    </div>

                    <div class="market-card-label">
                        {price_card_label}
                    </div>

                    <div class="market-card-value">
                        {
                            current_text
                            if market_is_live
                            else (
                                _money(
                                    latest_verified_close
                                )
                                if latest_verified_close
                                is not None
                                else "—"
                            )
                        }
                    </div>

                    <div class="{change_class}">
                        {change_icon}
                        {absolute_change_text}
                        {change_text}
                    </div>

                    <div class="market-card-sub">
                        {price_card_sub}
                    </div>

                </div>


                <div class="market-card green">

                    <div class="market-card-icon">
                        ▥
                    </div>

                    <div class="market-card-label">
                        Previous Close
                    </div>

                    <div class="market-card-value">
                        {previous_text}
                    </div>

                    <div class="market-card-sub">
                        Previous trading session
                    </div>

                </div>


                <div class="market-card orange">

                    <div class="market-card-icon">
                        ↗
                    </div>

                    <div class="market-card-label">
                        Today's Change
                    </div>

                    <div class="market-card-value {change_class}">
                        {change_icon}
                        {change_text}
                    </div>

                    <div class="market-card-sub">
                        {
                            "Absolute move: ₹"
                            + absolute_change_text
                            if market_is_live
                            else
                            "Live intraday change unavailable"
                        }
                    </div>

                </div>


                <div class="market-card purple">

                    <div class="market-card-icon">
                        ◎
                    </div>

                    <div class="market-card-label">
                        52 Week Range
                    </div>

                    <div
                        class="market-card-value"
                        style="font-size:19px;"
                    >
                        {range_text}
                    </div>

                    <div class="market-card-sub">
                        Low to high market range
                    </div>

                </div>

            </div>
            """
        )

    
        # ----------------------------------------------------
        # CHART HEADER
        # ----------------------------------------------------

        st.html(
            f"""
            <div class="market-chart-shell">
                <div class="market-chart-title">
                    {selected_security} ({selected_symbol})
                </div>
                <div class="market-chart-subtitle">
                    NSE: {selected_symbol}
                    &nbsp; • &nbsp;
                    {selected_period}
                    &nbsp; • &nbsp;
                    {selected_chart_type}
                </div>
            </div>
            """
        )

        # ----------------------------------------------------
        # CREATE PRICE + VOLUME CHART
        # ----------------------------------------------------

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.025,
            row_heights=[0.82, 0.18]
        )

        if selected_chart_type == "Candlestick":

            fig.add_trace(
                go.Candlestick(
                    x=chart_data["datetime"],
                    open=chart_data["open"],
                    high=chart_data["high"],
                    low=chart_data["low"],
                    close=chart_data["close"],
                    name=selected_symbol,
                    increasing_line_color="#16a34a",
                    decreasing_line_color="#dc2626",
                    increasing_fillcolor="#16a34a",
                    decreasing_fillcolor="#dc2626",
                    hoverlabel=dict(
                        namelength=-1
                    ),
                ),
                row=1,
                col=1
            )

        elif selected_chart_type == "Area":

            fig.add_trace(
                go.Scatter(
                    x=chart_data["datetime"],
                    y=chart_data["close"],
                    mode="lines",
                    name=selected_symbol,
                    line=dict(
                        color="#2563eb",
                        width=2.2
                    ),
                    fill="tozeroy",
                    fillcolor=(
                        "rgba(37, 99, 235, 0.10)"
                    ),
                    hovertemplate=(
                        "<b>%{x}</b>"
                        "<br>Price: ₹%{y:,.2f}"
                        "<extra></extra>"
                    ),
                ),
                row=1,
                col=1
            )

        else:

            fig.add_trace(
                go.Scatter(
                    x=chart_data["datetime"],
                    y=chart_data["close"],
                    mode="lines",
                    name=selected_symbol,
                    line=dict(
                        color="#2563eb",
                        width=2.4
                    ),
                    hovertemplate=(
                        "<b>%{x}</b>"
                        "<br>Price: ₹%{y:,.2f}"
                        "<extra></extra>"
                    ),
                ),
                row=1,
                col=1
            )

        volume_data = chart_data.copy()

        volume_data["volume"] = (
            pd.to_numeric(
                volume_data["volume"],
                errors="coerce"
            )
            .fillna(0)
        )

        if len(volume_data) > 1:

            previous_close_series = (
                pd.to_numeric(
                    volume_data["close"],
                    errors="coerce"
                ).shift(1)
            )

            volume_is_up = (
                volume_data["close"]
                >= previous_close_series
            )

        else:

            volume_is_up = pd.Series(
                [True] * len(volume_data)
            )

        volume_colors = [
            "rgba(22, 163, 74, 0.55)"
            if is_up
            else "rgba(220, 38, 38, 0.55)"
            for is_up in volume_is_up.fillna(True)
        ]

        fig.add_trace(
            go.Bar(
                x=volume_data["datetime"],
                y=volume_data["volume"],
                name="Volume",
                marker_color=volume_colors,
                hovertemplate=(
                    "<b>%{x}</b>"
                    "<br>Volume: %{y:,.0f}"
                    "<extra></extra>"
                ),
            ),
            row=2,
            col=1
        )

        if (
            current_price is not None
            and pd.notna(current_price)
        ):

            fig.add_hline(
                y=float(current_price),
                line_dash="dot",
                line_width=1,
                line_color="#64748b",
                annotation_text=(
                    f"₹{float(current_price):,.2f}"
                ),
                annotation_position="top right",
                row=1,
                col=1
            )

        fig.update_layout(
            height=535,
            hovermode="x unified",
            template="plotly_white",
            margin=dict(
                l=48,
                r=24,
                t=12,
                b=36
            ),
            showlegend=False,
            dragmode="zoom",
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(
                family="Arial, sans-serif",
                size=11,
                color="#334155"
            ),
            xaxis_rangeslider_visible=False,
        )

        fig.update_yaxes(
            title_text="Price",
            title_font=dict(
                size=11,
                color="#64748b"
            ),
            row=1,
            col=1,
            fixedrange=False,
            showgrid=True,
            gridcolor="#e9eef5",
            gridwidth=1,
            zeroline=False,
            tickprefix="₹",
            tickformat=",.2f",
        )

        fig.update_yaxes(
            title_text="Volume",
            title_font=dict(
                size=10,
                color="#64748b"
            ),
            row=2,
            col=1,
            fixedrange=False,
            showgrid=False,
            zeroline=False,
            separatethousands=True,
        )

        # ----------------------------------------------------
        # CLEAN TRADING-DAY / TRADING-HOUR X-AXIS
        # ----------------------------------------------------
        # 1D = remove overnight hours + weekends
        # Other periods = remove weekends only.

        if selected_period == "1D":

            x_rangebreaks = [
                dict(
                    bounds=["sat", "mon"]
                ),
                dict(
                    bounds=[15.5, 9.25],
                    pattern="hour"
                ),
            ]

        else:

            x_rangebreaks = [
            dict(
                bounds=["sat", "mon"]
            )

        ]

            for chart_row in [1, 2]:

                fig.update_xaxes(
                    showgrid=False,
                    showline=False,
                    rangeslider=dict(
                        visible=False
                    ),
                    fixedrange=False,
                    rangebreaks=x_rangebreaks,
                    row=chart_row,
                    col=1
                )

           
        st.plotly_chart(
            fig,
            width="stretch",
            config={
                "displaylogo": False,
                "scrollZoom": True,
                "displayModeBar": True,
                "responsive": True,
                "modeBarButtonsToRemove": [
                    "lasso2d",
                    "select2d",
                ],
            }
        )


                # ----------------------------------------------------
        # MARKET STATISTICS
        # ----------------------------------------------------
        #
        # These statistics represent the complete current
        # trading session, rather than only the last candle.
        # ----------------------------------------------------

        session_data = chart_data.copy()

        session_data["datetime"] = pd.to_datetime(
            session_data["datetime"],
            errors="coerce"
        )

        session_data = session_data[
            session_data["datetime"].notna()
        ].copy()

        # ----------------------------------------------------
        # NORMALIZE TIMEZONE TO IST
        # ----------------------------------------------------

        if session_data["datetime"].dt.tz is None:

            session_data["datetime"] = (
                session_data["datetime"]
                .dt.tz_localize(
                    "Asia/Kolkata"
                )
            )

        else:

            session_data["datetime"] = (
                session_data["datetime"]
                .dt.tz_convert(
                    "Asia/Kolkata"
                )
            )

        # ----------------------------------------------------
        # KEEP TODAY'S TRADING SESSION
        # ----------------------------------------------------

        today_date = datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).date()

        today_session = session_data[
            session_data["datetime"].dt.date
            == today_date
        ].copy()

        # ----------------------------------------------------
        # SAFETY FALLBACK
        # ----------------------------------------------------
        #
        # If today's session is not present in the selected
        # chart period, use the latest available trading day.
        # ----------------------------------------------------

        if today_session.empty:

            latest_date = (
                session_data["datetime"]
                .dt.date
                .max()
            )

            today_session = session_data[
                session_data["datetime"].dt.date
                == latest_date
            ].copy()

        # ----------------------------------------------------
        # NUMERIC VALUES
        # ----------------------------------------------------

        for column in [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]:

            if column in today_session.columns:

                today_session[column] = pd.to_numeric(
                    today_session[column],
                    errors="coerce"
                )

        # ----------------------------------------------------
        # SESSION OPEN
        # ----------------------------------------------------

        open_series = (
            today_session["open"]
            .dropna()
        )

        open_value = (
            float(open_series.iloc[0])
            if not open_series.empty
            else None
        )

        # ----------------------------------------------------
        # SESSION HIGH
        # ----------------------------------------------------

        high_series = (
            today_session["high"]
            .dropna()
        )

        high_value = (
            float(high_series.max())
            if not high_series.empty
            else None
        )

        # ----------------------------------------------------
        # SESSION LOW
        # ----------------------------------------------------

        low_series = (
            today_session["low"]
            .dropna()
        )

        low_value = (
            float(low_series.min())
            if not low_series.empty
            else None
        )

        # ----------------------------------------------------
        # TOTAL SESSION VOLUME
        # ----------------------------------------------------

        volume_series = (
            today_session["volume"]
            .dropna()
        )

        latest_volume = (
            float(volume_series.sum())
            if not volume_series.empty
            else None
        )

        # ----------------------------------------------------
        # AVERAGE VOLUME
        # ----------------------------------------------------

        average_volume = (
            float(
                volume_series.tail(20).mean()
            )
            if not volume_series.empty
            else None
        )
               
        
        market_cap_text = (
            _compact_number(market_cap)
            if market_cap is not None
            and pd.notna(market_cap)
            else "—"
        )

        st.html(
            f"""
            <div class="market-stat-row">

                <div class="market-stat">
                    <div class="market-stat-label">Open</div>
                    <div class="market-stat-value">
                        {_money(open_value)}
                    </div>
                </div>

                <div class="market-stat">
                    <div class="market-stat-label">High</div>
                    <div class="market-stat-value">
                        {_money(high_value)}
                    </div>
                </div>

                <div class="market-stat">
                    <div class="market-stat-label">Low</div>
                    <div class="market-stat-value">
                        {_money(low_value)}
                    </div>
                </div>

                <div class="market-stat">
                    <div class="market-stat-label">Volume</div>
                    <div class="market-stat-value">
                        {_compact_number(latest_volume)}
                    </div>
                </div>

                <div class="market-stat">
                    <div class="market-stat-label">
                        Avg. Volume
                    </div>
                    <div class="market-stat-value">
                        {_compact_number(average_volume)}
                    </div>
                </div>

                <div class="market-stat">
                    <div class="market-stat-label">
                        Market Cap
                    </div>
                    <div class="market-stat-value">
                        {market_cap_text}
                    </div>
                </div>

            </div>

            <div class="market-footer">
                📊 Market data from the configured market-data source
                &nbsp; • &nbsp;
                {selected_security}
                ({selected_symbol})
                &nbsp; • &nbsp;
                Interactive chart — zoom, pan and hover for details
            </div>
            """
        )

    except Exception as chart_error:

        st.warning(
            f"Market chart unavailable "
            f"for {selected_security}: "
            f"{chart_error}"
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

    from modules.input_database import list_share_movements

    master_movements = list_share_movements()

    movement_df = pd.DataFrame(
        master_movements
    )

    if not movement_df.empty:

        movement_df = movement_df.rename(
            columns={
                "number_of_shares": "movement_shares",
                "listed_company_name": "security",
            }
        )

except Exception as e:

    print(
        f"Master share movement load error: {e}"
    )

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
                    tickMinStep=86400000,
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
