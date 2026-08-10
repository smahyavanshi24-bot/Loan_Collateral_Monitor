import pandas as pd
import math


# ============================================================
# COLLATERAL POLICY
# ============================================================

REQUIRED_COVER = 2.00
RELEASE_COVER = 2.10


def calculate_collateral_rebalancing(df):
    """
    Borrower-level collateral rebalancing engine.

    Policy:

        Cover < 2.00x
            -> ADDITIONAL COLLATERAL REQUIRED

        2.00x <= Cover < 2.10x
            -> HOLD / MONITOR

        Cover >= 2.10x
            -> RELEASE ELIGIBLE

    Important rule:

        Only ONE security per borrower is selected
        for release or additional collateral.

    The module only recommends action.
    It never changes pledged shares.
    """

    if df is None or df.empty:
        return pd.DataFrame()

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
        col
        for col in required_columns
        if col not in data.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    # ========================================================
    # DATE
    # ========================================================

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce"
    )

    data = data[
        data["date"].notna()
    ].copy()

    if data.empty:
        return pd.DataFrame()

    data["date"] = data["date"].dt.normalize()

    # ========================================================
    # LATEST TRADING DATE
    # ========================================================

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
            errors="coerce"
        )

    data = data.dropna(
        subset=[
            "price",
            "shares",
            "loan_amount",
        ]
    ).copy()

    if data.empty:
        return pd.DataFrame()

    results = []

    # ========================================================
    # BORROWER LEVEL
    # ========================================================

    for borrower in data["borrower"].unique():

        borrower_df = data[
            data["borrower"] == borrower
        ].copy()

        loan_amount = float(
            borrower_df["loan_amount"].max()
        )

        if loan_amount <= 0:
            continue

        # ----------------------------------------------------
        # SECURITY VALUES
        # ----------------------------------------------------

        borrower_df["security_value"] = (
            borrower_df["price"]
            * borrower_df["shares"]
        )

        # ----------------------------------------------------
        # TOTAL BORROWER COLLATERAL
        # ----------------------------------------------------

        current_collateral = float(
            borrower_df["security_value"].sum()
        )

        # ----------------------------------------------------
        # CURRENT COVER
        # ----------------------------------------------------

        current_cover = (
            current_collateral
            / loan_amount
        )

        # ----------------------------------------------------
        # COLLATERAL TARGETS
        # ----------------------------------------------------

        minimum_collateral = (
            loan_amount
            * REQUIRED_COVER
        )

        release_target = (
            loan_amount
            * RELEASE_COVER
        )

        # ----------------------------------------------------
        # EXCESS / SHORTFALL
        # ----------------------------------------------------

        excess_value = max(
            0,
            current_collateral
            - release_target
        )

        shortfall_value = max(
            0,
            minimum_collateral
            - current_collateral
        )

        # ====================================================
        # DETERMINE BORROWER STATUS
        # ====================================================

        if current_cover < REQUIRED_COVER:

            borrower_action = (
                "🔴 ADDITIONAL COLLATERAL REQUIRED"
            )

        elif current_cover < RELEASE_COVER:

            borrower_action = (
                "🟡 HOLD / MONITOR"
            )

        else:

            borrower_action = (
                "🟢 RELEASE ELIGIBLE"
            )

        # ====================================================
        # SELECT EXACTLY ONE SECURITY
        # ====================================================

        selected_security = None

        # ====================================================
        # ADDITIONAL COLLATERAL CASE
        # ====================================================

        if current_cover < REQUIRED_COVER:

            candidates = borrower_df[
                borrower_df["price"] > 0
            ].copy()

            if not candidates.empty:

                # Select the security requiring the
                # fewest additional shares.

                candidates["shares_needed"] = (
                    shortfall_value
                    / candidates["price"]
                )

                selected_security = (
                    candidates
                    .sort_values(
                        [
                            "shares_needed",
                            "price",
                        ],
                        ascending=[
                            True,
                            False,
                        ],
                    )
                    .iloc[0]["security"]
                )

        # ====================================================
        # RELEASE CASE
        # ====================================================

        elif current_cover >= RELEASE_COVER:

            candidates = borrower_df[
                (borrower_df["price"] > 0)
                & (borrower_df["shares"] > 0)
            ].copy()

            if not candidates.empty:

                # For each security calculate how many
                # whole shares can be released while
                # keeping borrower cover >= 2.10x.

                candidates["max_release_shares"] = (
                    candidates.apply(
                        lambda row: min(
                            int(row["shares"]),
                            math.floor(
                                excess_value
                                / row["price"]
                            )
                        ),
                        axis=1
                    )
                )

                candidates["release_value"] = (
                    candidates["max_release_shares"]
                    * candidates["price"]
                )

                # Choose ONE security capable of providing
                # the largest practical release.

                selected_security = (
                    candidates
                    .sort_values(
                        [
                            "release_value",
                            "security_value",
                        ],
                        ascending=[
                            False,
                            False,
                        ],
                    )
                    .iloc[0]["security"]
                )

        # ====================================================
        # SECURITY LEVEL OUTPUT
        # ====================================================

        for _, row in borrower_df.iterrows():

            security = row["security"]

            price = float(
                row["price"]
            )

            current_shares = int(
                row["shares"]
            )

            security_value = (
                price
                * current_shares
            )

            shares_to_release = 0
            release_value = 0

            shares_to_add = 0
            additional_value = 0

            recommended_shares = (
                current_shares
            )

            # =================================================
            # SELECTED SECURITY
            # =================================================

            if security == selected_security:

                # ---------------------------------------------
                # ADD COLLATERAL
                # ---------------------------------------------

                if current_cover < REQUIRED_COVER:

                    if price > 0:

                        shares_to_add = math.ceil(
                            shortfall_value
                            / price
                        )

                    additional_value = (
                        shares_to_add
                        * price
                    )

                    recommended_shares = (
                        current_shares
                        + shares_to_add
                    )

                    action_reason = (
                        "This security is selected for "
                        "additional collateral because it "
                        "requires the fewest additional shares "
                        "to restore 2.00x borrower cover."
                    )

                # ---------------------------------------------
                # RELEASE
                # ---------------------------------------------

                elif current_cover >= RELEASE_COVER:

                    if price > 0:

                        shares_to_release = min(
                            current_shares,
                            math.floor(
                                excess_value
                                / price
                            )
                        )

                    release_value = (
                        shares_to_release
                        * price
                    )

                    recommended_shares = (
                        current_shares
                        - shares_to_release
                    )

                    if shares_to_release > 0:

                        action_reason = (
                            "This security is selected for "
                            "release. The release retains "
                            "borrower-level cover at or above "
                            "the 2.10x target."
                        )

                    else:

                        action_reason = (
                            "No practical whole-share release "
                            "is available."
                        )

                # ---------------------------------------------
                # HOLD
                # ---------------------------------------------

                else:

                    action_reason = (
                        "Borrower is compliant but below "
                        "the 2.10x release threshold."
                    )

            # =================================================
            # NON-SELECTED SECURITY
            # =================================================

            else:

                recommended_shares = (
                    current_shares
                )

                shares_to_release = 0
                release_value = 0

                shares_to_add = 0
                additional_value = 0

                if current_cover < REQUIRED_COVER:

                    action_reason = (
                        "No action on this security. "
                        "Additional collateral is being "
                        "recommended from another security."
                    )

                elif current_cover < RELEASE_COVER:

                    action_reason = (
                        "No action. Borrower cover is between "
                        "2.00x and 2.10x."
                    )

                else:

                    action_reason = (
                        "No action on this security. "
                        "Another security has been selected "
                        "for the borrower-level release."
                    )

            # =================================================
            # ACTION LABEL
            # =================================================

            if security == selected_security:

                if current_cover < REQUIRED_COVER:

                    action = (
                        "🔴 ADD SHARES"
                    )

                elif current_cover >= RELEASE_COVER:

                    if shares_to_release > 0:

                        action = (
                            "🟢 RELEASE SHARES"
                        )

                    else:

                        action = (
                            "🟡 HOLD"
                        )

                else:

                    action = (
                        "🟡 HOLD / MONITOR"
                    )

            else:

                action = (
                    "🟡 HOLD"
                )

            # =================================================
            # BORROWER COVER AFTER ACTION
            # =================================================

            borrower_collateral_after_action = (
                current_collateral
                - release_value
                + additional_value
            )

            cover_after_action = (
                borrower_collateral_after_action
                / loan_amount
            )

            # =================================================
            # RECOMMENDED COLLATERAL
            # =================================================

            recommended_collateral = (
                recommended_shares
                * price
            )

            # =================================================
            # RESULT
            # =================================================

            results.append(
                {
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
                            2
                        ),

                    "Current Shares":
                        current_shares,

                    "Current Collateral":
                        round(
                            security_value,
                            2
                        ),

                    "Loan Amount":
                        round(
                            loan_amount,
                            2
                        ),

                    "Minimum Required Collateral":
                        round(
                            minimum_collateral,
                            2
                        ),

                    "Release Target Collateral":
                        round(
                            release_target,
                            2
                        ),

                    "Current Cover":
                        round(
                            current_cover,
                            2
                        ),

                    "Excess Collateral":
                        round(
                            excess_value,
                            2
                        ),

                    "Shortfall Collateral":
                        round(
                            shortfall_value,
                            2
                        ),

                    "Shares To Release":
                        shares_to_release,

                    "Release Value":
                        round(
                            release_value,
                            2
                        ),

                    "Shares To Add":
                        shares_to_add,

                    "Additional Collateral":
                        round(
                            additional_value,
                            2
                        ),

                    "Recommended Shares":
                        recommended_shares,

                    "Recommended Collateral":
                        round(
                            recommended_collateral,
                            2
                        ),

                    "Cover After Action":
                        round(
                            cover_after_action,
                            2
                        ),

                    "Action":
                        action,

                    "Action Reason":
                        action_reason,
                }
            )

    return pd.DataFrame(results)