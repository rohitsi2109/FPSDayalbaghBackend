import openpyxl
import re
from decimal import Decimal
from .models import Category, Product

def process_stock_excel(file_path):
    """
    Parses the stock excel file and updates the database.
    Expects specific format:
    - Header rows (skip first 7)
    - Categories: Rows with name in col 1, empty stock/rate
    - Products: Rows starting with number in col 1, with stock and rate
    - Stock ' - ' means 0
    - 'TOTAL' rows are summaries
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active
    
    current_category = None
    processed_counts = {
        'categories_created': 0,
        'categories_updated': 0, # We just get/create, so mostly "touched"
        'products_created': 0,
        'products_updated': 0,
        'errors': []
    }

    # Start from row 8 to skip fixed headers
    # Row 8 in 1-based index is row 8
    # iter_rows yields tuples.
    # min_row=8 ensures we skip the top header
    
    for row_idx, row in enumerate(sheet.iter_rows(min_row=8, values_only=True), start=8):
        # row is a tuple (Description, Stock, Rate, ...)
        if not row or len(row) < 3:
            continue
            
        desc = row[0]
        stock_val = row[1]
        rate_val = row[2]

        # 1. Skip Empty Description
        if not desc:
            continue

        str_desc = str(desc).strip()
        
        # 2. Skip Footer / Marketing
        if "MARG ERP" in str_desc:
            continue
            
        # 3. Skip Total Rows
        # "TOTAL" might be in the description, usually indented
        if "TOTAL" in str_desc.upper():
            continue

        # 4. Determine Type: Category or Product
        # Category: Stock and Rate are None/Empty AND Description does NOT start with number usually
        # But wait, product description starts with number like "1 B.CELL".
        # Category description is like "BATTERY CELL".
        
        is_product_row = False
        # precise check for product: Description starts with a number followed by space/dot
        if re.match(r'^\d+', str_desc):
             is_product_row = True
        
        if is_product_row:
            if not current_category:
                processed_counts['errors'].append(f"Row {row_idx}: Product found before any category: {str_desc}")
                continue
                
            # Parse Product
            # Remove leading number and space/dot
            # e.g. "1 B.CELL..." -> "B.CELL..."
            product_name = re.sub(r'^\d+\s*[\.\-]?\s*', '', str_desc).strip()
            
            # Parse Stock
            stock = 0
            if stock_val is not None:
                s_str = str(stock_val).strip()
                if s_str in ['-', 'N/A', '']:
                     stock = 0
                else:
                    try:
                        stock = int(float(s_str)) # handle 8.0 -> 8
                    except ValueError:
                         stock = 0 # Default to 0 if weird
            
            # Parse Rate
            price = Decimal('0.00')
            if rate_val is not None:
                try:
                    price = Decimal(str(rate_val))
                except Exception:
                    price = Decimal('0.00')

            # Update DB
            product_obj, created = Product.objects.update_or_create(
                name=product_name,
                category=current_category,
                defaults={
                    'stock': stock,
                    'price': price
                }
            )
            
            if created:
                processed_counts['products_created'] += 1
            else:
                processed_counts['products_updated'] += 1
                
        else:
            # Assume Category if not product and not total
            # Check if stock/rate are largely empty to confirm it's a category
            # In the file: Category rows have None for stock and rate
            
            if stock_val is None and rate_val is None:
                category_name = str_desc
                cat_obj, created = Category.objects.get_or_create(name=category_name)
                current_category = cat_obj
                if created:
                    processed_counts['categories_created'] += 1
                else:
                    processed_counts['categories_updated'] += 1
            else:
                 # Ambiguous row, maybe header or noise?
                 # If it has values but didn't match product regex, it might be a product without number?
                 # In this specific file, all products seem numbered.
                 pass

    return processed_counts
