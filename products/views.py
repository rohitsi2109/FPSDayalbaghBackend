# from rest_framework.generics import ListAPIView
# from rest_framework.filters import SearchFilter, OrderingFilter
# from .models import Product
# from .serializers import ProductSerializer
#
# class ProductListView(ListAPIView):
#     serializer_class = ProductSerializer
#     queryset = Product.objects.select_related('category').all()
#     filter_backends = [SearchFilter, OrderingFilter]
#     search_fields = ['name', 'category__name']
#     ordering_fields = ['price', 'name', 'stock']
#     ordering = ['name']
#
#     def get_queryset(self):
#         qs = super().get_queryset()
#         category = self.request.query_params.get('category')
#         if category:
#             qs = qs.filter(category__name__iexact=category)
#         return qs
#
#
#
# products/views.py
from io import BytesIO
from datetime import datetime, date, timedelta
from django.utils.timezone import make_aware, get_current_timezone
from django.db import transaction
from django.db.models import Sum, F
from django.http import HttpResponse, FileResponse
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from openpyxl import Workbook, load_workbook

from .models import Product
from .serializers import (
    ProductSerializer,
    ProductBulkUpdateSerializer,
)

# ---------- Existing products list ----------
class ProductListView(ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related('category').all()
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'category__name']
    ordering_fields = ['price', 'name', 'stock']
    ordering = ['name']

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__name__iexact=category)
        return qs


# ---------- 1) Upload Excel -> Update stock/price ----------
class StockExcelUploadView(APIView):
    """
    POST multipart/form-data:
      - file: .xlsx with columns (any order):
          id | name | category | stock | price
      - dry_run: "1" to simulate without saving
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        f = request.FILES.get("file")
        dry_run = str(request.data.get("dry_run", "0")).lower() in {"1", "true", "yes"}
        if not f:
            return Response({"detail": "Upload 'file' (xlsx)."}, status=400)

        try:
            wb = load_workbook(filename=f, data_only=True)
            ws = wb.active
        except Exception as e:
            return Response({"detail": f"Invalid excel: {e}"}, status=400)

        # Read headers
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return Response({"detail": "Empty excel."}, status=400)
        headers = [str(h).strip().lower() if h is not None else "" for h in rows[0]]
        idx = {h: i for i, h in enumerate(headers)}

        def col(name):
            return idx.get(name)

        need_one_key = col("id") is not None or col("name") is not None
        if not need_one_key:
            return Response({"detail": "Must include 'id' or 'name' column."}, status=400)

        updated, created, skipped, errors = 0, 0, 0, []
        # Process data rows
        with transaction.atomic():
            for r in rows[1:]:
                if not r or all(v in (None, "", 0) for v in r):
                    continue

                pid = r[col("id")] if col("id") is not None else None
                pname = r[col("name")] if col("name") is not None else None
                stock = r[col("stock")] if col("stock") is not None else None
                price = r[col("price")] if col("price") is not None else None

                try:
                    obj = None
                    if pid not in (None, ""):
                        try:
                            obj = Product.objects.select_for_update().get(id=int(pid))
                        except Exception:
                            errors.append(f"Row {r}: Product id={pid} not found")
                            continue
                    elif pname:
                        try:
                            obj = Product.objects.select_for_update().get(name__iexact=str(pname).strip())
                        except Exception:
                            errors.append(f"Row {r}: Product name='{pname}' not found")
                            continue

                    changed = False
                    if stock not in (None, ""):
                        s = int(stock)
                        if obj.stock != s:
                            obj.stock = s
                            changed = True
                    if price not in (None, ""):
                        # supports numeric or string
                        p = float(price)
                        if float(obj.price) != p:
                            obj.price = p
                            changed = True

                    if changed:
                        if not dry_run:
                            obj.save(update_fields=["stock", "price"])
                        updated += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errors.append(f"Row {r}: {e}")

            if dry_run:
                transaction.set_rollback(True)

        return Response({
            "ok": True,
            "dry_run": dry_run,
            "updated": updated,
            "created": created,   # (not creating new products in this flow)
            "skipped": skipped,
            "errors": errors[:100],  # cap
        })


# ---------- 2) Download Excel of current stock ----------
class StockExcelDownloadView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        wb = Workbook()
        ws = wb.active
        ws.title = "Stock"
        ws.append(["ID", "Name", "Category", "Price", "Stock"])
        qs = Product.objects.select_related("category").order_by("name")
        for p in qs:
            ws.append([
                p.id,
                p.name,
                p.category.name if p.category_id else "",
                str(p.price),   # keep as string to avoid locale issues
                p.stock,
            ])

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        filename = f'stock_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        # FileResponse streams efficiently
        resp = FileResponse(
            buf,
            as_attachment=True,
            filename=filename,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        return resp


# ---------- 3) Bulk edit stock/price ----------
class ProductBulkUpdateView(APIView):
    """
    PATCH body:
    {
      "items": [
        {"id": 1, "stock": 10},
        {"id": 2, "price": 99.90},
        {"id": 3, "stock": 8, "price": 15.50}
      ]
    }
    """
    permission_classes = [IsAdminUser]

    def patch(self, request):
        ser = ProductBulkUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        items = ser.validated_data["items"]

        updated, errors = 0, []
        with transaction.atomic():
            for it in items:
                pid = it["id"]
                try:
                    obj = Product.objects.select_for_update().get(pk=pid)
                    fields = []
                    if "stock" in it:
                        obj.stock = int(it["stock"])
                        fields.append("stock")
                    if "price" in it:
                        obj.price = it["price"]
                        fields.append("price")
                    if fields:
                        obj.save(update_fields=fields)
                        updated += 1
                except Product.DoesNotExist:
                    errors.append(f"Product {pid} not found")
                except Exception as e:
                    errors.append(f"Product {pid}: {e}")

        return Response({"ok": True, "updated": updated, "errors": errors})


# ---------- 4) Daily sales report (JSON or ?format=xlsx) ----------
# Uses Order / OrderItem from your orders app.
from orders.models import Order, OrderItem, OrderStatus, OrderSource

class DailySalesReportView(APIView):
    """
    GET params:
      - date=YYYY-MM-DD (default: today)
      - format=xlsx -> download Excel, else JSON
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        tz = get_current_timezone()
        date_str = request.query_params.get("date")
        if date_str:
            y, m, d = map(int, date_str.split("-"))
            day = date(y, m, d)
        else:
            day = date.today()

        start = make_aware(datetime.combine(day, datetime.min.time()), tz)
        end = start + timedelta(days=1)

        paid_like = [OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.COMPLETED]

        orders = (
            Order.objects
            .filter(created_at__gte=start, created_at__lt=end, status__in=paid_like)
            .select_related("user")
        )

        # Totals
        orders_count = orders.count()
        revenue_total = orders.aggregate(s=Sum("total_amount"))["s"] or 0

        # Split by source
        src = (
            orders.values("source")
            .annotate(orders=Sum(1), revenue=Sum("total_amount"))
            .order_by()
        )
        by_source = {row["source"]: {"orders": row["orders"], "revenue": float(row["revenue"] or 0)} for row in src}

        # Items aggregation
        items = (
            OrderItem.objects
            .filter(order__in=orders)
            .select_related("product__category")
            .values("product_id", "product__name", "product__category__name")
            .annotate(qty=Sum("quantity"), amount=Sum("line_total"))
            .order_by("-qty")
        )
        by_product = [
            {
                "product_id": r["product_id"],
                "name": r["product__name"],
                "category": r["product__category__name"],
                "quantity": int(r["qty"] or 0),
                "amount": float(r["amount"] or 0),
            }
            for r in items
        ]
        units_sold = sum(x["quantity"] for x in by_product)

        if request.query_params.get("format") == "xlsx":
            # Build Excel
            wb = Workbook()
            ws1 = wb.active
            ws1.title = "Summary"
            ws1.append(["Date", str(day)])
            ws1.append(["Orders", orders_count])
            ws1.append(["Units sold", units_sold])
            ws1.append(["Revenue", float(revenue_total)])
            ws1.append([])
            ws1.append(["Source", "Orders", "Revenue"])
            for s in (OrderSource.ONLINE, OrderSource.POS):
                vals = by_source.get(s, {"orders": 0, "revenue": 0.0})
                ws1.append([s, vals["orders"], vals["revenue"]])

            ws2 = wb.create_sheet("By Product")
            ws2.append(["product_id", "name", "category", "quantity", "amount"])
            for r in by_product:
                ws2.append([r["product_id"], r["name"], r["category"], r["quantity"], r["amount"]])

            buf = BytesIO()
            wb.save(buf); buf.seek(0)
            resp = HttpResponse(
                buf.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            resp["Content-Disposition"] = f'attachment; filename="sales_{day.isoformat()}.xlsx"'
            return resp

        return Response({
            "date": day.isoformat(),
            "orders": orders_count,
            "units_sold": units_sold,
            "revenue": float(revenue_total),
            "by_source": by_source,
            "by_product": by_product[:500],  # cap
        })
