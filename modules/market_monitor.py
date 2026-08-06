import pandas as pd



def calculate_daily_change(current_price, previous_price):

    if previous_price == 0:
        return 0


    change = (
        (current_price - previous_price)
        /
        previous_price
    ) * 100


    return round(change, 2)




def check_price_alerts(
        current_price,
        previous_price,
        stock_name
):

    alerts = []


    daily_change = calculate_daily_change(
        current_price,
        previous_price
    )


    # 5% fall alert

    if daily_change <= -5:

        alerts.append(
            {
                "type": "PRICE FALL",
                "stock": stock_name,
                "message":
                f"{stock_name} fallen {daily_change}%"
            }
        )



    # Lower circuit approximation
    # Indian equity circuits generally 5%,10%,20%
    # This is a monitoring alert, not exchange confirmation


    if daily_change <= -9.5:

        alerts.append(
            {
                "type": "LOWER CIRCUIT",
                "stock": stock_name,
                "message":
                f"{stock_name} may be near lower circuit"
            }
        )



    # Upper circuit


    if daily_change >= 9.5:

        alerts.append(
            {
                "type": "UPPER CIRCUIT",
                "stock": stock_name,
                "message":
                f"{stock_name} may be near upper circuit"
            }
        )


    return alerts




def add_market_monitoring(df):

    """
    Add daily price movement analysis
    """

    result = df.copy()


    result["daily_change_%"] = 0


    result["market_alert"] = "Normal"



    for security in result["security"].unique():

        stock_data = result[
            result["security"] == security
        ]


        if len(stock_data) > 1:


            stock_data = stock_data.sort_values(
                "date"
            )


            current = stock_data.iloc[-1]

            previous = stock_data.iloc[-2]


            change = calculate_daily_change(
                current["price"],
                previous["price"]
            )


            result.loc[
                result.index == current.name,
                "daily_change_%"
            ] = change



            if change <= -5:


                result.loc[
                    result.index == current.name,
                    "market_alert"
                ] = "🚨 Price Fall Alert"



            elif change >= 5:


                result.loc[
                    result.index == current.name,
                    "market_alert"
                ] = "⚠️ Price Rise"



    return result