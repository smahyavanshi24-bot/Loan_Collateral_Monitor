import streamlit as st


def load_theme():

    st.markdown(
        """
        <style>

        .main {
            background-color: #f5f7fb;
        }

        .stMetric {
            background-color: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0px 2px 10px rgba(0,0,0,0.08);
        }

        h1 {
            color: #003366;
        }

        h2 {
            color: #003366;
        }

        h3 {
            color: #003366;
        }

        div[data-testid="stDataFrame"] {
            border-radius:10px;
            overflow:hidden;
        }

        </style>
        """,
        unsafe_allow_html=True
    )