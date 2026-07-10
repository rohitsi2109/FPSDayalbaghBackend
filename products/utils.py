import openpyxl
import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import Category, Product, StockMovement

# Cell values that explicitly mean "no stock / blank", as opposed to a value we
# simply failed to parse. Blanks are treated as 0; unparseable garbage is
# reported and the row's stock is left UNTOUCHED (never silently zeroed).
_BLANK_MARKERS = {"", "-", "—", "–", "n/a", "na"}


def normalize_name(name):
    if not name:
        return ""
    return re.sub(r'[^a-z0-9]', '', str(name).lower())


def _parse_stock(raw):
    """
    Returns (value, error). `value` is an int when parseable, or None when the
    cell should be skipped. `error` is a message string when the cell held a
    non-blank value we could not parse (so the caller can report and skip
    instead of writing 0).
    """
    if raw is None:
        return 0, None
    s = str(raw).strip()
    if s.lower() in _BLANK_MARKERS:
        return 0, None
    try:
        return int(float(s.replace(",", ""))), None
    except (ValueError, TypeError):
        return None, f"unreadable stock value {raw!r}"


def _parse_price(raw):
    """
    Returns (value, error). `value` is a Decimal when parseable, or None when
    the cell is blank/unparseable. A None value means "leave the existing price
    unchanged" for updates — we never overwrite a real price with 0.00 because a
    cell failed to parse.
    """
    if raw is None:
        return None, None
    s = str(raw).strip().replace(",", "")
    if s.lower() in _BLANK_MARKERS:
        return None, None
    try:
        return Decimal(s), None
    except (InvalidOperation, ValueError, TypeError):
        return None, f"unreadable price value {raw!r}"


def process_stock_excel(file_path, user=None):
    """
    Parse the stock-take Excel file and reconcile it into the database using
    bulk operations (kept fast for serverless timeouts).

    Safety guarantees (vs. the previous implementation):
      * A cell we cannot parse is reported in `errors` and SKIPPED — it never
        silently overwrites stock with 0 or price with 0.00.
      * Products are matched by (category, normalized name). When a name is
        ambiguous (duplicate products), the row is reported and skipped rather
        than updating an arbitrary product.
      * Stock changes are written through the StockMovement audit ledger.
      * The whole reconcile runs in a single transaction.
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active

    rows = list(sheet.iter_rows(min_row=8, values_only=True))

    category_names = set()
    parsed_rows = []
    current_cat_name = None

    # ---- Pass 1: structure rows into categories + products ----
    for r_idx, row in enumerate(rows, start=8):
        if not row or len(row) < 3:
            continue

        desc = str(row[0]).strip() if row[0] else ""
        if not desc or "MARG ERP" in desc or "TOTAL" in desc.upper():
            continue

        stock_val = row[1]
        rate_val = row[2]

        if re.match(r'^\d+', desc):
            # Product row (starts with a serial number).
            if current_cat_name:
                parsed_rows.append({
                    'cat_name': current_cat_name,
                    'desc': desc,
                    'stock': stock_val,
                    'rate': rate_val,
                    'row_idx': r_idx,
                })
        elif stock_val is None and rate_val is None:
            # Category header row.
            current_cat_name = desc
            category_names.add(desc)

    errors = []

    with transaction.atomic():
        # ---- Categories ----
        existing_cats = {c.name: c for c in Category.objects.filter(name__in=category_names)}
        new_cats = [Category(name=name) for name in category_names if name not in existing_cats]
        if new_cats:
            Category.objects.bulk_create(new_cats)
            existing_cats = {c.name: c for c in Category.objects.filter(name__in=category_names)}

        counts = {
            'categories_created': len(new_cats),
            'categories_matched': len(category_names) - len(new_cats),
            'products_created': 0,
            'products_updated': 0,
            'rows_skipped': 0,
            'errors': errors,
        }

        # ---- Index existing products by normalized name (category-aware) ----
        norm_index = defaultdict(list)
        for p in Product.objects.all():
            norm_index[normalize_name(p.name)].append(p)

        products_to_update = []
        movements = []
        new_products = []          # (product_instance, stock) awaiting pk after bulk_create

        for item in parsed_rows:
            cat_obj = existing_cats.get(item['cat_name'])
            if not cat_obj:
                continue

            clean_name = re.sub(r'^\d+\s*[\.\-]?\s*', '', item['desc']).strip()
            norm_key = normalize_name(clean_name)
            if not norm_key:
                continue

            stock, stock_err = _parse_stock(item['stock'])
            price, price_err = _parse_price(item['rate'])
            if stock_err:
                errors.append(f"Row {item['row_idx']} ({clean_name}): {stock_err}; stock left unchanged.")
                counts['rows_skipped'] += 1
                continue
            if price_err:
                # Non-fatal: keep existing price, still apply the stock count.
                errors.append(f"Row {item['row_idx']} ({clean_name}): {price_err}; price left unchanged.")

            # Match existing product, preferring the same category.
            candidates = norm_index.get(norm_key, [])
            existing_prod = None
            if len(candidates) == 1:
                existing_prod = candidates[0]
            elif len(candidates) > 1:
                same_cat = [c for c in candidates if c.category_id == cat_obj.id]
                if len(same_cat) == 1:
                    existing_prod = same_cat[0]
                else:
                    errors.append(
                        f"Row {item['row_idx']} ({clean_name}): ambiguous match "
                        f"({len(candidates)} existing products); skipped."
                    )
                    counts['rows_skipped'] += 1
                    continue

            if existing_prod:
                if existing_prod.pk:
                    delta = stock - existing_prod.stock
                    if delta != 0:
                        existing_prod.stock = stock
                        movements.append(StockMovement(
                            product=existing_prod, delta=delta, balance_after=stock,
                            reason=StockMovement.Reason.STOCKTAKE, reference="stock-upload",
                            created_by=user if getattr(user, "is_authenticated", False) else None,
                        ))
                    if price is not None:
                        existing_prod.price = price
                    if existing_prod not in products_to_update:
                        products_to_update.append(existing_prod)
                else:
                    # Already queued for creation earlier in this same file.
                    existing_prod.stock = stock
                    if price is not None:
                        existing_prod.price = price
            else:
                new_p = Product(
                    name=clean_name,
                    category=cat_obj,
                    stock=stock,
                    price=price if price is not None else Decimal('0.00'),
                )
                if price is None:
                    errors.append(
                        f"Row {item['row_idx']} ({clean_name}): new product has no valid "
                        f"price; created with 0.00."
                    )
                new_products.append(new_p)
                norm_index[norm_key].append(new_p)  # dedupe repeats within the file

        # ---- Commit ----
        if new_products:
            Product.objects.bulk_create(new_products)
            counts['products_created'] = len(new_products)
            for p in new_products:
                if p.stock:
                    movements.append(StockMovement(
                        product=p, delta=p.stock, balance_after=p.stock,
                        reason=StockMovement.Reason.STOCKTAKE, reference="stock-upload",
                        created_by=user if getattr(user, "is_authenticated", False) else None,
                    ))

        if products_to_update:
            Product.objects.bulk_update(products_to_update, ['stock', 'price'])
            counts['products_updated'] = len(products_to_update)

        if movements:
            StockMovement.objects.bulk_create(movements)

    return counts
