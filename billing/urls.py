from django.urls import path
from .views import POSCreateInvoiceView, InvoicePayView

urlpatterns = [
    path("pos/invoices/", POSCreateInvoiceView.as_view(), name="billing-pos-create"),
    path("invoices/<int:pk>/pay/", InvoicePayView.as_view(), name="billing-invoice-pay"),
]
