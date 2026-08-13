# -*- coding: utf-8 -*-

import sys
import pandas as pd
import yfinance as yf
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# STOCK SYMBOL CONFIGURATION
# ============================================================

SYMBOLS = {

    "JSW Energy": "JSWENERGY.NS",

    "JSW Steel": "JSWSTEEL.NS",

    "Jindal Steel & Power": "JINDALSTEL.NS"

}


# ============================================================
# GET STOCK DATA
# ============================================================

def get_stock_data(stock_name):

    """
    Fetch latest valid market data for an NSE-listed stock.

    Source:
        Yahoo Finance NSE-listed symbol

    Returns:

        {
            "price": latest closing price,
            "previous_close": previous trading-day close,
            "daily_change_%": daily percentage change,
            "52_week_low": 52-week low,
            "distance_from_52_week_low_%": percentage distance
        }

    Important:
    - Never returns zero as a valid price.
    - Raises an exception if valid price data is unavailable.
    """

    # ========================================================
    # CHECK SYMBOL
    # ========================================================

    if stock_name not in SYMBOLS:

        raise Exception(
            f"Symbol not configured for {stock_name}"
        )


    symbol = SYMBOLS[stock_name]


    print(
        f"Fetching NSE price for "
        f"{stock_name} ({symbol})..."
    )


    # ========================================================
    # FETCH DATA
    # ========================================================

    try:

        stock = yf.Ticker(
            symbol
        )


        data = stock.history(
            period="1y",
            interval="1d",
            auto_adjust=False
        )


        # ====================================================
        # CHECK DATA
        # ====================================================

        if data is None or data.empty:

            raise Exception(
                f"No market data received for "
                f"{stock_name}"
            )


        # ====================================================
        # CLOSE PRICES
        # ====================================================

        close_prices = (
            pd_series_numeric(
                data["Close"]
            )
            .dropna()
        )


        if close_prices.empty:

            raise Exception(
                f"No valid closing prices received "
                f"for {stock_name}"
            )


        # ====================================================
        # LATEST PRICE
        # ====================================================

        latest_price = float(
            close_prices.iloc[-1]
        )


        if latest_price <= 0:

            raise Exception(
                f"Invalid latest price "
                f"{latest_price} for {stock_name}"
            )


        # ====================================================
        # PREVIOUS CLOSE
        # ====================================================

        if len(close_prices) >= 2:

            previous_close = float(
                close_prices.iloc[-2]
            )

        else:

            previous_close = None


        # ====================================================
        # DAILY CHANGE
        # ====================================================

        if (
            previous_close is not None
            and previous_close > 0
        ):

            daily_change = (
                (
                    latest_price
                    -
                    previous_close
                )
                /
                previous_close
            ) * 100

        else:

            daily_change = None


        # ====================================================
        # 52 WEEK LOW
        # ====================================================

        week_52_low = float(
            close_prices.min()
        )


        if week_52_low <= 0:

            week_52_low = None


        # ====================================================
        # DISTANCE FROM 52 WEEK LOW
        # ====================================================

        if (
            week_52_low is not None
            and week_52_low > 0
        ):

            distance_from_low = (
                (
                    latest_price
                    -
                    week_52_low
                )
                /
                week_52_low
            ) * 100

        else:

            distance_from_low = None


        # ====================================================
        # ROUND VALUES
        # ====================================================

        latest_price = round(
            latest_price,
            2
        )


        if previous_close is not None:

            previous_close = round(
                previous_close,
                2
            )


        if daily_change is not None:

            daily_change = round(
                daily_change,
                2
            )


        if week_52_low is not None:

            week_52_low = round(
                week_52_low,
                2
            )


        if distance_from_low is not None:

            distance_from_low = round(
                distance_from_low,
                2
            )


        # ====================================================
        # DISPLAY
        # ====================================================

        print(
            f"NSE price received: "
            f"{stock_name} = ₹{latest_price:.2f}"
        )


        if previous_close is not None:

            print(
                f"Previous Close : "
                f"₹{previous_close:.2f}"
            )


        if daily_change is not None:

            print(
                f"Daily Change : "
                f"{daily_change:.2f}%"
            )


        if week_52_low is not None:

            print(
                f"52 Week Low : "
                f"₹{week_52_low:.2f}"
            )


        # ====================================================
        # RETURN DATA
        # ====================================================

        return {

            "price":
                latest_price,

            "previous_close":
                previous_close,

            "daily_change_%":
                daily_change,

            "52_week_low":
                week_52_low,

            "distance_from_52_week_low_%":
                distance_from_low

        }


    # ========================================================
    # ERROR
    # ========================================================

    except Exception as e:

        print()

        print(
            f"❌ Market data error for "
            f"{stock_name}: {e}"
        )


        raise Exception(
            f"Valid NSE market data unavailable "
            f"for {stock_name}"
        ) from e





    # ============================================================
# GET LIVE INTRADAY STOCK DATA
# ============================================================

def get_live_stock_data(stock_name):
    """
    Fetch latest intraday market price for an NSE-listed stock.

    Uses Yahoo Finance 1-minute intraday data.

    This function is ONLY for live dashboard monitoring.
    It does NOT modify the historical database.
    """

    if stock_name not in SYMBOLS:
        raise Exception(
            f"Symbol not configured for {stock_name}"
        )

    symbol = SYMBOLS[stock_name]

    print(
        f"Fetching LIVE NSE price for "
        f"{stock_name} ({symbol})..."
    )

    try:

        stock = yf.Ticker(symbol)

        # ----------------------------------------------------
        # LIVE / INTRADAY DATA
        # ----------------------------------------------------

        intraday = stock.history(
            period="1d",
            interval="1m",
            auto_adjust=False,
            prepost=False
        )

        if intraday is None or intraday.empty:
            raise Exception(
                f"No intraday data received for "
                f"{stock_name}"
            )

        # ----------------------------------------------------
        # VALID CLOSE VALUES
        # ----------------------------------------------------

        prices = (
            pd.to_numeric(
                intraday["Close"],
                errors="coerce"
            )
            .dropna()
        )

        prices = prices[
            prices > 0
        ]

        if prices.empty:
            raise Exception(
                f"No valid live price received for "
                f"{stock_name}"
            )

        # ----------------------------------------------------
        # LATEST INTRADAY PRICE
        # ----------------------------------------------------

        live_price = float(
            prices.iloc[-1]
        )

        # ----------------------------------------------------
        # PREVIOUS TRADING DAY CLOSE
        # ----------------------------------------------------

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
                pd.to_numeric(
                    daily_data["Close"],
                    errors="coerce"
                )
                .dropna()
            )

            if len(daily_closes) >= 2:
                previous_close = float(
                    daily_closes.iloc[-2]
                )

        # ----------------------------------------------------
        # LIVE DAILY CHANGE
        # ----------------------------------------------------

        daily_change = None

        if previous_close and previous_close > 0:
                  
            daily_change = (
                (live_price- previous_close)
                / previous_close
            ) * 100

        # ----------------------------------------------------
        # LAST MARKET DATA TIMESTAMP
        # ----------------------------------------------------

        
        last_timestamp = intraday.index[-1]

        # Convert to India time
        try:

            if last_timestamp.tzinfo is None:
                last_timestamp = last_timestamp.tz_localize(
                    "Asia/Kolkata"
                )
            else:
                last_timestamp = last_timestamp.tz_convert(
                    "Asia/Kolkata"
                )

        except Exception:
            pass

        return {
        
    "price": round(live_price, 2),

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

   
    "last_updated": last_timestamp.strftime(
        "%d-%b-%Y %H:%M:%S"
    ),
    "source": "Yahoo Finance Intraday"
}

    except Exception as e:

        print(
            f"❌ Live market data error for "
            f"{stock_name}: {e}"
        )

        raise Exception(
            f"Live NSE market data unavailable "
            f"for {stock_name}"
        ) from e



    # ========================================================
    # CHECK SYMBOL
    # ========================================================

    if stock_name not in SYMBOLS:

        raise Exception(
            f"Symbol not configured for {stock_name}"
        )


    symbol = SYMBOLS[stock_name]


    print(
        f"Fetching NSE price for "
        f"{stock_name} ({symbol})..."
    )


    # ========================================================
    # FETCH DATA
    # ========================================================

    try:

        stock = yf.Ticker(
            symbol
        )


        data = stock.history(
            period="1y",
            interval="1d",
            auto_adjust=False
        )


        # ====================================================
        # CHECK DATA
        # ====================================================

        if data is None or data.empty:

            raise Exception(
                f"No market data received for "
                f"{stock_name}"
            )


        # ====================================================
        # CLOSE PRICES
        # ====================================================

        close_prices = (
            pd_series_numeric(
                data["Close"]
            )
            .dropna()
        )


        if close_prices.empty:

            raise Exception(
                f"No valid closing prices received "
                f"for {stock_name}"
            )


        # ====================================================
        # LATEST PRICE
        # ====================================================

        latest_price = float(
            close_prices.iloc[-1]
        )


        if latest_price <= 0:

            raise Exception(
                f"Invalid latest price "
                f"{latest_price} for {stock_name}"
            )


        # ====================================================
        # PREVIOUS CLOSE
        # ====================================================

        if len(close_prices) >= 2:

            previous_close = float(
                close_prices.iloc[-2]
            )

        else:

            previous_close = None


        # ====================================================
        # DAILY CHANGE
        # ====================================================

        if (
            previous_close is not None
            and previous_close > 0
        ):

            daily_change = (
                (
                    latest_price
                    -
                    previous_close
                )
                /
                previous_close
            ) * 100

        else:

            daily_change = None


        # ====================================================
        # 52 WEEK LOW
        # ====================================================

        week_52_low = float(
            close_prices.min()
        )


        if week_52_low <= 0:

            week_52_low = None


        # ====================================================
        # DISTANCE FROM 52 WEEK LOW
        # ====================================================

        if (
            week_52_low is not None
            and week_52_low > 0
        ):

            distance_from_low = (
                (
                    latest_price
                    -
                    week_52_low
                )
                /
                week_52_low
            ) * 100

        else:

            distance_from_low = None


        # ====================================================
        # ROUND VALUES
        # ====================================================

        latest_price = round(
            latest_price,
            2
        )


        if previous_close is not None:

            previous_close = round(
                previous_close,
                2
            )


        if daily_change is not None:

            daily_change = round(
                daily_change,
                2
            )


        if week_52_low is not None:

            week_52_low = round(
                week_52_low,
                2
            )


        if distance_from_low is not None:

            distance_from_low = round(
                distance_from_low,
                2
            )


        # ====================================================
        # DISPLAY
        # ====================================================

        print(
            f"NSE price received: "
            f"{stock_name} = ₹{latest_price:.2f}"
        )


        if previous_close is not None:

            print(
                f"Previous Close : "
                f"₹{previous_close:.2f}"
            )


        if daily_change is not None:

            print(
                f"Daily Change : "
                f"{daily_change:.2f}%"
            )


        if week_52_low is not None:

            print(
                f"52 Week Low : "
                f"₹{week_52_low:.2f}"
            )


        # ====================================================
        # RETURN DATA
        # ====================================================

        return {

            "price":
                latest_price,

            "previous_close":
                previous_close,

            "daily_change_%":
                daily_change,

            "52_week_low":
                week_52_low,

            "distance_from_52_week_low_%":
                distance_from_low

        }


    # ========================================================
    # ERROR
    # ========================================================

    except Exception as e:

        print()

        print(
            f"❌ Market data error for "
            f"{stock_name}: {e}"
        )


        raise Exception(
            f"Valid NSE market data unavailable "
            f"for {stock_name}"
        ) from e



# ============================================================
# HELPER — NUMERIC SERIES
# ============================================================

def pd_series_numeric(series):

    """
    Convert a pandas Series into numeric values.

    Kept as a small helper so the main function
    remains easy to read.
    """

    import pandas as pd

    return pd.to_numeric(
        series,
        errors="coerce"
    )



# ============================================================
# GET STOCK PRICE
# ============================================================

def get_stock_price(stock_name):

    """
    Compatibility function used by main.py.

    Returns only the latest valid NSE closing price.
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
            f"Invalid NSE price for "
            f"{stock_name}"
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
    Return the latest 52-week low.
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
    Return all available market-monitoring information.
    """

    return get_stock_data(
        stock_name
    )



# ============================================================
# LOWER CIRCUIT
# ============================================================

def get_lower_circuit(stock_name):

    """
    Circuit data is intentionally NOT estimated.

    We previously used a 20% fallback. That has been removed.

    This function remains only for compatibility with any
    existing code that may call it.

    It returns None for the lower circuit because Yahoo
    Finance does not reliably provide the actual NSE
    exchange price-band limit.

    The system must never invent a circuit price.
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
# GET LIVE INTRADAY STOCK DATA
# ============================================================

def get_live_stock_data(stock_name):
    """
    Fetch the latest intraday price for the dashboard.
    This does NOT modify the historical database.
    """

    if stock_name not in SYMBOLS:
        raise Exception(
            f"Symbol not configured for {stock_name}"
        )

    symbol = SYMBOLS[stock_name]

    print(
        f"Fetching LIVE NSE price for "
        f"{stock_name} ({symbol})..."
    )

    try:

        stock = yf.Ticker(symbol)

        intraday = stock.history(
            period="1d",
            interval="1m",
            auto_adjust=False,
            prepost=False
        )

        if intraday is None or intraday.empty:
            raise Exception(
                f"No intraday data received for {stock_name}"
            )

        prices = (
            pd.to_numeric(
                intraday["Close"],
                errors="coerce"
            )
            .dropna()
        )

        prices = prices[prices > 0]

        if prices.empty:
            raise Exception(
                f"No valid live price received for {stock_name}"
            )

        live_price = float(prices.iloc[-1])

        # Previous trading-day close
        daily_data = stock.history(
            period="5d",
            interval="1d",
            auto_adjust=False,
            prepost=False
        )

        previous_close = None

        if daily_data is not None and not daily_data.empty:

            daily_closes = (
                pd.to_numeric(
                    daily_data["Close"],
                    errors="coerce"
                )
                .dropna()
            )

            if len(daily_closes) >= 2:
                previous_close = float(
                    daily_closes.iloc[-2]
                )

        daily_change = None

        if previous_close and previous_close > 0:

            daily_change = (
                (live_price - previous_close)
                / previous_close
            ) * 100

            # ----------------------------------------------------
            # LAST MARKET DATA TIMESTAMP
            # ----------------------------------------------------

            last_timestamp = intraday.index[-1]

            try:
                if last_timestamp.tzinfo is None:
                    last_timestamp = last_timestamp.tz_localize(
                        "Asia/Kolkata"
                        )
                else:
                    last_timestamp = last_timestamp.tz_convert(
            "Asia/Kolkata"
            )
            except Exception:
                pass

        return {
            "price": round(live_price, 2),
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
            "last_updated": last_timestamp.strftime(
                "%d-%b-%Y %H:%M:%S"
            ),
            "source": "Yahoo Finance Intraday"
        }

    except Exception as e:

        print(
            f"❌ Live market data error for "
            f"{stock_name}: {e}"
        )

        raise Exception(
            f"Live market data unavailable "
            f"for {stock_name}"
        ) from e