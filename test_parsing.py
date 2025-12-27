import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FPSDayalbaghBackend.settings')
django.setup()

from products.utils import process_stock_excel
from products.models import Product, Category

file_path = "REPORT.xlsx"
print(f"Testing parsing of {file_path}...")

try:
    # dry run essentially, but process_stock_excel commits to DB.
    # To test safely we might want to use a transaction or just let it update (user wants to update).
    # Given the user request is "I want to update stocks", running it *is* the task.
    # However, for verification, I'll print the results.
    
    results = process_stock_excel(file_path)
    print("Parsing Complete.")
    print("Results:", results)
    
    print("\n--- Verification ---")
    print(f"Total Categories: {Category.objects.count()}")
    print(f"Total Products: {Product.objects.count()}")
    
    # Check a specific item if known
    try:
        p = Product.objects.get(name__icontains="B.CELL- AA PENCIL")
        print(f"Sample Check: {p.name} - Stock: {p.stock}, Price: {p.price}")
    except Product.DoesNotExist:
        print("Sample 'B.CELL- AA PENCIL' not found.")
        
except Exception as e:
    print(f"Error: {e}")
