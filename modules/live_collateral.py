from datetime import date

from modules.input_database import (
    initialize_input_database,
    list_loans,
    list_securities,
    get_current_share_balance,
    list_repayments,
    list_prepayments,
)

def get_today_outstanding(
    loan,
):
    """
    Calculate today's outstanding amount.

    Starting point:
        Outstanding at onboarding

    Reduce by:
        Repayments dated on or before today
        Prepayments dated on or before today

    Future-dated repayments/prepayments are ignored.
    """

    today = date.today()

    outstanding = float(
        loan.get(
            "outstanding_at_onboarding_cr",
            0,
        )
        or 0
    )

    loan_db_id = loan["id"]

    # --------------------------------------------------------
    # REPAYMENTS UP TO TODAY
    # --------------------------------------------------------

    repayments = list_repayments(
        loan_db_id
    )

    for repayment in repayments:

        repayment_date = repayment.get(
            "repayment_date"
        )

        if not repayment_date:
            continue

        try:

            repayment_date = date.fromisoformat(
                str(
                    repayment_date
                )[:10]
            )

        except Exception:

            continue

        if repayment_date <= today:

            amount = float(
                repayment.get(
                    "repayment_amount_cr",
                    0,
                )
                or 0
            )

            outstanding -= amount

    # --------------------------------------------------------
    # PREPAYMENTS UP TO TODAY
    # --------------------------------------------------------

    prepayments = list_prepayments(
        loan_db_id
    )

    for prepayment in prepayments:

        prepayment_date = prepayment.get(
            "prepayment_date"
        )

        if not prepayment_date:
            continue

        try:

            prepayment_date = date.fromisoformat(
                str(
                    prepayment_date
                )[:10]
            )

        except Exception:

            continue

        if prepayment_date <= today:

            amount = float(
                prepayment.get(
                    "prepayment_amount_cr",
                    0,
                )
                or 0
            )

            outstanding -= amount

    # --------------------------------------------------------
    # OUTSTANDING CANNOT BE NEGATIVE
    # --------------------------------------------------------

    return max(
        outstanding,
        0,
    )


def get_active_live_securities():

   
    """
    Read active loans and active listed securities
    from the Input Portal database.

    Returns one dictionary per borrower/security position.
    """

    initialize_input_database()

    rows = []

    loans = list_loans(
        active_only=True
    )

    for loan in loans:

        loan_db_id = loan["id"]

        securities = list_securities(
            loan_db_id=loan_db_id,
            active_only=True,
        )

        for security in securities:

            # ------------------------------------------------
            # CURRENT PLEDGED SHARES
            # ------------------------------------------------

            try:

                current_shares = get_current_share_balance(
                    security["id"]
                )

            except Exception:

                current_shares = security[
                    "initial_pledged_shares"
                ]


            # ------------------------------------------------
            # NSE SYMBOL
            # ------------------------------------------------

            nse_symbol = (
                security.get("nse_symbol")
                or ""
            ).strip()


            # ------------------------------------------------
            # ISIN
            # ------------------------------------------------

            isin = (
                security.get("isin")
                or ""
            ).strip()


            # ------------------------------------------------
            # CREATE LIVE POSITION
            # ------------------------------------------------

            rows.append(
                {
                    "borrower": loan["borrower"],

                    "loan_id": loan["loan_id"],

                    "loan_db_id": loan_db_id,

                    "loan_amount": get_today_outstanding(
                        loan
                    ),
                    
                    "sanctioned_amount": float(
                        loan[
                            "sanctioned_amount_cr"
                        ]
                    ),

                    "required_cover": float(
                        loan[
                            "required_security_cover"
                        ]
                    ),

                    "loan_status": loan[
                        "loan_status"
                    ],

                    "security_id": security[
                        "id"
                    ],

                    "security": security[
                        "listed_company_name"
                    ],

                    "symbol": nse_symbol,

                    "nse_symbol": nse_symbol,

                    "isin": isin,

                    "initial_shares": int(
                        security[
                            "initial_pledged_shares"
                        ]
                    ),

                    "current_shares": int(
                        current_shares
                    ),

                    "pledge_date": security[
                        "initial_pledge_date"
                    ],

                    "security_required_cover": float(
                        security[
                            "collateralwise_security_cover"
                        ]
                    ),
                }
            )

    return rows