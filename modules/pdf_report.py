# =====================================================
# LOAN COLLATERAL MONITORING SYSTEM
# PDF REPORT MODULE
# =====================================================

import os
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib.styles import getSampleStyleSheet



# =====================================================
# Generate PDF Report
# =====================================================

def generate_pdf_report(df, filename):


    os.makedirs(
        "reports",
        exist_ok=True
    )


    # ---------------------------------------------
    # Clean Data
    # ---------------------------------------------

    df = df.copy()


    # Remove accidental header rows

    df = df[
        df["borrower"]
        .astype(str)
        .str.lower()
        !=
        "borrower"
    ]



    # Convert numeric fields

    numeric_columns = [

        "price",
        "cover",
        "required_cover",
        "shortfall_cover",
        "additional_collateral_required",
        "loan_amount",
        "collateral_value"

    ]


    for col in numeric_columns:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )



    df = df[
        df["borrower"]
        .notna()
    ]



    # ---------------------------------------------
    # PDF Setup
    # ---------------------------------------------

    pdf = SimpleDocTemplate(
        filename,
        pagesize=A4
    )


    styles = getSampleStyleSheet()


    elements = []



    # ---------------------------------------------
    # Title
    # ---------------------------------------------

    elements.append(

        Paragraph(
            "Loan Collateral Risk Monitoring Report",
            styles["Title"]
        )

    )


    elements.append(
        Spacer(1,20)
    )



    # ---------------------------------------------
    # Portfolio Summary
    # ---------------------------------------------

    total_loan = (

        df["loan_amount"]
        .drop_duplicates()
        .sum()

    )


    total_collateral = (

        df["collateral_value"]
        .sum()

    )


    portfolio_cover = (

        total_collateral /
        total_loan

    )



    summary_data = [

        [
            "Total Loan",
            f"₹{total_loan/10000000:.2f} Cr"
        ],

        [
            "Total Collateral",
            f"₹{total_collateral/10000000:.2f} Cr"
        ],

        [
            "Portfolio Cover",
            f"{portfolio_cover:.2f}x"
        ]

    ]



    summary_table = Table(
        summary_data
    )


    summary_table.setStyle(

        TableStyle(

            [

                (
                    "GRID",
                    (0,0),
                    (-1,-1),
                    0.5,
                    colors.black
                )

            ]

        )

    )


    elements.append(
        summary_table
    )


    elements.append(
        Spacer(1,20)
    )



    # ---------------------------------------------
    # Security Details
    # ---------------------------------------------

    elements.append(

        Paragraph(
            "Security Details",
            styles["Heading2"]
        )

    )



    security_data = [

        [

            "Borrower",
            "Security",
            "Price",
            "Cover",
            "Required",
            "Status",
            "Shortfall",
            "Additional Collateral"

        ]

    ]



    for _, row in df.iterrows():


        shortfall = row.get(
            "shortfall_cover",
            0
        )


        additional = row.get(
            "additional_collateral_required",
            0
        )


        if pd.isna(shortfall):

            shortfall = 0


        if pd.isna(additional):

            additional = 0



        security_data.append(

            [

                row["borrower"],

                row["security"],

                f"₹{row['price']:,.2f}",

                f"{row['cover']:.2f}x",

                f"{row['required_cover']:.2f}x",

                row["status"],

                f"{shortfall:.2f}x",

                f"₹{additional/10000000:.2f} Cr"

            ]

        )



    security_table = Table(
        security_data,
        repeatRows=1
    )


    security_table.setStyle(

        TableStyle(

            [

                (
                    "GRID",
                    (0,0),
                    (-1,-1),
                    0.5,
                    colors.black
                ),

                (
                    "BACKGROUND",
                    (0,0),
                    (-1,0),
                    colors.lightgrey
                )

            ]

        )

    )


    elements.append(
        security_table
    )


    elements.append(
        Spacer(1,20)
    )



    # ---------------------------------------------
    # Alerts
    # ---------------------------------------------

    elements.append(

        Paragraph(
            "Risk Alerts",
            styles["Heading2"]
        )

    )


    alerts = df[

        df["status"]
        .astype(str)
        .str.contains(
            "Shortfall"
        )

    ]



    if len(alerts) > 0:


        for _, row in alerts.iterrows():


            elements.append(

                Paragraph(

                    f"""
                    ALERT:
                    {row['borrower']}
                    -
                    {row['security']}

                    Current Cover:
                    {row['cover']:.2f}x

                    Required:
                    {row['required_cover']:.2f}x

                    Shortfall:
                    {row.get('shortfall_cover',0):.2f}x
                    """,

                    styles["Normal"]

                )

            )


            elements.append(
                Spacer(1,10)
            )


    else:


        elements.append(

            Paragraph(

                "No collateral shortfall detected.",

                styles["Normal"]

            )

        )



    # ---------------------------------------------
    # Create PDF
    # ---------------------------------------------

    pdf.build(
        elements
    )


    print(
        "PDF Report Created Successfully:",
        filename
    )