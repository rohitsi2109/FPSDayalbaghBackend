import openpyxl
import sys

try:
    file_path = "REPORT.xlsx"
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active
    
    print(f"Sheet Name: {sheet.title}")
    
    # Print first 20 rows
    for i, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        # formatted print for readability
        print(f"Row {i}: {row}")
        if i >= 200:
            break
            
except Exception as e:
    print(f"Error reading file: {e}")
