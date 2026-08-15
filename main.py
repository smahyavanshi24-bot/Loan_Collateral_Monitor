# -*- coding: utf-8 -*-

from datetime import datetime
from zoneinfo import ZoneInfo
import os
import sqlite3
import pandas as pd
import sys

from config import BORROWERS

from modules.market_data import get_stock_price

from modules.input_database import (
    initialize_input_database,
    list_loans,
    list_securities,
)

from modules.live_collateral import get_today_outstanding

from modules.database import (
    initialize_database,
    save_record,
    alert_already_sent,
    save_alert,
    get_records_by_date
)

from modules.excel_report import generate_excel_report
from modules.pdf_report import generate_pdf_report

from modules.whatsapp_alert import (
    generate_daily_summary,
    generate_alert,
    send_whatsapp_alert
)

from modules.risk_alert_engine import (
    generate_risk_alerts
)


# ============================================================
# UTF-8 CONSOLE
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# REQUIRED FOLDERS
# ============================================================

os.makedirs("reports", exist_ok=True)
os.makedirs("database", exist_ok=True)
os.makedirs("logs", exist_ok=True)


# ============================================================
# CHECK DUPLICATE RECORD
# ============================================================

def record_already_exists(
    date,
    borrower,
    security
):

    database_file = "database/collateral.db"

    try:

        connection = sqlite3.connect(
            database_file
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)

            FROM collateral_history

            WHERE date = ?

            AND borrower = ?

            AND security = ?

            """,

            (
                date,
                borrower,
                security
            )
        )

        result = cursor.fetchone()

        connection.close()

        return (
            result is not None
            and result[0] > 0
        )

    except Exception as e:

        print(
            f"Database duplicate-check error: {e}"
        )

        return False


# ============================================================
# SEND DAILY WHATSAPP POSITION
# ============================================================

def send_daily_whatsapp_position(
    trading_date
):

    print()
    print("=" * 70)
    print(
        "PREPARING DAILY WHATSAPP "
        "COLLATERAL POSITION"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # GET TODAY'S DATABASE RECORDS
    # --------------------------------------------------------

    records = get_records_by_date(
        trading_date
    )

    if not records:

        print()
        print(
            "No records found in database "
            "for today's trading date."
        )

        return

    print()
    print(
        f"Today's records found : {len(records)}"
    )

    # --------------------------------------------------------
    # GENERATE MESSAGE
    # --------------------------------------------------------

    try:

        message = generate_daily_summary(
            records
        )

    except Exception as e:

        print()
        print(
            f"Daily WhatsApp message "
            f"generation failed: {e}"
        )

        return

    if not message:

        print()
        print(
            "Daily WhatsApp message is empty."
        )

        return

    # --------------------------------------------------------
    # DISPLAY MESSAGE
    # --------------------------------------------------------

    print()
    print(
        "WhatsApp Daily Collateral Position:"
    )

    print()
    print(message)

    # --------------------------------------------------------
    # SEND
    # --------------------------------------------------------

    try:

        send_whatsapp_alert(
            message
        )

        print()
        print(
            "✅ Daily WhatsApp collateral "
            "position sent successfully."
        )

    except Exception as e:

        print()
        print(
            f"❌ Daily WhatsApp sending failed: {e}"
        )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("=" * 70)
    print("LOAN COLLATERAL MONITORING SYSTEM")
    print("=" * 70)

    # --------------------------------------------------------
    # INITIALIZE DATABASE
    # --------------------------------------------------------

    initialize_database()

    # --------------------------------------------------------
    # CURRENT DATE / TIME
    # --------------------------------------------------------

    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    # --------------------------------------------------------
    # WEEKEND CHECK
    # --------------------------------------------------------

    if now.weekday() >= 5:

        print()
        print(
            "WEEKEND DETECTED"
        )

        print(
            f"Today is "
            f"{now.strftime('%A, %d-%b-%Y')}"
        )

        print(
            "Market data will NOT be fetched."
        )

        print(
            "No database record will be created."
        )

        print(
            "No Excel/PDF report will be generated."
        )

        print()

        return

    # --------------------------------------------------------
    # TRADING DATE
    # --------------------------------------------------------

    today = now.strftime(
        "%d-%b-%Y"
    )

    print()
    print(
        f"Trading Date : {today}"
    )

    print(
        f"Day          : "
        f"{now.strftime('%A')}"
    )

    print()

    # --------------------------------------------------------
    # NEW RECORDS GENERATED DURING THIS RUN
    # --------------------------------------------------------

    new_records = []

    # ========================================================
    # PROCESS BORROWERS
    # ========================================================

    initialize_input_database()
    input_loans = list_loans(
        active_only=False
    )

    for db_loan in input_loans:

        borrower_name = db_loan["borrower"]

        loan_amount = (
            get_today_outstanding(
                db_loan
            )
            * 10_000_000
        )

        print()
        print(
            f"Borrower : {borrower_name}"
        )

        print(
            f"Loan Amount : "
            f"Rs.{loan_amount:,}"
        )

        print(
            "-" * 70
        )

        total_collateral = 0

        # ====================================================
        # PROCESS SECURITIES
        # ====================================================

        securities = list_securities(
            loan_db_id=db_loan["id"],
            active_only=True,
        )

        for security in securities:

            stock_name = security[
                "listed_company_name"
            ]

            shares = int(
                security[
                    "initial_pledged_shares"
                ]
            )

            required_cover = float(
                security[
                    "collateralwise_security_cover"
                ]
            )
            # ------------------------------------------------
            # DUPLICATE CHECK
            # ------------------------------------------------

            if record_already_exists(
                today,
                borrower_name,
                stock_name
            ):

                print()
                print(
                    "RECORD ALREADY EXISTS"
                )

                print(
                    f"{today} | "
                    f"{borrower_name} | "
                    f"{stock_name}"
                )

                print(
                    "Skipping duplicate entry."
                )

                print()

                continue

            # ------------------------------------------------
            # FETCH PRICE
            # ------------------------------------------------

            print()

            print(
                f"Fetching NSE price for "
                f"{stock_name}..."
            )

            try:

                price = get_stock_price(
                    stock_name
                )

            except Exception as e:

                print()
                print(
                    "PRICE NOT AVAILABLE"
                )

                print(
                    f"{stock_name}: {e}"
                )

                print(
                    "Record will NOT be saved."
                )

                print()

                continue

            # ------------------------------------------------
            # VALIDATE PRICE
            # ------------------------------------------------

            try:

                price = float(price)

            except (
                TypeError,
                ValueError
            ):

                print()
                print(
                    f"Invalid price received "
                    f"for {stock_name}"
                )

                print(
                    "Record will NOT be saved."
                )

                print()

                continue

            # ------------------------------------------------
            # ZERO PRICE PROTECTION
            # ------------------------------------------------

            if price <= 0:

                print()
                print(
                    f"INVALID MARKET PRICE "
                    f"FOR {stock_name}"
                )

                print(
                    f"Received price : "
                    f"Rs.{price:.2f}"
                )

                print(
                    "Record will NOT be saved."
                )

                print()

                continue

            # =================================================
            # COLLATERAL
            # =================================================

            collateral_value = (
                price * shares
            )

            # =================================================
            # COVER
            # =================================================

            if loan_amount > 0:

                cover = (
                    collateral_value /
                    loan_amount
                )

            else:

                cover = 0

            # =================================================
            # SECURITY STATUS
            # =================================================

            if cover >= required_cover:

                status = (
                    "OK Complied"
                )

                shortfall_cover = 0

                additional_collateral_required = 0

            else:

                status = (
                    "NOT OK Shortfall"
                )

                shortfall_cover = round(
                    required_cover - cover,
                    2
                )

                required_collateral_value = (
                    required_cover *
                    loan_amount
                )

                additional_collateral_required = (
                    required_collateral_value -
                    collateral_value
                )

            # =================================================
            # TOTAL COLLATERAL
            # =================================================

            total_collateral += (
                collateral_value
            )

            # =================================================
            # RECORD
            # =================================================

            record = {

                "date":
                    today,

                "borrower":
                    borrower_name,

                "security":
                    stock_name,

                "price":
                    round(
                        price,
                        2
                    ),

                "shares":
                    shares,

                "loan_amount":
                    loan_amount,

                "collateral_value":
                    collateral_value,

                "cover":
                    round(
                        cover,
                        2
                    ),

                "required_cover":
                    required_cover,

                "status":
                    status,

                "shortfall_cover":
                    round(
                        shortfall_cover,
                        2
                    ),

                "additional_collateral_required":
                    round(
                        additional_collateral_required,
                        2
                    )
            }

            # ------------------------------------------------
            # SAVE
            # ------------------------------------------------

            save_record(
                record
            )

            new_records.append(
                record
            )

            # =================================================
            # CRITICAL SHORTFALL ALERT
            # =================================================

            try:

                alert = generate_alert(
                    record
                )

            except Exception as e:

                print(
                    f"Alert generation issue: {e}"
                )

                alert = None

            if alert:

                if alert_already_sent(
                    record["date"],
                    record["borrower"],
                    record["security"]
                ):

                    print(
                        "Critical alert already "
                        "sent today."
                    )

                else:

                    print()
                    print(
                        "Sending Critical "
                        "WhatsApp Alert..."
                    )

                    print()
                    print(alert)

                    try:

                        send_whatsapp_alert(
                            alert
                        )

                        save_alert(
                            record["date"],
                            record["borrower"],
                            record["security"]
                        )

                        print(
                            "Critical alert sent."
                        )

                    except Exception as e:

                        print(
                            f"WhatsApp error: {e}"
                        )

            # =================================================
            # DISPLAY
            # =================================================

            print()
            print(
                stock_name
            )

            print(
                f"Price : "
                f"Rs.{price:.2f}"
            )

            print(
                f"Collateral : "
                f"Rs.{collateral_value:,.2f}"
            )

            print(
                f"Cover : "
                f"{cover:.2f}x"
            )

            print(
                f"Required Cover : "
                f"{required_cover:.2f}x"
            )

            print(
                f"Status : "
                f"{status}"
            )

            print()

        # ====================================================
        # TOTAL BORROWER COVER
        # ====================================================

        if loan_amount > 0:

            total_cover = (
                total_collateral /
                loan_amount
            )

        else:

            total_cover = 0

        print(
            "TOTAL COVER"
        )

        print(
            f"{total_cover:.2f}x"
        )

        total_required_cover = float(
            db_loan[
                "required_security_cover"
            ]
        )

        if total_cover >= total_required_cover:

            print(
                "Status : OK Complied"
            )

        else:

            print(
                "Status : NOT OK Shortfall"
            )

        print(
            "=" * 70
        )

    # ========================================================
    # GET TODAY'S DATABASE RECORDS
    # ========================================================

    today_records = get_records_by_date(
        today
    )

    print()
    print(
        f"Today's database records : "
        f"{len(today_records)}"
    )

    # ========================================================
    # REPORT GENERATION
    # ========================================================

    if new_records:

        df = pd.DataFrame(
            new_records
        )

        report_date = datetime.now(
            ZoneInfo("Asia/Kolkata")
            ).strftime(
            "%Y-%m-%d"
        )

        # ----------------------------------------------------
        # EXCEL
        # ----------------------------------------------------

        excel_file = (
            f"reports/"
            f"{report_date}"
            "_Collateral_Report.xlsx"
        )

        try:

            generate_excel_report(
                df,
                excel_file
            )

            print()
            print(
                "Excel Report Generated Successfully"
            )

            print(
                excel_file
            )

        except Exception as e:

            print(
                f"Excel report generation failed: {e}"
            )

        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        pdf_file = (
            f"reports/"
            f"{report_date}"
            "_Collateral_Report.pdf"
        )

        try:

            generate_pdf_report(
                df,
                pdf_file
            )

            print()
            print(
                "PDF Report Generated Successfully"
            )

            print(
                pdf_file
            )

        except Exception as e:

            print(
                f"PDF report generation failed: {e}"
            )

    else:

        print()
        print(
            "No new records generated."
        )

        print(
            "Today's existing database records "
            "will be used for WhatsApp."
        )

    # ========================================================
    # DAILY WHATSAPP POSITION
    # ========================================================

    send_daily_whatsapp_position(
        today
    )

    # ========================================================
    # COMPLETION
    # ========================================================

    print()
    print(
        "Database Updated Successfully"
    )

    print(
        f"New records saved : "
        f"{len(new_records)}"
    )

    print()
    print(
        "=" * 70
    )

    print(
        "MONITORING RUN COMPLETED"
    )

    print(
        "=" * 70
    )


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    main()