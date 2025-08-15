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
        return Response({
            "ok": True,
            "invoice_id": inv.id,
            "invoice_number": str(inv.id),   # helpful for clients
            "total": str(inv.total),
            "paid_amount": str(inv.paid_amount),
            "status": inv.status,
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
            "invoice_id": inv.id,
            "invoice_number": str(inv.id),
            "paid_amount": str(inv.paid_amount),
            "status": inv.status,
            "payment_id": payment.id,
        })
