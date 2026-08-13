import os
from datetime import datetime
from zoneinfo import ZoneInfo

import xlsxwriter



def generate_excel_report(df, filename):


    # Create reports folder

    os.makedirs(
        "reports",
        exist_ok=True
    )

    df.to_excel(
        filename,
        index=False
    )


    workbook = xlsxwriter.Workbook(
        filename
    )



    # -------------------------------------------------
    # Formats
    # -------------------------------------------------

    title_format = workbook.add_format(
        {
            "bold": True,
            "font_size": 16
        }
    )


    header_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#D9EAD3",
            "border": 1
        }
    )


    money_format = workbook.add_format(
        {
            "num_format": "₹#,##0.00",
            "border": 1
        }
    )


    number_format = workbook.add_format(
        {
            "border": 1
        }
    )


    status_format = workbook.add_format(
        {
            "border": 1
        }
    )


    cover_format = workbook.add_format(
        {
            "num_format": "0.00x",
            "border":1
        }
    )


    date_format = workbook.add_format(
        {
            "border":1
        }
    )



    # -------------------------------------------------
    # Summary Sheet
    # -------------------------------------------------

    summary = workbook.add_worksheet(
        "Summary"
    )


    summary.write(
        "A1",
        "Loan Collateral Monitoring Report",
        title_format
    )


    summary.write(
        "A3",
        "Report Date",
        header_format
    )


    summary.write(
        "B3",
        datetime.now(
            ZoneInfo("Asia/Kolkata")
            ).strftime(
            "%d-%b-%Y"
        )
    )


    summary.write(
        "A5",
        "Total Loan Exposure",
        header_format
    )


    total_loan = (
        df["loan_amount"]
        .drop_duplicates()
        .sum()
    )


    summary.write_number(
        "B5",
        total_loan,
        money_format
    )



    summary.write(
        "A6",
        "Total Collateral Value",
        header_format
    )


    total_collateral = (
        df["collateral_value"]
        .sum()
    )


    summary.write_number(
        "B6",
        total_collateral,
        money_format
    )



    summary.write(
        "A7",
        "Overall Cover",
        header_format
    )


    summary.write(
        "B7",
        f"{total_collateral/total_loan:.2f}x"
    )


    summary.set_column(
        "A:A",
        25
    )


    summary.set_column(
        "B:B",
        20
    )



    # -------------------------------------------------
    # Detail Sheet
    # -------------------------------------------------

    sheet = workbook.add_worksheet(
        "Collateral Details"
    )


    sheet.write(
        "A1",
        "Security Monitoring Details",
        title_format
    )



    headers = [

        "Date",

        "Borrower",

        "Security",

        "Price",

        "Shares",

        "Loan Amount",

        "Collateral Value",

        "Cover",

        "Required Cover",

        "Status"

    ]



    row = 2


    col = 0



    for h in headers:

        sheet.write(
            row,
            col,
            h,
            header_format
        )

        col += 1



    row += 1



    for _, data in df.iterrows():


        sheet.write(
            row,
            0,
            data["date"],
            date_format
        )


        sheet.write(
            row,
            1,
            data["borrower"],
            number_format
        )


        sheet.write(
            row,
            2,
            data["security"],
            number_format
        )


        sheet.write_number(
            row,
            3,
            data["price"],
            money_format
        )


        sheet.write_number(
            row,
            4,
            data["shares"],
            number_format
        )


        sheet.write_number(
            row,
            5,
            data["loan_amount"],
            money_format
        )


        sheet.write_number(
            row,
            6,
            data["collateral_value"],
            money_format
        )


        sheet.write_number(
            row,
            7,
            data["cover"],
            cover_format
        )


        sheet.write_number(
            row,
            8,
            data["required_cover"],
            cover_format
        )


        sheet.write(
            row,
            9,
            data["status"],
            status_format
        )


        row += 1



    # Column width

    sheet.set_column(
        "A:A",
        15
    )

    sheet.set_column(
        "B:C",
        20
    )

    sheet.set_column(
        "D:I",
        18
    )

    sheet.set_column(
        "J:J",
        18
    )



    workbook.close()


    return filename