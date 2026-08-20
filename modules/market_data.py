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
import io
import zipfile
import requests


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

}


    
# ============================================================
# BACKWARD-COMPATIBILITY SYMBOL DICTIONARY
# ============================================================

SYMBOLS = {
   
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
# NSE DAILY BHAVCOPY
# ============================================================

def get_nse_eod_price(
    nse_symbol=None,
    isin=None,
    trading_date=None,
):
    """
    Fetch the latest available official NSE CM Bhavcopy.

    NSE now exposes Bhavcopy through its Daily Reports API.
    We do NOT construct the filename ourselves.

    The function:

    1. Asks NSE which CM Bhavcopy is actually available.
    2. Selects the latest trading date <= requested date.
    3. Downloads the official ZIP.
    4. Reads the CSV inside the ZIP.
    5. Matches security using ISIN first, then NSE symbol.
    6. Returns official NSE closing price and actual trading date.

    Returns:

        {
            "price": float,
            "trading_date": date
        }

        or None if unavailable.
    """

    if trading_date is None:

        trading_date = datetime.now(
            IST
        ).date()

    headers = {

        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),

        "Accept": (
            "application/json, text/plain, */*"
        ),

        "Referer": (
            "https://www.nseindia.com/all-reports"
        ),
    }

    try:

        print(
            f"Finding latest NSE CM Bhavcopy "
            f"for {trading_date.strftime('%d-%b-%Y')}..."
        )

        # ----------------------------------------------------
        # NSE DAILY REPORTS API
        # ----------------------------------------------------

        session = requests.Session()

        session.headers.update(
            headers
        )

        reports_response = session.get(
            "https://www.nseindia.com/api/daily-reports?key=CM",
            timeout=30,
        )

        if reports_response.status_code != 200:

            print(
                "NSE daily-reports API unavailable. "
                f"HTTP {reports_response.status_code}"
            )

            return None

        reports_json = (
            reports_response.json()
        )

        # ----------------------------------------------------
        # FIND AVAILABLE BHAVCOPY REPORTS
        # ----------------------------------------------------

        candidates = []

        for bucket_name in (
            "CurrentDay",
            "PreviousDay",
        ):

            bucket = reports_json.get(
                bucket_name,
                []
            )

            if not isinstance(
                bucket,
                list
            ):
                continue

            for report in bucket:

                file_key = str(
                    report.get(
                        "fileKey",
                        ""
                    )
                ).upper()

                # ------------------------------------------------
                # ONLY USE NSE CM UDiFF COMMON BHAVCOPY FINAL
                # ------------------------------------------------
                #
                # Do NOT use:
                #
                #   CM-BHAVCOPY-PR-ZIP
                #   CM-BHAVCOPY-DAT
                #   SME-BHAVCOPY-CSV
                #   CM-BHAVDATA-FULL
                #
                # The UDiFF Common Bhavcopy Final is the official
                # security-price file containing the closing price.
                # ------------------------------------------------

                if file_key != "CM-UDIFF-BHAVCOPY-CSV":
                    continue

                report_date_text = (
                    report.get(
                        "tradingDate"
                    )
                )

                if not report_date_text:
                    continue

                try:

                    report_date = (
                        datetime.strptime(
                            report_date_text,
                            "%d-%b-%Y"
                        ).date()
                    )

                except Exception:

                    continue

                if report_date <= trading_date:

                    candidates.append(
                        (
                            report_date,
                            report
                        )
                    )

        if not candidates:

            print(
                "No NSE CM Bhavcopy is "
                "currently available."
            )

            return None

        # ----------------------------------------------------
        # SELECT LATEST AVAILABLE TRADING DATE
        # ----------------------------------------------------

        candidates.sort(
            key=lambda item: item[0],
            reverse=True
        )

        selected_date, selected_report = (
            candidates[0]
        )

        file_path = (
            selected_report.get(
                "filePath"
            )
            or ""
        ).rstrip("/")

        file_name = (
            selected_report.get(
                "fileActlName"
            )
            or ""
        )

        if not file_path or not file_name:

            print(
                "NSE report API returned an "
                "incomplete Bhavcopy record."
            )

            return None

        url = (
            f"{file_path}/{file_name}"
        )

        print(
            f"NSE Bhavcopy selected: "
            f"{file_name}"
        )

        print(
            f"NSE actual trading date: "
            f"{selected_date.strftime('%d-%b-%Y')}"
        )

        print(
            "Downloading NSE Bhavcopy..."
        )

        response = session.get(
            url,
            timeout=30,
        )

        if response.status_code != 200:

            print(
                "NSE Bhavcopy download failed. "
                f"HTTP {response.status_code}"
            )

            return None

        content = response.content

        if not content.startswith(
            b"PK"
        ):

            print(
                "NSE response is not a valid ZIP file."
            )

            return None

        # ----------------------------------------------------
        # READ ZIP
        # ----------------------------------------------------

        with zipfile.ZipFile(
            io.BytesIO(content)
        ) as archive:

            csv_files = [

                name

                for name
                in archive.namelist()

                if name.lower().endswith(
                    ".csv"
                )
            ]

            if not csv_files:

                print(
                    "NSE Bhavcopy ZIP contains "
                    "no CSV file."
                )

                return None

            print(
                f"NSE CSV inside ZIP: "
                f"{csv_files[0]}"
            )

            with archive.open(
                csv_files[0]
            ) as csv_file:

                df = pd.read_csv(
                    csv_file
                )

        # ----------------------------------------------------
        # NORMALIZE COLUMN NAMES
        # ----------------------------------------------------

        df.columns = (

            df.columns
            .astype(str)
            .str.strip()
        )

        # Create normalized helper columns.

        upper_columns = {
            str(column).strip().upper(): column
            for column in df.columns
        }

        # ----------------------------------------------------
        # FIND ISIN COLUMN
        # ----------------------------------------------------

        isin_column = None

        for candidate in (
            "ISIN",
            "ISINNO",
            "ISIN_NO",
            "ISINCODE",
        ):

            if candidate in upper_columns:

                isin_column = (
                    upper_columns[candidate]
                )

                break

        # ----------------------------------------------------
        # FIND SYMBOL COLUMN
        # ----------------------------------------------------

        symbol_column = None

        for candidate in (
            "TCKRSYMB",
            "TCKR_SYMB",
            "SYMBOL",
            "SYMBL",
            "SCTYSYMB",
            "SCTY_SYMB",
        ):

            if candidate in upper_columns:

                symbol_column = (
                    upper_columns[candidate]
                )

                break

        # ----------------------------------------------------
        # FIND CLOSING PRICE COLUMN
        # ----------------------------------------------------

        close_column = None

        for candidate in (
            "CLSPRIC",
            "CLS_PRIC",
            "CLSPRIC",
            "CLOSE",
            "CLOSEPRICE",
            "CLOSE_PRICE",
        ):

            if candidate in upper_columns:

                close_column = (
                    upper_columns[candidate]
                )

                break

        if close_column is None:

            print(
                "NSE Bhavcopy does not contain "
                "a recognizable closing-price column."
            )

            print(
                "Available columns:"
            )

            print(
                list(df.columns)
            )

            return None

        # ----------------------------------------------------
        # NORMALIZE MATCH FIELDS
        # ----------------------------------------------------

        if isin_column is not None:

            df["_ISIN"] = (

                df[isin_column]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

        if symbol_column is not None:

            df["_SYMBOL"] = (

                df[symbol_column]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

        # ----------------------------------------------------
        # MATCH SECURITY
        # ----------------------------------------------------

        matched = pd.DataFrame()

        if (
            isin
            and "_ISIN" in df.columns
        ):

            isin_normalized = (

                str(isin)
                .strip()
                .upper()
            )

            matched = df[
                df["_ISIN"]
                == isin_normalized
            ]

        if (
            matched.empty
            and nse_symbol
            and "_SYMBOL" in df.columns
        ):

            symbol_normalized = (

                str(nse_symbol)
                .strip()
                .upper()
                .replace(
                    ".NS",
                    ""
                )
            )

            matched = df[
                df["_SYMBOL"]
                == symbol_normalized
            ]

        if matched.empty:

            print(
                "NSE security not found: "
                f"{nse_symbol or isin}"
            )

            return None

        # ----------------------------------------------------
        # CLOSING PRICE
        # ----------------------------------------------------

        price_series = pd.to_numeric(
            matched[close_column],
            errors="coerce"
        ).dropna()

        price_series = (
            price_series[
                price_series > 0
            ]
        )

        if price_series.empty:

            print(
                "No valid NSE closing price for "
                f"{nse_symbol or isin}"
            )

            return None

        price = float(
            price_series.iloc[0]
        )

        print(
            "NSE OFFICIAL EOD PRICE: "
            f"{nse_symbol or isin} = "
            f"Rs.{price:.2f}"
        )

        print(
            "NSE OFFICIAL TRADING DATE: "
            f"{selected_date.strftime('%d-%b-%Y')}"
        )

        return {

            "price": round(
                price,
                2
            ),

            "trading_date": (
                selected_date
            ),
        }

    except Exception as e:

        print(
            f"NSE Bhavcopy error: {e}"
        )

        return None


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

        # ----------------------------------------------------
        # NSE OFFICIAL EOD BHAVCOPY
        # ----------------------------------------------------
        #
        # After market close, prefer the current trading day's
        # NSE Bhavcopy over Yahoo Finance.
        #
        # This prevents stale Yahoo daily data from being used
        # as today's closing price.
        # ----------------------------------------------------

        today = datetime.now(
            IST
        ).date()

        resolved = resolve_security(
            stock_display_name
            or yahoo_symbol
        )

        nse_result = get_nse_eod_price(
            nse_symbol=resolved.get(
                "nse_symbol"
            ),
            isin=resolved.get(
                "isin"
            ),
            trading_date=today,
        )

        nse_price = None
        nse_trading_date = None

        if nse_result is not None:

            nse_price = float(
                nse_result.get(
                    "price"
                )
            )

            nse_trading_date = (
                nse_result.get(
                    "trading_date"
                )
            )

        if nse_price is not None:

            # Use NSE official closing price.
            #
            # We still fetch Yahoo history below because the
            # existing function calculates previous close and
            # 52-week-low statistics from Yahoo's history.

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

                # NSE has today's authoritative close, so we
                # can still return today's price even if Yahoo
                # history is unavailable.

                return {
                    "price": round(
                        nse_price,
                        2
                    ),
                    "previous_close": None,
                    "daily_change_%": None,
                    "52_week_low": None,
                    "distance_from_52_week_low_%": None,
                    "last_updated": (
                        today.strftime(
                            "%d-%b-%Y"
                        )
                    ),
                    "source": (
                        "NSE Bhavcopy EOD"
                    ),
                }

            # Continue through the existing Yahoo-history
            # calculations, but today's price will be replaced
            # by the verified NSE close below.

        else:

            # NSE EOD unavailable.
            # Fall back to existing Yahoo Finance logic.

            stock = yf.Ticker(
                yahoo_symbol
            )

            data = stock.history(
                period="1y",
                interval="1d",
                auto_adjust=False,
                prepost=False
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

        if nse_price is not None:

            latest_price = float(
                nse_price
            )

        else:

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

        # If NSE Bhavcopy supplied today's official EOD price,
        # use the NSE trading date rather than Yahoo's date.
        # Yahoo may lag for securities such as REITs.

        if nse_price is not None:

            if nse_trading_date is not None:

                try:

                    if hasattr(
                        nse_trading_date,
                        "strftime"
                    ):

                        last_updated = (
                            nse_trading_date.strftime(
                                "%d-%b-%Y"
                            )
                        )

                    else:

                        last_updated = str(
                            nse_trading_date
                        )

                except Exception:

                    last_updated = str(
                        nse_trading_date
                    )

            else:

                last_updated = (
                    today.strftime(
                        "%d-%b-%Y"
                    )
                )

        else:

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
                "NSE UDiFF Common Bhavcopy"
                if nse_price is not None
                else "Yahoo Finance Daily Close"
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
    # VALID LIVE CLOSE VALUES
    # --------------------------------------------------------

    prices = pd_series_numeric(
        intraday["Close"]
    )

    # Keep only rows with a valid positive price. This preserves
    # the timestamp belonging to the actual price being used.
    valid_intraday = intraday.loc[
        prices.notna() & (prices > 0)
    ].copy()

    if valid_intraday.empty:

        raise Exception(
            f"No valid live price received "
            f"for {display_name}"
        )


    # --------------------------------------------------------
    # LAST INTRADAY TIMESTAMP
    # --------------------------------------------------------

    last_timestamp = valid_intraday.index[-1]

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


    # --------------------------------------------------------
    # CRITICAL LIVE-DATA VALIDATION
    # --------------------------------------------------------
    # During Indian market hours we must NEVER accept a
    # previous-day intraday response as today's live price.
    # Yahoo can occasionally return stale/lagging intraday
    # data for individual securities (notably some REITs).
    #
    # If the latest timestamp is not today's IST date, reject
    # it. The dashboard will then show "Price Unavailable"
    # instead of silently displaying yesterday's price.
    # --------------------------------------------------------

    now_ist = datetime.now(IST)

    if last_timestamp.date() != now_ist.date():

        raise Exception(
            f"Stale intraday data for {display_name}: "
            f"latest timestamp is "
            f"{last_timestamp.strftime('%d-%b-%Y %H:%M:%S')} IST, "
            f"but today is {now_ist.strftime('%d-%b-%Y')}."
        )


    # Do not accept a future-dated response. A small 5-minute
    # tolerance protects against minor provider clock skew.
    if last_timestamp > now_ist + pd.Timedelta(minutes=5):

        raise Exception(
            f"Invalid future intraday timestamp for {display_name}: "
            f"{last_timestamp.strftime('%d-%b-%Y %H:%M:%S')} IST"
        )


    # --------------------------------------------------------
    # LATEST INTRADAY PRICE
    # --------------------------------------------------------

    live_price = float(
        pd.to_numeric(
            valid_intraday["Close"],
            errors="coerce"
        ).iloc[-1]
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
    # last_timestamp was already normalized and validated above.

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

        If intraday fails during market hours:
            DO NOT fall back to a previous-day price.
            Raise an error so the dashboard shows that the
            live price is unavailable.

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

        # During market hours, NEVER substitute an EOD/previous-day
        # price when the live feed fails. A stale collateral price
        # is more dangerous than an explicit unavailable status.
        try:

            return get_intraday_market_data(
                yahoo_symbol,
                stock_display_name=stock_name
            )

        except Exception as intraday_error:

            print(
                f"⚠️ LIVE intraday data unavailable "
                f"for {stock_name}"
            )

            print(
                f"Reason: {intraday_error}"
            )

            raise Exception(
                f"Live market price unavailable for {stock_name}. "
                f"No previous-day price will be used during market hours."
            ) from intraday_error


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