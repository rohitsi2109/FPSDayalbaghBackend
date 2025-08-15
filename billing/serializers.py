from rest_framework import serializers
from .models import BillingInvoice, BillingItem, BillingPayment

class POSItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True)
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)

class POSCreateSerializer(serializers.Serializer):
    items = POSItemSerializer(many=True)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    payment_method = serializers.ChoiceField(
        choices=[c[0] for c in BillingPayment.METHOD_CHOICES], required=False, allow_null=True
    )
    customer_user_id = serializers.IntegerField(required=False, allow_null=True)

    def create(self, validated_data):
        request = self.context.get("request")
        cashier = request.user if request else None

        items = validated_data["items"]
        discount = validated_data.get("discount") or 0
        paid_amount = validated_data.get("paid_amount") or 0
        payment_method = validated_data.get("payment_method") or "cash"
        customer = None

        # Optional link to existing user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        uid = validated_data.get("customer_user_id")
        if uid:
            try:
                customer = User.objects.get(pk=uid)
            except User.DoesNotExist:
                customer = None

        inv = BillingInvoice.objects.create(
            mode=BillingInvoice.MODE_MANUAL,
            status=BillingInvoice.STATUS_OPEN,
            customer=customer,
            cashier=cashier,
            discount=discount,
        )

        for it in items:
            BillingItem.objects.create(
                invoice=inv,
                product_id=it.get("product_id"),
                name=it.get("name", ""),
                qty=it["qty"],
                unit_price=it["unit_price"],
            )

        inv.recalc(save=True)

        # take immediate payment if any
        if paid_amount and paid_amount > 0:
            BillingPayment.objects.create(
                invoice=inv,
                method=payment_method,
                amount=paid_amount,
                status="captured",
                received_by=cashier,
            )

        return inv


class InvoicePaySerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=[c[0] for c in BillingPayment.METHOD_CHOICES])
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    txn_id = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        inv = self.context["invoice"]
        request = self.context.get("request")
        return BillingPayment.objects.create(
            invoice=inv,
            method=validated_data["payment_method"],
            amount=validated_data["amount"],
            txn_id=validated_data.get("txn_id", ""),
            status="captured",
            received_by=request.user if request else None,
        )
