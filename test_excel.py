import xlsxwriter


file_path = "reports/test_excel.xlsx"


workbook = xlsxwriter.Workbook(file_path)

worksheet = workbook.add_worksheet("Test")


worksheet.write("A1", "Loan Collateral Monitoring System")

worksheet.write("A2", "Excel generation successful")


workbook.close()


print("Created:", file_path)