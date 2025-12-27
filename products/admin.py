from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import FieldDoesNotExist

import csv, io, re
from decimal import Decimal, InvalidOperation

from .models import Category, Product


# -------------------- helpers --------------------

def _has_field(model, field: str) -> bool:
    try:
        model._meta.get_field(field)
        return True
    except FieldDoesNotExist:
        return False

def _to_int(v) -> int:
    s = ("" if v is None else str(v)).strip()
    if s in {"", "-", "—", "–"}:
        return 0
    return int(s)

def _to_decimal(v) -> Decimal:
    s = ("" if v is None else str(v)).strip()
    if not s:
        return Decimal("0.00")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        raise ValueError(f"price must be a number, got {v!r}")

# Matches lines like: "  1 PRODUCT NAME    15    9.00"
LEDGER_LINE = re.compile(
    r"^\s*(?P<sn>\d+)\s+(?P<name>.+?)\s+(?P<qty>-|—|–|\d+)\s+(?P<price>\d+(?:\.\d+)?)\s*$"
)

def parse_ledger_text(text: str):
    """Parse your sectioned ledger (category headers, numbered rows, TOTAL lines)."""
    items = []
    current_category = None
    for raw in text.splitlines():
        line = (raw or "").strip()
        if not line:
            continue
        if line.upper().startswith("TOTAL"):
            continue
        m = LEDGER_LINE.match(line)
        if m:
            if not current_category:
                current_category = "Uncategorized"
            items.append({
                "category": current_category,
                "name": m.group("name").strip(),
                "stock": _to_int(m.group("qty")),
                "price": _to_decimal(m.group("price")),
            })
            continue
        # Non-matching line becomes the category header
        current_category = line
    return items

def parse_header_csv(file_obj) -> list[dict]:
    """Parse a normal CSV; accepts with/without 'code' column."""
    decoded = io.TextIOWrapper(file_obj, encoding="utf-8-sig", newline="")
    reader = csv.DictReader(decoded)
    if reader.fieldnames is None:
        raise ValueError("CSV appears to have no header.")
    header = {h.strip().lower() for h in reader.fieldnames if h}
    required = {"name", "category", "price", "stock"}
    missing = required - header
    if missing:
        raise ValueError(f"Missing columns: {sorted(list(missing))}")
    has_code = "code" in header

    rows = []
    for row in reader:
        rows.append({
            "code": ((row.get("code") or "").strip() if has_code else None),
            "name": (row.get("name") or "").strip(),
            "category": (row.get("category") or "").strip(),
            "price": _to_decimal(row.get("price")),
            "stock": _to_int(row.get("stock")),
        })
    return rows

def _unique_code_from_name(name: str, category_name: str) -> str:
    """Create a unique SKU-like code if Product has a `code` field."""
    base = slugify(f"{category_name}-{name}")[:48] or "item"
    code = base
    i = 2
    if not _has_field(Product, "code"):
        return ""  # caller should ignore if code field doesn't exist
    while Product.objects.filter(code=code).exists():
        code = f"{base}-{i}"
        i += 1
        if len(code) > 64:
            code = code[:64]
    return code


# -------------------- admin registrations --------------------

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # ---- your existing config (kept) ----
    list_display = ('name', 'category', 'price', 'stock', 'thumb')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')
    readonly_fields = ('preview',)
    fields = ('name', 'category', 'price', 'stock', 'image', 'preview')

    def thumb(self, obj):
        if getattr(obj, "image", None):
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', obj.image.url)
        return '-'
    thumb.short_description = 'Image'

    def preview(self, obj):
        if getattr(obj, "pk", None) and getattr(obj, "image", None):
            return format_html(
                '<img src="{}" style="max-height:220px;border:1px solid #e5e7eb;padding:6px;border-radius:8px;" />',
                obj.image.url
            )
        return 'Upload an image and save to see a preview.'
    preview.short_description = 'Preview'

    # ---- additions: custom buttons/views ----
    change_list_template = "admin/products/product/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("upload-excel/", self.admin_site.admin_view(self.upload_excel),
                 name="products_product_upload_excel"),
            path("export-excel/", self.admin_site.admin_view(self.export_excel),
                 name="products_product_export_excel"),
        ]
        return custom + urls

    def upload_excel(self, request):
        """
        Admin-only. Accepts Excel file with specific format.
        Uses products.utils.process_stock_excel.
        """
        if request.method == "POST":
            f = request.FILES.get("file")
            if not f:
                messages.error(request, "Please choose a file.")
                return redirect("admin:products_product_upload_excel")

            from .utils import process_stock_excel
            try:
                results = process_stock_excel(f)
                
                # Check for errors
                if results.get('errors'):
                    for err in results['errors'][:10]: # show first 10
                         messages.warning(request, err)
                    if len(results['errors']) > 10:
                        messages.warning(request, f"... and {len(results['errors']) - 10} more errors.")

                messages.success(request, 
                    f"Upload Complete. "
                    f"Categories: {results.get('categories_created')} created, {results.get('categories_updated')} updated. "
                    f"Products: {results.get('products_created')} created, {results.get('products_updated')} updated."
                )

            except Exception as e:
                messages.error(request, f"Parse error: {e}")
                return redirect("admin:products_product_upload_excel")

            return redirect("admin:products_product_changelist")

        # GET → simple form
        context = {
            "title": "Upload products Excel",
            "opts": self.model._meta,
            "app_label": self.model._meta.app_label,
            # We can reuse the csv template but renaming it or editing it would be cleaner. 
            # For now re-use or assume a generic upload template exists. 
            # Let's check templates later, or just use the same one if user hasn't provided details.
            # Ideally we should probably create 'admin/products/product/upload_excel.html'.
        }
        return render(request, "admin/products/product/upload_excel.html", context)

    def export_excel(self, request):
        """Download current inventory snapshot as Excel."""
        from openpyxl import Workbook
        from django.http import FileResponse
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Stock"

        qs = Product.objects.select_related("category").order_by("category__name", "name")
        now = timezone.now().strftime("%Y-%m-%d_%H%M%S")

        # Define columns (mirroring generic structure roughly, or just useful export)
        ws.append(["Category", "Product Name", "Stock", "Rate"])
        
        for p in qs:
            ws.append([
                p.category.name if p.category_id else "",
                p.name,
                p.stock,
                p.price
            ])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        
        return FileResponse(
            buf,
            as_attachment=True,
            filename=f"inventory_{now}.xlsx",
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
