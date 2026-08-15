import io
from datetime import date

import pandas as pd
import streamlit as st

from modules.input_database import (
    initialize_input_database,
    list_loans,
    get_loan,
    create_loan,
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
    page_title="Loan Collateral Input",
    page_icon="📋",
    layout="wide",
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_input_database()


# ============================================================
# HELPERS
# ============================================================

def loan_label(loan):

    return (
        f"{loan['borrower']} | "
        f"Loan ID: {loan['loan_id']}"
    )


def security_label(security):

    nse = security.get("nse_symbol") or "NSE Symbol Missing"
    isin = security.get("isin") or "ISIN Missing"

    return (
        f"{security['borrower']} | "
        f"{security['listed_company_name']} | "
        f"{nse} | "
        f"{isin}"
    )


def safe_date(value):

    if not value:
        return date.today()

    try:
        return pd.to_datetime(value).date()
    except Exception:
        return date.today()


# ============================================================
# HEADER
# ============================================================

st.title("📋 Loan Collateral Input")

st.caption(
    "Single master-data page for adding and editing "
    "borrowers, loans, securities and collateral-related data."
)


# ============================================================
# MAIN SECTIONS
# ============================================================

(
    tab_loan,
    tab_security,
    tab_collateral,
    tab_repayment,
    tab_prepayment,
    tab_movement,
) = st.tabs(
    [
        "🏦 Loan & Borrower",
        "📈 Listed Shares",
        "🛡️ Additional Collateral",
        "📅 Repayment Schedule",
        "💰 Prepayment",
        "🔄 Share Movement",
    ]
)


# ============================================================
# 1. LOAN & BORROWER
# ============================================================

with tab_loan:

    st.subheader("Loan & Borrower")

    loan_action = st.radio(
        "Action",
        [
            "Add New Loan",
            "Edit Existing Loan",
        ],
        horizontal=True,
        key="loan_action",
    )

    # --------------------------------------------------------
    # ADD NEW LOAN
    # --------------------------------------------------------

    if loan_action == "Add New Loan":

        st.markdown("### Add New Loan")

        with st.form(
            "add_loan_form",
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
                    "Loan Start Date",
                    value=date.today(),
                )

                expected_closure_date = st.date_input(
                    "Expected Closure Date",
                    value=date.today(),
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

                loan_status = st.selectbox(
                    "Loan Status",
                    [
                        "Active",
                        "Closed",
                    ],
                )

            submitted = st.form_submit_button(
                "💾 Save New Loan",
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

                    create_loan(
                        borrower,
                        loan_id,
                        loan_start_date,
                        expected_closure_date,
                        sanctioned_amount,
                        initial_disbursement,
                        outstanding,
                        required_cover,
                        loan_status,
                    )

                    st.success(
                        "New loan created successfully."
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Loan could not be created: {exc}"
                    )


    # --------------------------------------------------------
    # EDIT EXISTING LOAN
    # --------------------------------------------------------

    else:

        st.markdown("### Edit Existing Loan")

        loans = list_loans(
            active_only=False
        )

        if not loans:

            st.info(
                "No loans are available to edit."
            )

        else:

            selected_loan = st.selectbox(
                "Select Borrower / Loan",
                loans,
                format_func=loan_label,
                key="edit_loan_selector",
            )

            current_loan = get_loan(
                selected_loan["id"]
            )

            with st.form(
                "edit_loan_form"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    borrower = st.text_input(
                        "Borrower / Company",
                        value=current_loan[
                            "borrower"
                        ],
                    )

                    loan_id = st.text_input(
                        "Loan ID",
                        value=current_loan[
                            "loan_id"
                        ],
                    )

                    loan_start_date = st.date_input(
                        "Loan Start Date",
                        value=safe_date(
                            current_loan[
                                "loan_start_date"
                            ]
                        ),
                    )

                    expected_closure_date = st.date_input(
                        "Expected Closure Date",
                        value=safe_date(
                            current_loan[
                                "expected_closure_date"
                            ]
                        ),
                    )

                with col2:

                    sanctioned_amount = st.number_input(
                        "Sanctioned Amount (₹ Cr)",
                        min_value=0.0,
                        value=float(
                            current_loan[
                                "sanctioned_amount_cr"
                            ]
                        ),
                        step=1.0,
                        format="%.2f",
                    )

                    initial_disbursement = st.number_input(
                        "Initial Disbursement (₹ Cr)",
                        min_value=0.0,
                        value=float(
                            current_loan[
                                "initial_disbursement_cr"
                            ]
                        ),
                        step=1.0,
                        format="%.2f",
                    )

                    outstanding = st.number_input(
                        "Outstanding at Onboarding (₹ Cr)",
                        min_value=0.0,
                        value=float(
                            current_loan[
                                "outstanding_at_onboarding_cr"
                            ]
                        ),
                        step=1.0,
                        format="%.2f",
                    )

                    required_cover = st.number_input(
                        "Required Security Cover (x)",
                        min_value=0.0,
                        value=float(
                            current_loan[
                                "required_security_cover"
                            ]
                        ),
                        step=0.10,
                        format="%.2f",
                    )

                    loan_status = st.selectbox(
                        "Loan Status",
                        [
                            "Active",
                            "Closed",
                        ],
                        index=(
                            0
                            if current_loan[
                                "loan_status"
                            ] == "Active"
                            else 1
                        ),
                    )

                submitted = st.form_submit_button(
                    "💾 Update Loan",
                    type="primary",
                )

            if submitted:

                if not borrower.strip():

                    st.error(
                        "Borrower / Company cannot be blank."
                    )

                elif not loan_id.strip():

                    st.error(
                        "Loan ID cannot be blank."
                    )

                else:

                    try:

                        update_loan(
                            selected_loan["id"],
                            borrower,
                            loan_id,
                            loan_start_date,
                            expected_closure_date,
                            sanctioned_amount,
                            initial_disbursement,
                            outstanding,
                            required_cover,
                            loan_status,
                        )

                        st.success(
                            "Loan updated successfully."
                        )

                        st.rerun()

                    except Exception as exc:

                        st.error(
                            f"Loan could not be updated: {exc}"
                        )


    # --------------------------------------------------------
    # CURRENT LOANS
    # --------------------------------------------------------

    st.divider()

    st.subheader("Current Loans")

    all_loans = list_loans(
        active_only=False
    )

    if all_loans:

        loan_view = pd.DataFrame(
            all_loans
        ).rename(
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

        st.dataframe(
            loan_view[
                [
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
            ],
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No loans have been entered."
        )


# ============================================================
# 2. LISTED SHARES
# ============================================================

with tab_security:

    st.subheader("Listed Shares")

    security_action = st.radio(
        "Action",
        [
            "Add New Security",
            "Edit Existing Security",
        ],
        horizontal=True,
        key="security_action",
    )

    loans = list_loans(
        active_only=False
    )

    if not loans:

        st.info(
            "Create a loan first."
        )

    else:

        # ----------------------------------------------------
        # ADD NEW SECURITY
        # ----------------------------------------------------

        if security_action == "Add New Security":

            selected_loan = st.selectbox(
                "Borrower / Loan",
                loans,
                format_func=loan_label,
                key="add_security_loan",
            )

            with st.form(
                "add_security_form",
                clear_on_submit=True,
            ):

                listed_company_name = st.text_input(
                    "Listed Company Name *"
                )

                nse_symbol = st.text_input(
                    "NSE Symbol *",
                    placeholder="Example: KALYANKJIL",
                )

                isin = st.text_input(
                    "ISIN *",
                    placeholder="Example: INE303R01014",
                )

                initial_pledged_shares = st.number_input(
                    "Initial Pledged Shares *",
                    min_value=1,
                    step=1000,
                )

                initial_pledge_date = st.date_input(
                    "Initial Pledge Date",
                    value=date.today(),
                )

                collateralwise_security_cover = st.number_input(
                    "Collateral-wise Security Cover (x) *",
                    min_value=0.0,
                    step=0.10,
                    format="%.2f",
                )

                submitted = st.form_submit_button(
                    "💾 Add Listed Security",
                    type="primary",
                )

            if submitted:

                if not listed_company_name.strip():

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

                elif initial_pledged_shares <= 0:

                    st.error(
                        "Initial Pledged Shares must be greater than zero."
                    )

                elif collateralwise_security_cover <= 0:

                    st.error(
                        "Collateral-wise Security Cover must be greater than zero."
                    )

                else:

                    try:

                        add_security(
                            selected_loan["id"],
                            listed_company_name,
                            nse_symbol,
                            isin,
                            initial_pledged_shares,
                            initial_pledge_date,
                            collateralwise_security_cover,
                        )

                        st.success(
                            "Listed security added successfully."
                        )

                        st.rerun()

                    except Exception as exc:

                        st.error(
                            f"Security could not be added: {exc}"
                        )


        # ----------------------------------------------------
        # EDIT EXISTING SECURITY
        # ----------------------------------------------------

        else:

            selected_loan = st.selectbox(
                "Borrower / Loan",
                loans,
                format_func=loan_label,
                key="edit_security_loan",
            )

            securities = list_securities(
                selected_loan["id"],
                active_only=False,
            )

            if not securities:

                st.info(
                    "No securities are linked to this loan."
                )

            else:

                selected_security = st.selectbox(
                    "Select Security",
                    securities,
                    format_func=security_label,
                    key="edit_security_selector",
                )

                with st.form(
                    "edit_security_form"
                ):

                    listed_company_name = st.text_input(
                        "Listed Company Name",
                        value=(
                            selected_security[
                                "listed_company_name"
                            ]
                        ),
                    )

                    nse_symbol = st.text_input(
                        "NSE Symbol",
                        value=(
                            selected_security[
                                "nse_symbol"
                            ]
                            or ""
                        ),
                    )

                    isin = st.text_input(
                        "ISIN",
                        value=(
                            selected_security[
                                "isin"
                            ]
                            or ""
                        ),
                    )

                    initial_pledged_shares = st.number_input(
                        "Initial Pledged Shares",
                        min_value=1,
                        value=int(
                            selected_security[
                                "initial_pledged_shares"
                            ]
                        ),
                        step=1000,
                    )

                    initial_pledge_date = st.date_input(
                        "Initial Pledge Date",
                        value=safe_date(
                            selected_security[
                                "initial_pledge_date"
                            ]
                        ),
                    )

                    collateralwise_security_cover = st.number_input(
                        "Collateral-wise Security Cover (x)",
                        min_value=0.0,
                        value=float(
                            selected_security[
                                "collateralwise_security_cover"
                            ]
                        ),
                        step=0.10,
                        format="%.2f",
                    )

                    submitted = st.form_submit_button(
                        "💾 Update Security",
                        type="primary",
                    )

                if submitted:

                    if not listed_company_name.strip():

                        st.error(
                            "Listed Company Name cannot be blank."
                        )

                    elif not nse_symbol.strip():

                        st.error(
                            "NSE Symbol cannot be blank."
                        )

                    elif not isin.strip():

                        st.error(
                            "ISIN cannot be blank."
                        )

                    else:

                        try:

                            update_security(
                                selected_security["id"],
                                listed_company_name,
                                nse_symbol,
                                isin,
                                initial_pledged_shares,
                                initial_pledge_date,
                                collateralwise_security_cover,
                            )

                            st.success(
                                "Security updated successfully."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                f"Security could not be updated: {exc}"
                            )


    # --------------------------------------------------------
    # ALL SECURITIES
    # --------------------------------------------------------

    st.divider()

    st.subheader("Current Listed Securities")

    securities = list_securities(
        active_only=False
    )

    if securities:

        security_view = pd.DataFrame(
            securities
        ).rename(
            columns={
                "borrower": "Borrower",
                "loan_number": "Loan ID",
                "listed_company_name": "Listed Company",
                "nse_symbol": "NSE Symbol",
                "isin": "ISIN",
                "initial_pledged_shares": "Initial Shares",
                "initial_pledge_date": "Pledge Date",
                "collateralwise_security_cover": "Security Cover",
            }
        )

        st.dataframe(
            security_view[
                [
                    "Borrower",
                    "Loan ID",
                    "Listed Company",
                    "NSE Symbol",
                    "ISIN",
                    "Initial Shares",
                    "Pledge Date",
                    "Security Cover",
                ]
            ],
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No listed securities have been entered."
        )


# ============================================================
# 3. ADDITIONAL COLLATERAL
# ============================================================

with tab_collateral:

    st.subheader("Additional Collateral")

    loans = list_loans(
        active_only=False
    )

    if not loans:

        st.info(
            "Create a loan first."
        )

    else:

        selected_loan = st.selectbox(
            "Borrower / Loan",
            loans,
            format_func=loan_label,
            key="additional_collateral_loan",
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
                "💾 Add Additional Collateral",
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
                        selected_loan["id"],
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
                        f"Collateral could not be saved: {exc}"
                    )


        existing = list_additional_collateral(
            selected_loan["id"]
        )

        if existing:

            st.divider()

            st.subheader(
                "Existing Additional Collateral"
            )

            collateral_view = pd.DataFrame(
                existing
            ).rename(
                columns={
                    "collateral_type": "Type",
                    "collateral_amount_cr": "Amount (Cr)",
                    "collateral_date": "Date",
                    "maturity_release_date": "Maturity / Release",
                }
            )

            st.dataframe(
                collateral_view,
                width="stretch",
                hide_index=True,
            )


# ============================================================
# 4. REPAYMENT SCHEDULE
# ============================================================

with tab_repayment:

    st.subheader(
        "Repayment Schedule"
    )

    loans = list_loans(
        active_only=False
    )

    if not loans:

        st.info(
            "Create a loan first."
        )

    else:

        selected_loan = st.selectbox(
            "Borrower / Loan",
            loans,
            format_func=loan_label,
            key="repayment_loan",
        )

        st.caption(
            "Upload an Excel repayment schedule."
        )

        # --------------------------------------------------------
        # OPENING OUTSTANDING
        # --------------------------------------------------------

        opening_outstanding = float(
            selected_loan.get(
                "outstanding_at_onboarding_cr",
                0
            )
            or 0
        )

        # --------------------------------------------------------
        # EXCEL TEMPLATE
        # --------------------------------------------------------

        template_rows = 10

        template = pd.DataFrame(
            {
                "Repayment Date": [
                    date.today()
                ] + [
                    None
                ] * (template_rows - 1),

                "Opening Outstanding (Cr)": [
                    opening_outstanding
                ] + [
                    None
                ] * (template_rows - 1),

                "Repayment Amount (Cr)": [
                    0.0
                ] * template_rows,

                "Closing Outstanding (Cr)": [
                    None
                ] * template_rows,

                "Remarks": [
                    ""
                ] * template_rows,
            }
        )

        buffer = io.BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine="openpyxl"
        ) as writer:

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
            # LOAN INFORMATION
            # ----------------------------------------------------

            worksheet["A1"] = (
                "Loan Collateral Monitoring System - "
                "Repayment Schedule"
            )

            worksheet["A2"] = "Borrower"

            worksheet["B2"] = selected_loan[
                "borrower"
            ]

            worksheet["C2"] = "Loan No."

            worksheet["D2"] = selected_loan[
                "loan_id"
            ]

            worksheet["A3"] = (
                "Opening Outstanding (Cr)"
            )

            worksheet["B3"] = opening_outstanding

            # ----------------------------------------------------
            # FORMULAS
            # ----------------------------------------------------

            # Header is on Excel row 4.
            # Data starts on Excel row 5.

            for row in range(
                5,
                5 + template_rows
            ):

                if row == 5:

                    worksheet.cell(
                        row=row,
                        column=2,
                        value=opening_outstanding,
                    )

                else:

                    worksheet.cell(
                        row=row,
                        column=2,
                        value=f"=D{row - 1}",
                    )

                worksheet.cell(
                    row=row,
                    column=4,
                    value=(
                        f"=MAX(B{row}-C{row},0)"
                    ),
                )

                worksheet.cell(
                    row=row,
                    column=1,
                ).number_format = "dd-mmm-yyyy"

                for column in [2, 3, 4]:

                    worksheet.cell(
                        row=row,
                        column=column,
                    ).number_format = "#,##0.00"

            # ----------------------------------------------------
            # COLUMN WIDTH
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
            ].width = 30

            worksheet.freeze_panes = "A5"

        st.download_button(
            "⬇️ Download Excel Template",
            buffer.getvalue(),
            "repayment_schedule_template.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        uploaded = st.file_uploader(
            "Upload Repayment Schedule",
            type=[
                "xlsx",
                "xls",
            ],
            key="repayment_upload",
        )

        if uploaded:

            try:

                # ------------------------------------------------
                # READ UPLOADED EXCEL
                #
                # Template headers are on Excel row 4.
                # ------------------------------------------------

                xls = pd.read_excel(
                    uploaded,
                    header=3,
                )

                normalized = {
                    str(c).strip().lower(): c
                    for c in xls.columns
                }

                date_col = normalized.get(
                    "repayment date"
                )

                amount_col = normalized.get(
                    "repayment amount (cr)"
                )

                remarks_col = normalized.get(
                    "remarks"
                )

                if not date_col or not amount_col:

                    st.error(
                        "Excel must contain "
                        "'Repayment Date' and "
                        "'Repayment Amount (Cr)'."
                    )

                else:

                    # ------------------------------------------------
                    # PREPARE UPLOADED DATA
                    # ------------------------------------------------

                    working = pd.DataFrame()

                    working[
                        "repayment_date"
                    ] = pd.to_datetime(
                        xls[date_col],
                        errors="coerce",
                    )

                    working[
                        "repayment_amount_cr"
                    ] = pd.to_numeric(
                        xls[amount_col],
                        errors="coerce",
                    )

                    if remarks_col:

                        working[
                            "remarks"
                        ] = (
                            xls[remarks_col]
                            .fillna("")
                            .astype(str)
                        )

                    else:

                        working[
                            "remarks"
                        ] = ""

                    # ------------------------------------------------
                    # REMOVE COMPLETELY BLANK ROWS
                    # ------------------------------------------------

                    working = working[
                        ~(
                            working[
                                "repayment_date"
                            ].isna()
                            &
                            working[
                                "repayment_amount_cr"
                            ].isna()
                        )
                    ].copy()

                    # ------------------------------------------------
                    # VALIDATE
                    # ------------------------------------------------

                    if working.empty:

                        st.error(
                            "No repayment rows found in "
                            "the uploaded Excel file."
                        )

                    elif working[
                        "repayment_date"
                    ].isna().any():

                        st.error(
                            "One or more repayment dates "
                            "are invalid."
                        )

                    elif working[
                        "repayment_amount_cr"
                    ].isna().any():

                        st.error(
                            "One or more repayment amounts "
                            "are invalid."
                        )

                    elif (
                        working[
                            "repayment_amount_cr"
                        ] < 0
                    ).any():

                        st.error(
                            "Repayment amount cannot "
                            "be negative."
                        )

                    else:

                        # ------------------------------------------------
                        # SORT BY REPAYMENT DATE
                        # ------------------------------------------------

                        working = (
                            working
                            .sort_values(
                                "repayment_date"
                            )
                            .reset_index(
                                drop=True
                            )
                        )

                        # ------------------------------------------------
                        # CALCULATE OUTSTANDING
                        # ------------------------------------------------

                        current_outstanding = float(
                            selected_loan.get(
                                "outstanding_at_onboarding_cr",
                                0,
                            )
                            or 0
                        )

                        opening_values = []
                        closing_values = []

                        calculation_error = None

                        for repayment_amount in (
                            working[
                                "repayment_amount_cr"
                            ]
                        ):

                            repayment_amount = float(
                                repayment_amount
                            )

                            if repayment_amount > current_outstanding:

                                calculation_error = (
                                    "Repayment amount "
                                    f"{repayment_amount:,.2f} Cr "
                                    "cannot exceed opening "
                                    f"outstanding "
                                    f"{current_outstanding:,.2f} Cr."
                                )

                                break

                            opening_values.append(
                                current_outstanding
                            )

                            closing_outstanding = (
                                current_outstanding
                                - repayment_amount
                            )

                            closing_values.append(
                                closing_outstanding
                            )

                            current_outstanding = (
                                closing_outstanding
                            )

                        if calculation_error:

                            st.error(
                                calculation_error
                            )

                        else:

                            # ------------------------------------------------
                            # STORE CALCULATED VALUES
                            # ------------------------------------------------

                            working[
                                "opening_outstanding_cr"
                            ] = opening_values

                            working[
                                "closing_outstanding_cr"
                            ] = closing_values

                            working[
                                "repayment_date"
                            ] = (
                                working[
                                    "repayment_date"
                                ]
                                .dt.strftime(
                                    "%Y-%m-%d"
                                )
                            )

                            # ------------------------------------------------
                            # PREVIEW
                            # ------------------------------------------------

                            preview = working[
                                [
                                    "repayment_date",
                                    "opening_outstanding_cr",
                                    "repayment_amount_cr",
                                    "closing_outstanding_cr",
                                    "remarks",
                                ]
                            ].copy()

                            preview = preview.rename(
                                columns={
                                    "repayment_date":
                                        "Repayment Date",

                                    "opening_outstanding_cr":
                                        "Opening Outstanding (Cr)",

                                    "repayment_amount_cr":
                                        "Repayment Amount (Cr)",

                                    "closing_outstanding_cr":
                                        "Closing Outstanding (Cr)",

                                    "remarks":
                                        "Remarks",
                                }
                            )

                            st.subheader(
                                "Repayment Schedule Preview"
                            )

                            st.dataframe(
                                preview,
                                width="stretch",
                                hide_index=True,
                            )

                            # ------------------------------------------------
                            # SAVE NEW SCHEDULE
                            #
                            # add_repayment_rows() deletes the
                            # existing schedule for this loan
                            # and then inserts this new schedule.
                            # ------------------------------------------------

                            if st.button(
                                "💾 Save Repayment Schedule",
                                type="primary",
                                key="save_repayment_schedule",
                            ):

                                count = add_repayment_rows(
                                    selected_loan["id"],
                                    working.to_dict(
                                        "records"
                                    ),
                                )

                                st.success(
                                    f"Saved {count} repayment row(s). "
                                    "Previous repayment schedule "
                                    "has been replaced."
                                )

                                st.rerun()

            except Exception as exc:

                st.error(
                    f"Could not read Excel file: {exc}"
                )


        existing = list_repayments(
            selected_loan["id"]
        )
                
        
        if existing:

            st.divider()

            st.subheader(
                "Existing Repayment Schedule"
            )

            # ------------------------------------------------
            # BUILD BUSINESS-FACING REPAYMENT VIEW
            # ------------------------------------------------

            repayment_view = pd.DataFrame(
                existing
            ).copy()

            repayment_view[
                "repayment_date"
            ] = pd.to_datetime(
                repayment_view[
                    "repayment_date"
                ],
                errors="coerce",
            )

            repayment_view = (
                repayment_view
                .sort_values(
                    "repayment_date"
                )
                .reset_index(
                    drop=True
                )
            )

            # ------------------------------------------------
            # CALCULATE OPENING / CLOSING OUTSTANDING
            #
            # Existing database records currently store only
            # repayment amount. Therefore these balances are
            # derived for display from the loan onboarding
            # outstanding.
            # ------------------------------------------------

            opening_outstanding = float(
                selected_loan.get(
                    "outstanding_at_onboarding_cr",
                    0
                )
                or 0
            )

            opening_values = []
            closing_values = []

            for repayment_amount in (
                pd.to_numeric(
                    repayment_view[
                        "repayment_amount_cr"
                    ],
                    errors="coerce",
                )
                .fillna(0)
            ):

                opening_values.append(
                    opening_outstanding
                )

                closing_outstanding = (
                    opening_outstanding
                    - float(
                        repayment_amount
                    )
                )

                closing_outstanding = max(
                    closing_outstanding,
                    0
                )

                closing_values.append(
                    closing_outstanding
                )

                opening_outstanding = (
                    closing_outstanding
                )

            repayment_view[
                "Opening Outstanding (Cr)"
            ] = opening_values

            repayment_view[
                "Closing Outstanding (Cr)"
            ] = closing_values

            # ------------------------------------------------
            # FORMAT DISPLAY
            # ------------------------------------------------

            repayment_view[
                "Repayment Date"
            ] = (
                repayment_view[
                    "repayment_date"
                ]
                .dt.strftime(
                    "%d-%b-%Y"
                )
            )

            repayment_view[
                "Opening Outstanding (Cr)"
            ] = repayment_view[
                "Opening Outstanding (Cr)"
            ].map(
                lambda x:
                f"{x:,.2f}"
            )

            repayment_view[
                "Repayment Amount (Cr)"
            ] = pd.to_numeric(
                repayment_view[
                    "repayment_amount_cr"
                ],
                errors="coerce",
            ).fillna(0).map(
                lambda x:
                f"{x:,.2f}"
            )

            repayment_view[
                "Closing Outstanding (Cr)"
            ] = repayment_view[
                "Closing Outstanding (Cr)"
            ].map(
                lambda x:
                f"{x:,.2f}"
            )

            repayment_view[
                "Remarks"
            ] = (
                repayment_view[
                    "remarks"
                ]
                .fillna("")
                .astype(str)
            )

            # ------------------------------------------------
            # FINAL BUSINESS-FACING COLUMNS
            # ------------------------------------------------

            repayment_view = repayment_view[
                [
                    "Repayment Date",
                    "Opening Outstanding (Cr)",
                    "Repayment Amount (Cr)",
                    "Closing Outstanding (Cr)",
                    "Remarks",
                ]
            ]

            st.dataframe(
                repayment_view,
                width="stretch",
                hide_index=True,
            )

# ============================================================
# 5. PREPAYMENT
# ============================================================

with tab_prepayment:

    st.subheader(
        "Prepayment"
    )

    loans = list_loans(
        active_only=False
    )

    if not loans:

        st.info(
            "Create a loan first."
        )

    else:

        selected_loan = st.selectbox(
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
                        selected_loan["id"],
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
            selected_loan["id"]
        )

        if existing:

            st.divider()

            st.subheader(
                "Existing Prepayments"
            )

            prepayment_view = pd.DataFrame(
                existing
            ).rename(
                columns={
                    "prepayment_date": "Date",
                    "amount_cr": "Amount (Cr)",
                    "remarks": "Remarks",
                }
            )

            st.dataframe(
                prepayment_view,
                width="stretch",
                hide_index=True,
            )


# ============================================================
# 6. SHARE MOVEMENT
# ============================================================

with tab_movement:

    st.subheader(
        "Share Movement"
    )

    st.caption(
        "Record additions or releases of pledged shares."
    )

    securities = list_securities(
        active_only=True
    )

    if not securities:

        st.info(
            "Add a listed security first."
        )

    else:

        selected_security = st.selectbox(
            "Borrower / Security",
            securities,
            format_func=security_label,
            key="movement_security",
        )

        current_shares = get_current_share_balance(
            selected_security["id"]
        )

        st.metric(
            "Current Pledged Shares",
            f"{current_shares:,}",
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
                "Movement Type",
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

                movement_id, resulting = add_share_movement(
                    selected_security["id"],
                    movement_date,
                    movement_type,
                    quantity,
                    remarks,
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
            selected_security["id"]
        )

        if existing:

            st.divider()

            st.subheader(
                "Share Movement History"
            )

            movement_view = pd.DataFrame(
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

            movement_view[
                "Shares"
            ] = movement_view[
                "Shares"
            ].map(
                lambda x: f"{int(x):,}"
            )

            movement_view[
                "Resulting Shares"
            ] = movement_view[
                "Resulting Shares"
            ].map(
                lambda x: f"{int(x):,}"
            )

            st.dataframe(
                movement_view[
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
    "Loan Collateral Monitoring System — "
    "Master/Input Data Management"
)