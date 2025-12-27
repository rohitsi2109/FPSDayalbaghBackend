import openpyxl
import sys

try:
    file_path = "REPORT.xlsx"
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active
    
    with open("excel_content.txt", "w", encoding="utf-8") as f:
        f.write(f"Sheet Name: {sheet.title}\n")
        
        # Print all rows
        for i, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            f.write(f"Row {i}: {row}\n")
            
except Exception as e:
    with open("excel_content.txt", "w", encoding="utf-8") as f:
        f.write(f"Error reading file: {e}")
