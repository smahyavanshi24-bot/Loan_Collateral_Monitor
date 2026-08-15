import pandas as pd


# ============================================================
# COLLATERAL STRESS TESTING ENGINE
# ============================================================
#
# Stress is ALWAYS applied to the underlying security price.
#
# Modes:
#   1. Single Scrip
#   2. Combined Scrips
#   3. Custom Scrips
#
# Every stress produces:
#   - Security-wise stressed result
#   - Borrower-wise resulting stressed cover
#
# Status logic:
#
#   SAFE:
#       Cover > Required Cover + 0.10x
#
#   WATCH:
#       Required Cover <= Cover <= Required Cover + 0.10x
#
#   ACTION REQUIRED:
#       Cover < Required Cover
#
# Historical database records are never modified.
# ============================================================


DEFAULT_PRICE_FALLS = [
    0,
    5,
    10,
    15,
    20,
    25,
    30,
    40,
    50,
]


# ============================================================
# STATUS
# ============================================================

def get_stress_status(
    cover,
    required_cover,
):
    """
    Determine SAFE / WATCH / ACTION REQUIRED.

    SAFE:
        Cover > Required Cover + 0.10x

    WATCH:
        Required Cover <= Cover <= Required Cover + 0.10x

    ACTION REQUIRED:
        Cover < Required Cover
    """

    if cover is None or pd.isna(cover):
        return "⚪ Price Unavailable"

    if required_cover is None or pd.isna(required_cover):
        return "⚪ Requirement Unavailable"

    safe_threshold = (
        float(required_cover) + 0.10
    )

    if cover > safe_threshold:

        return "🟢 SAFE"

    elif cover >= float(required_cover):

        return "🟡 WATCH"

    else:

        return "🔴 ACTION REQUIRED"


# ============================================================
# NORMALIZE LIVE DATA
# ============================================================

def _prepare_data(df):
    """
    Prepare live collateral dataframe.

    Expected columns include:

        borrower
        security
        price
        shares
        loan_amount
        collateral_value
        required_cover
        borrower_required_cover

    required_cover:
        Security-wise required cover.

    borrower_required_cover:
        Borrower-wise required cover.
    """

    if df is None:
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    data = df.copy()


    # --------------------------------------------------------
    # NUMERIC FIELDS
    # --------------------------------------------------------

    numeric_columns = [
        "price",
        "shares",
        "loan_amount",
        "collateral_value",
        "required_cover",
        "borrower_required_cover",
    ]

    for column in numeric_columns:

        if column in data.columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )


    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if "date" in data.columns:

        data["date"] = pd.to_datetime(
            data["date"],
            errors="coerce"
        )


    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = [
        "borrower",
        "security",
        "price",
        "shares",
        "loan_amount",
        "collateral_value",
        "required_cover",
        "borrower_required_cover",
    ]

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:

        raise ValueError(
            "Stress testing is missing required "
            f"columns: {', '.join(missing)}"
        )


    # --------------------------------------------------------
    # LATEST TRADING DATE
    # --------------------------------------------------------

    if "date" in data.columns:

        data = data[
            data["date"].notna()
        ].copy()

        if data.empty:
            return pd.DataFrame()

        # Ignore weekends
        data = data[
            data["date"].dt.weekday < 5
        ].copy()

        if data.empty:
            return pd.DataFrame()

        latest_date = data["date"].max()

        data = data[
            data["date"] == latest_date
        ].copy()


    # --------------------------------------------------------
    # VALID MARKET DATA
    # --------------------------------------------------------

    data = data[
        data["price"].notna()
        &
        (data["price"] > 0)
        &
        data["shares"].notna()
        &
        (data["shares"] >= 0)
        &
        data["loan_amount"].notna()
        &
        (data["loan_amount"] > 0)
    ].copy()


    return data


# ============================================================
# BUILD STRESS MAP
# ============================================================

def _build_stress_map(
    data,
    mode,
    selected_security=None,
    price_fall=0,
    custom_stresses=None,
):
    """
    Return a dictionary:

        security -> price fall %

    Example:

        {
            "Kalyan Jewellers India Limited": 10,
            "Mindspace Business Parks REIT": 0
        }

    Modes:

        single
        combined
        custom
    """

    mode = str(
        mode or ""
    ).strip().lower()


    # --------------------------------------------------------
    # SINGLE SCRIP
    # --------------------------------------------------------

    if mode in {
        "single",
        "single scrip",
        "single security",
    }:

        if not selected_security:

            raise ValueError(
                "Please select a security."
            )

        selected_security = str(
            selected_security
        ).strip()

        available = set(
            data["security"]
            .astype(str)
            .str.strip()
        )

        if selected_security not in available:

            raise ValueError(
                f"Security '{selected_security}' "
                "is not available for stress testing."
            )

        fall = abs(
            float(price_fall or 0)
        )

        return {
            selected_security: fall
        }


    # --------------------------------------------------------
    # COMBINED SCRIPS
    # --------------------------------------------------------

    if mode in {
        "combined",
        "combined scrips",
        "combined securities",
    }:

        fall = abs(
            float(price_fall or 0)
        )

        return {
            str(security).strip(): fall
            for security in data["security"]
            .dropna()
            .unique()
        }


    # --------------------------------------------------------
    # CUSTOM SCRIPS
    # --------------------------------------------------------

    if mode in {
        "custom",
        "custom scrips",
        "custom securities",
    }:

        if not custom_stresses:

            raise ValueError(
                "Please select at least one security "
                "for custom stress testing."
            )

        available = set(
            data["security"]
            .astype(str)
            .str.strip()
        )

        stress_map = {}

        for security, fall in custom_stresses.items():

            security = str(
                security
            ).strip()

            if security not in available:

                raise ValueError(
                    f"Security '{security}' "
                    "is not available for this borrower."
                )

            stress_map[security] = abs(
                float(fall or 0)
            )

        return stress_map


    raise ValueError(
        "Invalid stress mode. "
        "Use Single Scrip, Combined Scrips "
        "or Custom Scrips."
    )


# ============================================================
# RUN STRESS TEST
# ============================================================

def run_stress_test(
    df,
    mode="Combined Scrips",
    selected_security=None,
    price_fall=0,
    custom_stresses=None,
):
    """
    Run collateral stress testing.

    Parameters
    ----------
    df:
        Current live collateral dataframe.

    mode:
        Single Scrip
        Combined Scrips
        Custom Scrips

    selected_security:
        Used for Single Scrip mode.

    price_fall:
        Underlying price fall percentage for
        Single / Combined mode.

    custom_stresses:
        Dictionary for Custom mode.

        Example:

            {
                "Kalyan Jewellers India Limited": 20,
                "Mindspace Business Parks REIT": 10
            }


    Returns
    -------
    dict containing:

        security_result
        borrower_result
        stress_map
        mode
    """


    # --------------------------------------------------------
    # PREPARE DATA
    # --------------------------------------------------------

    data = _prepare_data(df)

    if data.empty:

        return {
            "security_result": pd.DataFrame(),
            "borrower_result": pd.DataFrame(),
            "stress_map": {},
            "mode": mode,
        }


    # --------------------------------------------------------
    # CREATE STRESS MAP
    # --------------------------------------------------------

    stress_map = _build_stress_map(
        data=data,
        mode=mode,
        selected_security=selected_security,
        price_fall=price_fall,
        custom_stresses=custom_stresses,
    )


    # --------------------------------------------------------
    # APPLY STRESS
    # --------------------------------------------------------

    security_rows = []


    for _, row in data.iterrows():

        security = str(
            row["security"]
        ).strip()

        borrower = row["borrower"]

        current_price = float(
            row["price"]
        )

        shares = float(
            row["shares"]
        )

        loan_amount = float(
            row["loan_amount"]
        )

        required_security_cover = float(
            row["required_cover"]
        )

        borrower_required_cover = float(
            row["borrower_required_cover"]
        )


        # ----------------------------------------------------
        # DETERMINE STRESS FOR THIS SECURITY
        # ----------------------------------------------------

        fall = float(
            stress_map.get(
                security,
                0
            )
        )


        # ----------------------------------------------------
        # STRESSED PRICE
        # ----------------------------------------------------

        stressed_price = (
            current_price
            * (
                1
                -
                (fall / 100)
            )
        )


        # ----------------------------------------------------
        # STRESSED COLLATERAL
        #
        # Price is in ₹.
        #
        # Convert to ₹ Crore:
        #
        # ₹ × shares / 1 crore
        # ----------------------------------------------------

        stressed_collateral = (
            stressed_price
            * shares
            / 10_000_000
        )


        # ----------------------------------------------------
        # STRESSED SECURITY COVER
        # ----------------------------------------------------

        stressed_security_cover = (
            stressed_collateral
            / loan_amount
        )


        # ----------------------------------------------------
        # SECURITY BUFFER
        # ----------------------------------------------------

        security_buffer = (
            stressed_security_cover
            -
            required_security_cover
        )


        # ----------------------------------------------------
        # SECURITY STATUS
        # ----------------------------------------------------

        security_status = get_stress_status(
            stressed_security_cover,
            required_security_cover,
        )


        # ----------------------------------------------------
        # STORE SECURITY RESULT
        # ----------------------------------------------------

        security_rows.append(
            {
                "Borrower":
                    borrower,

                "Security":
                    security,

                "Stressed Price":
                    stressed_price,

                "Stressed Collateral":
                    stressed_collateral,

                "Stressed Cover":
                    stressed_security_cover,

                "Required Cover":
                    required_security_cover,

                "Buffer":
                    security_buffer,

                "Status":
                    security_status,

                # Internal calculation fields
                "_loan_amount":
                    loan_amount,

                "_borrower_required_cover":
                    borrower_required_cover,

                "_current_collateral":
                    float(
                        row["collateral_value"]
                    ),

                "_stress_pct":
                    fall,
            }
        )


    security_result = pd.DataFrame(
        security_rows
    )


    if security_result.empty:

        return {
            "security_result":
                pd.DataFrame(),

            "borrower_result":
                pd.DataFrame(),

            "stress_map":
                stress_map,

            "mode":
                mode,
        }


    # ========================================================
    # BORROWER-LEVEL RESULT
    # ========================================================

    borrower_rows = []


    for borrower, group in security_result.groupby(
        "Borrower",
        sort=False
    ):

        # ----------------------------------------------------
        # LOAN AMOUNT
        # ----------------------------------------------------

        loan_amount = float(
            group["_loan_amount"].iloc[0]
        )


        # ----------------------------------------------------
        # BORROWER REQUIRED COVER
        # ----------------------------------------------------

        required_borrower_cover = float(
            group[
                "_borrower_required_cover"
            ].max()
        )


        # ----------------------------------------------------
        # CURRENT COLLATERAL
        # ----------------------------------------------------

        current_collateral = float(
            group[
                "_current_collateral"
            ].sum()
        )


        # ----------------------------------------------------
        # STRESSED COLLATERAL
        # ----------------------------------------------------

        stressed_collateral = float(
            group[
                "Stressed Collateral"
            ].sum()
        )


        # ----------------------------------------------------
        # CURRENT BORROWER COVER
        # ----------------------------------------------------

        current_borrower_cover = (
            current_collateral
            / loan_amount
        )


        # ----------------------------------------------------
        # STRESSED BORROWER COVER
        # ----------------------------------------------------

        stressed_borrower_cover = (
            stressed_collateral
            / loan_amount
        )


        # ----------------------------------------------------
        # BUFFER
        # ----------------------------------------------------

        borrower_buffer = (
            stressed_borrower_cover
            -
            required_borrower_cover
        )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        borrower_status = get_stress_status(
            stressed_borrower_cover,
            required_borrower_cover,
        )


        # ----------------------------------------------------
        # STORE BORROWER RESULT
        # ----------------------------------------------------

        borrower_rows.append(
            {
                "Borrower":
                    borrower,

                "Stressed Collateral":
                    stressed_collateral,

                "Stressed Cover":
                    stressed_borrower_cover,

                "Required Cover":
                    required_borrower_cover,

                "Buffer":
                    borrower_buffer,

                "Status":
                    borrower_status,

                # Additional useful fields
                "_Current Collateral":
                    current_collateral,

                "_Current Cover":
                    current_borrower_cover,

                "_Loan Amount":
                    loan_amount,
            }
        )


    borrower_result = pd.DataFrame(
        borrower_rows
    )


    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "security_result":
            security_result,

        "borrower_result":
            borrower_result,

        "stress_map":
            stress_map,

        "mode":
            mode,
    }


# ============================================================
# HELPER: GET SECURITY LIST
# ============================================================

def get_available_securities(
    df,
    borrower=None,
):
    """
    Return active securities available for
    stress testing.

    If borrower is supplied, only that borrower's
    securities are returned.
    """

    data = _prepare_data(df)

    if data.empty:
        return []


    if borrower:

        data = data[
            data["borrower"].astype(str)
            ==
            str(borrower)
        ]


    return sorted(
        data["security"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


# ============================================================
# HELPER: GET BORROWER LIST
# ============================================================

def get_available_borrowers(df):
    """
    Return borrowers available for stress testing.
    """

    data = _prepare_data(df)

    if data.empty:
        return []


    return sorted(
        data["borrower"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )