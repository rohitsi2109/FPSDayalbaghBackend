import openpyxl

def inspect_excel(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    sheet = wb.active
    print(f"Sheet: {sheet.title}")
    # Print more columns to see where data is
    for i, row in enumerate(sheet.iter_rows(min_row=1, max_row=50, values_only=True), 1):
        print(f"Row {i}: {row}")

if __name__ == "__main__":
    inspect_excel("REPORT (1).xlsx")
