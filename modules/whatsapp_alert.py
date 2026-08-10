# -*- coding: utf-8 -*-

# ============================================================
# LOAN COLLATERAL MONITORING SYSTEM
# WHATSAPP ALERT MODULE
#
# WhatsApp contains ONLY:
# 1. Borrower-level total cover
# 2. Security-level cover
# 3. Critical collateral exceptions
#
# No market movement information is included.
# ============================================================

from datetime import datetime
import requests

from config import (
    WHATSAPP_PHONE_ID,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_RECEIVERS,
    BORROWERS
)


# ============================================================
# HELPER
# ============================================================

def format_crore(amount):

    """
    Convert INR amount into Crores.
    """

    try:

        return (
            float(amount) / 10000000
        )

    except Exception:

        return 0.0


# ============================================================
# 1. FIND BORROWER TOTAL REQUIRED COVER
# ============================================================

def get_borrower_required_cover(borrower_name):

    """
    Gets borrower-level required cover from config.py.

    Example:

    {
        "name": "Everbest",
        "loan_amount": 1200000000,
        "total_required_cover": 2.00
    }
    """

    for borrower in BORROWERS:

        if borrower.get("name") == borrower_name:

            return float(
                borrower.get(
                    "total_required_cover",
                    2.00
                )
            )

    # Safe default

    return 2.00


# ============================================================
# 2. GENERATE DAILY COLLATERAL POSITION
# ============================================================

def generate_daily_summary(records):

    if records is None or len(records) == 0:

        return None

    date = datetime.now().strftime(
        "%d-%b-%Y"
    )

    message = []

    message.append(
        "📊 DAILY COLLATERAL POSITION"
    )

    message.append(
        f"Date: {date}"
    )

    message.append(
        "============================"
    )

    # ========================================================
    # GROUP RECORDS BORROWER-WISE
    # ========================================================

    borrowers = {}

    for record in records:

        borrower = record["borrower"]

        if borrower not in borrowers:

            borrowers[borrower] = []

        borrowers[borrower].append(
            record
        )

    # ========================================================
    # BORROWER LOOP
    # ========================================================

    critical_records = []

    critical_borrowers = []

    for borrower_name, borrower_records in borrowers.items():

        # ----------------------------------------------------
        # LOAN AMOUNT
        # ----------------------------------------------------

        loan_amount = float(
            borrower_records[0]["loan_amount"]
        )

        # ----------------------------------------------------
        # TOTAL COLLATERAL
        # ----------------------------------------------------

        total_collateral = sum(

            float(
                record["collateral_value"]
            )

            for record in borrower_records

        )

        # ----------------------------------------------------
        # TOTAL COVER
        # ----------------------------------------------------

        if loan_amount > 0:

            total_cover = (
                total_collateral /
                loan_amount
            )

        else:

            total_cover = 0

        # ----------------------------------------------------
        # BORROWER REQUIRED COVER
        # ----------------------------------------------------

        required_cover = (
            get_borrower_required_cover(
                borrower_name
            )
        )

        # ----------------------------------------------------
        # BUFFER
        # ----------------------------------------------------

        buffer = (
            total_cover -
            required_cover
        )

        # ----------------------------------------------------
        # BORROWER STATUS
        # ----------------------------------------------------

        if total_cover >= required_cover:

            borrower_status = (
                "🟢 COMPLIED"
            )

        else:

            borrower_status = (
                "🔴 SHORTFALL"
            )

            critical_borrowers.append(
                borrower_name
            )

        # ====================================================
        # BORROWER SUMMARY
        # ====================================================

        message.append(
            f"\n👤 {borrower_name.upper()}"
        )

        message.append(
            f"Loan Amount: "
            f"₹{format_crore(loan_amount):.2f} Cr"
        )

        message.append(
            f"Total Collateral: "
            f"₹{format_crore(total_collateral):.2f} Cr"
        )

        message.append(
            f"Total Cover: "
            f"{total_cover:.2f}x"
        )

        message.append(
            f"Required Cover: "
            f"{required_cover:.2f}x"
        )

        message.append(
            f"Buffer: "
            f"{buffer:+.2f}x"
        )

        message.append(
            f"Status: "
            f"{borrower_status}"
        )

        # ====================================================
        # SECURITY-WISE POSITION
        # ====================================================

        message.append(
            "\nSECURITY-WISE POSITION"
        )

        for record in borrower_records:

            security = record[
                "security"
            ]

            price = float(
                record.get(
                    "price",
                    0
                )
            )

            shares = float(
                record.get(
                    "shares",
                    0
                )
            )

            collateral = float(
                record.get(
                    "collateral_value",
                    0
                )
            )

            cover = float(
                record.get(
                    "cover",
                    0
                )
            )

            security_required_cover = float(
                record.get(
                    "required_cover",
                    0
                )
            )

            security_buffer = (
                cover -
                security_required_cover
            )

            # ------------------------------------------------
            # SECURITY STATUS
            # ------------------------------------------------

            if (
                cover >=
                security_required_cover
            ):

                security_status = (
                    "🟢 COMPLIED"
                )

            else:

                security_status = (
                    "🔴 SHORTFALL"
                )

                critical_records.append(
                    record
                )

            # ------------------------------------------------
            # SECURITY MESSAGE
            # ------------------------------------------------

            message.append(
                f"\n• {security}"
            )

            message.append(
                f"  Shares: "
                f"{shares:,.0f}"
            )

            message.append(
                f"  Price: "
                f"₹{price:,.2f}"
            )

            message.append(
                f"  Collateral: "
                f"₹{format_crore(collateral):.2f} Cr"
            )

            message.append(
                f"  Cover: "
                f"{cover:.2f}x"
            )

            message.append(
                f"  Required: "
                f"{security_required_cover:.2f}x"
            )

            message.append(
                f"  Buffer: "
                f"{security_buffer:+.2f}x"
            )

            message.append(
                f"  Status: "
                f"{security_status}"
            )

        message.append(
            "\n----------------------------"
        )

    # ========================================================
    # CRITICAL SECTION
    # ========================================================

    if (
        critical_borrowers
        or
        critical_records
    ):

        message.append(
            "\n🚨 CRITICAL POSITION"
        )

        message.append(
            "============================"
        )

        # ----------------------------------------------------
        # BORROWER LEVEL CRITICAL
        # ----------------------------------------------------

        for borrower_name in critical_borrowers:

            borrower_records = borrowers[
                borrower_name
            ]

            loan_amount = float(
                borrower_records[0][
                    "loan_amount"
                ]
            )

            total_collateral = sum(

                float(
                    record[
                        "collateral_value"
                    ]
                )

                for record in borrower_records

            )

            total_cover = (
                total_collateral /
                loan_amount
                if loan_amount > 0
                else 0
            )

            required_cover = (
                get_borrower_required_cover(
                    borrower_name
                )
            )

            shortfall = (
                required_cover -
                total_cover
            )

            additional_collateral = (
                shortfall *
                loan_amount
            )

            message.append(
                f"\n🚨 {borrower_name}"
            )

            message.append(
                "Borrower Total Cover Below Requirement"
            )

            message.append(
                f"Current Cover: "
                f"{total_cover:.2f}x"
            )

            message.append(
                f"Required Cover: "
                f"{required_cover:.2f}x"
            )

            message.append(
                f"Shortfall: "
                f"{shortfall:.2f}x"
            )

            message.append(
                f"Additional Collateral Required: "
                f"₹{format_crore(additional_collateral):.2f} Cr"
            )

        # ----------------------------------------------------
        # SECURITY LEVEL CRITICAL
        # ----------------------------------------------------

        for record in critical_records:

            cover = float(
                record["cover"]
            )

            required = float(
                record["required_cover"]
            )

            shortfall = (
                required -
                cover
            )

            additional_collateral = float(
                record.get(
                    "additional_collateral_required",
                    shortfall *
                    float(record["loan_amount"])
                )
            )

            message.append(
                f"\n🚨 {record['borrower']}"
            )

            message.append(
                f"Security: "
                f"{record['security']}"
            )

            message.append(
                f"Current Cover: "
                f"{cover:.2f}x"
            )

            message.append(
                f"Required Cover: "
                f"{required:.2f}x"
            )

            message.append(
                f"Shortfall: "
                f"{shortfall:.2f}x"
            )

            message.append(
                f"Additional Collateral Required: "
                f"₹{format_crore(additional_collateral):.2f} Cr"
            )

        message.append(
            "\n🚨 ACTION REQUIRED"
        )

        message.append(
            "Please review collateral immediately."
        )

    else:

        message.append(
            "\n✅ NO CRITICAL COLLATERAL SHORTFALL"
        )

    return "\n".join(
        message
    )


# ============================================================
# 3. GENERATE INDIVIDUAL CRITICAL ALERT
# ============================================================

def generate_alert(record):

    if record is None:

        return None

    cover = float(
        record.get(
            "cover",
            0
        )
    )

    required_cover = float(
        record.get(
            "required_cover",
            0
        )
    )

    # --------------------------------------------------------
    # No critical condition
    # --------------------------------------------------------

    if cover >= required_cover:

        return None

    shortfall = (
        required_cover -
        cover
    )

    additional_collateral = float(
        record.get(
            "additional_collateral_required",
            shortfall *
            float(
                record.get(
                    "loan_amount",
                    0
                )
            )
        )
    )

    date = record.get(
        "date",
        datetime.now().strftime(
            "%d-%b-%Y"
        )
    )

    message = []

    message.append(
        "🚨 CRITICAL COLLATERAL ALERT"
    )

    message.append(
        "============================"
    )

    message.append(
        f"Date: {date}"
    )

    message.append(
        f"Borrower: "
        f"{record['borrower']}"
    )

    message.append(
        f"Security: "
        f"{record['security']}"
    )

    message.append(
        ""
    )

    message.append(
        f"Current Cover: "
        f"{cover:.2f}x"
    )

    message.append(
        f"Required Cover: "
        f"{required_cover:.2f}x"
    )

    message.append(
        f"Shortfall: "
        f"{shortfall:.2f}x"
    )

    message.append(
        f"Additional Collateral Required: "
        f"₹{format_crore(additional_collateral):.2f} Cr"
    )

    message.append(
        ""
    )

    message.append(
        "🚨 ACTION REQUIRED"
    )

    message.append(
        "Please review collateral immediately."
    )

    return "\n".join(
        message
    )


# ============================================================
# 4. SEND WHATSAPP MESSAGE
# ============================================================

def send_whatsapp_alert(message):

    url = (
        f"https://graph.facebook.com/v22.0/"
        f"{WHATSAPP_PHONE_ID}/messages"
    )

    headers = {
        "Authorization":
        f"Bearer {WHATSAPP_ACCESS_TOKEN}",

        "Content-Type":
        "application/json"
    }

    successful = 0
    failed = 0

    for receiver in WHATSAPP_RECEIVERS:

        payload = {
            "messaging_product": "whatsapp",

            "recipient_type": "individual",

            "to": receiver,

            "type": "text",

            "text": {
                "preview_url": False,
                "body": message
            }
        }

        try:

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            print()
            print("==============================")

            print(
                "WhatsApp Recipient:",
                receiver
            )

            print(
                "Status Code:",
                response.status_code
            )

            print(
                "Response:"
            )

            print(
                response.text
            )

            if response.status_code == 200:

                successful += 1

                print(
                    "✅ Message Accepted"
                )

            else:

                failed += 1

                print(
                    "❌ Message Failed"
                )

        except Exception as e:

            failed += 1

            print(
                "❌ WhatsApp Error for:",
                receiver
            )

            print(e)

    print()
    print("==============================")
    print(
        f"WhatsApp Summary: "
        f"{successful} successful, "
        f"{failed} failed"
    )
    print("==============================")

    if failed > 0:

        raise Exception(
            f"WhatsApp sending failed for "
            f"{failed} recipient(s)"
        )

    return True

# ============================================================
# 5. PREVIEW DAILY MESSAGE WITHOUT SENDING
# ============================================================

def preview_daily_summary(records):

    message = generate_daily_summary(
        records
    )

    if message:

        print()
        print(
            "=============================="
        )

        print(
            "WHATSAPP DAILY COVER PREVIEW"
        )

        print(
            "=============================="
        )

        print(
            message
        )

    else:

        print(
            "No records available."
        )


# ============================================================
# 6. PREVIEW CRITICAL ALERT WITHOUT SENDING
# ============================================================

def preview_critical_alert(record):

    message = generate_alert(
        record
    )

    if message:

        print()
        print(
            "=============================="
        )

        print(
            "WHATSAPP CRITICAL ALERT PREVIEW"
        )

        print(
            "=============================="
        )

        print(
            message
        )

    else:

        print(
            "No critical alert."
        )