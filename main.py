from datetime import datetime
import os
import pandas as pd


from config import BORROWERS


from modules.market_data import get_stock_price


from modules.database import (
    initialize_database,
    save_record,
    alert_already_sent,
    save_alert
)


from modules.excel_report import (
    generate_excel_report
)


from modules.pdf_report import (
    generate_pdf_report
)


from modules.whatsapp_alert import (
    generate_alert,
    send_whatsapp_alert
)



# -------------------------------------------------
# Create Required Folders
# -------------------------------------------------

os.makedirs(
    "reports",
    exist_ok=True
)


os.makedirs(
    "database",
    exist_ok=True
)



# -------------------------------------------------
# Main Program
# -------------------------------------------------

def main():


    print("=" * 70)
    print("LOAN COLLATERAL MONITORING SYSTEM")
    print("=" * 70)



    initialize_database()



    all_records = []



    for borrower in BORROWERS:


        borrower_name = borrower["name"]

        loan_amount = borrower["loan_amount"]



        print("\n")
        print(
            f"Borrower : {borrower_name}"
        )

        print(
            f"Loan Amount : ₹{loan_amount:,}"
        )

        print("-" * 70)



        total_collateral = 0



        for security in borrower["securities"]:


            stock_name = security["name"]

            shares = security["shares"]

            required_cover = security["required_cover"]



            price = get_stock_price(
                stock_name
            )



            collateral_value = (
                price *
                shares
            )



            cover = (
                collateral_value /
                loan_amount
            )



            if cover >= required_cover:

                status = "✅ Complied"
                shortfall_cover = 0
                additional_collateral_required = 0

            else:

                status = "❌ Shortfall"

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
                
            total_collateral += collateral_value



            record = {

                "date":
                datetime.now().strftime(
                    "%d-%b-%Y"
                ),

                "borrower":
                borrower_name,

                "security":
                stock_name,

                "price":
                price,

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
                "shortfall_cover",

                "additional_collateral_required":
                round(
                    additional_collateral_required,
                    2

                )

            }



            all_records.append(
                record
            )


            save_record(
                record
            )



            # ---------------------------------
            # WhatsApp Alert Integration
            # ---------------------------------

            alert = generate_alert(
                record
            )



            if alert:


                if alert_already_sent(
                    record["date"],
                    record["borrower"],
                    record["security"]
                ):


                    print(
                        "\n⚠ WhatsApp alert already sent today."
                    )

                    print(
                        f"{record['borrower']} - {record['security']}"
                    )


                else:


                    print(
                        "\nSending WhatsApp Alert..."
                    )


                    print(
                        alert
                    )


                    send_whatsapp_alert(
                        alert
                    )


                    save_alert(
                        record["date"],
                        record["borrower"],
                        record["security"]
                    )



            print(
                stock_name
            )


            print(
                f"Price : ₹{price}"
            )


            print(
                f"Collateral : ₹{collateral_value:,.2f}"
            )


            print(
                f"Cover : {cover:.2f}x"
            )


            print(
                f"Status : {status}"
            )


            print()
                        # End of Security Loop



        # ---------------------------------
        # Total Cover Calculation
        # ---------------------------------

        total_cover = (
            total_collateral /
            loan_amount
        )


        print(
            "TOTAL COVER"
        )


        print(
            f"{total_cover:.2f}x"
        )



        if total_cover >= borrower.get(
            "total_required_cover",
            2
        ):


            print(
                "Status : ✅ Complied"
            )


        else:


            print(
                "Status : ❌ Shortfall"
            )



        print(
            "=" * 70
        )



    # ---------------------------------
    # Convert Records To DataFrame
    # ---------------------------------

    df = pd.DataFrame(
        all_records
    )



    today = datetime.now().strftime(
        "%Y-%m-%d"
    )



    # ---------------------------------
    # Excel Report
    # ---------------------------------

    excel_file = (
        f"reports/{today}_Collateral_Report.xlsx"
    )


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



    # ---------------------------------
    # PDF Report
    # ---------------------------------

    pdf_file = (
        f"reports/{today}_Collateral_Report.pdf"
    )


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



    print()

    print(
        "Database Updated Successfully"
    )



# -------------------------------------------------
# Start Program
# -------------------------------------------------

if __name__ == "__main__":

    main()