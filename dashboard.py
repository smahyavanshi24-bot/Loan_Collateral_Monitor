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
"Credit Risk Dashboard | Collateral, Security Cover & Share Movement Monitoring"
)

# ============================================================

# LOAD COLLATERAL HISTORY

# ============================================================

df = get_collateral_history()

# ============================================================

# NO DATA CHECK

# ============================================================

if df.empty:

```
st.warning("No collateral data available.")

st.info(
    "Please run the collateral monitoring process first."
)

st.stop()
```

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

df = df[
df["date"].notna()
].copy()

df["date"] = (
df["date"]
.dt.normalize()
)

# ============================================================

# REMOVE SATURDAY AND SUNDAY

# ============================================================

df = df[
df["date"].dt.weekday < 5
].copy()

# ============================================================

# NUMERIC COLUMNS

# ============================================================

for column in [
"price",
"shares",
"loan_amount",
"collateral_value",
"cover",
"required_cover"
]:

```
if column in df.columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )
```

# ============================================================

# SORT HISTORICAL DATA

# ============================================================

df = df.sort_values(
[
"date",
"borrower",
"security"
]
).reset_index(
drop=True
)

# ============================================================

# LATEST TRADING DATE

# ============================================================

latest_trading_date = df["date"].max()

# ============================================================

# ============================================================

# CURRENT SHARE POSITION

# ============================================================

#

# IMPORTANT:

#

# Historical database records are NEVER modified.

#

# Historical shares:

# remain exactly as recorded in collateral.db

#

# Current shares:

# historical latest shares

# + additions

# - releases

#

# Current collateral:

# current shares × latest price

#

# Current cover:

# current collateral / loan amount

#

# ============================================================

# ============================================================

latest_df = df[
df["date"] == latest_trading_date
].copy()

# ============================================================

# GET CURRENT SHARE POSITION

# ============================================================

current_share_records = []

for _, row in latest_df.iterrows():

```
borrower = row["borrower"]
security = row["security"]

historical_shares = int(
    row["shares"]
)

try:

    current_shares = get_current_shares(
        borrower,
        security,
        historical_shares
    )

except TypeError:

    try:

        current_shares = get_current_shares(
            borrower,
            security
        )

    except Exception:

        current_shares = historical_shares

except Exception:

    current_shares = historical_shares


try:

    current_shares = int(
        current_shares
    )

except Exception:

    current_shares = historical_shares


current_share_records.append(
    {
        "borrower": borrower,
        "security": security,
        "historical_shares": historical_shares,
        "current_shares": current_shares
    }
)
```

current_shares_df = pd.DataFrame(
current_share_records
)

# ============================================================

# BUILD CURRENT COLLATERAL DATA

# ============================================================

current_df = latest_df.merge(
current_shares_df,
on=[
"borrower",
"security"
],
how="left"
)

# ============================================================

# CURRENT COLLATERAL

# ============================================================

current_df["current_collateral"] = (
current_df["price"]
*
current_df["current_shares"]
)

# ============================================================

# CURRENT COVER

# ============================================================

current_df["current_cover"] = (
current_df["current_collateral"]
/
current_df["loan_amount"]
)

# ============================================================

# REQUIRED COVER

# ============================================================

if "required_cover" not in current_df.columns:

```
current_df["required_cover"] = 2.00
```

else:

```
current_df["required_cover"] = (
    current_df["required_cover"]
    .fillna(2.00)
)
```

# ============================================================

# CURRENT BUFFER

# ============================================================

current_df["current_buffer"] = (
current_df["current_cover"]
-
current_df["required_cover"]
)

# ============================================================

# CURRENT STATUS

# ============================================================

def current_status(row):

```
if row["current_cover"] < row["required_cover"]:

    return "🔴 ADDITIONAL COLLATERAL REQUIRED"

return "🟢 COVER COMPLIANT"
```

current_df["current_status"] = (
current_df.apply(
current_status,
axis=1
)
)

# ============================================================

# SHARE CHANGE

# ============================================================

current_df["share_change"] = (
current_df["current_shares"]
-
current_df["historical_shares"]
)

# ============================================================

# ============================================================

# 1. CURRENT BORROWER COVER SUMMARY

# ============================================================

# ============================================================

st.subheader(
"👥 Current Borrower Cover Summary"
)

borrower_current = (
current_df
.groupby(
"borrower",
as_index=False
)
.agg(
loan_amount=(
"loan_amount",
"first"
),
current_collateral=(
"current_collateral",
"sum"
),
required_cover=(
"required_cover",
"first"
)
)
)

borrower_current["current_cover"] = (
borrower_current["current_collateral"]
/
borrower_current["loan_amount"]
)

borrower_current["buffer"] = (
borrower_current["current_cover"]
-
borrower_current["required_cover"]
)

borrower_current["status"] = (
borrower_current.apply(
lambda row:
"🔴 ADDITIONAL COLLATERAL REQUIRED"
if row["current_cover"]
<
row["required_cover"]
else
"🟢 COVER COMPLIANT",
axis=1
)
)

borrower_view = borrower_current.copy()

borrower_view = borrower_view.rename(
columns={
"borrower": "Borrower",
"loan_amount": "Loan Amount",
"current_collateral": "Current Collateral",
"current_cover": "Current Cover",
"required_cover": "Required Cover",
"buffer": "Buffer",
"status": "Status"
}
)

borrower_view["Loan Amount"] = (
borrower_view["Loan Amount"]
.apply(format_crore)
)

borrower_view["Current Collateral"] = (
borrower_view["Current Collateral"]
.apply(format_crore)
)

borrower_view["Current Cover"] = (
borrower_view["Current Cover"]
.apply(format_cover)
)

borrower_view["Required Cover"] = (
borrower_view["Required Cover"]
.apply(format_cover)
)

borrower_view["Buffer"] = (
borrower_view["Buffer"]
.apply(format_cover)
)

st.dataframe(
borrower_view,
width="stretch",
hide_index=True
)

# ============================================================

# ============================================================

# 2. CURRENT SECURITY POSITION

# ============================================================

# ============================================================

st.subheader(
"🔐 Current Security Position"
)

security_view = current_df[
[
"date",
"borrower",
"security",
"price",
"historical_shares",
"current_shares",
"share_change",
"current_collateral",
"loan_amount",
"current_cover",
"required_cover",
"current_buffer",
"current_status"
]
].copy()

security_view = security_view.rename(
columns={
"date": "Trading Date",
"borrower": "Borrower",
"security": "Security",
"price": "Price",
"historical_shares": "Historical Shares",
"current_shares": "Current Shares",
"share_change": "Share Change",
"current_collateral": "Current Collateral",
"loan_amount": "Loan Amount",
"current_cover": "Current Cover",
"required_cover": "Required Cover",
"current_buffer": "Buffer",
"current_status": "Status"
}
)

security_view["Trading Date"] = (
security_view["Trading Date"]
.dt.strftime("%d-%b-%Y")
)

security_view["Price"] = (
security_view["Price"]
.apply(
lambda x:
f"₹{x:,.2f}"
)
)

for column in [
"Historical Shares",
"Current Shares",
"Share Change"
]:

```
security_view[column] = (
    security_view[column]
    .apply(
        lambda x:
        f"{int(x):,}"
    )
)
```

security_view["Current Collateral"] = (
security_view["Current Collateral"]
.apply(format_crore)
)

security_view["Loan Amount"] = (
security_view["Loan Amount"]
.apply(format_crore)
)

security_view["Current Cover"] = (
security_view["Current Cover"]
.apply(format_cover)
)

security_view["Required Cover"] = (
security_view["Required Cover"]
.apply(format_cover)
)

security_view["Buffer"] = (
security_view["Buffer"]
.apply(format_cover)
)

security_view = security_view.sort_values(
[
"Borrower",
"Security"
]
)

st.dataframe(
security_view,
width="stretch",
hide_index=True
)

st.caption(
"Current shares include recorded additions/releases. "
"Historical database records remain unchanged."
)

# ============================================================

# ============================================================

# 3. ADDITIONAL COLLATERAL REQUIRED

# ============================================================

# ============================================================

st.subheader(
"🚨 Additional Collateral Required"
)

shortfall_df = current_df[
current_df["current_cover"]
<
current_df["required_cover"]
].copy()

if not shortfall_df.empty:

```
st.error(
    f"{len(shortfall_df)} security record(s) "
    "are below the required cover."
)


shortfall_view = shortfall_df[
    [
        "borrower",
        "security",
        "current_shares",
        "price",
        "current_collateral",
        "loan_amount",
        "current_cover",
        "required_cover"
    ]
].copy()


shortfall_view["additional_collateral_required"] = (
    shortfall_view["loan_amount"]
    *
    shortfall_view["required_cover"]
    -
    shortfall_view["current_collateral"]
)


shortfall_view = shortfall_view.rename(
    columns={
        "borrower": "Borrower",
        "security": "Security",
        "current_shares": "Current Shares",
        "price": "Price",
        "current_collateral": "Current Collateral",
        "loan_amount": "Loan Amount",
        "current_cover": "Current Cover",
        "required_cover": "Required Cover",
        "additional_collateral_required":
            "Additional Collateral Required"
    }
)


shortfall_view["Current Shares"] = (
    shortfall_view["Current Shares"]
    .apply(
        lambda x:
        f"{int(x):,}"
    )
)


shortfall_view["Price"] = (
    shortfall_view["Price"]
    .apply(
        lambda x:
        f"₹{x:,.2f}"
    )
)


shortfall_view["Current Collateral"] = (
    shortfall_view["Current Collateral"]
    .apply(format_crore)
)


shortfall_view["Loan Amount"] = (
    shortfall_view["Loan Amount"]
    .apply(format_crore)
)


shortfall_view["Current Cover"] = (
    shortfall_view["Current Cover"]
    .apply(format_cover)
)


shortfall_view["Required Cover"] = (
    shortfall_view["Required Cover"]
    .apply(format_cover)
)


shortfall_view[
    "Additional Collateral Required"
] = (
    shortfall_view[
        "Additional Collateral Required"
    ]
    .apply(format_crore)
)


st.dataframe(
    shortfall_view,
    width="stretch",
    hide_index=True
)
```

else:

```
st.success(
    "No additional collateral is currently required."
)
```

# ============================================================

# ============================================================

# 4. SHARE MOVEMENT ENTRY

# ============================================================

# ============================================================

#

# This section records ADD / RELEASE separately.

#

# It DOES NOT modify historical collateral records.

#

# ============================================================

st.subheader(
"🔄 Record Share Movement"
)

st.caption(
"Record an actual addition or release of pledged shares. "
"The historical collateral record is never changed."
)

movement_borrowers = sorted(
current_df["borrower"]
.dropna()
.unique()
.tolist()
)

if movement_borrowers:

```
movement_borrower = st.selectbox(
    "Borrower",
    movement_borrowers,
    key="movement_borrower"
)


movement_securities = sorted(
    current_df.loc[
        current_df["borrower"]
        ==
        movement_borrower,
        "security"
    ]
    .dropna()
    .unique()
    .tolist()
)


movement_security = st.selectbox(
    "Security",
    movement_securities,
    key="movement_security"
)


selected_current = current_df[
    (
        current_df["borrower"]
        ==
        movement_borrower
    )
    &
    (
        current_df["security"]
        ==
        movement_security
    )
].copy()


if not selected_current.empty:

    selected_row = (
        selected_current
        .iloc[0]
    )


    current_position = int(
        selected_row[
            "current_shares"
        ]
    )


    movement_price = float(
        selected_row[
            "price"
        ]
    )


    st.write(
        f"Current pledged shares: "
        f"**{current_position:,}**"
    )


    st.write(
        f"Current price: "
        f"**₹{movement_price:,.2f}**"
    )


    movement_type = st.radio(
        "Movement Type",
        [
            "ADD SHARES",
            "RELEASE SHARES"
        ],
        horizontal=True,
        key="movement_type"
    )


    movement_shares = st.number_input(
        "Number of Shares",
        min_value=1,
        value=1000,
        step=1000,
        key="movement_shares"
    )


    if movement_type == "RELEASE SHARES":

        if movement_shares > current_position:

            st.error(
                "Release shares cannot exceed "
                "the current pledged shares."
            )

            movement_valid = False

        else:

            movement_valid = True

    else:

        movement_valid = True


    movement_date = st.date_input(
        "Movement Date",
        value=latest_trading_date.date(),
        key="movement_date"
    )


    movement_reference = st.text_input(
        "Reference / Remarks",
        placeholder=(
            "e.g. Credit approval / pledge addition / "
            "partial release"
        ),
        key="movement_reference"
    )


    if st.button(
        "💾 Record Share Movement",
        key="record_share_movement"
    ):

        if not movement_valid:

            st.error(
                "Invalid share movement."
            )

        else:

            try:

                movement_result = (
                    record_share_movement(
                        movement_date,
                        movement_borrower,
                        movement_security,
                        movement_type,
                        int(movement_shares),
                        movement_reference
                    )
                )


                st.success(
                    "Share movement recorded successfully."
                )


                st.info(
                    "Historical collateral data has NOT "
                    "been modified."
                )


                st.rerun()


            except TypeError:

                try:

                    movement_result = (
                        record_share_movement(
                            date=movement_date,
                            borrower=movement_borrower,
                            security=movement_security,
                            movement_type=movement_type,
                            shares=int(
                                movement_shares
                            ),
                            remarks=movement_reference
                        )
                    )


                    st.success(
                        "Share movement recorded successfully."
                    )


                    st.info(
                        "Historical collateral data has NOT "
                        "been modified."
                    )


                    st.rerun()


                except Exception as e:

                    st.error(
                        "Share movement could not be recorded: "
                        + str(e)
                    )


            except Exception as e:

                st.error(
                    "Share movement could not be recorded: "
                    + str(e)
                )
```

# ============================================================

# ============================================================

# 5. SHARE MOVEMENT HISTORY

# ============================================================

# ============================================================

st.subheader(
"📋 Share Movement History"
)

try:

```
movements_df = get_share_movements()


if (
    movements_df is not None
    and not movements_df.empty
):

    movement_view = (
        movements_df
        .copy()
    )


    # --------------------------------------------
    # Rename common columns
    # --------------------------------------------

    movement_view = movement_view.rename(
        columns={
            "date": "Movement Date",
            "borrower": "Borrower",
            "security": "Security",
            "movement_type": "Movement Type",
            "shares": "Shares",
            "remarks": "Remarks",
            "reference": "Reference"
        }
    )


    # --------------------------------------------
    # Format date
    # --------------------------------------------

    if "Movement Date" in movement_view.columns:

        movement_view[
            "Movement Date"
        ] = pd.to_datetime(
            movement_view[
                "Movement Date"
            ],
            errors="coerce"
        ).dt.strftime(
            "%d-%b-%Y"
        )


    # --------------------------------------------
    # Format shares
    # --------------------------------------------

    if "Shares" in movement_view.columns:

        movement_view[
            "Shares"
        ] = pd.to_numeric(
            movement_view[
                "Shares"
            ],
            errors="coerce"
        ).fillna(0).astype(int).apply(
            lambda x:
            f"{x:,}"
        )


    st.dataframe(
        movement_view,
        width="stretch",
        hide_index=True
    )


else:

    st.info(
        "No share movements have been recorded yet."
    )
```

except Exception as e:

```
st.warning(
    "Share movement history could not be loaded: "
    + str(e)
)
```

# ============================================================

# ============================================================

# 6. SECURITY RISK MONITORING

# ============================================================

# ============================================================

st.subheader(
"🚦 Security Risk Monitoring"
)

try:

```
risk_df = calculate_risk(
    df.copy()
)


if "date" in risk_df.columns:

    risk_df["date"] = pd.to_datetime(
        risk_df["date"],
        errors="coerce"
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


security_risk = risk_df[
    risk_df["date"]
    ==
    latest_trading_date
].copy()


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
    if column in security_risk.columns
]


security_risk = security_risk[
    available_security_columns
]


security_risk = (
    security_risk
    .sort_values(
        [
            "borrower",
            "security"
        ]
    )
)


if "date" in security_risk.columns:

    security_risk["date"] = (
        security_risk["date"]
        .dt.strftime(
            "%d-%b-%Y"
        )
    )


if "cover" in security_risk.columns:

    security_risk["cover"] = (
        security_risk["cover"]
        .apply(format_cover)
    )


if "required_cover" in security_risk.columns:

    security_risk["required_cover"] = (
        security_risk[
            "required_cover"
        ]
        .apply(format_cover)
    )


if "buffer" in security_risk.columns:

    security_risk["buffer"] = (
        security_risk["buffer"]
        .apply(format_cover)
    )


st.dataframe(
    security_risk,
    width="stretch",
    hide_index=True
)
```

except Exception as e:

```
st.warning(
    "Security risk monitoring could not be calculated: "
    + str(e)
)
```

# ============================================================

# ============================================================

# 7. IMMEDIATE ATTENTION REQUIRED

# ============================================================

# ============================================================

st.subheader(
"🚨 Immediate Attention Required"
)

try:

```
critical = risk_df[
    risk_df[
        "risk_status"
    ].astype(str)
    ==
    "🔴 Action Required"
].copy()


critical_latest = critical[
    critical["date"]
    ==
    latest_trading_date
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
        "risk_status"
    ]


    available_critical_columns = [
        column
        for column in critical_columns
        if column in critical_latest.columns
    ]


    critical_view = (
        critical_latest[
            available_critical_columns
        ]
        .copy()
    )


    if "date" in critical_view.columns:

        critical_view["date"] = (
            critical_view["date"]
            .dt.strftime(
                "%d-%b-%Y"
            )
        )


    if "cover" in critical_view.columns:

        critical_view["cover"] = (
            critical_view["cover"]
            .apply(format_cover)
        )


    if "required_cover" in critical_view.columns:

        critical_view[
            "required_cover"
        ] = (
            critical_view[
                "required_cover"
            ]
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
        hide_index=True
    )


else:

    st.success(
        "No collateral shortfall detected "
        "for the latest trading date."
    )
```

except Exception as e:

```
st.warning(
    "Immediate attention calculation failed: "
    + str(e)
)
```

# ============================================================

# ============================================================

# 8. MARKET MOVEMENT MONITORING

# ============================================================

# ============================================================

st.subheader(
"📉 Market Movement Monitoring"
)

try:

```
market_df = add_market_monitoring(
    risk_df.copy()
)


if "date" in market_df.columns:

    market_df["date"] = pd.to_datetime(
        market_df["date"],
        errors="coerce"
    )


    market_df = market_df[
        market_df["date"].notna()
    ].copy()


    market_df["date"] = (
        market_df["date"]
        .dt.normalize()
    )


market_view = market_df[
    market_df["date"]
    ==
    latest_trading_date
].copy()


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
    if column in market_view.columns
]


market_view = market_view[
    available_market_columns
]


market_view = market_view.sort_values(
    [
        "borrower",
        "security"
    ]
)


if "date" in market_view.columns:

    market_view["date"] = (
        market_view["date"]
        .dt.strftime(
            "%d-%b-%Y"
        )
    )


if "price" in market_view.columns:

    market_view["price"] = (
        market_view["price"]
        .apply(
            lambda x:
            f"₹{x:,.2f}"
        )
    )


st.dataframe(
    market_view,
    width="stretch",
    hide_index=True
)
```

except Exception as e:

```
st.warning(
    "Market movement monitoring could not be calculated: "
    + str(e)
)
```

# ============================================================

# ============================================================

# 9. COLLATERAL STRESS TESTING

# ============================================================

# ============================================================

st.subheader(
"📉 Collateral Stress Testing"
)

try:

```
stress_df = run_stress_test(
    df.copy()
)


if (
    stress_df is not None
    and not stress_df.empty
):

    stress_view = (
        stress_df
        .copy()
    )


    for column in [
        "Current Collateral",
        "Stressed Collateral",
        "Loan Amount"
    ]:

        if column in stress_view.columns:

            stress_view[column] = (
                stress_view[column]
                .apply(format_crore)
            )


    for column in [
        "Cover",
        "Required Cover"
    ]:

        if column in stress_view.columns:

            stress_view[column] = (
                stress_view[column]
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
```

except Exception as e:

```
st.warning(
    "Stress testing could not be calculated: "
    + str(e)
)
```

# ============================================================

# ============================================================

# 10. COMPLETE HISTORICAL DATA

# ============================================================

# ============================================================

st.subheader(
"📚 Complete Historical Collateral Data"
)

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

historical_view = (
historical_view[
available_historical_columns
]
.sort_values(
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
)

if "date" in historical_view.columns:

```
historical_view["date"] = (
    historical_view["date"]
    .dt.strftime(
        "%d-%b-%Y"
    )
)
```

for column in [
"loan_amount",
"collateral_value"
]:

```
if column in historical_view.columns:

    historical_view[column] = (
        historical_view[column]
        .apply(format_crore)
    )
```

for column in [
"cover",
"required_cover"
]:

```
if column in historical_view.columns:

    historical_view[column] = (
        historical_view[column]
        .apply(format_cover)
    )
```

if "price" in historical_view.columns:

```
historical_view["price"] = (
    historical_view["price"]
    .apply(
        lambda x:
        f"₹{x:,.2f}"
    )
)
```

if "shares" in historical_view.columns:

```
historical_view["shares"] = (
    historical_view["shares"]
    .apply(
        lambda x:
        f"{int(x):,}"
    )
)
```

st.dataframe(
historical_view,
width="stretch",
hide_index=True
)

st.caption(
"Historical records are displayed exactly as stored. "
"Share additions/releases do not alter historical records."
)

# ============================================================

# ============================================================

# 11. HISTORICAL BORROWER COVER MOVEMENT

# ============================================================

# ============================================================

st.subheader(
"📈 Historical Borrower Cover Movement"
)

cover_history = df.copy()

cover_history["collateral_value"] = (
pd.to_numeric(
cover_history[
"collateral_value"
],
errors="coerce"
)
)

cover_history["loan_amount"] = (
pd.to_numeric(
cover_history[
"loan_amount"
],
errors="coerce"
)
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
"borrower"
],
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

borrower_daily["total_cover"] = (
borrower_daily[
"collateral_value"
]
/
borrower_daily[
"loan_amount"
]
)

borrower_daily = (
borrower_daily
.sort_values(
[
"date",
"borrower"
]
)
.reset_index(
drop=True
)
)

cover_table = borrower_daily[
[
"date",
"borrower",
"total_cover"
]
].copy()

cover_table["date"] = (
cover_table["date"]
.dt.strftime(
"%d-%b-%Y"
)
)

cover_table["total_cover"] = (
cover_table[
"total_cover"
]
.round(2)
)

st.dataframe(
cover_table,
width="stretch",
hide_index=True
)

# ============================================================

# HISTORICAL COVER CHART

# ============================================================

if not borrower_daily.empty:

```
chart_data = borrower_daily[
    [
        "date",
        "borrower",
        "total_cover"
    ]
].copy()


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


cover_chart = (
    alt.Chart(
        chart_data
    )
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
```

# ============================================================

# FOOTER

# ============================================================

st.divider()

st.caption(
"Loan Collateral Risk Monitoring System | "
"Historical records are retained by trading date. "
"Share movements are tracked separately and used "
"only to calculate the current collateral position."
)