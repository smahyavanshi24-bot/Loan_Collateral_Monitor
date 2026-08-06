import streamlit as st


from modules.dashboard_data import (
    get_collateral_history,
    get_borrower_summary
)


from modules.risk_analysis import (
    calculate_risk
)


from modules.market_monitor import (
    add_market_monitoring
)



# -------------------------------------------------
# Page Configuration
# -------------------------------------------------

st.set_page_config(
    page_title="Loan Collateral Risk Dashboard",
    page_icon="📊",
    layout="wide"
)



# -------------------------------------------------
# Header
# -------------------------------------------------

st.title(
    "📊 Loan Collateral Risk Monitoring System"
)


st.caption(
    "Credit Risk Dashboard | Collateral & Security Cover Monitoring"
)



# -------------------------------------------------
# Load Database
# -------------------------------------------------

df = get_collateral_history()



if df.empty:

    st.warning(
        "No data available. Please run main.py first."
    )

    st.stop()



# -------------------------------------------------
# Risk Calculation
# -------------------------------------------------

risk_df = calculate_risk(df)



# -------------------------------------------------
# Market Monitoring
# -------------------------------------------------

market_df = add_market_monitoring(
    risk_df
)



# -------------------------------------------------
# Executive Summary
# -------------------------------------------------

st.subheader(
    "📌 Executive Summary"
)



total_loan = (
    df["loan_amount"]
    .drop_duplicates()
    .sum()
)



total_collateral = (
    df["collateral_value"]
    .sum()
)



portfolio_cover = (
    total_collateral /
    total_loan
)



critical_count = len(
    risk_df[
        risk_df["risk_status"]
        ==
        "🔴 Action Required"
    ]
)



if critical_count > 0:

    portfolio_status = "🔴 Action Required"


elif portfolio_cover < 2:

    portfolio_status = "🟡 Watch"


else:

    portfolio_status = "🟢 Safe"




col1, col2, col3, col4 = st.columns(4)



with col1:

    st.metric(
        "Loan Exposure",
        f"₹{total_loan/10000000:.2f} Cr"
    )



with col2:

    st.metric(
        "Collateral Value",
        f"₹{total_collateral/10000000:.2f} Cr"
    )



with col3:

    st.metric(
        "Portfolio Cover",
        f"{portfolio_cover:.2f}x"
    )



with col4:

    st.metric(
        "Risk Status",
        portfolio_status
    )



# -------------------------------------------------
# Borrower Summary
# -------------------------------------------------

st.subheader(
    "👥 Borrower Wise Position"
)



borrower_summary = get_borrower_summary()



st.dataframe(
    borrower_summary,
    use_container_width=True
)



# -------------------------------------------------
# Security Risk Monitoring
# -------------------------------------------------

st.subheader(
    "🚦 Security Risk Monitoring"
)



security_view = risk_df[
    [
        "borrower",
        "security",
        "cover",
        "required_cover",
        "buffer",
        "risk_status"
    ]
]



st.dataframe(
    security_view,
    use_container_width=True
)



# -------------------------------------------------
# Critical Alerts
# -------------------------------------------------

st.subheader(
    "🚨 Immediate Attention Required"
)



critical = risk_df[
    risk_df["risk_status"]
    ==
    "🔴 Action Required"
]



if len(critical) > 0:

    st.error(
        f"{len(critical)} securities below required cover"
    )


    st.dataframe(
        critical,
        use_container_width=True
    )


else:

    st.success(
        "No collateral shortfall detected"
    )



# -------------------------------------------------
# Market Movement
# -------------------------------------------------

st.subheader(
    "📉 Market Movement Monitoring"
)



market_view = market_df[
    [
        "borrower",
        "security",
        "price",
        "daily_change_%",
        "market_alert"
    ]
]



st.dataframe(
    market_view,
    use_container_width=True
)



market_alerts = market_df[
    market_df["market_alert"]
    !=
    "Normal"
]



if len(market_alerts) > 0:

    st.warning(
        "🚨 Market Movement Alert"
    )


    st.dataframe(
        market_alerts,
        use_container_width=True
    )


else:

    st.success(
        "No major price movement detected"
    )



# -------------------------------------------------
# Charts
# -------------------------------------------------

st.subheader(
    "📈 Security Cover Comparison"
)



chart_data = risk_df[
    [
        "security",
        "cover"
    ]
]



st.bar_chart(
    chart_data.set_index(
        "security"
    )
)



# -------------------------------------------------
# Complete Data
# -------------------------------------------------

with st.expander(
    "View Complete Historical Data"
):

    st.dataframe(
        market_df,
        use_container_width=True
    )