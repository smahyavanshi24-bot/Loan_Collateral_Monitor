import yfinance as yf



def get_stock_price(stock_name):

    """
    Fetch latest market price
    """


    symbols = {

        "JSW Energy": "JSWENERGY.NS",

        "JSW Steel": "JSWSTEEL.NS",

        "Jindal Steel & Power": "JINDALSTEL.NS"

    }


    if stock_name not in symbols:

        raise Exception(
            f"Symbol not configured for {stock_name}"
        )



    symbol = symbols[stock_name]


    try:


        stock = yf.Ticker(symbol)


        data = stock.history(
            period="1d"
        )


        if data.empty:

            raise Exception(
                "No market data received"
            )


        price = float(
            data["Close"].iloc[-1]
        )


        return round(
            price,
            2
        )


    except Exception as e:


        print(
            "Market Data Error:",
            e
        )


        return 0