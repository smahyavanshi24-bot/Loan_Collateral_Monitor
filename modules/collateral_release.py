import pandas as pd
import math

# ============================================================
# COLLATERAL RELEASE POLICY
# ============================================================

REQUIRED_COVER = 2.00
RELEASE_COVER = 2.10


def calculate_release_request(
    df,
    borrower,
    security,
    requested_shares,
):
    """
    Checks whether a borrower can release a requested
    number of pledged shares.

    Rules:
        Cover < 2.00x
            -> RELEASE NOT ALLOWED

        2.00x <= Cover < 2.10x
            -> RELEASE NOT ALLOWED

        Cover >= 2.10x
            -> Release allowed only if borrower remains
               at or above 2.10x after the release.

    This function only provides a recommendation.
    It does not modify pledged shares.
    """

    # ========================================================
    # VALIDATE INPUT
    # ========================================================

    if df is None or df.empty:
        return {
            "status": "ERROR",
            "message": "No collateral data available."
        }

    if not borrower:
        return {
            "status": "ERROR",
            "message": "Borrower is required."
        }

    if not security:
        return {
            "status": "ERROR",
            "message": "Security is required."
        }

    try:
        requested_shares = int(requested_shares)
    except (TypeError, ValueError):
        return {
            "status": "ERROR",
            "message": "Requested shares must be a valid number."
        }

    if requested_shares <= 0:
        return {
            "status": "ERROR",
            "message": "Requested shares must be greater than zero."
        }

    data = df.copy()

    # ========================================================
    # REQUIRED COLUMNS
    # ========================================================

    required_columns = [
        "date",
        "borrower",
        "security",
        "price",
        "shares",
        "loan_amount",
    ]

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:
        return {
            "status": "ERROR",
            "message": (
                "Missing required columns: "
                + ", ".join(missing)
            )
        }

    # ========================================================
    # DATE
    # ========================================================

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    data = data[
        data["date"].notna()
    ].copy()

    if data.empty:
        return {
            "status": "ERROR",
            "message": "No valid trading-date data available."
        }

    latest_date = data["date"].max()

    data = data[
        data["date"] == latest_date
    ].copy()

    # ========================================================
    # NUMERIC DATA
    # ========================================================

    for column in [
        "price",
        "shares",
        "loan_amount",
    ]:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    data = data.dropna(
        subset=[
            "price",
            "shares",
            "loan_amount",
        ]
    ).copy()

    # ========================================================
    # BORROWER DATA
    # ========================================================

    borrower_df = data[
        data["borrower"].astype(str).str.strip()
        == str(borrower).strip()
    ].copy()

    if borrower_df.empty:
        return {
            "status": "ERROR",
            "message": (
                f"Borrower '{borrower}' was not found."
            )
        }

    # ========================================================
    # SECURITY DATA
    # ========================================================

    security_df = borrower_df[
        borrower_df["security"].astype(str).str.strip()
        == str(security).strip()
    ].copy()

    if security_df.empty:
        return {
            "status": "ERROR",
            "message": (
                f"Security '{security}' was not found "
                f"for borrower '{borrower}'."
            )
        }

    # We expect one security record.
    security_row = security_df.iloc[0]

    # ========================================================
    # LOAN AMOUNT
    # ========================================================

    loan_amount = float(
        borrower_df["loan_amount"].max()
    )

    if loan_amount <= 0:
        return {
            "status": "ERROR",
            "message": "Loan amount must be greater than zero."
        }

    # ========================================================
    # CURRENT BORROWER COLLATERAL
    # ========================================================

    borrower_df["security_value"] = (
        borrower_df["price"]
        * borrower_df["shares"]
    )

    current_collateral = float(
        borrower_df["security_value"].sum()
    )

    current_cover = (
        current_collateral
        / loan_amount
    )

    # ========================================================
    # REQUESTED SECURITY
    # ========================================================

    price = float(
        security_row["price"]
    )

    current_shares = int(
        security_row["shares"]
    )

    if price <= 0:
        return {
            "status": "ERROR",
            "message": "Security price must be greater than zero."
        }

    if requested_shares > current_shares:
        return {
            "status": "NOT APPROVED",
            "message": (
                "Requested release exceeds the current "
                "pledged share balance."
            ),
            "Borrower": borrower,
            "Security": security,
            "Current Shares": current_shares,
            "Requested Shares": requested_shares,
        }

    # ========================================================
    # RELEASE VALUE
    # ========================================================

    release_value = (
        requested_shares
        * price
    )

    # ========================================================
    # COLLATERAL AFTER RELEASE
    # ========================================================

    collateral_after_release = (
        current_collateral
        - release_value
    )

    cover_after_release = (
        collateral_after_release
        / loan_amount
    )

    # ========================================================
    # TARGET COLLATERAL
    # ========================================================

    minimum_collateral = (
        loan_amount
        * REQUIRED_COVER
    )

    release_target = (
        loan_amount
        * RELEASE_COVER
    )

    # ========================================================
    # MAXIMUM SAFE RELEASE
    # ========================================================

    excess_value = max(
        0,
        current_collateral
        - release_target
    )

    maximum_release_shares = (
        math.floor(
            excess_value
            / price
        )
        if price > 0
        else 0
    )

    maximum_release_shares = min(
        maximum_release_shares,
        current_shares,
    )

    maximum_release_value = (
        maximum_release_shares
        * price
    )

    # ========================================================
    # DECISION
    # ========================================================

    if current_cover < REQUIRED_COVER:

        status = "NOT APPROVED"

        message = (
            "Release not permitted because borrower "
            "cover is below the required 2.00x."
        )

    elif current_cover < RELEASE_COVER:

        status = "NOT APPROVED"

        message = (
            "Release not permitted because borrower "
            "cover is below the 2.10x release threshold."
        )

    elif cover_after_release < RELEASE_COVER:

        status = "NOT APPROVED"

        message = (
            "Requested release is too high. "
            "The borrower would fall below the "
            "2.10x release target."
        )

    else:

        status = "APPROVED"

        message = (
            "Release is permissible while retaining "
            "borrower-level cover at or above 2.10x. "
            "Credit approval is still required."
        )

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "Trading Date":
            latest_date.strftime(
                "%d-%b-%Y"
            ),

        "Borrower":
            borrower,

        "Security":
            security,

        "Price":
            round(
                price,
                2,
            ),

        "Current Shares":
            current_shares,

        "Requested Shares":
            requested_shares,

        "Release Value":
            round(
                release_value,
                2,
            ),

        "Current Collateral":
            round(
                current_collateral,
                2,
            ),

        "Loan Amount":
            round(
                loan_amount,
                2,
            ),

        "Minimum Required Collateral":
            round(
                minimum_collateral,
                2,
            ),

        "Release Target Collateral":
            round(
                release_target,
                2,
            ),

        "Current Cover":
            round(
                current_cover,
                2,
            ),

        "Collateral After Release":
            round(
                collateral_after_release,
                2,
            ),

        "Cover After Release":
            round(
                cover_after_release,
                2,
            ),

        "Maximum Safe Release Shares":
            maximum_release_shares,

        "Maximum Safe Release Value":
            round(
                maximum_release_value,
                2,
            ),

        "Status":
            status,

        "Message":
            message,
    }