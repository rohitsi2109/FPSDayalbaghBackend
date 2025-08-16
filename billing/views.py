# billing/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import BillingInvoice
from .serializers import POSCreateSerializer, InvoicePaySerializer


class IsShopkeeper(IsAuthenticated):
    def has_permission(self, request, view):
        ok = super().has_permission(request, view)
        if not ok:
            return False
        u = request.user
        return bool(getattr(u, "is_staff", False) or getattr(u, "is_superuser", False))


class POSCreateInvoiceView(APIView):
    permission_classes = [IsShopkeeper]

    def post(self, request):
        ser = POSCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        inv = ser.save()

        # Order is created in the serializer for POS; still guard just in case
        order_id = inv.order_id

        return Response({
            "ok": True,
            "order_id": order_id,                 # <-- use this as the bill number
            "invoice_id": inv.id,
            "status": inv.status,
            "total": str(inv.total),
            "paid_amount": str(inv.paid_amount),
            "mode": inv.mode,
            "customer_id": inv.customer_id,
            "cashier_id": inv.cashier_id,
        })


class InvoicePayView(APIView):
    permission_classes = [IsShopkeeper]

    def post(self, request, pk: int):
        try:
            inv = BillingInvoice.objects.get(pk=pk)
        except BillingInvoice.DoesNotExist:
            return Response({"detail": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        ser = InvoicePaySerializer(data=request.data, context={"invoice": inv, "request": request})
        ser.is_valid(raise_exception=True)
        payment = ser.save()
        inv.refresh_from_db()

        return Response({
            "ok": True,
            "order_id": inv.order_id,            # <-- bill number
            "invoice_id": inv.id,
            "status": inv.status,
            "paid_amount": str(inv.paid_amount),
            "payment_id": payment.id,
            "mode": inv.mode,
            "customer_id": inv.customer_id,
            "cashier_id": inv.cashier_id,
        })
