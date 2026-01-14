import openpyxl
import re
from decimal import Decimal
from .models import Category, Product

from django.db import transaction

def normalize_name(name):
    if not name:
        return ""
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

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
    # Use aggressive normalization for matching
    all_products = Product.objects.all()
    product_map = {
        normalize_name(p.name): p 
        for p in all_products
    }
    
    products_to_create = []
    products_to_update = []
    
    # 5. Process Products
    for item in parsed_rows:
        cat_obj = existing_cats.get(item['cat_name'])
        if not cat_obj:
            continue 
            
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

        # Check existence using aggressive normalization
        norm_key = normalize_name(clean_name)
        existing_prod = product_map.get(norm_key)
        
        if existing_prod:
            # Update instance directly (it might be in product_map or products_to_create)
            existing_prod.stock = stock
            existing_prod.price = price
            
            # If it's an existing DB product and not in update list yet
            if existing_prod.pk and existing_prod not in products_to_update:
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
            # Add to map to prevent duplicates within the same file
            product_map[norm_key] = new_p

    # 6. Bulk Commit Products
    with transaction.atomic():
        if products_to_create:
            Product.objects.bulk_create(products_to_create)
            processed_counts['products_created'] = len(products_to_create)
            
        if products_to_update:
            to_update_db = [p for p in products_to_update if p.pk]
            if to_update_db:
                Product.objects.bulk_update(to_update_db, ['stock', 'price'])
                processed_counts['products_updated'] = len(to_update_db)

    return processed_counts
