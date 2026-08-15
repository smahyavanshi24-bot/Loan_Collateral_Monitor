import io
from datetime import date

import pandas as pd
import streamlit as st

from modules.input_database import (
    initialize_input_database,
    list_loans,
    create_loan,
    get_loan,
    update_loan,
    list_securities,
    add_security,
    update_security,
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


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Loan Collateral Data Input",
    page_icon="📋",
    layout="wide",
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_input_database()


# ============================================================
# HEADER
# ============================================================

st.title("📋 Loan Collateral Data Input Portal")

st.caption(
    "Master Data Input | Loans | Securities | Collateral | Repayment | Share Movement"
)

st.divider()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def loan_label(loan):
    return (
        f"{loan['borrower']} | "
        f"Loan ID: {loan['loan_id']}"
    )


def security_label(security):
    return (
        f"{security['borrower']} | "
        f"{security['listed_company_name']} | "
        f"{security['nse_symbol']} | "
        f"{security['isin']}"
    )


def format_cr(value):
    if value is None:
        return "₹0.00 Cr"

    return f"₹{float(value):,.2f} Cr"


# ============================================================
# TABS
# ============================================================

tab_loan, tab_security, tab_collateral, tab_repayment, tab_prepayment, tab_movement = st.tabs(
    [
        "🏦 Loan & Borrower",
        "📈 Listed Share",
        "💰 Additional Collateral",
        "📅 Repayment Schedule",
        "💵 Prepayment",
        "📊 Share Movement",
    ]
)


# ============================================================
# 1. LOAN & BORROWER DETAILS
# ============================================================

with tab_loan:

    st.header("Loan & Borrower Details")

    st.caption(
        "Create a new loan record. This information will automatically become available in the dashboard."
    )

    with st.form(
        "loan_form",
        clear_on_submit=True,
    ):

        col1, col2 = st.columns(2)

        with col1:

            borrower = st.text_input(
                "Borrower / Company *"
            )

            loan_id = st.text_input(
                "Loan ID *"
            )

            loan_start_date = st.date_input(
                "Loan Start Date *",
                value=date.today(),
            )

            expected_closure_date = st.date_input(
                "Expected Closure Date",
                value=date.today(),
            )

            loan_status = st.selectbox(
                "Loan Status *",
                [
                    "Active",
                    "Closed",
                ],
            )

        with col2:

            sanctioned_amount = st.number_input(
                "Sanctioned Amount (₹ Cr) *",
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )

            initial_disbursement = st.number_input(
                "Initial Disbursement (₹ Cr)",
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )

            outstanding = st.number_input(
                "Outstanding at Onboarding (₹ Cr)",
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )

            required_cover = st.number_input(
                "Required Security Cover (x) *",
                min_value=0.0,
                step=0.10,
                format="%.2f",
            )

        submitted = st.form_submit_button(
            "💾 Save Loan",
            type="primary",
        )

    if submitted:

        if not borrower.strip():

            st.error(
                "Borrower / Company is required."
            )

        elif not loan_id.strip():

            st.error(
                "Loan ID is required."
            )

        elif sanctioned_amount <= 0:

            st.error(
                "Sanctioned Amount must be greater than zero."
            )

        elif required_cover <= 0:

            st.error(
                "Required Security Cover must be greater than zero."
            )

        else:

            try:

                loan_db_id = create_loan(
                    borrower=borrower,
                    loan_id=loan_id,
                    loan_start_date=loan_start_date,
                    expected_closure_date=expected_closure_date,
                    sanctioned_amount_cr=sanctioned_amount,
                    initial_disbursement_cr=initial_disbursement,
                    outstanding_at_onboarding_cr=outstanding,
                    required_security_cover=required_cover,
                    loan_status=loan_status,
                )

                st.success(
                    f"Loan saved successfully. Database ID: {loan_db_id}"
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Loan could not be saved: {exc}"
                )


    # --------------------------------------------------------
    # EXISTING LOANS
    # --------------------------------------------------------

    st.divider()

    st.subheader("Existing Loans")

    loans = list_loans()

    if not loans:

        st.info(
            "No loans have been entered yet."
        )

    else:

        loan_view = pd.DataFrame(loans)

        loan_view = loan_view.rename(
            columns={
                "borrower": "Borrower",
                "loan_id": "Loan ID",
                "loan_start_date": "Start Date",
                "expected_closure_date": "Expected Closure",
                "sanctioned_amount_cr": "Sanctioned (Cr)",
                "initial_disbursement_cr": "Initial Disbursement (Cr)",
                "outstanding_at_onboarding_cr": "Outstanding (Cr)",
                "required_security_cover": "Required Cover",
                "loan_status": "Status",
            }
        )

        columns = [
            "Borrower",
            "Loan ID",
            "Start Date",
            "Expected Closure",
            "Sanctioned (Cr)",
            "Initial Disbursement (Cr)",
            "Outstanding (Cr)",
            "Required Cover",
            "Status",
        ]

        st.dataframe(
            loan_view[columns],
            width="stretch",
            hide_index=True,
        )


    # --------------------------------------------------------
    # EDIT EXISTING LOAN
    # --------------------------------------------------------

    if loans:

        st.divider()

        st.subheader("✏️ Edit Existing Loan")

        selected_loan = st.selectbox(
            "Select Loan",
            loans,
            format_func=loan_label,
            key="edit_loan_select",
        )

        current_loan = get_loan(
            selected_loan["id"]
        )

        if current_loan:

            with st.form(
                "edit_loan_form"
            ):

                c1, c2 = st.columns(2)

                with c1:

                    edit_borrower = st.text_input(
                        "Borrower / Company",
                        value=current_loan["borrower"],
                    )

                    edit_loan_id = st.text_input(
                        "Loan ID",
                        value=current_loan["loan_id"],
                    )

                    edit_start = st.date_input(
                        "Loan Start Date",
                        value=pd.to_datetime(
                            current_loan["loan_start_date"]
                        ).date(),
                    )

                    edit_closure = st.date_input(
                        "Expected Closure Date",
                        value=pd.to_datetime(
                            current_loan["expected_closure_date"]
                        ).date()
                        if current_loan["expected_closure_date"]
                        else date.today(),
                    )

                with c2:

                    edit_sanctioned = st.number_input(
                        "Sanctioned Amount (₹ Cr)",
                        min_value=0.0,
                        value=float(
                            current_loan["sanctioned_amount_cr"]
                        ),
                        step=1.0,
                    )

                    edit_disbursement = st.number_input(
                        "Initial Disbursement (₹ Cr)",
                        min_value=0.0,
                        value=float(
                            current_loan["initial_disbursement_cr"]
                        ),
                        step=1.0,
                    )

                    edit_outstanding = st.number_input(
                        "Outstanding at Onboarding (₹ Cr)",
                        min_value=0.0,
                        value=float(
                            current_loan["outstanding_at_onboarding_cr"]
                        ),
                        step=1.0,
                    )

                    edit_cover = st.number_input(
                        "Required Security Cover (x)",
                        min_value=0.0,
                        value=float(
                            current_loan["required_security_cover"]
                        ),
                        step=0.10,
                    )

                    edit_status = st.selectbox(
                        "Loan Status",
                        [
                            "Active",
                            "Closed",
                        ],
                        index=(
                            0
                            if current_loan["loan_status"] == "Active"
                            else 1
                        ),
                    )

                update_loan_button = st.form_submit_button(
                    "💾 Update Loan",
                    type="primary",
                )

            if update_loan_button:

                try:

                    update_loan(
                        selected_loan["id"],
                        edit_borrower,
                        edit_loan_id,
                        edit_start,
                        edit_closure,
                        edit_sanctioned,
                        edit_disbursement,
                        edit_outstanding,
                        edit_cover,
                        edit_status,
                    )

                    st.success(
                        "Loan updated successfully."
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Loan update failed: {exc}"
                    )


# ============================================================
# 2. UNDERLYING LISTED SHARE
# ============================================================

with tab_security:

    st.header("Underlying Listed Share")

    st.caption(
        "Enter both NSE Symbol and ISIN. NSE Symbol is used for live market-price lookup."
    )

    loans = list_loans()

    if not loans:

        st.warning(
            "Create a Loan & Borrower record first."
        )

    else:

        selected_loan = st.selectbox(
            "Borrower / Loan",
            loans,
            format_func=loan_label,
            key="security_loan",
        )

        with st.form(
            "security_form",
            clear_on_submit=True,
        ):

            listed_company = st.text_input(
                "Listed Company Name *"
            )

            nse_symbol = st.text_input(
                "NSE Symbol *",
                placeholder="Example: TATASTEEL",
            )

            isin = st.text_input(
                "ISIN *",
                placeholder="Example: INE081A01020",
            )

            pledged_shares = st.number_input(
                "Initial Pledged Shares *",
                min_value=1,
                step=1000,
            )

            pledge_date = st.date_input(
                "Initial Pledge Date *",
                value=date.today(),
            )

            security_cover = st.number_input(
                "Collateral-wise Security Cover (x) *",
                min_value=0.0,
                step=0.10,
                format="%.2f",
            )

            submitted = st.form_submit_button(
                "💾 Save Listed Security",
                type="primary",
            )

        if submitted:

            if not listed_company.strip():

                st.error(
                    "Listed Company Name is required."
                )

            elif not nse_symbol.strip():

                st.error(
                    "NSE Symbol is required."
                )

            elif not isin.strip():

                st.error(
                    "ISIN is required."
                )

            elif pledged_shares <= 0:

                st.error(
                    "Initial Pledged Shares must be greater than zero."
                )

            elif security_cover <= 0:

                st.error(
                    "Collateral-wise Security Cover must be greater than zero."
                )

            else:

                try:

                    security_id = add_security(
                        selected_loan["id"],
                        listed_company,
                        nse_symbol,
                        isin,
                        pledged_shares,
                        pledge_date,
                        security_cover,
                    )

                    st.success(
                        f"Security saved successfully. Security ID: {security_id}"
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Security could not be saved: {exc}"
                    )


        # ----------------------------------------------------
        # EXISTING SECURITIES
        # ----------------------------------------------------

        st.divider()

        st.subheader("Existing Listed Securities")

        securities = list_securities(
            selected_loan["id"]
        )

        if not securities:

            st.info(
                "No securities have been entered for this loan."
            )

        else:

            security_view = pd.DataFrame(
                securities
            )

            security_view = security_view.rename(
                columns={
                    "listed_company_name": "Listed Company",
                    "nse_symbol": "NSE Symbol",
                    "isin": "ISIN",
                    "initial_pledged_shares": "Initial Shares",
                    "initial_pledge_date": "Pledge Date",
                    "collateralwise_security_cover": "Security Cover",
                }
            )

            columns = [
                "Listed Company",
                "NSE Symbol",
                "ISIN",
                "Initial Shares",
                "Pledge Date",
                "Security Cover",
            ]

            st.dataframe(
                security_view[columns],
                width="stretch",
                hide_index=True,
            )


        # ----------------------------------------------------
        # EDIT SECURITY
        # ----------------------------------------------------

        if securities:

            st.divider()

            st.subheader(
                "✏️ Edit Existing Security"
            )

            selected_security = st.selectbox(
                "Select Security",
                securities,
                format_func=security_label,
                key="edit_security_select",
            )

            with st.form(
                "edit_security_form"
            ):

                edit_company = st.text_input(
                    "Listed Company Name",
                    value=selected_security[
                        "listed_company_name"
                    ],
                )

                edit_nse = st.text_input(
                    "NSE Symbol",
                    value=selected_security[
                        "nse_symbol"
                    ] or "",
                )

                edit_isin = st.text_input(
                    "ISIN",
                    value=selected_security[
                        "isin"
                    ],
                )

                edit_shares = st.number_input(
                    "Initial Pledged Shares",
                    min_value=1,
                    value=int(
                        selected_security[
                            "initial_pledged_shares"
                        ]
                    ),
                    step=1000,
                )

                edit_date = st.date_input(
                    "Initial Pledge Date",
                    value=pd.to_datetime(
                        selected_security[
                            "initial_pledge_date"
                        ]
                    ).date(),
                )

                edit_security_cover = st.number_input(
                    "Collateral-wise Security Cover (x)",
                    min_value=0.0,
                    value=float(
                        selected_security[
                            "collateralwise_security_cover"
                        ]
                    ),
                    step=0.10,
                )

                update_button = st.form_submit_button(
                    "💾 Update Security",
                    type="primary",
                )

            if update_button:

                try:

                    update_security(
                        selected_security["id"],
                        edit_company,
                        edit_nse,
                        edit_isin,
                        edit_shares,
                        edit_date,
                        edit_security_cover,
                    )

                    st.success(
                        "Security updated successfully."
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Security update failed: {exc}"
                    )


# ============================================================
# 3. ADDITIONAL COLLATERAL
# ============================================================

with tab_collateral:

    st.header("Additional Collateral")

    loans = list_loans()

    if not loans:

        st.info(
            "Create a loan first."
        )

    else:

        selected = st.selectbox(
            "Borrower / Loan",
            loans,
            format_func=loan_label,
            key="collateral_loan",
        )

        with st.form(
            "additional_collateral_form",
            clear_on_submit=True,
        ):

            collateral_type = st.selectbox(
                "Collateral Type",
                [
                    "FD",
                    "MF",
                ],
            )

            collateral_amount = st.number_input(
                "Collateral Amount (₹ Cr)",
                min_value=0.0,
                step=0.50,
                format="%.2f",
            )

            collateral_date = st.date_input(
                "Collateral Date",
                value=date.today(),
            )

            maturity_release_date = st.date_input(
                "Maturity / Release Date",
                value=date.today(),
            )

            submitted = st.form_submit_button(
                "💾 Save Additional Collateral",
                type="primary",
            )

        if submitted:

            if collateral_amount <= 0:

                st.error(
                    "Collateral amount must be greater than zero."
                )

            else:

                try:

                    add_additional_collateral(
                        selected["id"],
                        collateral_type,
                        collateral_amount,
                        collateral_date,
                        maturity_release_date,
                    )

                    st.success(
                        "Additional collateral saved."
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Could not save collateral: {exc}"
                    )


        existing = list_additional_collateral(
            selected["id"]
        )

        if existing:

            st.divider()

            st.subheader(
                "Existing Additional Collateral"
            )

            view = pd.DataFrame(
                existing
            ).rename(
                columns={
                    "collateral_type": "Type",
                    "collateral_amount_cr": "Amount (Cr)",
                    "collateral_date": "Collateral Date",
                    "maturity_release_date": "Maturity / Release Date",
                }
            )

            st.dataframe(
                view[
                    [
                        "Type",
                        "Amount (Cr)",
                        "Collateral Date",
                        "Maturity / Release Date",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )


# ============================================================
# 4. REPAYMENT SCHEDULE
# ============================================================

with tab_repayment:

    st.header("Repayment Schedule")

    loans = list_loans()

    if not loans:

        st.info(
            "Create a loan first."
        )

    else:

        selected = st.selectbox(
            "Borrower / Loan",
            loans,
            format_func=lambda x:
                f"{x['borrower']} | Loan ID: {x['id']}",
            key="repayment_loan",
        )

        # --------------------------------------------------------
        # ORIGINAL LOAN AMOUNT
        # --------------------------------------------------------

        loan_amount = float(
            selected.get(
                "loan_amount_cr",
                selected.get(
                    "loan_amount",
                    0
                )
            )
            or 0
        )

        st.metric(
            "Original Loan Amount",
            f"₹{loan_amount:,.2f} Cr"
        )

        st.caption(
            "Upload an Excel repayment schedule. "
            "Opening and Closing Outstanding should reconcile "
            "with the repayment amount."
        )

        # --------------------------------------------------------
        # EXCEL TEMPLATE
        # --------------------------------------------------------

        st.subheader(
            "Download Excel Template"
        )

        st.write(
            "The template contains the original loan amount, "
            "opening outstanding, repayment amount, closing "
            "outstanding and remarks."
        )

        template = pd.DataFrame(
            {
                "Repayment Date": [
                    date.today()
                ],
                "Opening Outstanding (Cr)": [
                    loan_amount
                ],
                "Repayment Amount (Cr)": [
                    0.0
                ],
                "Closing Outstanding (Cr)": [
                    loan_amount
                ],
                "Remarks": [
                    ""
                ],
            }
        )

        buffer = io.BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine="openpyxl"
        ) as writer:

            # ----------------------------------------------------
            # MAIN SHEET
            # ----------------------------------------------------

            template.to_excel(
                writer,
                index=False,
                startrow=3,
                sheet_name="Repayment Schedule",
            )

            worksheet = writer.sheets[
                "Repayment Schedule"
            ]

            # ----------------------------------------------------
            # TITLE
            # ----------------------------------------------------

            worksheet["A1"] = (
                "Loan Collateral Input - Repayment Schedule"
            )

            worksheet["A2"] = (
                "Original Loan Amount (Cr)"
            )

            worksheet["B2"] = loan_amount

            # ----------------------------------------------------
            # FORMATTING
            # ----------------------------------------------------

            from openpyxl.styles import Font, PatternFill, Alignment

            worksheet["A1"].font = Font(
                bold=True,
                size=14
            )

            worksheet["A2"].font = Font(
                bold=True
            )

            worksheet["B2"].number_format = (
                '#,##0.00'
            )

            header_fill = PatternFill(
                "solid",
                fgColor="D9EAF7"
            )

            for cell in worksheet[4]:

                cell.font = Font(
                    bold=True
                )

                cell.fill = header_fill

                cell.alignment = Alignment(
                    horizontal="center"
                )

            # ----------------------------------------------------
            # COLUMN WIDTHS
            # ----------------------------------------------------

            worksheet.column_dimensions[
                "A"
            ].width = 18

            worksheet.column_dimensions[
                "B"
            ].width = 25

            worksheet.column_dimensions[
                "C"
            ].width = 23

            worksheet.column_dimensions[
                "D"
            ].width = 25

            worksheet.column_dimensions[
                "E"
            ].width = 35

        st.download_button(
            "⬇️ Download Excel Template",
            buffer.getvalue(),
            "repayment_schedule_template.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # --------------------------------------------------------
        # UPLOAD REPAYMENT SCHEDULE
        # --------------------------------------------------------

        st.subheader(
            "Upload Repayment Schedule"
        )

        uploaded = st.file_uploader(
            "Upload Excel Repayment Schedule",
            type=[
                "xlsx",
                "xls",
            ],
            key="repayment_upload",
        )

        if uploaded:

            try:

                xls = pd.read_excel(
                    uploaded,
                    header=3
                )

                # ------------------------------------------------
                # NORMALIZE COLUMN NAMES
                # ------------------------------------------------

                normalized = {
                    str(c).strip().lower(): c
                    for c in xls.columns
                }

                date_col = next(
                    (
                        normalized[k]
                        for k in normalized
                        if k in {
                            "repayment date",
                            "date",
                            "due date",
                        }
                    ),
                    None
                )

                opening_col = next(
                    (
                        normalized[k]
                        for k in normalized
                        if k in {
                            "opening outstanding (cr)",
                            "opening outstanding",
                            "opening balance",
                        }
                    ),
                    None
                )

                amount_col = next(
                    (
                        normalized[k]
                        for k in normalized
                        if k in {
                            "repayment amount (cr)",
                            "repayment amount",
                            "amount",
                            "amount (cr)",
                        }
                    ),
                    None
                )

                closing_col = next(
                    (
                        normalized[k]
                        for k in normalized
                        if k in {
                            "closing outstanding (cr)",
                            "closing outstanding",
                            "closing balance",
                        }
                    ),
                    None
                )

                remarks_col = next(
                    (
                        normalized[k]
                        for k in normalized
                        if k in {
                            "remarks",
                            "remark",
                        }
                    ),
                    None
                )

                # ------------------------------------------------
                # VALIDATE REQUIRED COLUMNS
                # ------------------------------------------------

                if not date_col or not amount_col:

                    st.error(
                        "Excel must contain "
                        "'Repayment Date' and "
                        "'Repayment Amount (Cr)'."
                    )

                else:

                    parsed = pd.DataFrame()

                    parsed[
                        "repayment_date"
                    ] = (
                        pd.to_datetime(
                            xls[date_col],
                            errors="coerce"
                        )
                        .dt.strftime(
                            "%Y-%m-%d"
                        )
                    )

                    parsed[
                        "repayment_amount_cr"
                    ] = pd.to_numeric(
                        xls[amount_col],
                        errors="coerce"
                    )

                    # ------------------------------------------------
                    # OPENING OUTSTANDING
                    # ------------------------------------------------

                    if opening_col:

                        parsed[
                            "opening_outstanding_cr"
                        ] = pd.to_numeric(
                            xls[opening_col],
                            errors="coerce"
                        )

                    else:

                        parsed[
                            "opening_outstanding_cr"
                        ] = None

                    # ------------------------------------------------
                    # CLOSING OUTSTANDING
                    # ------------------------------------------------

                    if closing_col:

                        parsed[
                            "closing_outstanding_cr"
                        ] = pd.to_numeric(
                            xls[closing_col],
                            errors="coerce"
                        )

                    else:

                        parsed[
                            "closing_outstanding_cr"
                        ] = None

                    # ------------------------------------------------
                    # REMARKS
                    # ------------------------------------------------

                    if remarks_col:

                        parsed[
                            "remarks"
                        ] = (
                            xls[
                                remarks_col
                            ]
                            .fillna("")
                            .astype(str)
                        )

                    else:

                        parsed[
                            "remarks"
                        ] = ""

                    # ------------------------------------------------
                    # REMOVE INVALID ROWS
                    # ------------------------------------------------

                    parsed = parsed.dropna(
                        subset=[
                            "repayment_date",
                            "repayment_amount_cr",
                        ]
                    )

                    # ------------------------------------------------
                    # DISPLAY PREVIEW
                    # ------------------------------------------------

                    st.subheader(
                        "Repayment Schedule Preview"
                    )

                    display_columns = [
                        "repayment_date",
                        "opening_outstanding_cr",
                        "repayment_amount_cr",
                        "closing_outstanding_cr",
                        "remarks",
                    ]

                    st.dataframe(
                        parsed[
                            display_columns
                        ],
                        width="stretch",
                        hide_index=True,
                    )

                    # ------------------------------------------------
                    # SAVE
                    # ------------------------------------------------

                    if st.button(
                        "💾 Save Repayment Schedule",
                        type="primary",
                    ):

                        if parsed.empty:

                            st.error(
                                "No valid repayment rows found."
                            )

                        else:

                            count = add_repayment_rows(
                                selected["id"],
                                parsed.to_dict(
                                    "records"
                                ),
                                uploaded.name,
                            )

                            st.success(
                                f"Saved {count} repayment row(s)."
                            )

                            st.rerun()

            except Exception as exc:

                st.error(
                    f"Could not read the Excel file: {exc}"
                )

        # --------------------------------------------------------
        # EXISTING REPAYMENT SCHEDULE
        # --------------------------------------------------------

        existing = list_repayments(
            selected["id"]
        )

        if existing:

            st.divider()

            st.subheader(
                "Existing Repayment Schedule"
            )

            view = pd.DataFrame(
                existing
            ).rename(
                columns={
                    "repayment_date":
                        "Repayment Date",

                    "repayment_amount_cr":
                        "Repayment Amount (Cr)",

                    "opening_outstanding_cr":
                        "Opening Outstanding (Cr)",

                    "closing_outstanding_cr":
                        "Closing Outstanding (Cr)",

                    "remarks":
                        "Remarks",
                }
            )

            available_columns = [
                column
                for column in [
                    "Repayment Date",
                    "Opening Outstanding (Cr)",
                    "Repayment Amount (Cr)",
                    "Closing Outstanding (Cr)",
                    "Remarks",
                ]
                if column in view.columns
            ]

            st.dataframe(
                view[
                    available_columns
                ],
                width="stretch",
                hide_index=True,
            )

# ============================================================
# 5. PREPAYMENT
# ============================================================

with tab_prepayment:

    st.header("Prepayment")

    loans = list_loans()

    if not loans:

        st.info(
            "Create a loan first."
        )

    else:

        selected = st.selectbox(
            "Borrower / Loan",
            loans,
            format_func=loan_label,
            key="prepayment_loan",
        )

        with st.form(
            "prepayment_form",
            clear_on_submit=True,
        ):

            prepayment_date = st.date_input(
                "Prepayment Date",
                value=date.today(),
            )

            amount = st.number_input(
                "Prepayment Amount (₹ Cr)",
                min_value=0.0,
                step=0.50,
                format="%.2f",
            )

            remarks = st.text_area(
                "Remarks"
            )

            submitted = st.form_submit_button(
                "💾 Save Prepayment",
                type="primary",
            )

        if submitted:

            if amount <= 0:

                st.error(
                    "Prepayment amount must be greater than zero."
                )

            else:

                try:

                    add_prepayment(
                        selected["id"],
                        prepayment_date,
                        amount,
                        remarks,
                    )

                    st.success(
                        "Prepayment saved."
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Prepayment could not be saved: {exc}"
                    )


        existing = list_prepayments(
            selected["id"]
        )

        if existing:

            st.divider()

            st.subheader(
                "Existing Prepayments"
            )

            view = pd.DataFrame(
                existing
            ).rename(
                columns={
                    "prepayment_date": "Date",
                    "amount_cr": "Amount (Cr)",
                    "remarks": "Remarks",
                }
            )

            st.dataframe(
                view[
                    [
                        "Date",
                        "Amount (Cr)",
                        "Remarks",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )


# ============================================================
# 6. SHARE MOVEMENT
# ============================================================

with tab_movement:

    st.header("Share Movement")

    st.caption(
        "Record additions or releases of pledged shares. Historical movements are retained."
    )

    securities = list_securities()

    if not securities:

        st.info(
            "Add a listed security first."
        )

    else:

        selected = st.selectbox(
            "Borrower / Security",
            securities,
            format_func=security_label,
            key="movement_security",
        )

        current = get_current_share_balance(
            selected["id"]
        )

        st.metric(
            "Current Pledged Shares",
            f"{current:,}",
        )

        with st.form(
            "movement_form",
            clear_on_submit=True,
        ):

            movement_date = st.date_input(
                "Share Movement Date",
                value=date.today(),
            )

            movement_type = st.selectbox(
                "Addition or Release",
                [
                    "Addition",
                    "Release",
                ],
            )

            quantity = st.number_input(
                "Number of Shares",
                min_value=1,
                step=1000,
            )

            remarks = st.text_area(
                "Remarks"
            )

            submitted = st.form_submit_button(
                "💾 Save Share Movement",
                type="primary",
            )

        if submitted:

            try:

                movement_id, resulting = (
                    add_share_movement(
                        selected["id"],
                        movement_date,
                        movement_type,
                        quantity,
                        remarks,
                    )
                )

                st.success(
                    "Share movement saved. "
                    f"Resulting pledged shares: {resulting:,}"
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    str(exc)
                )


        existing = list_share_movements(
            selected["id"]
        )

        if existing:

            st.divider()

            st.subheader(
                "Share Movement History"
            )

            view = pd.DataFrame(
                existing
            ).rename(
                columns={
                    "movement_date": "Date",
                    "movement_type": "Movement",
                    "number_of_shares": "Shares",
                    "remarks": "Remarks",
                    "resulting_shares": "Resulting Shares",
                }
            )

            view["Shares"] = view[
                "Shares"
            ].map(
                lambda x: f"{int(x):,}"
            )

            view["Resulting Shares"] = view[
                "Resulting Shares"
            ].map(
                lambda x: f"{int(x):,}"
            )

            st.dataframe(
                view[
                    [
                        "Date",
                        "Movement",
                        "Shares",
                        "Remarks",
                        "Resulting Shares",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Input Portal v2 | Master data is stored in the project database."
)