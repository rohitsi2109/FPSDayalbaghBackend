import openpyxl
import re
from decimal import Decimal
from .models import Category, Product

from django.db import transaction

def process_stock_excel(file_path):
    """
    Parses the stock excel file and updates the database using BULK operations.
    Performance optimized for Vercel timeouts.
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active
    
    # 1. Read all rows into memory (it's small, ~700 rows)
    rows = list(sheet.iter_rows(min_row=8, values_only=True))
    
    category_names = set()
    parsed_rows = [] 
    
    # 2. First Pass: Collect Categories and structure data
    # We need to know which row belongs to which category
    # to associate products correctly.
    
    current_cat_name = None
    
    for r_idx, row in enumerate(rows, start=8):
        if not row or len(row) < 3: continue
        
        desc = str(row[0]).strip() if row[0] else ""
        if not desc or "MARG ERP" in desc or "TOTAL" in desc.upper():
            continue
            
        stock_val = row[1]
        rate_val = row[2]
        
        # Check if Product
        if re.match(r'^\d+', desc):
            if current_cat_name:
                parsed_rows.append({
                    'type': 'product',
                    'cat_name': current_cat_name,
                    'desc': desc,
                    'stock': stock_val,
                    'rate': rate_val,
                    'row_idx': r_idx
                })
        else:
            # Category?
            if stock_val is None and rate_val is None:
                current_cat_name = desc
                category_names.add(desc)
                
    # 3. Bulk Handle Categories
    existing_cats = {c.name: c for c in Category.objects.filter(name__in=category_names)}
    new_cats = [
        Category(name=name) 
        for name in category_names 
        if name not in existing_cats
    ]
    
    if new_cats:
        Category.objects.bulk_create(new_cats)
        # Re-fetch to get IDs
        existing_cats = {c.name: c for c in Category.objects.filter(name__in=category_names)}
        
    processed_counts = {
        'categories_created': len(new_cats),
        'categories_updated': len(existing_cats) - len(new_cats),
        'products_created': 0,
        'products_updated': 0,
        'errors': []
    }

    # 4. Prepare Product Maps
    # We need to map (category_id, clean_name) -> product_obj
    all_products = Product.objects.all()
    product_map = {
        (p.category_id, p.name.lower().strip()): p 
        for p in all_products
    }
    
    products_to_create = []
    products_to_update = []
    
    # 5. Process Products
    for item in parsed_rows:
        cat_obj = existing_cats.get(item['cat_name'])
        if not cat_obj:
            continue # Should not happen
            
        # Parse Name
        raw_name = item['desc']
        clean_name = re.sub(r'^\d+\s*[\.\-]?\s*', '', raw_name).strip()
        
        # Parse Stock
        stock = 0
        s_str = str(item['stock']).strip()
        if item['stock'] is not None and s_str not in ['-', 'N/A', '']:
            try:
                stock = int(float(s_str))
            except ValueError:
                stock = 0
                
        # Parse Rate
        price = Decimal('0.00')
        if item['rate'] is not None:
            try:
                price = Decimal(str(item['rate']))
            except Exception:
                price = Decimal('0.00')

        # Check existence
        key = (cat_obj.id, clean_name.lower())
        existing_prod = product_map.get(key)
        
        if existing_prod:
            # Update if changed
            if existing_prod.stock != stock or existing_prod.price != price:
                existing_prod.stock = stock
                existing_prod.price = price
                products_to_update.append(existing_prod)
        else:
            # Create new
            new_p = Product(
                name=clean_name,
                category=cat_obj,
                stock=stock,
                price=price
            )
            products_to_create.append(new_p)
            # Add to map to prevent duplicates within the same file!
            product_map[key] = new_p

    # 6. Bulk Commit Products
    with transaction.atomic():
        if products_to_create:
            Product.objects.bulk_create(products_to_create)
            processed_counts['products_created'] = len(products_to_create)
            
        if products_to_update:
            Product.objects.bulk_update(products_to_update, ['stock', 'price'])
            processed_counts['products_updated'] = len(products_to_update)

    return processed_counts
