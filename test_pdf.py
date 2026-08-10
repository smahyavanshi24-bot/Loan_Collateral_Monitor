from modules.dashboard_data import get_collateral_history

from modules.pdf_report import generate_pdf_report


df = get_collateral_history()


file = generate_pdf_report(
    df,
    "reports/test_report.pdf"
)


print(
    "Created:",
    file
)