import io
from datetime import date

import pandas as pd
import streamlit as st

from modules.input_database import (
    initialize_input_database,
    list_loans,
    create_loan,
    get_loan,
    list_securities,
    add_security,
    add_additional_collateral,
    list_additional_collateral,
    add_prepayment,
    list_prepayments,
    add_repayment_rows,
    list_repayments,
    get_current_share_balance,
    add_share_movement,
    list_share_movements,
)

st.set_page_config(
    page_title="Loan Collateral Data Input",
    page_icon="📝",
    layout="wide",
)

initialize_input_database()

st.title("📝 Loan Collateral Data Input")
st.caption("Enter master data here. The monitoring dashboard will use these records instead of hardcoded borrower/security lists.")


def loan_options():
    loans = list_loans()
    return loans


def loan_label(loan):
    return f"{loan['borrower']} | {loan['loan_id']}"


tab_loan, tab_security, tab_collateral, tab_repayment, tab_prepayment, tab_movement = st.tabs([
    "1. Loan & Borrower",
    "2. Listed Shares",
    "3. Additional Collateral",
    "4. Repayment Schedule",
    "5. Prepayment",
    "6. Share Movement",
])

with tab_loan:
    st.subheader("Loan & Borrower Details")
    with st.form("loan_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            borrower = st.text_input("Borrower / Company *")
            loan_id = st.text_input("Loan ID *")
            loan_start_date = st.date_input("Loan Start Date", value=date.today())
            expected_closure_date = st.date_input("Expected Closure Date", value=None)
            loan_status = st.selectbox("Loan Status", ["Active", "Closed"])
        with c2:
            sanctioned_amount = st.number_input("Sanctioned Amount (₹ Cr) *", min_value=0.0, step=1.0, format="%.2f")
            initial_disbursement = st.number_input("Initial Disbursement (₹ Cr)", min_value=0.0, step=1.0, format="%.2f")
            outstanding = st.number_input("Outstanding at Onboarding (₹ Cr)", min_value=0.0, step=1.0, format="%.2f")
            required_cover = st.number_input("Required Security Cover - Borrower Level (x) *", min_value=0.0, step=0.05, value=2.0, format="%.2f")
        submitted = st.form_submit_button("💾 Save Loan", type="primary")

    if submitted:
        if not borrower.strip() or not loan_id.strip():
            st.error("Borrower / Company and Loan ID are required.")
        elif sanctioned_amount <= 0:
            st.error("Sanctioned Amount must be greater than zero.")
        elif expected_closure_date and expected_closure_date < loan_start_date:
            st.error("Expected Closure Date cannot be before Loan Start Date.")
        else:
            try:
                new_id = create_loan(
                    borrower, loan_id, loan_start_date,
                    expected_closure_date, sanctioned_amount,
                    initial_disbursement, outstanding,
                    required_cover, loan_status,
                )
                st.success(f"Loan saved successfully. Internal ID: {new_id}")
                st.rerun()
            except Exception as exc:
                if "UNIQUE constraint failed: loans.loan_id" in str(exc):
                    st.error("That Loan ID already exists. Use a unique Loan ID.")
                else:
                    st.error(f"Loan could not be saved: {exc}")

    loans = loan_options()
    if loans:
        st.subheader("Existing Loans")
        view = pd.DataFrame(loans)
        view = view.rename(columns={
            "borrower": "Borrower",
            "loan_id": "Loan ID",
            "loan_start_date": "Loan Start Date",
            "expected_closure_date": "Expected Closure Date",
            "sanctioned_amount_cr": "Sanctioned (Cr)",
            "initial_disbursement_cr": "Initial Disbursement (Cr)",
            "outstanding_at_onboarding_cr": "Outstanding (Cr)",
            "required_security_cover": "Required Cover",
            "loan_status": "Status",
        })
        show = [c for c in ["Borrower", "Loan ID", "Loan Start Date", "Expected Closure Date", "Sanctioned (Cr)", "Initial Disbursement (Cr)", "Outstanding (Cr)", "Required Cover", "Status"] if c in view.columns]
        st.dataframe(view[show], width="stretch", hide_index=True)

with tab_security:
    st.subheader("Underlying Listed Share")
    loans = loan_options()
    if not loans:
        st.info("Create a loan first in the Loan & Borrower tab.")
    else:
        selected = st.selectbox("Borrower / Loan", loans, format_func=loan_label, key="security_loan")
        with st.form("security_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                company = st.text_input("Listed Company Name *")
                symbol = st.text_input("NSE Symbol / ISIN *", placeholder="e.g. JSWENERGY.NS or ISIN")
                pledged = st.number_input("Initial Pledged Shares *", min_value=1, step=1000)
            with c2:
                pledge_date = st.date_input("Initial Pledge Date", value=date.today())
                security_cover = st.number_input("Collateral-wise Security Cover (x) *", min_value=0.0, step=0.05, value=1.0, format="%.2f")
            submitted = st.form_submit_button("➕ Add Listed Security", type="primary")
        if submitted:
            if not company.strip() or not symbol.strip():
                st.error("Listed Company Name and NSE Symbol / ISIN are required.")
            else:
                try:
                    add_security(selected["id"], company, symbol, pledged, pledge_date, security_cover)
                    st.success("Listed security added successfully.")
                    st.rerun()
                except Exception as exc:
                    if "UNIQUE constraint failed" in str(exc):
                        st.error("This security/symbol is already registered for this loan.")
                    else:
                        st.error(f"Security could not be added: {exc}")

        securities = list_securities(selected["id"])
        if securities:
            view = pd.DataFrame(securities)
            view = view.rename(columns={
                "listed_company_name": "Listed Company",
                "nse_symbol_isin": "NSE Symbol / ISIN",
                "initial_pledged_shares": "Initial Pledged Shares",
                "initial_pledge_date": "Initial Pledge Date",
                "collateralwise_security_cover": "Collateral-wise Cover",
            })
            cols = ["Listed Company", "NSE Symbol / ISIN", "initial_pledged_shares", "Initial Pledge Date", "Collateral-wise Cover"]
            view = view.rename(columns={"initial_pledged_shares": "Initial Pledged Shares"})
            st.dataframe(view[["Listed Company", "NSE Symbol / ISIN", "Initial Pledged Shares", "Initial Pledge Date", "Collateral-wise Cover"]], width="stretch", hide_index=True)

with tab_collateral:
    st.subheader("Additional Collateral")
    loans = loan_options()
    if not loans:
        st.info("Create a loan first.")
    else:
        selected = st.selectbox("Borrower / Loan", loans, format_func=loan_label, key="collateral_loan")
        with st.form("collateral_form", clear_on_submit=True):
            collateral_type = st.selectbox("Collateral Type", ["FD", "MF"])
            amount = st.number_input("Collateral Amount (₹ Cr)", min_value=0.0, step=0.50, format="%.2f")
            collateral_date = st.date_input("Collateral Date", value=date.today())
            maturity = st.date_input("Maturity / Release Date", value=None)
            submitted = st.form_submit_button("➕ Add Additional Collateral", type="primary")
        if submitted:
            if amount <= 0:
                st.error("Collateral Amount must be greater than zero.")
            else:
                try:
                    add_additional_collateral(selected["id"], collateral_type, amount, collateral_date, maturity)
                    st.success("Additional collateral saved.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Collateral could not be saved: {exc}")
        rows = list_additional_collateral(selected["id"])
        if rows:
            view = pd.DataFrame(rows).rename(columns={
                "collateral_type": "Type",
                "collateral_amount_cr": "Amount (Cr)",
                "collateral_date": "Collateral Date",
                "maturity_release_date": "Maturity / Release Date",
            })
            st.dataframe(view[["Type", "Amount (Cr)", "Collateral Date", "Maturity / Release Date"]], width="stretch", hide_index=True)

with tab_repayment:
    st.subheader("Repayment Schedule — Excel Upload")
    loans = loan_options()
    if not loans:
        st.info("Create a loan first.")
    else:
        selected = st.selectbox("Borrower / Loan", loans, format_func=loan_label, key="repayment_loan")
        st.caption("Excel must contain: Repayment Date and Repayment Amount (Cr). An optional Remarks column is supported.")
        template = pd.DataFrame({"Repayment Date": [date.today()], "Repayment Amount (Cr)": [0.0], "Remarks": [""]})
        buf = io.BytesIO()
        template.to_excel(buf, index=False, engine="openpyxl")
        st.download_button("⬇️ Download Excel Template", buf.getvalue(), "repayment_schedule_template.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        uploaded = st.file_uploader("Upload Repayment Schedule", type=["xlsx", "xls"], key="repayment_upload")
        if uploaded:
            try:
                xls = pd.read_excel(uploaded)
                normalized = {str(c).strip().lower(): c for c in xls.columns}
                date_col = next((normalized[k] for k in normalized if k in {"repayment date", "date", "due date"}), None)
                amount_col = next((normalized[k] for k in normalized if k in {"repayment amount (cr)", "repayment amount", "amount", "amount (cr)"}), None)
                remarks_col = next((normalized[k] for k in normalized if k in {"remarks", "remark"}), None)
                if not date_col or not amount_col:
                    st.error("Excel needs 'Repayment Date' and 'Repayment Amount (Cr)' columns. Use the template above.")
                else:
                    parsed = pd.DataFrame()
                    parsed["repayment_date"] = pd.to_datetime(xls[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
                    parsed["repayment_amount_cr"] = pd.to_numeric(xls[amount_col], errors="coerce")
                    parsed["remarks"] = xls[remarks_col].fillna("").astype(str) if remarks_col else ""
                    parsed = parsed.dropna(subset=["repayment_date", "repayment_amount_cr"])
                    st.dataframe(parsed, width="stretch", hide_index=True)
                    if st.button("💾 Save Repayment Schedule", type="primary"):
                        if parsed.empty:
                            st.error("No valid repayment rows found.")
                        else:
                            count = add_repayment_rows(selected["id"], parsed.to_dict("records"), uploaded.name)
                            st.success(f"Saved {count} repayment row(s).")
                            st.rerun()
            except Exception as exc:
                st.error(f"Could not read the Excel file: {exc}")
        existing = list_repayments(selected["id"])
        if existing:
            view = pd.DataFrame(existing).rename(columns={
                "repayment_date": "Repayment Date",
                "repayment_amount_cr": "Amount (Cr)",
                "remarks": "Remarks",
            })
            st.dataframe(view[["Repayment Date", "Amount (Cr)", "Remarks"]], width="stretch", hide_index=True)

with tab_prepayment:
    st.subheader("Prepayment")
    loans = loan_options()
    if not loans:
        st.info("Create a loan first.")
    else:
        selected = st.selectbox("Borrower / Loan", loans, format_func=loan_label, key="prepayment_loan")
        with st.form("prepayment_form", clear_on_submit=True):
            pdate = st.date_input("Prepayment Date", value=date.today())
            amount = st.number_input("Prepayment Amount (₹ Cr)", min_value=0.0, step=0.50, format="%.2f")
            remarks = st.text_area("Remarks")
            submitted = st.form_submit_button("💾 Save Prepayment", type="primary")
        if submitted:
            if amount <= 0:
                st.error("Prepayment amount must be greater than zero.")
            else:
                try:
                    add_prepayment(selected["id"], pdate, amount, remarks)
                    st.success("Prepayment saved.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Prepayment could not be saved: {exc}")
        existing = list_prepayments(selected["id"])
        if existing:
            view = pd.DataFrame(existing).rename(columns={
                "prepayment_date": "Date",
                "amount_cr": "Amount (Cr)",
                "remarks": "Remarks",
            })
            st.dataframe(view[["Date", "Amount (Cr)", "Remarks"]], width="stretch", hide_index=True)

with tab_movement:
    st.subheader("Share Movement")
    securities = list_securities()
    if not securities:
        st.info("Add a listed security first.")
    else:
        selected = st.selectbox("Borrower / Security", securities, format_func=lambda x: f"{x['borrower']} | {x['listed_company_name']} | {x['nse_symbol_isin']}", key="movement_security")
        current = get_current_share_balance(selected["id"])
        st.metric("Current Pledged Shares", f"{current:,}")
        with st.form("movement_form", clear_on_submit=True):
            movement_date = st.date_input("Share Movement Date", value=date.today())
            movement_type = st.selectbox("Addition or Release", ["Addition", "Release"])
            quantity = st.number_input("Number of Shares", min_value=1, step=1000)
            remarks = st.text_area("Remarks")
            submitted = st.form_submit_button("💾 Save Share Movement", type="primary")
        if submitted:
            try:
                movement_id, resulting = add_share_movement(selected["id"], movement_date, movement_type, quantity, remarks)
                st.success(f"Share movement saved. Resulting pledged shares: {resulting:,}")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        existing = list_share_movements(selected["id"])
        if existing:
            view = pd.DataFrame(existing).rename(columns={
                "movement_date": "Date",
                "movement_type": "Movement",
                "number_of_shares": "Shares",
                "remarks": "Remarks",
                "resulting_shares": "Resulting Shares",
            })
            view["Shares"] = view["Shares"].map(lambda x: f"{int(x):+,}")
            view["Resulting Shares"] = view["Resulting Shares"].map(lambda x: f"{int(x):+,}")
            st.dataframe(view[["Date", "Movement", "Shares", "Remarks", "Resulting Shares"]], width="stretch", hide_index=True)

st.divider()
st.caption("Input Portal v1 — master/input data is stored separately from the existing historical collateral records.")
