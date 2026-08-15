# -*- coding: utf-8 -*-

"""
Loan Collateral Monitoring System
---------------------------------
Central market-data module.

Supports:
    - NSE ticker symbols
    - NSE ticker symbols with .NS
    - ISINs
    - Company names

Market data source:
    Yahoo Finance via yfinance

Behaviour:
    - During Indian market hours:
        Try latest intraday price first.
    - Outside market hours:
        Use latest completed daily closing price.
    - If intraday data is unavailable:
        Fall back to latest daily close.

Important:
    This module NEVER modifies the collateral database.
"""

import sys
import re
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf


# ============================================================
# WINDOWS / UTF-8 OUTPUT
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# TIMEZONE
# ============================================================

IST = ZoneInfo("Asia/Kolkata")


# ============================================================
# MARKET HOURS
# ============================================================

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


# ============================================================
# SECURITY MASTER
# ============================================================
#
# The database currently contains:
#
# Kalyan Jewellers:
#     ISIN = INE303R01014
#     NSE  = KALYANKJIL
#
# Mindspace Business Parks REIT:
#     ISIN = INE0CCU25019
#     NSE  = MINDSPACE
#
# Existing securities:
#     JSW Energy
#     JSW Steel
#     Jindal Steel & Power
#
# This mapping is intentionally kept here as a market-data
# resolution layer. It does NOT control borrowers, loans,
# shares or collateral positions.
#
# New securities can be added here when their market identifier
# is not already available as an NSE ticker.
# ============================================================

SECURITY_MASTER = {

    # --------------------------------------------------------
    # Kalyan Jewellers India Limited
    # --------------------------------------------------------
    "KALYAN JEWELLERS INDIA LIMITED": {
        "nse_symbol": "KALYANKJIL",
        "isin": "INE303R01014",
    },

    "KALYANKJIL": {
        "nse_symbol": "KALYANKJIL",
        "isin": "INE303R01014",
    },

    "INE303R01014": {
        "nse_symbol": "KALYANKJIL",
        "isin": "INE303R01014",
    },


    # --------------------------------------------------------
    # Mindspace Business Parks REIT
    # --------------------------------------------------------
    "MINDSPACE BUSINESS PARKS REIT": {
        "nse_symbol": "MINDSPACE",
        "isin": "INE0CCU25019",
    },

    "MINDSPACE": {
        "nse_symbol": "MINDSPACE",
        "isin": "INE0CCU25019",
    },

    "INE0CCU25019": {
        "nse_symbol": "MINDSPACE",
        "isin": "INE0CCU25019",
    },


    # --------------------------------------------------------
    # Existing securities
    # --------------------------------------------------------
    "JSW ENERGY": {
        "nse_symbol": "JSWENERGY",
        "isin": "",
    },

    "JSWENERGY": {
        "nse_symbol": "JSWENERGY",
        "isin": "",
    },

    "JSW STEEL": {
        "nse_symbol": "JSWSTEEL",
        "isin": "",
    },

    "JSWSTEEL": {
        "nse_symbol": "JSWSTEEL",
        "isin": "",
    },

    "JINDAL STEEL & POWER": {
        "nse_symbol": "JINDALSTEL",
        "isin": "",
    },

    "JINDALSTEL": {
        "nse_symbol": "JINDALSTEL",
        "isin": "",
    },
}


# ============================================================
# BACKWARD-COMPATIBILITY SYMBOL DICTIONARY
# ============================================================

SYMBOLS = {
    "JSW Energy": "JSWENERGY.NS",
    "JSW Steel": "JSWSTEEL.NS",
    "Jindal Steel & Power": "JINDALSTEL.NS",

    "Kalyan Jewellers India Limited": "KALYANKJIL.NS",
    "Mindspace Business Parks REIT": "MINDSPACE.NS",
}


# ============================================================
# NORMALIZE INPUT
# ============================================================

def normalize_identifier(value):
    """
    Normalize a security identifier.

    Examples:
        "Kalyan Jewellers India Limited"
            -> "KALYAN JEWELLERS INDIA LIMITED"

        "KALYANKJIL.NS"
            -> "KALYANKJIL"

        "INE303R01014"
            -> "INE303R01014"
    """

    if value is None:
        return ""

    value = str(value).strip()

    if not value:
        return ""

    value = value.upper()

    # Remove Yahoo NSE suffix
    if value.endswith(".NS"):
        value = value[:-3]

    # Normalize multiple spaces
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ============================================================
# RESOLVE SECURITY
# ============================================================

def resolve_security(identifier):
    """
    Resolve company name / NSE symbol / ISIN into an NSE ticker.

    Returns:

        {
            "nse_symbol": "KALYANKJIL",
            "yahoo_symbol": "KALYANKJIL.NS",
            "isin": "INE303R01014"
        }

    """

    normalized = normalize_identifier(identifier)

    if not normalized:
        raise ValueError("Security identifier is empty")

    # --------------------------------------------------------
    # 1. Known security
    # --------------------------------------------------------

    if normalized in SECURITY_MASTER:

        record = SECURITY_MASTER[normalized]

        return {
            "nse_symbol": record["nse_symbol"],
            "yahoo_symbol": record["nse_symbol"] + ".NS",
            "isin": record.get("isin", ""),
        }


    # --------------------------------------------------------
    # 2. Already looks like an NSE ticker
    # --------------------------------------------------------

    # Example:
    #     ABC
    #     RELIANCE
    #     TCS
    #
    # We allow this as a generic NSE ticker.
    #
    # This is useful when the Input Portal stores the actual
    # NSE symbol rather than an ISIN.
    # --------------------------------------------------------

    if re.fullmatch(r"[A-Z0-9&_-]{2,30}", normalized):

        return {
            "nse_symbol": normalized,
            "yahoo_symbol": normalized + ".NS",
            "isin": "",
        }


    # --------------------------------------------------------
    # 3. Unknown company name
    # --------------------------------------------------------

    raise ValueError(
        f"Unable to resolve market symbol for: {identifier}"
    )


# ============================================================
# MARKET HOURS CHECK
# ============================================================

def is_market_open(now=None):
    """
    Return True if Indian equity market is currently open.

    Monday-Friday:
        09:15 to 15:30 IST
    """

    if now is None:
        now = datetime.now(IST)

    # Saturday / Sunday
    if now.weekday() >= 5:
        return False

    current_time = now.time()

    return (
        MARKET_OPEN
        <= current_time
        <= MARKET_CLOSE
    )


# ============================================================
# NUMERIC SERIES HELPER
# ============================================================

def pd_series_numeric(series):
    """
    Convert a pandas Series into numeric values.
    """

    return pd.to_numeric(
        series,
        errors="coerce"
    )


# ============================================================
# DAILY MARKET DATA
# ============================================================

def get_daily_market_data(
    yahoo_symbol,
    stock_display_name=None
):
    """
    Get daily NSE market data.

    Used primarily after market close or when intraday
    data is unavailable.

    Returns:

        price
        previous_close
        daily_change_%
        52_week_low
        distance_from_52_week_low_%
        last_updated
        source
    """

    display_name = (
        stock_display_name
        or yahoo_symbol
    )

    print(
        f"Fetching DAILY NSE price for "
        f"{display_name} ({yahoo_symbol})..."
    )

    try:

        stock = yf.Ticker(
            yahoo_symbol
        )

        data = stock.history(
            period="1y",
            interval="1d",
            auto_adjust=False,
            prepost=False
        )

        if data is None or data.empty:

            raise Exception(
                f"No daily market data received "
                f"for {display_name}"
            )


        # ----------------------------------------------------
        # CLOSE PRICES
        # ----------------------------------------------------

        close_prices = (
            pd_series_numeric(
                data["Close"]
            )
            .dropna()
        )

        close_prices = close_prices[
            close_prices > 0
        ]


        if close_prices.empty:

            raise Exception(
                f"No valid closing prices received "
                f"for {display_name}"
            )


        # ----------------------------------------------------
        # LATEST CLOSE
        # ----------------------------------------------------

        latest_price = float(
            close_prices.iloc[-1]
        )


        # ----------------------------------------------------
        # PREVIOUS CLOSE
        # ----------------------------------------------------

        previous_close = None

        if len(close_prices) >= 2:

            previous_close = float(
                close_prices.iloc[-2]
            )


        # ----------------------------------------------------
        # DAILY CHANGE
        # ----------------------------------------------------

        daily_change = None

        if (
            previous_close is not None
            and previous_close > 0
        ):

            daily_change = (
                (
                    latest_price
                    - previous_close
                )
                / previous_close
            ) * 100


        # ----------------------------------------------------
        # 52 WEEK LOW
        # ----------------------------------------------------

        week_52_low = float(
            close_prices.min()
        )

        if week_52_low <= 0:
            week_52_low = None


        # ----------------------------------------------------
        # DISTANCE FROM 52 WEEK LOW
        # ----------------------------------------------------

        distance_from_low = None

        if (
            week_52_low is not None
            and week_52_low > 0
        ):

            distance_from_low = (
                (
                    latest_price
                    - week_52_low
                )
                / week_52_low
            ) * 100


        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        last_updated = None

        if len(data.index) > 0:

            last_timestamp = data.index[-1]

            try:

                if last_timestamp.tzinfo is None:

                    last_timestamp = (
                        last_timestamp
                        .tz_localize("Asia/Kolkata")
                    )

                else:

                    last_timestamp = (
                        last_timestamp
                        .tz_convert("Asia/Kolkata")
                    )

                last_updated = (
                    last_timestamp.strftime(
                        "%d-%b-%Y %H:%M:%S"
                    )
                )

            except Exception:

                last_updated = (
                    str(last_timestamp)
                )


        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        result = {

            "price": round(
                latest_price,
                2
            ),

            "previous_close": (
                round(previous_close, 2)
                if previous_close is not None
                else None
            ),

            "daily_change_%": (
                round(daily_change, 2)
                if daily_change is not None
                else None
            ),

            "52_week_low": (
                round(week_52_low, 2)
                if week_52_low is not None
                else None
            ),

            "distance_from_52_week_low_%": (
                round(distance_from_low, 2)
                if distance_from_low is not None
                else None
            ),

            "last_updated": (
                last_updated
                or "Unavailable"
            ),

            "source": (
                "Yahoo Finance Daily Close"
            ),
        }


        print(
            f"Daily price received: "
            f"{display_name} = "
            f"₹{result['price']:.2f}"
        )

        return result


    except Exception as e:

        print(
            f"❌ Daily market data error "
            f"for {display_name}: {e}"
        )

        raise Exception(
            f"Daily NSE market data unavailable "
            f"for {display_name}"
        ) from e


# ============================================================
# LIVE / INTRADAY MARKET DATA
# ============================================================

def get_intraday_market_data(
    yahoo_symbol,
    stock_display_name=None
):
    """
    Get latest intraday market price.

    Uses Yahoo Finance 1-minute data.
    """

    display_name = (
        stock_display_name
        or yahoo_symbol
    )

    print(
        f"Fetching LIVE NSE price for "
        f"{display_name} ({yahoo_symbol})..."
    )

    stock = yf.Ticker(
        yahoo_symbol
    )


    # --------------------------------------------------------
    # INTRADAY
    # --------------------------------------------------------

    intraday = stock.history(
        period="1d",
        interval="1m",
        auto_adjust=False,
        prepost=False
    )


    if intraday is None or intraday.empty:

        raise Exception(
            f"No intraday data received "
            f"for {display_name}"
        )


    # --------------------------------------------------------
    # VALID CLOSE VALUES
    # --------------------------------------------------------

    prices = (
        pd_series_numeric(
            intraday["Close"]
        )
        .dropna()
    )

    prices = prices[
        prices > 0
    ]


    if prices.empty:

        raise Exception(
            f"No valid live price received "
            f"for {display_name}"
        )


    # --------------------------------------------------------
    # LATEST INTRADAY PRICE
    # --------------------------------------------------------

    live_price = float(
        prices.iloc[-1]
    )


    # --------------------------------------------------------
    # PREVIOUS TRADING DAY CLOSE
    # --------------------------------------------------------

    daily_data = stock.history(
        period="5d",
        interval="1d",
        auto_adjust=False,
        prepost=False
    )


    previous_close = None


    if (
        daily_data is not None
        and not daily_data.empty
    ):

        daily_closes = (
            pd_series_numeric(
                daily_data["Close"]
            )
            .dropna()
        )

        daily_closes = daily_closes[
            daily_closes > 0
        ]


        if len(daily_closes) >= 2:

            previous_close = float(
                daily_closes.iloc[-2]
            )


    # --------------------------------------------------------
    # DAILY CHANGE
    # --------------------------------------------------------

    daily_change = None


    if (
        previous_close is not None
        and previous_close > 0
    ):

        daily_change = (
            (
                live_price
                - previous_close
            )
            / previous_close
        ) * 100


    # --------------------------------------------------------
    # LAST MARKET TIMESTAMP
    # --------------------------------------------------------

    last_timestamp = intraday.index[-1]

    try:

        if last_timestamp.tzinfo is None:

            last_timestamp = (
                last_timestamp
                .tz_localize("Asia/Kolkata")
            )

        else:

            last_timestamp = (
                last_timestamp
                .tz_convert("Asia/Kolkata")
            )

    except Exception:

        pass


    last_updated = (
        last_timestamp.strftime(
            "%d-%b-%Y %H:%M:%S"
        )
    )


    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    result = {

        "price": round(
            live_price,
            2
        ),

        "previous_close": (
            round(previous_close, 2)
            if previous_close is not None
            else None
        ),

        "daily_change_%": (
            round(daily_change, 2)
            if daily_change is not None
            else None
        ),

        "last_updated": last_updated,

        "source": (
            "Yahoo Finance Intraday"
        ),
    }


    print(
        f"LIVE price received: "
        f"{display_name} = "
        f"₹{result['price']:.2f}"
    )

    return result


# ============================================================
# GET COMPLETE STOCK DATA
# ============================================================

def get_stock_data(stock_name):
    """
    Compatibility function used by main.py.

    Returns latest valid daily market data.
    """

    resolved = resolve_security(
        stock_name
    )

    return get_daily_market_data(
        resolved["yahoo_symbol"],
        stock_display_name=stock_name
    )


# ============================================================
# GET LIVE STOCK DATA
# ============================================================

def get_live_stock_data(stock_name):
    """
    Main function used by the live dashboard.

    Behaviour:

        During market hours:
            Intraday price.

        Outside market hours:
            Latest daily closing price.

        If intraday fails:
            Automatically fall back to daily data.

    Historical database is NOT modified.
    """

    resolved = resolve_security(
        stock_name
    )

    yahoo_symbol = resolved[
        "yahoo_symbol"
    ]


    now = datetime.now(
        IST
    )


    print()
    print(
        "=" * 60
    )

    print(
        f"MARKET DATA REQUEST"
    )

    print(
        f"Input       : {stock_name}"
    )

    print(
        f"NSE Symbol  : "
        f"{resolved['nse_symbol']}"
    )

    print(
        f"Yahoo       : "
        f"{yahoo_symbol}"
    )

    print(
        f"ISIN        : "
        f"{resolved.get('isin', '') or 'Not configured'}"
    )

    print(
        f"IST Time    : "
        f"{now.strftime('%d-%b-%Y %H:%M:%S')}"
    )

    print(
        f"Market Open : "
        f"{is_market_open(now)}"
    )

    print(
        "=" * 60
    )


    # ========================================================
    # MARKET OPEN
    # ========================================================

    if is_market_open(now):

        try:

            return get_intraday_market_data(
                yahoo_symbol,
                stock_display_name=stock_name
            )

        except Exception as intraday_error:

            print(
                f"⚠️ Intraday data unavailable "
                f"for {stock_name}"
            )

            print(
                f"Reason: {intraday_error}"
            )

            print(
                "Attempting daily close fallback..."
            )


    # ========================================================
    # MARKET CLOSED
    # ========================================================

    else:

        print(
            "Indian market is currently closed."
        )

        print(
            "Using latest completed daily close."
        )


    # ========================================================
    # DAILY FALLBACK
    # ========================================================

    try:

        return get_daily_market_data(
            yahoo_symbol,
            stock_display_name=stock_name
        )

    except Exception as daily_error:

        print(
            f"❌ Market data unavailable "
            f"for {stock_name}"
        )

        print(
            f"Reason: {daily_error}"
        )

        raise Exception(
            f"Valid market data unavailable "
            f"for {stock_name}"
        ) from daily_error


# ============================================================
# GET STOCK PRICE
# ============================================================

def get_stock_price(stock_name):
    """
    Compatibility function.

    Returns only the latest valid price.
    """

    data = get_stock_data(
        stock_name
    )

    price = data.get(
        "price"
    )

    if (
        price is None
        or price <= 0
    ):

        raise Exception(
            f"Invalid NSE price "
            f"for {stock_name}"
        )

    return price


# ============================================================
# GET DAILY CHANGE
# ============================================================

def get_daily_change(stock_name):
    """
    Return latest daily percentage change.
    """

    data = get_stock_data(
        stock_name
    )

    return data.get(
        "daily_change_%"
    )


# ============================================================
# GET 52 WEEK LOW
# ============================================================

def get_52_week_low(stock_name):
    """
    Return latest 52-week low.
    """

    data = get_stock_data(
        stock_name
    )

    return data.get(
        "52_week_low"
    )


# ============================================================
# GET COMPLETE MARKET MONITORING DATA
# ============================================================

def get_market_monitoring_data(stock_name):
    """
    Return complete market monitoring information.
    """

    return get_stock_data(
        stock_name
    )


# ============================================================
# LOWER CIRCUIT
# ============================================================

def get_lower_circuit(stock_name):
    """
    Yahoo Finance does not reliably provide the actual
    NSE price-band limit.

    Therefore the system deliberately does NOT estimate
    or invent a circuit price.
    """

    data = get_stock_data(
        stock_name
    )

    return {

        "current_price":
            data["price"],

        "lower_circuit":
            None,

        "distance_percent":
            None,

        "status":
            "⚪ Circuit Data Not Available"
    }


# ============================================================
# TEST / DEBUG
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "LOAN COLLATERAL MARKET DATA TEST"
    )
    print(
        "=" * 60
    )

    test_securities = [

        "Kalyan Jewellers India Limited",

        "INE303R01014",

        "KALYANKJIL",

        "Mindspace Business Parks REIT",

        "INE0CCU25019",

        "MINDSPACE",

        "JSW Energy",

        "JSW Steel",

        "Jindal Steel & Power",
    ]


    for security in test_securities:

        print()
        print(
            "-" * 60
        )

        try:

            data = get_live_stock_data(
                security
            )

            print(
                f"SUCCESS: {security}"
            )

            print(
                f"Price        : "
                f"{data.get('price')}"
            )

            print(
                f"Previous     : "
                f"{data.get('previous_close')}"
            )

            print(
                f"Daily Change : "
                f"{data.get('daily_change_%')}%"
            )

            print(
                f"Updated      : "
                f"{data.get('last_updated')}"
            )

            print(
                f"Source       : "
                f"{data.get('source')}"
            )

        except Exception as e:

            print(
                f"FAILED: {security}"
            )

            print(
                f"Reason: {e}"
            )