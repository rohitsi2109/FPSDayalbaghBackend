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
            path("upload-csv/", self.admin_site.admin_view(self.upload_csv),
                 name="products_product_upload_csv"),
            path("export-csv/", self.admin_site.admin_view(self.export_csv),
                 name="products_product_export_csv"),
        ]
        return custom + urls

    def upload_csv(self, request):
        """
        Admin-only. Accepts your ledger format OR a normal headered CSV.
        Upserts by (category, name). Existing -> update stock & price; new -> create.
        """
        if request.method == "POST":
            f = request.FILES.get("file")
            dry_run = request.POST.get("dry_run") == "on"
            if not f:
                messages.error(request, "Please choose a file.")
                return redirect("admin:products_product_upload_csv")

            raw = f.read()
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw.decode("cp1252", errors="ignore")

            # Detect format
            first = (text.splitlines() or [""])[0].lower()
            use_header_csv = ("," in first) and ("name" in first and "category" in first)

            try:
                if use_header_csv:
                    rows = parse_header_csv(io.BytesIO(raw))
                else:
                    rows = parse_ledger_text(text)
                    rows = [{"code": None, **r} for r in rows]  # normalise shape
            except Exception as e:
                messages.error(request, f"Parse error: {e}")
                return redirect("admin:products_product_upload_csv")

            created_products = 0
            updated_products = 0
            created_categories = 0
            errors = []
            seen_cats = set()
            has_code_field = _has_field(Product, "code")

            try:
                with transaction.atomic():
                    for idx, r in enumerate(rows, start=1):
                        try:
                            cat_name = (r["category"] or "").strip()
                            if not cat_name:
                                raise ValueError("Missing category")
                            category, cat_created = Category.objects.get_or_create(name=cat_name)
                            if cat_created and cat_name.lower() not in seen_cats:
                                created_categories += 1
                                seen_cats.add(cat_name.lower())

                            name = (r["name"] or "").strip()
                            if not name:
                                raise ValueError("Missing name")

                            price = r["price"]
                            stock = r["stock"]

                            existing = Product.objects.filter(
                                category=category, name__iexact=name
                            ).first()

                            if existing:
                                changed = False
                                if existing.price != price:
                                    existing.price = price; changed = True
                                if existing.stock != stock:
                                    existing.stock = stock; changed = True
                                if changed:
                                    existing.save(update_fields=["price", "stock"])
                                    updated_products += 1
                            else:
                                data = {
                                    "name": name,
                                    "category": category,
                                    "price": price,
                                    "stock": stock,
                                }
                                if has_code_field:
                                    code = (r.get("code") or "").strip() or _unique_code_from_name(name, cat_name)
                                    data["code"] = code
                                Product.objects.create(**data)
                                created_products += 1

                        except Exception as e:
                            errors.append({"row": idx, "name": r.get("name"), "error": str(e)})

                    if dry_run:
                        # rollback intentionally
                        raise RuntimeError("__dry_run__")

            except RuntimeError as e:
                if str(e) != "__dry_run__":
                    messages.error(request, f"Error: {e}")
                    return redirect("admin:products_product_upload_csv")

            context = {
                "title": "Upload products CSV (result)",
                "created_products": created_products,
                "updated_products": updated_products,
                "created_categories": created_categories,
                "errors": errors,
                "dry_run": dry_run,
                "opts": self.model._meta,
                "app_label": self.model._meta.app_label,
            }
            return render(request, "admin/products/product/upload_csv_result.html", context)

        # GET → simple form
        context = {
            "title": "Upload products CSV",
            "opts": self.model._meta,
            "app_label": self.model._meta.app_label,
        }
        return render(request, "admin/products/product/upload_csv.html", context)

    def export_csv(self, request):
        """Download current inventory snapshot as CSV."""
        qs = Product.objects.select_related("category").order_by("category__name", "name")
        now = timezone.now().strftime("%Y-%m-%d_%H%M%S")

        has_code = _has_field(Product, "code")
        has_active = _has_field(Product, "is_active")
        has_updated = _has_field(Product, "updated_at")

        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="inventory_{now}.csv"'
        w = csv.writer(resp)

        header = []
        if has_code: header.append("code")
        header += ["name", "category", "price", "stock"]
        if has_active: header.append("is_active")
        if has_updated: header.append("updated_at")
        w.writerow(header)

        for p in qs:
            row = []
            if has_code: row.append(getattr(p, "code", ""))
            row += [
                p.name,
                (p.category.name if p.category_id else ""),
                f"{p.price:.2f}",
                p.stock,
            ]
            if has_active: row.append("1" if getattr(p, "is_active", True) else "0")
            if has_updated: row.append(getattr(p, "updated_at", "") or "")
            w.writerow(row)

        return resp
