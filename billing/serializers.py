# billing/serializers.py
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import BillingInvoice, BillingItem, BillingPayment
from orders.models import Order, OrderItem, OrderStatus,OrderSource
from products.models import Product


class POSItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)  # required for OrderItem FK
    name = serializers.CharField(required=False, allow_blank=True)
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)


class POSCreateSerializer(serializers.Serializer):
    # Cart
    items = POSItemSerializer(many=True)

    # Discounts & payment
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    paid = serializers.BooleanField(required=False, default=False)

    # Case-insensitive; mapped to Orders.payment_method (COD/ONLINE)
    payment_method = serializers.CharField(required=False, allow_null=True, allow_blank=True, default="cash")

    # Ad hoc customer info (also stored on invoice)
    customer_name = serializers.CharField(required=False, allow_blank=True, default="")
    customer_phone = serializers.CharField(required=False, allow_blank=True, default="")

    # Optional: if provided, link INVOICE to this customer (Order still belongs to cashier)
    customer_user_id = serializers.IntegerField(required=False, allow_null=True)

    # Optional shipping snapshot for Order (POS can use defaults)
    shipping_name = serializers.CharField(required=False, allow_blank=True, default="")
    shipping_phone = serializers.CharField(required=False, allow_blank=True, default="")
    address_line1 = serializers.CharField(required=False, allow_blank=True, default="")
    address_line2 = serializers.CharField(required=False, allow_blank=True, default="")
    city = serializers.CharField(required=False, allow_blank=True, default="")
    state = serializers.CharField(required=False, allow_blank=True, default="")
    pincode = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        pm = (data.get("payment_method") or "cash").lower()
        valid = [c[0] for c in BillingPayment.METHOD_CHOICES]  # online/cash/upi/card/cod
        if pm not in valid:
            raise serializers.ValidationError({"payment_method": f"Unsupported method. Use one of {valid}."})
        data["payment_method"] = pm
        if not data.get("items"):
            raise serializers.ValidationError({"items": "At least one item is required."})
        return data

    def _map_payment_to_order_method(self, pm: str) -> str:
        # Orders.payment_method choices: COD / ONLINE
        pm = (pm or "").lower()
        if pm in {"online", "upi", "card"}:
            return "ONLINE"
        return "COD"  # treat cash & cod as COD

    def _fill_address_defaults(self, data):
        defaults = getattr(settings, "BILLING_POS_DEFAULT_ADDRESS", {
            "address_line1": "POS COUNTER",
            "address_line2": "",
            "city": "Local",
            "state": "Local",
            "pincode": "000000",
        })
        return {
            "shipping_name": (data.get("shipping_name") or data.get("customer_name") or "").strip() or "POS Customer",
            "shipping_phone": (data.get("shipping_phone") or data.get("customer_phone") or "").strip() or "NA",
            "address_line1": data.get("address_line1") or defaults.get("address_line1") or "POS COUNTER",
            "address_line2": data.get("address_line2") or defaults.get("address_line2") or "",
            "city": data.get("city") or defaults.get("city") or "Local",
            "state": data.get("state") or defaults.get("state") or "Local",
            "pincode": data.get("pincode") or defaults.get("pincode") or "000000",
        }

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        cashier = request.user  # The staff user creating the POS bill

        items = validated_data["items"]
        discount = Decimal(validated_data.get("discount") or 0)
        paid_flag = bool(validated_data.get("paid") or False)
        paid_amount = Decimal(validated_data.get("paid_amount") or 0)
        pm_billing = validated_data.get("payment_method") or "cash"
        pm_order = self._map_payment_to_order_method(pm_billing)

        # Optional: link INVOICE to a known customer account (Order still belongs to cashier)
        invoice_customer = None
        uid = validated_data.get("customer_user_id")
        if uid:
            User = get_user_model()
            try:
                invoice_customer = User.objects.get(pk=uid)
            except User.DoesNotExist:
                invoice_customer = None

        addr = self._fill_address_defaults(validated_data)

        # ---- Create ORDER + ITEMS (owned by CASHIER for audit) ----
        order = Order.objects.create(
            user=cashier,
            status=OrderStatus.PENDING,
            source=OrderSource.POS,
            payment_method=pm_order,
            shipping_name=addr["shipping_name"],
            shipping_phone=addr["shipping_phone"],
            address_line1=addr["address_line1"],
            address_line2=addr["address_line2"],
            city=addr["city"],
            state=addr["state"],
            pincode=addr["pincode"],
        )

        # Lock & map products
        product_ids = [int(i["product_id"]) for i in items]
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        pmap = {p.id: p for p in products}

        total = Decimal("0")
        oi_rows = []
        for it in items:
            pid = int(it["product_id"])
            qty = Decimal(it["qty"])
            unit_price = Decimal(it["unit_price"])

            p = pmap.get(pid)
            if not p:
                raise serializers.ValidationError({"items": f"Product {pid} not found."})
            if qty <= 0:
                raise serializers.ValidationError({"items": "Quantity must be >= 1."})
            if p.stock < int(qty):
                raise serializers.ValidationError({"items": f"Insufficient stock for {p.name}."})

            # decrement stock
            p.stock -= int(qty)
            p.save(update_fields=["stock"])

            line_total = qty * unit_price
            total += line_total

            oi_rows.append(OrderItem(
                order=order,
                product=p,
                quantity=int(qty),
                unit_price=unit_price,
                line_total=line_total,
            ))

        OrderItem.objects.bulk_create(oi_rows)

        # keep gross in order.total_amount (matches online flow)
        order.total_amount = total
        if paid_flag or paid_amount >= max(total - discount, Decimal("0")):
            order.status = OrderStatus.PAID
        order.save(update_fields=["total_amount", "status"])

        # ---- Create INVOICE linked to ORDER ----
        inv = BillingInvoice.objects.create(
            mode=BillingInvoice.MODE_MANUAL,
            status=BillingInvoice.STATUS_OPEN,
            order=order,
            customer=invoice_customer,  # optional linkage to a real customer
            cashier=cashier,            # who billed
            discount=discount,
            customer_name=(validated_data.get("customer_name") or addr["shipping_name"]),
            customer_phone=(validated_data.get("customer_phone") or addr["shipping_phone"]),
        )

        # Mirror items to invoice lines
        for it in items:
            pid = int(it["product_id"])
            name = it.get("name", "") or pmap[pid].name
            BillingItem.objects.create(
                invoice=inv,
                product_id=pid,
                name=name,
                qty=it["qty"],
                unit_price=it["unit_price"],
            )

        inv.recalc(save=True)

        # Auto-capture payment if indicated
        if paid_flag and (not paid_amount or paid_amount <= 0):
            paid_amount = inv.total

        if paid_amount and paid_amount > 0:
            BillingPayment.objects.create(
                invoice=inv,
                method=pm_billing,  # "cash"/"upi"/"card"/"online"/"cod"
                amount=paid_amount,
                status="captured",
                received_by=cashier,
            )

        return inv


class InvoicePaySerializer(serializers.Serializer):
    payment_method = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    txn_id = serializers.CharField(required=False, allow_blank=True)

    def validate_payment_method(self, value):
        v = (value or "").lower()
        valid = [c[0] for c in BillingPayment.METHOD_CHOICES]
        if v not in valid:
            raise serializers.ValidationError(f"Unsupported method. Use one of {valid}.")
        return v

    def create(self, validated_data):
        inv: BillingInvoice = self.context["invoice"]
        request = self.context.get("request")
        return BillingPayment.objects.create(
            invoice=inv,
            method=validated_data["payment_method"],
            amount=validated_data["amount"],
            txn_id=validated_data.get("txn_id", ""),
            status="captured",
            received_by=request.user if request else None,
        )
