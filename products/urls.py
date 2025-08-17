# products/urls.py
from django.urls import path
from .views import (
    ProductListView,
    StockExcelUploadView,
    StockExcelDownloadView,
    ProductBulkUpdateView,
    DailySalesReportView,
)

urlpatterns = [
    path("products/", ProductListView.as_view(), name="products-list"),
    path("products/stock/upload/", StockExcelUploadView.as_view(), name="products-stock-upload"),
    path("products/stock/download/", StockExcelDownloadView.as_view(), name="products-stock-download"),
    path("products/bulk_update/", ProductBulkUpdateView.as_view(), name="products-bulk-update"),
    path("reports/daily-sales/", DailySalesReportView.as_view(), name="reports-daily-sales"),
]


#updated today